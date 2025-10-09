import os
from decimal import Decimal

# 단가(예시): 1K 토큰당 USD
# 실제 가격과 다를 수 있으니 OPENAI_PRICE_PROMPT_1K / OPENAI_PRICE_COMPLETION_1K 로 재설정 가능
# 나중에 환경변수로 설정해보기
PRICES = {
  "gpt-4o-mini": {
      "prompt_per_1k": Decimal(os.getenv("OPENAI_PRICE_PROMPT_1K", "0.0003")),
      "completion_per_1k": Decimal(os.getenv("OPENAI_PRICE_COMPLETION_1K", "0.0006")),
  },
  "gpt-5.1-mini": {
      "prompt_per_1k": Decimal(os.getenv("OPENAI_PRICE_PROMPT_1K", "0.0003")),
      "completion_per_1k": Decimal(os.getenv("OPENAI_PRICE_COMPLETION_1K", "0.0006")),
  },
}

def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> Decimal:
    price = PRICES.get(model)
    if not price:
        # 모르는 모델이면 0원 처리(또는 안전하게 약간 높게 잡아도 됨)
        return Decimal("0")
    p = (Decimal(prompt_tokens) / Decimal(1000)) * price["prompt_per_1k"]
    c = (Decimal(completion_tokens) / Decimal(1000)) * price["completion_per_1k"]
    return (p + c).quantize(Decimal("0.000001"))