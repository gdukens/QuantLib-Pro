"""Test different JWT configurations for FactSet."""

import json
from datetime import datetime, timedelta
from jose import jwt
import requests

# Load JWK
with open("factset_jwk.json", "r") as f:
    data = json.load(f)
    jwk_data = data.get("jwk", data)
    client_id = data.get("clientId", "35a64bba4b7d4daeaaa0cc6d2b7845ed")

token_endpoint = "https://auth.factset.com/as/token.oauth2"

def run_config(name, aud, scope):
    """Test a specific JWT configuration."""
    print(f"\n{'='*70}")
    print(f"Test: {name}")
    print(f"{'='*70}")
    print(f"Audience: {aud}")
    print(f"Scope: {scope}")
    
    now = datetime.utcnow()
    claims = {
        "iss": client_id,
        "sub": client_id,
        "aud": aud,
        "exp": int((now + timedelta(minutes=5)).timestamp()),
        "iat": int(now.timestamp()),
    }
    
    token = jwt.encode(
        claims,
        jwk_data,
        algorithm="RS256",
        headers={"kid": jwk_data.get("kid"), "typ": "JWT"}
    )
    
    payload = {
        "grant_type": "client_credentials",
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion": token,
    }
    
    if scope:
        payload["scope"] = scope
    
    try:
        response = requests.post(
            token_endpoint,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ SUCCESS!")
            return True
        else:
            print("❌ FAILED")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

# Test different configurations
configs = [
    ("Token endpoint as audience, no scope", token_endpoint, None),
    ("Token endpoint as audience, api scope", token_endpoint, "api"),
    ("Token endpoint as audience, mcp scope", token_endpoint, "mcp"),
    ("Issuer as audience, no scope", "https://auth.factset.com", None),
    ("Issuer as audience, mcp scope", "https://auth.factset.com", "mcp"),
    ("Issuer as audience, openid scope", "https://auth.factset.com", "openid"),
]

success = None
for name, aud, scope in configs:
    if run_config(name, aud, scope):
        success = (name, aud, scope)
        break

if success:
    print(f"\n{'='*70}")
    print(f"✅ FOUND WORKING CONFIGURATION")
    print(f"{'='*70}")
    print(f"Name: {success[0]}")
    print(f"Audience: {success[1]}")
    print(f"Scope: {success[2]}")
else:
    print(f"\n{'='*70}")
    print(f"❌ NO WORKING CONFIGURATION FOUND")
    print(f"{'='*70}")
    print("\nPossible issues:")
    print("1. The JWK might not be properly registered with FactSet")
    print("2. The client ID might be incorrect")
    print("3. Additional claims might be required")
    print("4. The authentication method might need to be different")
    print("\nContact FactSet support for assistance.")
