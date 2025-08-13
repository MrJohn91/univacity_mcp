from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel
from typing import Optional
from config import get_connection
import time

mcp = FastMCP("EduMatch MCP Server")

# ✅ Tool input schema
class ProgramsToolArguments(BaseModel):
    program_name: Optional[str] = None
    country_name: Optional[str] = None
    institution_name: Optional[str] = None
    max_tuition: Optional[float] = None
    limit: Optional[int] = 20
    offset: Optional[int] = 0

@mcp.tool()
def programs_list(args: ProgramsToolArguments):
    """
    Fetch a list of educational programs from the database with flexible filters.

    Parameters:
    - program_name (str, optional): Partial or full name of the program to search.
    - country_name (str, optional): Name of the country where the program is offered.
    - institution_name (str, optional): Name of the institution offering the program.
    - max_tuition (float, optional): Maximum tuition cost to filter programs.
    - limit (int, optional): Maximum number of results to return (default 20).
    - offset (int, optional): Number of results to skip for pagination (default 0).

    Returns:
    - List of programs including program name, country, institution, duration,
      tuition, CTR, total views, and total impressions.

    Notes:
    - All filters are optional; if none are provided, all programs are returned.
    - Supports case-insensitive partial matches for text fields.
    """
    start_time = time.time()
    print("\n[DEBUG] programs_list called")
    print(f"[DEBUG] Parameters: {args}")

    try:
        print("[DEBUG] Connecting to database...")
        conn = get_connection()
        cur = conn.cursor()
        print("[DEBUG] Database connection established.")
    except Exception as e:
        print(f"[ERROR] Failed to connect to database: {e}")
        return {"error": str(e)}

    query = """
        SELECT
            p.program_id,
            p.program_name,
            c.institute_country AS country,
            i.institution_name AS institution,
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

    print(f"[DEBUG] Final SQL Query:\n{query}")
    print(f"[DEBUG] Parameters: {params}")

    try:
        cur.execute(query, params)
        results = cur.fetchall()
        print(f"[DEBUG] Query executed successfully. Rows returned: {len(results)}")
    except Exception as e:
        print(f"[ERROR] Query execution failed: {e}")
        cur.close()
        conn.close()
        return {"error": str(e)}

    cur.close()
    conn.close()
    print("[DEBUG] Database connection closed.")

    programs = []
    for row in results:
        programs.append({
            "program_id": row[0],
            "program_name": row[1],
            "country": row[2],
            "institution": row[3],
            "duration_months": row[4],
            "tuition": row[5],
            "ctr": row[6],
            "total_views": row[7],
            "total_impressions": row[8],
        })

    elapsed_time = round(time.time() - start_time, 3)
    print(f"[DEBUG] programs_list completed in {elapsed_time} seconds.\n")

    return programs

def main():
    print("EduMatch MCP Server started. Waiting for MCP client requests...")
    mcp.run()

if __name__ == "__main__":
    main()