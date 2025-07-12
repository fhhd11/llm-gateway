from litellm import acompletion
from litellm import completion
from app.config import settings
from app.monitoring.callbacks import track_cost_callback

# Setup LiteLLM
litellm.success_callback = [track_cost_callback]  # From monitoring

# Example fallback router (configure as needed)
litellm.Router(
    model_list=[
        {"model_name": "gpt-4", "litellm_params": {"model": "openai/gpt-4"}},
        {"model_name": "claude-3", "litellm_params": {"model": "anthropic/claude-3-sonnet"}},
    ]
)
router = litellm.Router(...)

async def call_llm(model: str, messages: list, stream: bool = False):
    response = await router.acompletion(model=model, messages=messages, stream=stream)  # Использует router для fallbacks
    return response