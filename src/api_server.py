from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import StreamingResponse, RedirectResponse
import asyncio
import requests
from urllib.parse import urlencode
from server import programs_list, rank_programs, usage_guide, ProgramsToolArguments, RankProgramsArguments

app = FastAPI(title="EduMatch MCP API")

# -----------------------------
# Constants / Reusable definitions
# -----------------------------
ALLOWED_USERS = ["patunalu", "MrJohn91"]

TOOLS = [
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
                "offset": {"type": "number", "default": 0},
            },
        },
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
                "limit": {"type": "number", "default": 10},
            },
        },
    },
]

def mcp_response(request_id, result=None, error=None):
    response = {"jsonrpc": "2.0", "id": request_id}
    if error:
        response["error"] = error
    else:
        response["result"] = result
    return response

async def verify_authorized_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="GitHub authentication required")
    
    access_token = auth_header.split(" ")[1]
    
    # Verify token with GitHub and get user info
    user_resp = requests.get("https://api.github.com/user", headers={"Authorization": f"Bearer {access_token}"})
    if user_resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid GitHub token")
    
    user_data = user_resp.json()
    username = user_data.get("login")
    
    # Check if user is authorized
    if username not in ALLOWED_USERS:
        raise HTTPException(status_code=403, detail=f"Access denied. User '{username}' not authorized")
    
    return user_data

# -----------------------------
# Root endpoint
# -----------------------------
@app.get("/")
async def root():
    return {"message": "EduMatch MCP Server", "status": "running"}

# -----------------------------
# Standard POST endpoints
# -----------------------------
@app.post("/programs")
async def programs_endpoint(request: Request, args: ProgramsToolArguments):
    await verify_authorized_user(request)
    return programs_list(args)

@app.post("/rank")
async def rank_endpoint(request: Request, args: RankProgramsArguments):
    await verify_authorized_user(request)
    return rank_programs(args)

@app.get("/usage")
def usage():
    return usage_guide()

# -----------------------------
# MCP handler
# -----------------------------
async def mcp_handler(request_data: dict):
    request_id = request_data.get("id")
    method = request_data.get("method")
    params = request_data.get("params", {})

    try:
        if method == "initialize":
            return mcp_response(
                request_id,
                result={
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
                    "serverInfo": {"name": "EduMatch MCP Server", "version": "1.0.0"},
                },
            )

        elif method == "tools/list":
            return mcp_response(request_id, result={"tools": TOOLS})

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
                return mcp_response(
                    request_id,
                    error={"code": -32601, "message": "Method not found"},
                )

            return mcp_response(
                request_id,
                result={"content": [{"type": "text", "text": str(result)}]},
            )
        
        elif method == "prompts/list":
            return mcp_response(
                request_id,
                result={
                    "prompts": [
                        {
                            "name": "program_summary",
                            "description": "Template for creating user-friendly program summaries and recommendations",
                            "arguments": []
                        }
                    ]
                }
            )
        
        elif method == "prompts/get":
            prompt_name = params.get("name")
            if prompt_name == "program_summary":
                prompt_content = """
When presenting educational programs to users, structure your response as follows:

## Program Recommendations

For each program, include:
- **Program Name** at [Institution Name]
- **Location**: Country
- **Duration**: X months
- **Tuition**: $X (if available)
- **Popularity**: Describe engagement metrics in user-friendly terms
- **Why it's a good match**: Based on their search criteria

## Summary
- Total programs found: X
- Key insights about their options
- Suggestions for refining search if needed

Keep the tone helpful and informative. Translate technical metrics (CTR, views, impressions) into user-friendly language like "highly popular" or "well-regarded program."
"""
                return mcp_response(
                    request_id,
                    result={
                        "description": "Template for creating user-friendly program summaries and recommendations",
                        "messages": [
                            {
                                "role": "user",
                                "content": {
                                    "type": "text",
                                    "text": prompt_content
                                }
                            }
                        ]
                    }
                )
            else:
                return mcp_response(
                    request_id,
                    error={"code": -32601, "message": "Prompt not found"}
                )
        
        elif method == "resources/list":
            return mcp_response(
                request_id,
                result={
                    "resources": [
                        {
                            "uri": "guide://usage",
                            "name": "Usage Guide",
                            "description": "Quick reference guide for using the EduMatch MCP server effectively",
                            "mimeType": "application/json"
                        }
                    ]
                }
            )
        
        elif method == "resources/read":
            resource_uri = params.get("uri")
            if resource_uri == "guide://usage":
                resource_content = usage_guide()
                return mcp_response(
                    request_id,
                    result={
                        "contents": [
                            {
                                "uri": "guide://usage",
                                "mimeType": "application/json",
                                "text": str(resource_content)
                            }
                        ]
                    }
                )
            else:
                return mcp_response(
                    request_id,
                    error={"code": -32601, "message": "Resource not found"}
                )

        else:
            return mcp_response(
                request_id,
                error={"code": -32601, "message": "Method not found"},
            )

    except Exception as e:
        return mcp_response(request_id, error={"code": -32603, "message": str(e)})

# -----------------------------
# SSE endpoint
# -----------------------------
@app.get("/sse")
async def sse_endpoint():
    import json

    async def event_generator():
        init_msg = {"jsonrpc": "2.0", "method": "initialize", "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
            "clientInfo": {"name": "EduMatch MCP Server", "version": "1.0.0"},
        }}
        yield f"data: {json.dumps(init_msg)}\n\n"

        tools_msg = {"jsonrpc": "2.0", "method": "tools/list", "result": {"tools": TOOLS}}
        yield f"data: {json.dumps(tools_msg)}\n\n"

        while True:
            yield f"data: {json.dumps({'type': 'ping'})}\n\n"
            await asyncio.sleep(30)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# -----------------------------
# GitHub OAuth helpers
# -----------------------------
def github_request(url, headers=None, data=None):
    resp = requests.post(url, headers=headers, data=data)
    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail="GitHub request failed")
    return resp.json()

# -----------------------------
# GitHub OAuth endpoints
# -----------------------------
@app.get("/auth/github/authorize")
async def github_authorize(client_id: str, redirect_uri: str, scope: str = "read:user", state: str = None):
    params = {"client_id": client_id, "redirect_uri": redirect_uri, "scope": scope, "state": state}
    github_url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
    return RedirectResponse(url=github_url)

@app.post("/auth/github/token")
async def github_token(client_id: str = Form(), client_secret: str = Form(), code: str = Form(), redirect_uri: str = Form()):
    try:
        return github_request(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={"client_id": client_id, "client_secret": client_secret, "code": code, "redirect_uri": redirect_uri}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/user")
async def get_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    access_token = auth_header.split(" ")[1]
    try:
        user_resp = requests.get("https://api.github.com/user", headers={"Authorization": f"Bearer {access_token}"})
        if user_resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Failed to get user info")
        return user_resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/callback")
async def oauth_callback(code: str, state: str = None):
    return {"code": code, "state": state, "message": "OAuth callback received"}

# -----------------------------
# /session endpoint for MCP Inspector
# -----------------------------
@app.api_route("/session", methods=["GET", "POST"])
async def session_debug(request: Request):
    data = {}
    if request.method == "POST":
        try:
            data = await request.json()
        except Exception:
            data = {"raw_body": await request.body()}
    return {
        "method": request.method,
        "message": "Redirected to /session instead of /callback",
        "query_params": dict(request.query_params),
        "body": data,
        "url": str(request.url)
    }

# -----------------------------
# /streamable endpoint
# -----------------------------
@app.post("/")
async def mcp_handler_endpoint(request: Request):
    await verify_authorized_user(request)
    request_data = await request.json()
    return await mcp_handler(request_data)

@app.post("/streamable")
async def streamable_endpoint(request: Request):
    await verify_authorized_user(request)
    request_data = await request.json()
    return await mcp_handler(request_data)

# -----------------------------
# Run server
# -----------------------------
if __name__ == "__main__":
    import uvicorn
    import os
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))