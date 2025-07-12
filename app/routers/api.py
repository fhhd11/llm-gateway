from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import StreamingResponse
from app.models.schemas import ChatCompletionRequest, ChatCompletionResponse
from app.services.litellm_service import call_llm
from app.services.billing_service import estimate_cost, update_balance, get_balance
from app.dependencies import get_current_user, get_supabase_client
from app.config import settings
from supabase import Client
from app.utils.exceptions import InsufficientFundsError
from app.main import app

router = APIRouter()

async def get_user_key(request: Request):
    user_id = await get_current_user(authorization=request.headers.get("Authorization"))
    return user_id

@router.post("/v1/chat/completions")
@app.state.limiter.limit("10/minute", key_func=get_user_key)  # 10 req/min per user
async def chat_completions(
    request: ChatCompletionRequest,
    user_id: str = Depends(get_current_user),
    db: Client = Depends(get_supabase_client)
):
    # Estimate tokens (simplified)
    input_tokens = sum(len(msg.content) for msg in request.messages) // 4  # Rough est

    est_cost = estimate_cost(request.model, input_tokens)
    if await get_balance(db, user_id) < est_cost:
        raise InsufficientFundsError("Insufficient balance")

    try:
        response = await call_llm(request.model, [msg.dict() for msg in request.messages], request.stream)
        
        if not request.stream:
            # Non-stream: Update billing after
            actual_cost = response.usage.total_tokens * 0.00002 * (1 + settings.lite_llm_markup)  # Adjust
            await update_balance(db, user_id, -actual_cost, f"LLM call: {request.model}")
            return ChatCompletionResponse(choices=response.choices, usage=response.usage)
        
        # Streaming
        async def stream_generator():
        total_tokens = 0
        async for chunk in response:  # Предполагая async iterator от acompletion
            total_tokens += 1  # Все еще rough, но OK
            yield chunk
        # Теперь await возможен в async gen
        await update_balance(db, user_id, -actual_cost, f"LLM call: {request.model}")

    return StreamingResponse(stream_generator(), media_type="text/event-stream"