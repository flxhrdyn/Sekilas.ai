from fastapi import APIRouter, HTTPException
from backend.api.schemas.api_models import QAQuery
from backend.services.news_service import NewsService

router = APIRouter(prefix="/qa", tags=["qa"])

@router.post("")
def qa_agent(req: QAQuery):
    qa_chain = NewsService.get_qa_chain()
    try:
        ans = qa_chain.answer(req.question)
        return {
            "answer": ans.answer, 
            "sources": ans.sources,
            "retrieved": [{
                 "url": r.url,
                 "title": r.title,
                 "source": r.source
            } for r in ans.retrieved]
        }
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))
