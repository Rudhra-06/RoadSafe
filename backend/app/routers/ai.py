from fastapi import APIRouter, Depends, HTTPException, status
from app.core.dependencies import get_current_user_claims
from app.schemas.ai import AIAskRequest, AIAskResponse
from app.services.ai_knowledge_service import AIKnowledgeService

router = APIRouter(prefix="/ai", tags=["AI Assistant"])


@router.post("/ask", response_model=AIAskResponse)
async def ask_roadsafe_assistant(
    payload: AIAskRequest,
    claims=Depends(get_current_user_claims)
):
    """
    RAG-grounded RoadSafe Knowledge Assistant query.
    Retrieves verified emergency, service, and safety information from ChromaDB.
    """
    try:
        result = await AIKnowledgeService.ask_assistant(
            question=payload.question,
            role=claims.get("role", "CUSTOMER")
        )
        return AIAskResponse(
            answer=result["answer"],
            sources=result["sources"],
            grounded=result["grounded"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to process assistant query: {str(e)}"
        )
