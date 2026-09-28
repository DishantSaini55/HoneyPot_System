import importlib.util
from pathlib import Path


module_path = Path(__file__).parents[1] / "main.py"
spec = importlib.util.spec_from_file_location("http_honeypot_main", module_path)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
decoy_response = module.decoy_response


def test_login_is_a_harmless_decoy():
    response = decoy_response("/login", "GET")
    assert response.status_code == 200
    assert b"Administrator Sign In" in response.body


def test_sensitive_file_does_not_return_secrets():
    response = decoy_response("/.env", "GET")
    assert response.status_code == 404
    assert response.body == b"Not Found"


def test_unknown_path_is_escaped():
    response = decoy_response("/<script>alert(1)</script>", "GET")
    assert b"<script>" not in response.body
    assert b"&lt;script&gt;" in response.body
