from fastapi import FastAPI, HTTPException, BackgroundTasks
import os
import requests
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
import time
from datetime import datetime
from pathlib import Path

from .models.schemas import (
    AdvisoryRequest,
    AdvisoryResponse,
    SystemHealth,
    DataSource,
    SendOtpRequest,
    SendOtpResponse,
    VerifyOtpRequest,
    VerifyOtpResponse,
)
from .coordination.coordinator import AdvisoryCoordinator
from .storage.user_store import UserStore
# Optional Twilio client for SMS (if env vars exist)
try:
    from twilio.rest import Client as TwilioClient
except Exception:
    TwilioClient = None  # type: ignore


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


