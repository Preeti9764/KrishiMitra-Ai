from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi import UploadFile, File, Form
import os
import requests
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv
import json
import base64

from .models.schemas import (
    AdvisoryRequest,
    AdvisoryResponse,
    SystemHealth,
    DataSource,
    SendOtpRequest,
    SendOtpResponse,
    VerifyOtpRequest,
    VerifyOtpResponse,
    ChatMessage,
    ChatResponse,
)
from .coordination.coordinator import AdvisoryCoordinator
from .storage.user_store import UserStore
# Optional Twilio client for SMS (if env vars exist)
try:
    from twilio.rest import Client as TwilioClient
except Exception:
    TwilioClient = None  # type: ignore

# Optional OpenAI client for chatbot fallback
try:
    from openai import OpenAI as _OpenAIClient  # type: ignore
except Exception:
    _OpenAIClient = None  # type: ignore


def _normalize_indian(num: str) -> tuple[str, str]:
    """Return (e164, digits) for Indian mobile numbers.
    e164: +91XXXXXXXXXX, digits: 91XXXXXXXXXX without plus.
    """
    n = (num or "").strip().replace(" ", "").replace("-", "")
    if n.startswith("+91"):
        return n, n[1:]
    if n.startswith("0"):
        n = n[1:]
    if n.startswith("91") and len(n) == 12:
        return "+" + n, n
    if n.isdigit() and len(n) == 10:
        return "+91" + n, "91" + n
    # Fallback
    return (n if n.startswith("+") else "+" + n), n.lstrip("+")


def _send_sms_via_provider(phone: str, message: str, otp_code: str | None = None) -> bool:
    """Send SMS via one of providers configured by env.
    Supported: MSG91, Gupshup, Textlocal, Twilio (fallback)."""
    provider = (os.getenv("SMS_PROVIDER") or "").lower().strip()
    e164, digits = _normalize_indian(phone)

    try:
        if provider == "msg91":
            authkey = os.getenv("MSG91_AUTHKEY")
            sender = os.getenv("MSG91_SENDER")
            flow_id = os.getenv("MSG91_FLOW_ID")
            if authkey and sender:
                headers = {"authkey": authkey, "Content-Type": "application/json"}
                if flow_id:
                    url = "https://api.msg91.com/api/v5/flow/"
                    payload = {
                        "flow_id": flow_id,
                        "sender": sender,
                        "recipients": [{
                            "mobiles": digits,
                            # Common variable names; your flow can map to either
                            "OTP": otp_code or message,
                            "TEXT": message
                        }]
                    }
                else:
                    url = "https://api.msg91.com/api/v2/sendsms"
                    payload = {"sender": sender, "route": "4", "country": "91", "sms": [{"message": message, "to": [digits[-10:]]}]}
                r = requests.post(url, json=payload, headers=headers, timeout=8)
                if r.ok:
                    return True

        if provider == "gupshup":
            api_key = os.getenv("GUPSHUP_API_KEY")
            source = os.getenv("GUPSHUP_SOURCE")
            if api_key and source:
                url = "https://api.gupshup.io/sm/api/v1/msg"
                headers = {"apikey": api_key, "Content-Type": "application/x-www-form-urlencoded"}
                data = {"channel": "sms", "source": source, "destination": digits[-10:], "message": message}
                r = requests.post(url, headers=headers, data=data, timeout=8)
                if r.ok:
                    return True

        if provider == "textlocal":
            api_key = os.getenv("TEXTLOCAL_API_KEY")
            sender = os.getenv("TEXTLOCAL_SENDER")
            if api_key and sender:
                url = "https://api.textlocal.in/send/"
                data = {"apikey": api_key, "numbers": digits, "sender": sender, "message": message}
                r = requests.post(url, data=data, timeout=8)
                if r.ok:
                    return True

        # Fallback to Twilio when configured
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        from_number = os.getenv("TWILIO_FROM_NUMBER")
        if all([TwilioClient, account_sid, auth_token, from_number]):
            client = TwilioClient(account_sid, auth_token)  # type: ignore
            client.messages.create(body=message, from_=from_number, to=e164)
            return True
    except Exception as exc:
        print(f"[SMS-ERROR] provider={provider} err={exc}")

    return False


app = FastAPI(
    title="Multi-Agent AI Farm Advisory System", 
    version="2.0.0",
    description="Enhanced farm advisory system with 7 specialized AI agents"
)

# Load environment variables from .env next to this file (robust to CWD)
_loaded_local = False
try:
    _ENV_PATH = Path(__file__).resolve().parent / ".env"
    _loaded_local = load_dotenv(dotenv_path=_ENV_PATH)
except Exception:
    _loaded_local = False
if not _loaded_local:
    # Fallback: load .env from current working directory
    load_dotenv()

# Allow local dev frontends by default
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

coordinator = AdvisoryCoordinator()
user_store = UserStore(Path(__file__).resolve().parent.parent / "data" / "users.json")

# System startup time for uptime calculation
startup_time = datetime.now()

# In-memory stores for demo auth/OTP functionality
otp_store = {}  # phone -> { code: str, expires_at: datetime }
phone_to_farmer = {}  # phone -> { farmer_id: str, name: str }


@app.get("/")
async def root():
    """Redirect to API documentation"""
    return RedirectResponse(url="/docs")


@app.get("/api/health")
def health_check() -> dict:
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }


@app.get("/api/system/health", response_model=SystemHealth)
def system_health() -> SystemHealth:
    """Detailed system health check"""
    agent_status = coordinator.get_agent_status()
    
    # Calculate uptime
    uptime = datetime.now() - startup_time
    uptime_percentage = 99.9  # Mock uptime for demo
    
    # Mock data sources
    data_sources = [
        DataSource(
            name="NASA POWER API",
            type="weather",
            url="https://power.larc.nasa.gov/",
            last_updated=datetime.now(),
            reliability_score=0.95
        ),
        DataSource(
            name="AGMARKNET",
            type="market",
            url="https://agmarknet.gov.in/",
            last_updated=datetime.now(),
            reliability_score=0.90
        ),
        DataSource(
            name="Soil Health Database",
            type="soil",
            url="https://soilhealth.dac.gov.in/",
            last_updated=datetime.now(),
            reliability_score=0.85
        )
    ]
    
    return SystemHealth(
        status="operational",
        agents_online=agent_status["agents_online"],
        total_agents=agent_status["total_agents"],
        data_sources=data_sources,
        response_time_ms=150.0,  # Mock response time
        uptime_percentage=uptime_percentage
    )


@app.get("/api/agents/status")
def agent_status() -> dict:
    """Get status of all agents"""
    return coordinator.get_agent_status()


@app.get("/api/agents/{agent_name}/info")
def agent_info(agent_name: str) -> dict:
    """Get detailed information about a specific agent"""
    agents = coordinator.agents
    
    if agent_name not in agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
    
    agent = agents[agent_name]
    
    # Get agent-specific information
    agent_info = {
        "name": agent_name,
        "type": agent.__class__.__name__,
        "description": agent.__doc__ or "AI agent for farm advisory",
        "status": "online",
        "capabilities": getattr(agent, 'capabilities', []),
        "data_sources": getattr(agent, 'data_sources', [])
    }
    
    return agent_info


@app.get("/api/coordination/rules")
def conflict_rules() -> dict:
    """Get conflict resolution rules"""
    return coordinator.get_conflict_rules()


@app.get("/api/user/by-id/{farmer_id}")
def get_user_by_id(farmer_id: str) -> dict:
    rec = user_store.get_by_farmer_id(farmer_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Farmer not found")
    return rec


@app.get("/api/user/by-phone/{phone}")
def get_user_by_phone(phone: str) -> dict:
    e164, _ = _normalize_indian(phone)
    farmer_id = user_store.get_farmer_id_by_phone(e164)
    if not farmer_id:
        raise HTTPException(status_code=404, detail="No farmer mapped to this phone")
    rec = user_store.get_by_farmer_id(farmer_id)
    return rec or {"farmer_id": farmer_id}


# ========== AUTH / OTP ENDPOINTS (MVP) ==========
@app.post("/api/auth/send-otp", response_model=SendOtpResponse)
def send_otp(payload: SendOtpRequest) -> SendOtpResponse:
    """Send an OTP to the provided phone number. For MVP, we generate a code and log it to server stdout.
    In production, integrate an SMS provider (e.g., Twilio, AWS SNS, Gupshup)."""
    try:
        phone = payload.phone.strip()
        if not phone:
            raise HTTPException(status_code=400, detail="Phone is required")

        # Generate a 4-digit OTP for MVP
        import random
        code = f"{random.randint(1000, 9999)}"

        # Set TTL 5 minutes
        expires_at = datetime.now() + timedelta(minutes=5)
        otp_store[phone] = {"code": code, "expires_at": expires_at}

        # If this is a new phone and name provided, tentatively store name (farmer id after verification)
        if payload.name:
            phone_to_farmer.setdefault(phone, {"farmer_id": None, "name": payload.name})
            # Also persist a draft record to disk store without farmer_id yet

        # Try to send via configured provider (MSG91/Gupshup/Textlocal/Twilio)
        sent_via_sms = _send_sms_via_provider(phone, f"Your Farm Advisory OTP is {code}. It expires in 5 minutes.")

        # Always log for dev visibility
        print(f"[OTP] Phone={phone} Code={code} Expires={expires_at} SMS={sent_via_sms}")

        return SendOtpResponse(success=True, message="OTP sent successfully", expires_at=expires_at, dev_code=(None if sent_via_sms else code))
    except HTTPException:
        raise
    except Exception as exc:
        print(f"Error sending OTP: {exc}")
        raise HTTPException(status_code=500, detail="Failed to send OTP")


from datetime import timedelta


@app.post("/api/auth/verify-otp", response_model=VerifyOtpResponse)
def verify_otp(payload: VerifyOtpRequest) -> VerifyOtpResponse:
    """Verify an OTP for a phone number. If valid, return or create a farmer_id bound to this phone."""
    try:
        phone = payload.phone.strip()
        otp_record = otp_store.get(phone)
        if not otp_record:
            raise HTTPException(status_code=400, detail="No OTP requested for this phone")

        if datetime.now() > otp_record["expires_at"]:
            del otp_store[phone]
            raise HTTPException(status_code=400, detail="OTP expired. Please request a new one")

        if payload.otp != otp_record["code"]:
            raise HTTPException(status_code=400, detail="Invalid OTP")

        # OTP valid → bind or create farmer profile
        mapping = phone_to_farmer.get(phone)
        e164, _digits = _normalize_indian(phone)
        farmer_id = None
        # Check persistent store first
        existing_id = user_store.get_farmer_id_by_phone(e164)
        if existing_id:
            farmer_id = existing_id
            mapping = mapping or {"farmer_id": existing_id, "name": None}
        if not mapping or not mapping.get("farmer_id"):
            farmer_id = farmer_id or f"farmer_{int(time.time())}"
            if not mapping:
                mapping = {"farmer_id": farmer_id, "name": "Farmer"}
            else:
                mapping["farmer_id"] = farmer_id
            phone_to_farmer[phone] = mapping
        else:
            farmer_id = mapping["farmer_id"]

        # Persist phone→farmer mapping and name
        user_store.bind_phone(farmer_id, e164)
        try:
            user_store.upsert_farmer(farmer_id, name=mapping.get("name"), phone_e164=e164)
        except Exception:
            pass

        # Clean up used OTP
        del otp_store[phone]

        return VerifyOtpResponse(
            success=True,
            message="OTP verified",
            farmer_id=farmer_id,
            name=mapping.get("name"),
            phone=phone,
        )
    except HTTPException:
        raise
    except Exception as exc:
        print(f"Error verifying OTP: {exc}")
        raise HTTPException(status_code=500, detail="Failed to verify OTP")


@app.post("/api/advisory", response_model=AdvisoryResponse)
async def get_advisory(payload: AdvisoryRequest):
    """Get comprehensive farm advisory from all agents"""
    start_time = time.time()
    
    try:
        # Validate request
        if not payload.profile.farmer_id:
            raise HTTPException(status_code=400, detail="Farmer ID is required")
        
        if not payload.profile.crop:
            raise HTTPException(status_code=400, detail="Crop type is required")
        
        # Persist latest profile against farmer_id for future sessions
        try:
            user_store.save_profile(payload.profile.farmer_id, payload.profile.dict())
        except Exception as _:
            pass

        # Get advisory plan
        plan = await coordinator.build_advisory_plan(payload)
        
        # Calculate response time
        response_time = (time.time() - start_time) * 1000
        
        # Add response time to plan
        plan.response_time_ms = response_time
        
        return plan
        
    except HTTPException:
        raise
    except Exception as exc:
        # Log the error for debugging
        print(f"Error generating advisory: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error while generating advisory")


@app.post("/api/advisory/quick")
async def quick_advisory(payload: AdvisoryRequest):
    """Get quick advisory from core agents only (irrigation, fertilizer, pest, market)"""
    start_time = time.time()
    
    try:
        # Create a simplified request with only core agents
        core_agents = ["irrigation", "fertilizer", "pest", "market"]
        
        # Get recommendations from core agents only
        agent_outputs = []
        for agent_name in core_agents:
            if agent_name in coordinator.agents:
                try:
                    result = await coordinator.agents[agent_name].recommend(payload)
                    agent_outputs.append(result)
                except Exception as e:
                    print(f"Error in {agent_name} agent: {e}")
                    # Create fallback
                    fallback = coordinator._create_fallback_recommendation(agent_name, payload)
                    agent_outputs.append(fallback)
        
        # Simple unified plan
        unified_plan = []
        for rec in sorted(agent_outputs, key=lambda r: r.priority, reverse=True):
            unified_plan.extend(rec.tasks[:2])  # Top 2 tasks per agent
        
        # Apply language translation if requested
        if payload.language != "en":
            # Import coordinator for translation
            from .coordination.coordinator import AdvisoryCoordinator
            coordinator = AdvisoryCoordinator()
            
            # Translate unified plan
            unified_plan = [coordinator._translate_text(task, payload.language) for task in unified_plan]
            
            # Translate agent outputs
            for rec in agent_outputs:
                rec.summary = coordinator._translate_text(rec.summary, payload.language)
                rec.explanation = coordinator._translate_text(rec.explanation, payload.language)
                rec.tasks = [coordinator._translate_text(task, payload.language) for task in rec.tasks]
        
        response_time = (time.time() - start_time) * 1000
        
        return AdvisoryResponse(
            farmer_id=payload.profile.farmer_id,
            crop=payload.profile.crop,
            horizon_days=payload.horizon_days,
            generated_at=datetime.now(),
            recommendations=agent_outputs,
            unified_plan=unified_plan[:8],  # Limit to 8 tasks
            confidence_overall=0.8,
            risk_assessment={"overall_risk_level": "low"},
            response_time_ms=response_time
        )
        
    except Exception as exc:
        print(f"Error generating quick advisory: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/crops/supported")
def supported_crops() -> dict:
    """Get list of supported crops"""
    return {
        "crops": [
            {"name": "wheat", "scientific_name": "Triticum aestivum", "season": "Rabi"},
            {"name": "rice", "scientific_name": "Oryza sativa", "season": "Kharif"},
            {"name": "maize", "scientific_name": "Zea mays", "season": "Kharif"},
            {"name": "cotton", "scientific_name": "Gossypium hirsutum", "season": "Kharif"},
            {"name": "sugarcane", "scientific_name": "Saccharum officinarum", "season": "Year-round"},
            {"name": "pulses", "scientific_name": "Various", "season": "Rabi/Kharif"},
            {"name": "oilseeds", "scientific_name": "Various", "season": "Kharif"},
            {"name": "vegetables", "scientific_name": "Various", "season": "Year-round"}
        ]
    }


@app.get("/api/soil/types")
def soil_types() -> dict:
    """Get supported soil types"""
    return {
        "soil_types": [
            {"name": "loam", "description": "Well-balanced soil with good drainage"},
            {"name": "clay", "description": "Heavy soil with high water retention"},
            {"name": "sandy", "description": "Light soil with good drainage"},
            {"name": "silt", "description": "Fine-textured soil with moderate drainage"},
            {"name": "clay_loam", "description": "Mixture of clay and loam"},
            {"name": "sandy_loam", "description": "Mixture of sandy and loam"}
        ]
    }


@app.get("/api/growth/stages")
def growth_stages() -> dict:
    """Get crop growth stages"""
    return {
        "growth_stages": [
            {"name": "sowing", "description": "Seed planting stage"},
            {"name": "germination", "description": "Seed sprouting stage"},
            {"name": "vegetative", "description": "Leaf and stem growth"},
            {"name": "tillering", "description": "Branch development (for cereals)"},
            {"name": "booting", "description": "Flower bud formation"},
            {"name": "flowering", "description": "Flower development"},
            {"name": "grain_filling", "description": "Grain development"},
            {"name": "maturity", "description": "Crop ripening"},
            {"name": "harvesting", "description": "Crop collection"}
        ]
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )


# For `python -m uvicorn backend.app.main:app --reload`
def get_app() -> FastAPI:
    return app



# ==================== DISEASE DETECTION (MVP) ====================
try:
    import numpy as _np  # type: ignore
    from PIL import Image as _Image  # type: ignore
except Exception:
    _np = None  # type: ignore
    _Image = None  # type: ignore


def _analyze_leaf_image(file_bytes: bytes) -> Dict[str, Any]:
    """Very lightweight heuristic analyzer for leaf disease detection.
    Not a real ML model. Uses simple color statistics to guess conditions.
    Returns a dict with keys: disease, confidence, stats, suggestions.
    """
    if _np is None or _Image is None:
        return {
            "disease": "unknown",
            "confidence": 0.3,
            "stats": {},
            "suggestions": [
                "Enable Pillow and NumPy for on-device analysis (install 'pillow').",
                "Alternatively, consult agronomist if disease suspected.",
            ],
        }

    try:
        img = _Image.open(io.BytesIO(file_bytes)).convert("RGB")  # type: ignore
    except Exception:
        return {
            "disease": "invalid_image",
            "confidence": 0.0,
            "stats": {},
            "suggestions": ["Please upload a valid leaf image (JPG/PNG)."],
        }

    # Resize small for faster stats
    img_small = img.resize((256, 256))
    arr = _np.asarray(img_small).astype("float32")  # shape (H, W, 3)
    if arr.ndim != 3 or arr.shape[2] != 3:
        return {
            "disease": "invalid_image",
            "confidence": 0.0,
            "stats": {},
            "suggestions": ["Please upload a valid RGB leaf image."],
        }

    r = arr[:, :, 0]
    g = arr[:, :, 1]
    b = arr[:, :, 2]

    # Basic color ratios
    green_ratio = float((g > r) & (g > b)).sum() / float(arr.shape[0] * arr.shape[1])
    brown_mask = (r > 80) & (g > 40) & (b < 60)
    brown_ratio = float(brown_mask.sum()) / float(arr.shape[0] * arr.shape[1])
    yellow_mask = (r > 170) & (g > 170) & (b < 130)
    yellow_ratio = float(yellow_mask.sum()) / float(arr.shape[0] * arr.shape[1])

    # Edge/spot proxy via channel variance
    variability = float(arr.var() / (255.0 ** 2))

    # Heuristic rules (very rough, for demo only)
    guess = "healthy"
    confidence = 0.6
    reasons: List[str] = []

    if brown_ratio > 0.08 and variability > 0.02:
        guess = "leaf_blight"
        confidence = min(0.9, 0.5 + brown_ratio * 2.0)
        reasons.append("brown lesions with mottling pattern detected")
    elif yellow_ratio > 0.08 and green_ratio < 0.6:
        guess = "nutrient_deficiency"
        confidence = min(0.85, 0.5 + yellow_ratio * 1.5)
        reasons.append("yellowing/chlorosis areas detected")
    elif variability > 0.03 and green_ratio < 0.6:
        guess = "rust_or_spot"
        confidence = 0.7
        reasons.append("spotty texture detected")
    else:
        reasons.append("no strong disease patterns detected")

    suggestions_map = {
        "healthy": [
            "Leaf appears healthy. Continue routine scouting and balanced irrigation.",
            "Avoid overwatering and ensure good airflow to prevent fungal growth.",
        ],
        "leaf_blight": [
            "Remove heavily affected leaves to limit spread.",
            "Apply recommended fungicide as per local guidelines.",
            "Improve airflow and avoid overhead irrigation in evenings.",
        ],
        "nutrient_deficiency": [
            "Conduct a quick soil test for NPK and micronutrients.",
            "Apply balanced fertilizer or foliar feed based on deficiency.",
        ],
        "rust_or_spot": [
            "Scout nearby plants for similar lesions.",
            "Apply targeted fungicide if spread is increasing.",
            "Avoid leaf wetness for long durations.",
        ],
        "unknown": [
            "Unable to analyze image. Re-take photo in good light, single leaf filling frame.",
        ],
        "invalid_image": [
            "Please upload a clear photo of a single leaf against plain background.",
        ],
    }

    stats = {
        "green_ratio": round(green_ratio, 4),
        "brown_ratio": round(brown_ratio, 4),
        "yellow_ratio": round(yellow_ratio, 4),
        "variability": round(variability, 5),
        "reasons": reasons,
    }

    return {
        "disease": guess,
        "confidence": round(confidence, 2),
        "stats": stats,
        "suggestions": suggestions_map.get(guess, []),
    }


import io  # placed after FastAPI app to avoid circular issues


@app.get("/api/disease/labels")
def disease_labels() -> Dict[str, Any]:
    return {
        "supported_crops": [
            "wheat",
            "rice",
            "maize",
            "cotton",
            "vegetables",
        ],
        "possible_conditions": [
            "healthy",
            "leaf_blight",
            "rust_or_spot",
            "nutrient_deficiency",
        ],
    }


@app.post("/api/disease/diagnose")
async def diagnose_disease(
    crop: str = Form("generic"),
    language: str = Form("en"),
    image: UploadFile = File(...),
):
    try:
        if not _OpenAIClient:
            raise HTTPException(status_code=500, detail="OpenAI client not available on server")
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")

        # Read and downscale image to reduce payload size
        content = await image.read()
        try:
            from PIL import Image as _PILImage  # type: ignore
            import io as _io
            with _PILImage.open(_io.BytesIO(content)) as _img:
                _img = _img.convert("RGB")
                _img.thumbnail((1024, 1024))
                _buf = _io.BytesIO()
                _img.save(_buf, format="JPEG", quality=85)
                content = _buf.getvalue()
            ctype = "image/jpeg"
        except Exception:
            ctype = image.content_type or "image/jpeg"

        b64 = base64.b64encode(content).decode("utf-8")

        client = _OpenAIClient(api_key=api_key)
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        sys = (
            "You are an expert agronomist. Analyze leaf images for crop diseases. "
            "Be practical and safe. Respond ONLY in valid JSON with keys: "
            "disease (snake_case), confidence (0..1), reasons (list of strings), suggestions (list of strings). "
            "Use the user's requested language for reasons and suggestions."
        )
        user_text = (
            f"Language={language}. Crop={crop}. "
            "Identify likely disease and give actionable suggestions."
        )
        messages = [
            {"role": "system", "content": sys},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_text},
                    {"type": "image_url", "image_url": {"url": f"data:{ctype};base64,{b64}"}},
                ],
            },
        ]
        try:
            comp = client.chat.completions.create(
                model=model,
                messages=messages,  # type: ignore[arg-type]
                temperature=0.2,
                max_tokens=400,
            )
            raw = (comp.choices[0].message.content or "").strip()
        except Exception as oai_exc:
            print(f"OpenAI vision call failed: {oai_exc}")
            raw = "{\n  \"disease\": \"unknown\",\n  \"confidence\": 0.0,\n  \"reasons\": [],\n  \"suggestions\": [\"Unable to analyze image right now. Please try again.\"]\n}"

        parsed = None
        try:
            parsed = json.loads(raw)
        except Exception:
            import re
            m = re.search(r"\{[\s\S]*\}", raw)
            if m:
                parsed = json.loads(m.group(0))

        if not isinstance(parsed, dict):
            parsed = {"disease": "unknown", "confidence": 0.0, "reasons": [], "suggestions": ["Could not parse AI response."]}

        result = {
            "disease": str(parsed.get("disease") or "unknown"),
            "confidence": float(parsed.get("confidence") or 0.0),
            "stats": {"reasons": parsed.get("reasons") or []},
            "suggestions": parsed.get("suggestions") or [],
        }

        # Translate to requested language if necessary
        if language != "en":
            try:
                result["suggestions"] = [coordinator._translate_text(s, language) for s in (result.get("suggestions") or [])]
                stats = result.get("stats") or {}
                reasons = stats.get("reasons") or []
                stats["reasons"] = [coordinator._translate_text(r, language) for r in reasons]
                result["stats"] = stats
            except Exception:
                pass

        return {"crop": crop, **result}
    except Exception as exc:
        print(f"Disease diagnose error: {exc}")
        raise HTTPException(status_code=500, detail="Failed to analyze image")


# ==================== SIMPLE MULTILINGUAL CHATBOT (MVP) ====================
@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatMessage) -> ChatResponse:
    """A lightweight, rule-based chatbot that routes to agents when possible and
    answers in the requested language using best-effort translation.
    """
    try:
        text = (payload.message or "").strip()
        language = payload.language or "en"
        topic = "general"
        lower = text.lower()

        # Try knowledge base first
        from .knowledge_base import get_faq_answer
        kb_answer = get_faq_answer(text)
        if kb_answer:
            reply_text = kb_answer
            if language != "en":
                try:
                    reply_text = coordinator._translate_text(reply_text, language)
                except Exception:
                    pass
            return ChatResponse(reply=reply_text, topic="faq", language=language)
        
        # If no FAQ answer found, try OpenAI fallback first
        api_key = os.getenv("OPENAI_API_KEY")
        if _OpenAIClient and api_key:
            try:
                client = _OpenAIClient(api_key=api_key)
                model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                sys = (
                    "You are KrishiMitra, an expert agricultural assistant for Indian farmers. "
                    "Your job is to answer farming questions with practical, region-specific, and actionable advice. "
                    "Always use reliable sources and best practices for Indian agriculture. "
                    "If the user asks about crops, pests, irrigation, fertilizer, weather, market, finance, or government schemes, provide detailed, step-by-step guidance. "
                    "Be concise, clear, and safe. If you don't know, say so. Always respond in the user's requested language."
                )
                user_ctx = []
                if payload.crop:
                    user_ctx.append(f"crop={payload.crop}")
                if payload.state:
                    user_ctx.append(f"state={payload.state}")
                if payload.district:
                    user_ctx.append(f"district={payload.district}")
                if payload.irrigation_type:
                    user_ctx.append(f"irrigation={payload.irrigation_type}")
                ctx_str = ("; ".join(user_ctx)) or "no extra context"
                messages = [
                    {"role": "system", "content": sys},
                    {"role": "user", "content": f"Language={language}. Context: {ctx_str}. Question: {text}"},
                ]
                comp = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=400,
                )
                reply_text = (comp.choices[0].message.content or "").strip()
                return ChatResponse(reply=reply_text, topic="openai", language=language)
            except Exception as e:
                print(f"OpenAI fallback failed: {e}")
                # Continue to agent routing if OpenAI fails

        # Expanded keyword routing for farming topics
        if any(k in lower for k in ["irrigation", "water", "moisture", "drip", "sprinkler", "canal", "rainfed"]):
            topic = "irrigation"
        elif any(k in lower for k in ["fertilizer", "nutrient", "npk", "urea", "dap", "manure", "compost", "soil health"]):
            topic = "fertilizer"
        elif any(k in lower for k in ["pest", "insect", "disease", "fungus", "blight", "rust", "aphid", "borer", "mite", "trap"]):
            topic = "pest"
        elif any(k in lower for k in ["market", "price", "sell", "msp", "scheme", "loan", "mandi", "profit", "storage", "demand", "supply"]):
            topic = "market"
        elif any(k in lower for k in ["weather", "rain", "wind", "heat", "storm", "drought", "flood", "hail", "cyclone", "temperature"]):
            topic = "weather_risk"
        elif any(k in lower for k in ["seed", "variety", "crop selection", "sowing", "harvest", "yield", "season", "recommendation"]):
            topic = "seed_crop"
        elif any(k in lower for k in ["finance", "policy", "insurance", "subsidy", "government", "credit", "pm-kisan", "bima", "loan"]):
            topic = "finance_policy"

        # Build a minimal AdvisoryRequest using stored profile if available
        minimal_request = AdvisoryRequest(
            profile={
                "farmer_id": payload.farmer_id or "chat_farmer",
                "name": payload.name or "Farmer",
                "location_lat": payload.location_lat or 28.6,
                "location_lon": payload.location_lon or 77.2,
                "district": payload.district or "",
                "state": payload.state or "",
                "farm_size_hectares": payload.farm_size_hectares or 1.0,
                "crop": payload.crop or "wheat",
                "growth_stage": payload.growth_stage or None,
                "soil_type": payload.soil_type or None,
                "irrigation_type": payload.irrigation_type or None,
                "farming_practice": payload.farming_practice or None,
            },
            sensors=None,
            weather=None,
            market=None,
            soil_health=None,
            horizon_days=7,
            language="en",  # run agents in English
        )

        # Route to specific agent when relevant, else provide general guidance
        reply_lines: List[str] = []
        used_openai = False
        agent_success = False
        
        try:
            if topic in coordinator.agents:
                agent = coordinator.agents[topic]
                rec = await agent.recommend(minimal_request)
                if rec and rec.summary and rec.summary.strip():
                    reply_lines.append(f"{rec.summary}")
                    for t in rec.tasks[:3]:
                        if t and t.strip():
                            reply_lines.append(f"- {t}")
                    agent_success = True
                else:
                    print(f"Agent {topic} returned empty or invalid response")
            
            # If no specific agent or agent failed, try to provide topic-specific guidance
            if not agent_success:
                topic_guidance = {
                    "irrigation": "For irrigation, check soil moisture daily. Water early morning or evening. Avoid overwatering which can cause root rot.",
                    "fertilizer": "Apply fertilizers based on soil test results. Use balanced NPK for most crops. Apply during active growth periods.",
                    "pest": "Scout fields regularly for pest signs. Use integrated pest management. Apply treatments only when threshold levels are reached.",
                    "market": "Monitor local market prices. Consider storage options for better prices. Plan harvest timing based on market demand.",
                    "weather_risk": "Check weather forecasts daily. Prepare for extreme weather events. Adjust farming activities based on predictions.",
                    "seed_crop": "Choose varieties suited to your climate and soil. Use certified seeds. Follow recommended planting dates.",
                    "finance_policy": "Check government schemes like PM-KISAN. Maintain good credit history. Apply for crop insurance."
                }
                
                guidance = topic_guidance.get(topic, "I can help with irrigation, fertilizer use, pest control, weather risks, and markets.")
                reply_lines.append(guidance)
                
        except Exception as e:
            print(f"Chat agent error: {e}")
            # Fall back to OpenAI if configured
            api_key = os.getenv("OPENAI_API_KEY")
            if _OpenAIClient and api_key:
                try:
                    client = _OpenAIClient(api_key=api_key)
                    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                    sys = (
                        "You are KrishiMitra, an expert agricultural assistant for Indian farmers. "
                        "Your job is to answer farming questions with practical, region-specific, and actionable advice. "
                        "Always use reliable sources and best practices for Indian agriculture. "
                        "If the user asks about crops, pests, irrigation, fertilizer, weather, market, finance, or government schemes, provide detailed, step-by-step guidance. "
                        "Be concise, clear, and safe. If you don't know, say so. Always respond in the user's requested language."
                    )
                    user_ctx = []
                    if payload.crop:
                        user_ctx.append(f"crop={payload.crop}")
                    if payload.state:
                        user_ctx.append(f"state={payload.state}")
                    if payload.district:
                        user_ctx.append(f"district={payload.district}")
                    if payload.irrigation_type:
                        user_ctx.append(f"irrigation={payload.irrigation_type}")
                    ctx_str = ("; ".join(user_ctx)) or "no extra context"
                    messages = [
                        {"role": "system", "content": sys},
                        {"role": "user", "content": f"Language={language}. Context: {ctx_str}. Question: {text}"},
                    ]
                    comp = client.chat.completions.create(
                        model=model,
                        messages=messages,  # type: ignore[arg-type]
                        temperature=0.3,
                        max_tokens=400,
                    )
                    reply_text = (comp.choices[0].message.content or "").strip()
                    used_openai = True
                    return ChatResponse(reply=reply_text, topic=topic, language=language)
                except Exception as ee:
                    print(f"OpenAI fallback failed: {ee}")
            # If OpenAI not available or failed, keep a graceful message
            reply_lines.append("Sorry, I could not fetch expert advice right now.")

        # If OpenAI wasn't used, finalize rule-based reply
        if not used_openai:
            if text:
                reply_lines.append("")
                reply_lines.append(f"Question understood (approx.): '{text[:120]}'")
            reply_text = "\n".join(reply_lines).strip()
            if language != "en":
                try:
                    reply_text = coordinator._translate_text(reply_text, language)
                except Exception:
                    pass
            return ChatResponse(reply=reply_text, topic=topic, language=language)
    except HTTPException:
        raise
    except Exception as exc:
        print(f"Chat error: {exc}")
        raise HTTPException(status_code=500, detail="Chat failed")

