import os
import pytest
import responses
import respx
import httpx

# Set environment variables before importing app to avoid Startup Errors
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["SUPABASE_URL"] = "https://mock-project.supabase.co"
os.environ["SUPABASE_KEY"] = "mock-key"
os.environ["RESEND_API_KEY"] = "mock-resend-key"

from app import app as flask_app

@pytest.fixture
def app():
    flask_app.config.update({
        "TESTING": True,
        "SECRET_KEY": "test-secret-key",
    })
    return flask_app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def mock_supabase():
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        with respx.mock(assert_all_called=False, assert_all_mocked=False) as respx_mock:
            class CombinedMock:
                def add(self, method, url, **kwargs):
                    # Register with responses (for requests)
                    rsps.add(method, url, **kwargs)
                    # Register with respx (for httpx/supabase)
                    method_lower = method.lower()
                    json_data = kwargs.get("json", [])
                    status = kwargs.get("status", 200)
                    
                    # For respx, we extract the base path and match parameters more loosely
                    # because supabase-py may change order or add select=*
                    if isinstance(url, str):
                        if "?" in url:
                            base_path = url.split("?", 1)[0]
                            getattr(respx_mock, method_lower)(url__startswith=base_path).mock(
                                return_value=httpx.Response(status, json=json_data)
                            )
                        else:
                            getattr(respx_mock, method_lower)(url=url).mock(
                                return_value=httpx.Response(status, json=json_data)
                            )
                    elif hasattr(url, 'match'): # re.Pattern
                         getattr(respx_mock, method_lower)(url=url).mock(
                            return_value=httpx.Response(status, json=json_data)
                        )
                
                def add_callback(self, method, url, callback, **kwargs):
                    # Delegate callback
                    rsps.add_callback(method, url, callback, **kwargs)
                    
                    def respx_callback(request):
                        status, headers, body = callback(request)
                        import json
                        return httpx.Response(status, headers=headers, json=json.loads(body))
                    
                    method_lower = method.lower()
                    getattr(respx_mock, method_lower)(url=url).mock(side_effect=respx_callback)

            yield CombinedMock()
