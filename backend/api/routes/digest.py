from fastapi import APIRouter
from backend.services.news_service import NewsService
from backend.config.monitor import SystemMonitor
from backend.api.schemas.api_models import UsageUpdateRequest

router = APIRouter(prefix="/digest", tags=["digest"])

@router.get("")
def get_daily_digest():
    latest = NewsService.get_latest_digest()
    if not latest:
        return {"data": None, "message": "No digest available"}
    
    return {
        "date": latest.get("date"),
        "generated_at": latest.get("generated_at"),
        "headline": latest.get("headline"),
        "top_stories": latest.get("top_stories", []),
        "other_news": latest.get("other_news", {}),
        "stats": latest.get("pipeline_stats", {}),
        "categories": list(latest.get("other_news", {}).keys()),
    }

@router.get("/system/status")
def get_system_status():
    return SystemMonitor.get_stats()

@router.post("/system/usage")
def update_system_usage(req: UsageUpdateRequest):
    SystemMonitor.update_usage(req.count)
    return {"status": "ok"}
