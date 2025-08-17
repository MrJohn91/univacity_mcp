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

# SSE endpoint for MCP Inspector
@app.get("/sse")
async def sse_endpoint():
    async def event_generator():
        i = 1
        while True:
            yield f"data: Event {i}\n\n"
            i += 1
            await asyncio.sleep(1)
    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))