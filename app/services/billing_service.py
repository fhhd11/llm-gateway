from supabase import Client
from fastapi import Depends
from app.dependencies import get_supabase_client
from app.utils.exceptions import InsufficientFundsError
from app.config import settings

async def get_balance(db: Client, user_id: str) -> float:
    result = db.table("balances").select("balance").eq("user_id", user_id).execute()
    if not result.data:
        return 0.0
    return result.data[0]["balance"]

async def update_balance(db: Client, user_id: str, amount: float, description: str):
    # Atomic update: Use Supabase RPC if setup, else transaction
    current_balance = await get_balance(db, user_id)
    new_balance = current_balance + amount
    if new_balance < 0:
        raise InsufficientFundsError("Insufficient balance")
    
    # Update balance
    db.table("balances").upsert({"user_id": user_id, "balance": new_balance}).execute()
    
result = db.table("balances").select("balance").eq("user_id", user_id).execute()
if result.data[0]["balance"] < 0:
    # Rollback logic if needed, but for now raise (though unlikely due to pre-check)
    raise InsufficientFundsError("Balance went negative after update")

    # Insert transaction
    db.table("transactions").insert({
        "user_id": user_id,
        "amount": amount,
        "type": "debit" if amount < 0 else "credit",
        "description": description
    }).execute()

# Estimated cost func (simplified, base on tokens est)
def estimate_cost(model: str, input_tokens: int) -> float:
    # Dummy prices, adjust per model
    price_per_token = 0.00002  # e.g., for GPT-4
    return input_tokens * price_per_token * (1 + settings.lite_llm_markup)