# src/server.py

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel
from typing import Optional
from config import get_connection
import time

# ==========================
# MCP Server Initialization
# ==========================
mcp = FastMCP("EduMatch MCP Server")

# ==========================
# Tool Schemas
# ==========================
class ProgramsToolArguments(BaseModel):
    program_name: Optional[str] = None
    country_name: Optional[str] = None
    institution_name: Optional[str] = None
    max_tuition: Optional[float] = None
    limit: Optional[int] = 20
    offset: Optional[int] = 0

class RankProgramsArguments(BaseModel):
    country_name: Optional[str] = None
    institution_name: Optional[str] = None
    max_tuition: Optional[float] = None
    ranking_method: Optional[str] = "popularity"  # "popularity", "cost_effectiveness", "engagement"
    limit: Optional[int] = 10

# ==========================
# Tools
# ==========================
@mcp.tool()
def programs_list(args: ProgramsToolArguments):
    """
    Fetch educational programs with flexible filtering options.
    
    Use this to help users find programs based on their preferences for:
    - Country/location preferences
    - Institution preferences  
    - Budget constraints
    - Program name searches
    
    Returns program details including costs, duration, and popularity metrics.
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        query = """
            SELECT
                p.program_id,
                p.program_name,
                c.institute_country,
                i.institution_name,
                i.institution_type,
                p.duration_months,
                p.tuition,
                p.ctr,
                p.total_views,
                p.total_impressions
            FROM programs p
            JOIN countries c ON p.country_id = c.country_id
            JOIN institutions i ON p.institution_id = i.institution_id
            WHERE 1=1
        """
        params = []

        if args.program_name:
            query += " AND p.program_name ILIKE %s"
            params.append(f"%{args.program_name}%")
        if args.country_name:
            query += " AND c.institute_country ILIKE %s"
            params.append(f"%{args.country_name}%")
        if args.institution_name:
            query += " AND i.institution_name ILIKE %s"
            params.append(f"%{args.institution_name}%")
        if args.max_tuition is not None:
            query += " AND p.tuition <= %s"
            params.append(args.max_tuition)

        query += " ORDER BY p.program_name LIMIT %s OFFSET %s"
        params.extend([args.limit, args.offset])

        cur.execute(query, params)
        results = cur.fetchall()
        cur.close()
        conn.close()

        programs = []
        for row in results:
            programs.append({
                "program_id": row[0],
                "program_name": row[1],
                "country": row[2],
                "institution": row[3],
                "institution_type": row[4],
                "duration_months": row[5],
                "tuition": float(row[6]) if row[6] else None,
                "ctr": float(row[7]) if row[7] else None,
                "total_views": row[8],
                "total_impressions": row[9]
            })

        return {
            "programs": programs,
            "count": len(programs),
            "filters_applied": {k: v for k, v in args.dict().items() if v is not None}
        }
        
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def rank_programs(args: RankProgramsArguments):
    """
    Rank and score programs based on engagement metrics and user preferences.
    
    Ranking methods:
    - popularity: Based on views and impressions
    - cost_effectiveness: Considers tuition vs engagement
    - engagement: Based on click-through rates
    
    Use this to provide personalized program recommendations.
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Base query with scoring based on method
        if args.ranking_method == "engagement":
            score_formula = "p.ctr * 100"
        elif args.ranking_method == "cost_effectiveness":
            score_formula = "(p.total_views::float / NULLIF(p.tuition, 0)) * 1000"
        else:  # popularity (default)
            score_formula = "p.total_views + (p.total_impressions * 0.1)"
            
        query = f"""
            SELECT
                p.program_id,
                p.program_name,
                c.institute_country,
                i.institution_name,
                i.institution_type,
                p.duration_months,
                p.tuition,
                p.ctr,
                p.total_views,
                p.total_impressions,
                ({score_formula}) as ranking_score
            FROM programs p
            JOIN countries c ON p.country_id = c.country_id
            JOIN institutions i ON p.institution_id = i.institution_id
            WHERE p.ctr > 0 AND p.total_views > 0
        """
        params = []

        if args.country_name:
            query += " AND c.institute_country ILIKE %s"
            params.append(f"%{args.country_name}%")
        if args.institution_name:
            query += " AND i.institution_name ILIKE %s"
            params.append(f"%{args.institution_name}%")
        if args.max_tuition is not None:
            query += " AND p.tuition <= %s"
            params.append(args.max_tuition)

        query += " ORDER BY ranking_score DESC LIMIT %s"
        params.append(args.limit)

        cur.execute(query, params)
        results = cur.fetchall()
        cur.close()
        conn.close()

        programs = []
        for row in results:
            programs.append({
                "program_id": row[0],
                "program_name": row[1],
                "country": row[2],
                "institution": row[3],
                "institution_type": row[4],
                "duration_months": row[5],
                "tuition": float(row[6]) if row[6] else None,
                "ctr": float(row[7]) if row[7] else None,
                "total_views": row[8],
                "total_impressions": row[9],
                "ranking_score": float(row[10]) if row[10] else 0
            })

        return {
            "ranked_programs": programs,
            "ranking_method": args.ranking_method,
            "count": len(programs)
        }
        
    except Exception as e:
        return {"error": str(e)}

# ==========================
# Resources
# ==========================
@mcp.resource("guide://usage")
def usage_guide():
    """
    Quick reference guide for using the EduMatch MCP server effectively.
    """
    return {
        "description": "EduMatch Program Discovery Assistant",
        "available_tools": {
            "programs_list": {
                "purpose": "Search and filter educational programs", 
                "key_filters": ["country_name", "institution_name", "program_name", "max_tuition"],
                "example": "Find programs in Germany under $20000"
            },
            "rank_programs": {
                "purpose": "Get ranked program recommendations",
                "ranking_methods": ["popularity", "engagement", "cost_effectiveness"],
                "example": "Show top 5 most popular programs in Canada"
            }
        },
        "data_insights": {
            "metrics": "Programs include CTR (click-through rate), views, and impressions",
            "cost_info": "Tuition amounts available for budget filtering",
            "locations": "Programs available from institutions worldwide"
        }
    }

# ==========================
# Prompts
# ==========================
@mcp.prompt()
def program_summary():
    """
    Template for creating user-friendly program summaries and recommendations.
    """
    return """
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

# ==========================
# Main Entry Point
# ==========================
def main():
    print("EduMatch MCP Server ready...")
    mcp.run()

if __name__ == "__main__":
    main()