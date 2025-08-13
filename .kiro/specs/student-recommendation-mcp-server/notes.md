# Project Notes - Student Recommendation MCP Server

## Project Overview
Building a local Model Context Protocol (MCP) server that provides intelligent educational recommendations using PostgreSQL as the data backend.

## Key Decisions Made
- **Database Choice**: PostgreSQL instead of direct Parquet file access for better query performance and scalability
- **Data Pipeline**: External ETL process loads gold-layer Parquet data into PostgreSQL
- **Architecture**: Layered design with MCP protocol, business logic, and data access layers
- **Caching Strategy**: In-memory caching combined with PostgreSQL query optimization

## Data Sources
- **Gold Layer Location**: `local_data/gold/`
- **Available Datasets**:
  - `gold_country_program_summary/` - Country-level aggregated metrics
  - `gold_institute_engagement/` - Institution engagement data
  - `gold_institute_program_summary/` - Institution program summaries
  - `gold_program_engagement/` - Individual program metrics

## MCP Server Capabilities
### Tools (3)
1. `recommend_countries` - Ranked country recommendations with filtering
2. `recommend_institutions` - Institution recommendations by engagement metrics
3. `recommend_programs` - Program recommendations with multi-criteria filtering

### Resources (3)
1. `countries` - Read-only access to country summary data
2. `institutions` - Read-only access to institution engagement data
3. `programs` - Read-only access to program engagement data

### Prompts
- Guided prompts for common recommendation scenarios
- Usage examples and metric interpretation guides
- Best practices for AI agents using the recommendation system

## Technical Stack
- **Language**: Python
- **Database**: PostgreSQL with optimized indexes
- **Key Dependencies**: 
  - `mcp` - Model Context Protocol implementation
  - `psycopg2-binary` or `asyncpg` - PostgreSQL drivers
  - `pydantic` - Data validation and serialization
  - `pandas` - Data manipulation (if needed)

## Database Schema Highlights
- **Countries Table**: Aggregated metrics with JSONB for top programs
- **Institutions Table**: Engagement metrics with country and type indexing
- **Programs Table**: Detailed program info with array support for multi-country programs
- **Indexes**: Optimized for CTR-based ranking and filtering operations

## Next
What’s next?
	•	Design actual PostgreSQL tables with schema reflecting the datasets.
	•	Implement data loading pipelines (you’ll load parquet -> PostgreSQL).
	•	Build recommendation tools/services to query PostgreSQL and serve results.
	•	Integrate with the LLaMA 3 based AI agent that uses these recommendations.

## Challenges for the institute table
## 	Cleaned and mapped the country IDs correctly.
	•	Inserted missing countries into the countries table.
	•	Inserted the institutions with correct foreign keys.
	•	Verified the inserted data is accurate.

  ## Challenges:
	•	Missing country_id for some programs (only 8 rows).
	•	Dataframe columns didn’t exactly match database schema (extra columns like rank_by_ctr).
	•	program_id had nulls but is a required auto-increment key.
	•	Pandas-specific null types (NAType) caused insertion errors.

Solutions:
	•	Kept rows with missing country_id but excluded them from country-based logic.
	•	Aligned dataframe columns exactly to DB schema by removing extras.
	•	Dropped program_id from insertion so DB auto-generates it.
	•	Converted or cleaned nulls to native Python types to avoid type errors.
	•	Used execute_batch for bulk insert.
	•	Verified insertion by querying the database afterward.


  {
  "country_name": "Germany",
  "limit": 5
}



{
  "max_tuition": 20000,
  "limit": 10
}



{
  "ranking_method": "popularity",
  "limit": 5
}


