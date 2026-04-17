from fastapi import APIRouter, HTTPException
from backend.api.schemas.api_models import SearchQuery
from backend.services.news_service import NewsService

router = APIRouter(prefix="/search", tags=["search"])

@router.post("")
def search_articles(req: SearchQuery):
    retriever = NewsService.get_retriever()
    try:
        results = retriever.search(req.query, top_k=req.top_k, category_filter=req.category_filter)
        return {
             "results": [{
                 "url": r.url,
                 "title": r.title,
                 "source": r.source,
                 "category": r.category,
                 "published_at": r.published_at,
                 "summary": r.summary,
                 "key_points": r.key_points,
                 "score": r.score
             } for r in results]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
