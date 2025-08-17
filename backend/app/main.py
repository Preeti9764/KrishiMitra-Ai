from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
from datetime import datetime

from .models.schemas import AdvisoryRequest, AdvisoryResponse, SystemHealth, DataSource
from .coordination.coordinator import AdvisoryCoordinator


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

# System startup time for uptime calculation
startup_time = datetime.now()


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


