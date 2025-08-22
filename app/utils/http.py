from fastapi import HTTPException
import httpx
import asyncio

async def fetch_with_retries(url: str, retries: int = 3, delay: float = 1.0) -> httpx.Response: # type: ignore
  """
  Fetch a URL with retry logic.
  Uses exponential backoff: delay, delay*2, delay*4...
  """
  last_exc: Exception | None = None

  for attempt in range(retries):
    try:
      async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10)
        # Retry only on 5xx, not 4xx
        if response.status_code >= 500:
          raise httpx.HTTPStatusError(
            f"Server error: {response.status_code}",
            request=response.request,
            response=response,
          )
        response.raise_for_status()
        return response
    except (httpx.RequestError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
      last_exc = e
      if attempt < retries - 1:
        await asyncio.sleep(delay * 2**attempt)
      else:
        raise last_exc
      
def raise_404(str):
  raise HTTPException(status_code=404, detail=str)
