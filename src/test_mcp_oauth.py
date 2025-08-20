import webbrowser
import requests
from urllib.parse import urlencode, urlparse, parse_qs

# === MCP OAuth config ===
MCP_SERVER = "https://univacitymcp.nfluncvjohn.workers.dev"  # Your Cloudflare URL
CLIENT_ID = "Ov23liugGqrsItstfCA8"     
CLIENT_SECRET = "5264771967209702b6954389b1fcdd94ffeb3cc6"  
REDIRECT_URI = "http://localhost:8000/callback" 

def test_oauth_flow():
    """Test GitHub OAuth integration with your MCP server"""
    
    print("Testing GitHub OAuth with MCP Server")
    print("=" * 50)
    
    # Step 1: Check if OAuth endpoints exist
    try:
        response = requests.get(f"{MCP_SERVER}/auth/github/authorize")
        print("✅ OAuth authorize endpoint exists")
    except Exception as e:
        print("❌ OAuth endpoints not found:", e)
        return
    
    # Step 2: Generate authorization URL
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "read:user",
        "state": "test123"  # Add state for security
    }
    auth_url = f"{MCP_SERVER}/auth/github/authorize?{urlencode(params)}"
    
    print(f"\n🔗 Authorization URL: {auth_url}")
    print("\n1. Opening browser for GitHub OAuth...")
    webbrowser.open(auth_url)
    
    # Step 3: Get authorization code
    print("\n2. After authorizing, you'll be redirected to localhost:8000/callback")
    print("   Copy the FULL redirect URL from your browser address bar")
    redirect_response = input("\nPaste the full redirect URL here: ")
    
    try:
        # Extract the code from the redirect URL
        query = urlparse(redirect_response).query
        parsed_query = parse_qs(query)
        
        if "code" not in parsed_query:
            print("❌ No authorization code found in URL")
            return
            
        code = parsed_query["code"][0]
        print(f"✅ Authorization code received: {code[:10]}...")
        
        # Step 4: Exchange code for token
        print("\n3. Exchanging code for access token...")
        token_response = requests.post(
            f"{MCP_SERVER}/auth/github/token",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "code": code,
                "redirect_uri": REDIRECT_URI,
            },
            headers={"Accept": "application/json"}
        )
        
        if token_response.status_code == 200:
            token_data = token_response.json()
            print("✅ Token exchange successful!")
            print(f"Access token: {token_data.get('access_token', 'N/A')[:10]}...")
            print(f"Token type: {token_data.get('token_type', 'N/A')}")
            print(f"Scope: {token_data.get('scope', 'N/A')}")
            
            # Step 5: Test authenticated request (if you have protected endpoints)
            access_token = token_data.get('access_token')
            if access_token:
                print("\n4. Testing authenticated request...")
                headers = {"Authorization": f"Bearer {access_token}"}
                user_response = requests.get(f"{MCP_SERVER}/user", headers=headers)
                
                if user_response.status_code == 200:
                    print("✅ Authenticated request successful!")
                    print("User data:", user_response.json())
                else:
                    print(f"⚠️ Authenticated request failed: {user_response.status_code}")
        else:
            print(f"❌ Token exchange failed: {token_response.status_code}")
            print("Response:", token_response.text)
            
    except Exception as e:
        print(f"❌ Error during OAuth flow: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 OAuth testing complete!")

if __name__ == "__main__":
    test_oauth_flow()