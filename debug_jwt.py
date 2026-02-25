"""Debug JWT generation for FactSet OAuth2."""

import json
from datetime import datetime, timedelta
from jose import jwt
import base64

# Load JWK
with open("factset_jwk.json", "r") as f:
    data = json.load(f)
    jwk_data = data.get("jwk", data)
    client_id = data.get("clientId", "35a64bba4b7d4daeaaa0cc6d2b7845ed")

print("=" * 70)
print("JWT Debug")
print("=" * 70)
print(f"\nClient ID: {client_id}")
print(f"JWK kid: {jwk_data.get('kid')}")
print(f"JWK alg: {jwk_data.get('alg')}")
print(f"JWK kty: {jwk_data.get('kty')}")

# Generate JWT
now = datetime.utcnow()
claims = {
    "iss": client_id,
    "sub": client_id,
    "aud": "https://auth.factset.com",
    "exp": int((now + timedelta(minutes=5)).timestamp()),
    "iat": int(now.timestamp()),
}

print(f"\nClaims:")
for k, v in claims.items():
    print(f"  {k}: {v}")

try:
    token =jwt.encode(
        claims,
        jwk_data,
        algorithm="RS256",
        headers={"kid": jwk_data.get("kid"), "typ": "JWT"}
    )
    print(f"\n✓ JWT generated successfully")
    print(f"  Length: {len(token)} chars")
    print(f"  First 50: {token[:50]}...")
    
    # Decode without verification to see contents
    parts = token.split('.')
    print(f"\nJWT Parts:")
    print(f"  Header: {base64.urlsafe_b64decode(parts[0] + '==').decode()}")
    print(f"  Payload: {base64.urlsafe_b64decode(parts[1] + '==').decode()}")
    print(f"  Signature: {len(parts[2])} chars")
    
    # Try to verify with public key
    decoded = jwt.decode(
        token,
        jwk_data,
        algorithms=["RS256"],
        options={"verify_aud": False}
    )
    print(f"\n✓ JWT verified successfully")
    print(f"  Decoded claims: {decoded}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Now try the actual token request
print("\n" + "=" * 70)
print("Token Request Test")
print("=" * 70)

import requests

token_endpoint = "https://auth.factset.com/as/token.oauth2"

payload = {
    "grant_type": "client_credentials",
    "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
    "client_assertion": token,
    "scope": "api"
}

print(f"\nPayload:")
for k, v in payload.items():
    if k == "client_assertion":
        print(f"  {k}: {v[:50]}...")
    else:
        print(f"  {k}: {v}")

try:
    response = requests.post(
        token_endpoint,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30
    )
    print(f"\nResponse status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        token_data = response.json()
        print(f"\n✅ SUCCESS!")
        print(f"  Access token: {token_data.get('access_token', '')[:50]}...")
        print(f"  Token type: {token_data.get('token_type')}")
        print(f"  Expires in: {token_data.get('expires_in')}s")
    else:
        print(f"\n❌ FAILED")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
