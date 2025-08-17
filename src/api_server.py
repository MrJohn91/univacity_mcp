from fastapi import FastAPI
import os
from pydantic import BaseModel
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))