
import time
import logging

import litellm
from litellm.caching import Cache

from app.config import LLM_API_KEYS, LLM_MODEL, ENABLE_FAILURE_SIMULATION

# Configure LiteLLM's built-in local cache
litellm.cache = Cache(type="local")
litellm.enable_cache()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_failure_header(header: str | None) -> dict:
    """Read failure simulation instructions from the request header."""
    failures = {}

    if not header:
        return failures

    for item in header.split(","):
        if "=" not in item:
            continue

        key_id, status = item.strip().split("=", 1)

        try:
            status_code = int(status.strip())
            if status_code in (429, 500, 502, 503):
                failures[key_id.strip()] = status_code
        except ValueError:
            continue

    return failures


def generate_reply(messages: list, failure_header: str | None = None) -> dict:
    """
    Generate an AI response using LiteLLM.
    Try the configured API keys in order if a provider fails.
    """

    if not LLM_API_KEYS:
        raise RuntimeError("No LLM API keys configured")

    failures = {}

    if ENABLE_FAILURE_SIMULATION:
        failures = parse_failure_header(failure_header)

    # Simulated requests bypass cache so failover can be tested reliably.
    use_cache = not bool(failures)

    start_time = time.perf_counter()
    fallback_attempts = 0

    for index, api_key in enumerate(LLM_API_KEYS):
        key_id = f"key_{index + 1}"

        try:
            # Simulate a provider failure when requested.
            simulated_status = failures.get(key_id, failures.get("*"))

            if simulated_status:
                raise RuntimeError(
                    f"Simulated provider failure: HTTP {simulated_status}"
                )

            response = litellm.completion(
                model=LLM_MODEL,
                messages=messages,
                api_key=api_key,
                caching=use_cache,
                num_retries=0,
                timeout=90
            )

            elapsed_ms = int((time.perf_counter() - start_time) * 1000)

            hidden_params = getattr(response, "_hidden_params", {}) or {}
            cache_hit = hidden_params.get("cache_hit", False)

            usage = getattr(response, "usage", None)

            input_tokens = int(
                getattr(usage, "prompt_tokens", 0) or 0
            )
            output_tokens = int(
                getattr(usage, "completion_tokens", 0) or 0
            )

            reply = response.choices[0].message.content or ""

            return {
                "reply": reply,
                "resolution_source": (
                    "LLM_CACHE" if cache_hit else "LIVE_INFERENCE"
                ),
                "model": getattr(response, "model", None) or LLM_MODEL,
                "latency_ms": elapsed_ms,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "key_id": None if cache_hit else key_id,
                "fallback_attempts": 0 if cache_hit else fallback_attempts
            }

        except Exception as error:
            logger.error(
                "Provider %s failed (%s): %s",
                 key_id,
                 type(error).__name__,
                 str(error)
                )
        fallback_attempts += 1

    raise RuntimeError("all providers unavailable")
