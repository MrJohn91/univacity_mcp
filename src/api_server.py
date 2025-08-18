from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import os
import asyncio
from server import programs_list, rank_programs, usage_guide, ProgramsToolArguments, RankProgramsArguments

app = FastAPI(title="EduMatch MCP API")

# POST endpoint for programs_list
@app.post("/programs")
def programs_endpoint(args: ProgramsToolArguments):
    return programs_list(args)

# POST endpoint for rank_programs
@app.post("/rank")
def rank_endpoint(args: RankProgramsArguments):
    return rank_programs(args)

# usage guide 
@app.get("/usage")
def usage():
    return usage_guide()

# MCP tool call endpoint
@app.post("/tools/call")
async def mcp_tool_call(request_data: dict):
    tool_name = request_data.get("params", {}).get("name")
    tool_args = request_data.get("params", {}).get("arguments", {})
    request_id = request_data.get("id")
    
    try:
        if tool_name == "programs_list":
            args = ProgramsToolArguments(**tool_args)
            result = programs_list(args)
        elif tool_name == "rank_programs":
            args = RankProgramsArguments(**tool_args)
            result = rank_programs(args)
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": "Method not found"}
            }
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [{"type": "text", "text": str(result)}]
            }
        }
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32603, "message": str(e)}
        }

# SSE endpoint for MCP Inspector
@app.get("/sse")
async def sse_endpoint():
    async def event_generator():
        # Send MCP initialize message
        init_msg = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {},
                    "prompts": {}
                },
                "clientInfo": {
                    "name": "EduMatch MCP Server",
                    "version": "1.0.0"
                }
            }
        }
        import json
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
            yield f"data: {{\"type\": \"ping\"}}\n\n"
            await asyncio.sleep(30)
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))