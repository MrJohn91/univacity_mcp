from fastapi import FastAPI
from pydantic import BaseModel
from src.server import programs_list, rank_programs, usage_guide, ProgramsToolArguments, RankProgramsArguments

app = FastAPI(title="EduMatch MCP API")

# POST endpoint for programs_list
@app.post("/programs")
def programs_endpoint(args: ProgramsToolArguments):
    return programs_list(args)

# POST endpoint for rank_programs
@app.post("/rank")
def rank_endpoint(args: RankProgramsArguments):
    return rank_programs(args)

# Optional: usage guide endpoint
@app.get("/usage")
def usage():
    return usage_guide()