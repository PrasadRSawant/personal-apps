import time
from fastapi.testclient import TestClient
from fastapi import APIRouter, Depends, status
from fastapi_limiter.depends import RateLimiter
from app.main import app

# 1. Define a temporary route for testing the limiter
TEST_LIMIT_TIMES = 2
TEST_LIMIT_SECONDS = 5

# --- FIX IS HERE: Change the handler function to a regular 'def' ---
@app.get("/test-limit", dependencies=[
    Depends(RateLimiter(times=TEST_LIMIT_TIMES, seconds=TEST_LIMIT_SECONDS))
])
def test_limit_route_handler():
    return {"message": "Access allowed."}
# ------------------------------------------------------------------

def test_rate_limiter_blocks_excessive_requests(client: TestClient):
    """
    Tests if the RateLimiter correctly allows and blocks requests.
    """
    # 1. --- Send Allowed Requests (2 allowed) ---
    print(f"\n--- Testing Rate Limit: {TEST_LIMIT_TIMES} requests per {TEST_LIMIT_SECONDS} seconds ---")
    
    # Hit the route the exact number of times allowed (e.g., 2 times)
    for i in range(1, TEST_LIMIT_TIMES + 1):
        # NOTE: Ensure you hit the correct route path
        response = client.get("/test-limit") 
        
        # Must assert that the status code is 200 OK for the allowed requests
        assert response.status_code == status.HTTP_200_OK, f"Request {i} failed unexpectedly."
        print(f"✅ Request {i}/{TEST_LIMIT_TIMES}: Allowed (Status 200)")

    # 2. --- Send Blocked Request (3rd request) ---
    response_blocked = client.get("/test-limit")
    
    # Must assert that the status code is 429 Too Many Requests
    assert response_blocked.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    print(f"❌ Request {TEST_LIMIT_TIMES + 1}: Blocked (Status 429 - SUCCESS)")
    
    assert "Too Many Requests" in response_blocked.json()['detail']
    
    # 3. --- Wait for Reset and Test Successful Access Again ---
    print(f"\n--- Waiting {TEST_LIMIT_SECONDS} seconds for limit to reset... ---")
    time.sleep(TEST_LIMIT_SECONDS + 1)
    
    response_reset = client.get("/test-limit")
    
    # Must assert that the request is successful after the time window expires
    assert response_reset.status_code == status.HTTP_200_OK
    print("✅ Request after reset: Allowed (Status 200 - SUCCESS)")