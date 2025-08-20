from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import StreamingResponse, RedirectResponse
import os
import asyncio
import requests
from urllib.parse import urlencode
from server import programs_list, rank_programs, usage_guide, ProgramsToolArguments, RankProgramsArguments

app = FastAPI(title="EduMatch MCP API")

@app.get("/")
async def root():
    """Root endpoint for basic server info"""
    return {"message": "EduMatch MCP Server", "status": "running"}

# -----------------------------
# Standard POST endpoints
# -----------------------------
@app.post("/programs")
def programs_endpoint(args: ProgramsToolArguments):
    return programs_list(args)

@app.post("/rank")
def rank_endpoint(args: RankProgramsArguments):
    return rank_programs(args)

@app.get("/usage")
def usage():
    return usage_guide()

# -----------------------------
# MCP Protocol endpoints
# -----------------------------
@app.post("/")
async def mcp_handler(request_data: dict):
    request_id = request_data.get("id")
    method = request_data.get("method")
    params = request_data.get("params", {})

    try:
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
                    "serverInfo": {"name": "EduMatch MCP Server", "version": "1.0.0"}
                }
            }
        
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [
                        {
                            "name": "programs_list",
                            "description": "Search and filter educational programs",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "program_name": {"type": "string"},
                                    "country_name": {"type": "string"},
                                    "institution_name": {"type": "string"},
                                    "max_tuition": {"type": "number"},
                                    "limit": {"type": "number", "default": 20},
                                    "offset": {"type": "number", "default": 0}
                                }
                            }
                        },
                        {
                            "name": "rank_programs",
                            "description": "Get ranked program recommendations",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "country_name": {"type": "string"},
                                    "institution_name": {"type": "string"},
                                    "max_tuition": {"type": "number"},
                                    "ranking_method": {"type": "string", "default": "popularity"},
                                    "limit": {"type": "number", "default": 10}
                                }
                            }
                        }
                    ]
                }
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            
            if tool_name == "programs_list":
                args = ProgramsToolArguments(**tool_args)
                result = programs_list(args)
            elif tool_name == "rank_programs":
                args = RankProgramsArguments(**tool_args)
                result = rank_programs(args)
            else:
                return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": "Method not found"}}
            
            return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": str(result)}]}}
        
        else:
            return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": "Method not found"}}

    except Exception as e:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32603, "message": str(e)}}

# -----------------------------
# SSE endpoint for backward compatibility
# -----------------------------
@app.get("/sse")
async def sse_endpoint():
    async def event_generator():
        import json

        # Initialize MCP
        init_msg = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
                "clientInfo": {"name": "EduMatch MCP Server", "version": "1.0.0"}
            }
        }
        yield f"data: {json.dumps(init_msg)}\n\n"

        # Send tools list
        tools_msg = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "result": {
                "tools": [
                    {
                        "name": "programs_list",
                        "description": "Search and filter educational programs",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "program_name": {"type": "string"},
                                "country_name": {"type": "string"},
                                "institution_name": {"type": "string"},
                                "max_tuition": {"type": "number"},
                                "limit": {"type": "number", "default": 20},
                                "offset": {"type": "number", "default": 0}
                            }
                        }
                    },
                    {
                        "name": "rank_programs",
                        "description": "Get ranked program recommendations",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "country_name": {"type": "string"},
                                "institution_name": {"type": "string"},
                                "max_tuition": {"type": "number"},
                                "ranking_method": {"type": "string", "default": "popularity"},
                                "limit": {"type": "number", "default": 10}
                            }
                        }
                    }
                ]
            }
        }
        yield f"data: {json.dumps(tools_msg)}\n\n"

        # Keep connection alive
        while True:
            yield f"data: {json.dumps({'type': 'ping'})}\n\n"
            await asyncio.sleep(30)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# -----------------------------
# GitHub OAuth endpoints
# -----------------------------
@app.get("/auth/github/authorize")
async def github_authorize(client_id: str, redirect_uri: str, scope: str = "read:user", state: str = None):
    """Redirect to GitHub for OAuth authorization"""
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "state": state
    }
    github_url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
    return RedirectResponse(url=github_url)

@app.post("/auth/github/token")
async def github_token(
    client_id: str = Form(),
    client_secret: str = Form(),
    code: str = Form(),
    redirect_uri: str = Form()
):
    """Exchange authorization code for access token"""
    try:
        # Exchange code for token with GitHub
        token_response = requests.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "redirect_uri": redirect_uri
            },
            headers={"Accept": "application/json"}
        )
        
        if token_response.status_code == 200:
            return token_response.json()
        else:
            raise HTTPException(status_code=400, detail="Token exchange failed")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/user")
async def get_user(request: Request):
    """Get authenticated user info"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    access_token = auth_header.split(" ")[1]
    
    try:
        # Get user info from GitHub
        user_response = requests.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if user_response.status_code == 200:
            return user_response.json()
        else:
            raise HTTPException(status_code=401, detail="Failed to get user info")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/callback")
async def oauth_callback(code: str, state: str = None):
    """Handle OAuth callback from GitHub"""
    return {"code": code, "state": state, "message": "OAuth callback received"}

@app.get("/session")
async def session_debug(request: Request):
    """Debug endpoint to see what's being sent to /session"""
    return {
        "message": "Redirected to /session instead of /callback",
        "query_params": dict(request.query_params),
        "url": str(request.url)
    }

# -----------------------------
# StreamableHttp endpoint for MCP Inspector
# -----------------------------
@app.post("/streamable")
async def streamable_endpoint(request: Request):
    """
    StreamableHttp-compatible endpoint for MCP Inspector.
    """
    return await mcp_handler(await request.json())

# -----------------------------
# Run server
# -----------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))