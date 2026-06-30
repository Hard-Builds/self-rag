import functools
import time
from typing import Callable

from google.api_core.exceptions import ResourceExhausted
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, \
    wait_exponential

from app.core import logger, settings

# Gemini 2.0 Flash pricing (USD per 1M tokens)
_INPUT_COST_PER_M = 0.10
_OUTPUT_COST_PER_M = 0.40

llm_model = ChatGoogleGenerativeAI(model=settings.GEMINI_MODEL)
str_parser = StrOutputParser()

llm_retry = retry(
    retry=retry_if_exception_type(ResourceExhausted),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    stop=stop_after_attempt(5),
    reraise=True,
)


def llm_call(fn: Callable) -> Callable:
    """Wrap an async LLM callable with retry + logging (request/response content, token usage, cost, latency)."""
    retried = llm_retry(fn)

    @functools.wraps(fn)
    async def wrapper(*args, **kwargs):
        request_preview = str(args[0])[:500] if args else ""
        logger.debug("LLM request | fn=%s | input=%s", fn.__qualname__, request_preview)

        start = time.perf_counter()
        try:
            result = await retried(*args, **kwargs)
        except Exception:
            elapsed = time.perf_counter() - start
            logger.error("LLM call failed | fn=%s | latency=%.3fs", fn.__qualname__, elapsed)
            raise

        elapsed = time.perf_counter() - start

        usage = getattr(result, "usage_metadata", None) or getattr(
            getattr(result, "response_metadata", None), "get", lambda *_: None
        )("usage", None)

        if usage:
            input_tokens = getattr(usage, "input_tokens", None) or getattr(usage, "prompt_token_count", 0)
            output_tokens = getattr(usage, "output_tokens", None) or getattr(usage, "candidates_token_count", 0)
            cost = (input_tokens * _INPUT_COST_PER_M + output_tokens * _OUTPUT_COST_PER_M) / 1_000_000
            logger.info(
                "LLM response | fn=%s | latency=%.3fs | input_tokens=%d | output_tokens=%d | cost_usd=%.6f",
                fn.__qualname__, elapsed, input_tokens, output_tokens, cost,
            )
        else:
            logger.info("LLM response | fn=%s | latency=%.3fs | tokens=unavailable", fn.__qualname__, elapsed)

        response_preview = str(result)[:500]
        logger.debug("LLM response content | fn=%s | output=%s", fn.__qualname__, response_preview)

        return result

    return wrapper
