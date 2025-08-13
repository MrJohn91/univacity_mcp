# Design Document

## Overview

The Student Recommendation MCP Server is a Python-based Model Context Protocol server that serves as a Program Discovery Assistant for educational programs. The server leverages pre-aggregated analytics stored in PostgreSQL to help students, counselors, and AI agents discover and evaluate study programs based on preferences and engagement metrics.

The architecture emphasizes performance through PostgreSQL's native querying capabilities, intelligent caching, and optimized data access patterns. The system reads from existing Parquet files in the gold layer and loads them into a normalized PostgreSQL database for efficient querying and recommendations.

## Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "Claude Desktop Client"
        A[User Query] --> B[Claude Desktop]
        B --> C[MCP Client]
    end
    
    subgraph "MCP Protocol"
        C --> D[JSON-RPC Connection]
        D --> E[MCP Server]
    end
    
    subgraph "EduMatch MCP Server"
        E --> F[FastMCP Framework]
        F --> G[Tool Handlers]
        F --> H[Resource Handlers] 
        F --> I[Prompt Templates]
        
        G --> J[programs_list Tool]
        G --> K[rank_programs Tool]
        H --> L[usage_guide Resource]
        I --> M[program_summary Prompt]
        
        J --> N[Database Access Layer]
        K --> N
        N --> O[(PostgreSQL Database)]
    end
    
    subgraph "Data Pipeline"
        P[Gold Layer Parquet Files] --> Q[ETL Process]
        Q --> O
    end
```

### Component Architecture

The server follows a layered architecture optimized for MCP protocol communication and program discovery:

- **MCP Protocol Layer**: FastMCP framework handles JSON-RPC communication with Claude Desktop
- **Tool Layer**: Implements `programs_list` and `rank_programs` functions with parameter validation
- **Resource Layer**: Provides `usage_guide` documentation for AI agents
- **Prompt Layer**: Offers `program_summary` template for consistent response formatting
- **Data Access Layer**: Manages PostgreSQL connections and query execution
- **Database Layer**: PostgreSQL with normalized schema and optimized indexes

### MCP Protocol Flow

**Connection Establishment:**
1. Claude Desktop launches the MCP server using the configured uv command
2. Server establishes JSON-RPC connection over stdin/stdout
3. Claude requests available tools, resources, and prompts

**Tool Execution:**
1. Claude sends `tools/call` JSON-RPC message with tool name and parameters
2. Server validates parameters using Pydantic schemas
3. Server executes database queries and returns structured results
4. Claude formats results using prompt templates for user presentation

**Resource Access:**
1. Claude requests `mcp://usage_guide` for documentation
2. Server returns static guide with tool descriptions and examples
3. Claude uses guide to understand available functionality

## Database Schema

Based on the implemented notebooks, the database uses a normalized relational schema:

### Countries Table
```sql
CREATE TABLE countries (
    country_id SERIAL PRIMARY KEY,
    institute_country TEXT NOT NULL UNIQUE,
    num_institutes INT DEFAULT 0,
    total_programs INT DEFAULT 0,
    avg_ctr NUMERIC(5,2) DEFAULT 0.00,
    total_views BIGINT DEFAULT 0,
    total_impressions BIGINT DEFAULT 0,
    top_programs JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Institutions Table
```sql
CREATE TABLE institutions (
    institution_id SERIAL PRIMARY KEY,
    institution_name TEXT NOT NULL,
    country_id INT REFERENCES countries(country_id) ON DELETE CASCADE,
    institution_type TEXT,
    ctr NUMERIC(5,2) DEFAULT 0.00,
    total_views BIGINT DEFAULT 0,
    total_impressions BIGINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Programs Table
```sql
CREATE TABLE programs (
    program_id SERIAL PRIMARY KEY,
    program_name TEXT NOT NULL,
    institution_id INT REFERENCES institutions(institution_id) ON DELETE CASCADE,
    country_id INT REFERENCES countries(country_id) ON DELETE CASCADE,
    duration_months INT,
    tuition NUMERIC(12,2),
    ctr NUMERIC(5,2) DEFAULT 0.00,
    total_views BIGINT DEFAULT 0,
    total_impressions BIGINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Indexes for Performance
```sql
-- Country indexes
CREATE INDEX idx_countries_ctr ON countries(avg_ctr DESC);
CREATE INDEX idx_countries_programs ON countries(total_programs DESC);

-- Institution indexes
CREATE INDEX idx_institutions_ctr ON institutions(ctr DESC);
CREATE INDEX idx_institutions_country ON institutions(country_id);
CREATE INDEX idx_institutions_type ON institutions(institution_type);

-- Program indexes
CREATE INDEX idx_programs_ctr ON programs(ctr DESC);
CREATE INDEX idx_programs_country ON programs(country_id);
CREATE INDEX idx_programs_institution ON programs(institution_id);
CREATE INDEX idx_programs_duration ON programs(duration_months);
CREATE INDEX idx_programs_tuition ON programs(tuition);
```

## MCP Server Implementation

### 1. FastMCP Framework Integration

**Purpose**: Provides the MCP protocol implementation using the FastMCP framework

**Key Features**:
- Automatic JSON-RPC handling for Claude Desktop communication
- Pydantic-based parameter validation for tools
- Decorator-based tool, resource, and prompt registration
- Built-in error handling and response formatting

**Server Initialization**:
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("EduMatch MCP Server")

@mcp.tool()
def programs_list(args: ProgramsToolArguments):
    """Tool implementation"""

@mcp.resource("guide://usage")
def usage_guide():
    """Resource implementation"""

@mcp.prompt()
def program_summary():
    """Prompt template"""
```

### 2. Tool Parameter Schemas

**Purpose**: Define and validate parameters for MCP tools using Pydantic

**Programs List Tool Schema**:
```python
class ProgramsToolArguments(BaseModel):
    program_name: Optional[str] = None
    country_name: Optional[str] = None
    institution_name: Optional[str] = None
    max_tuition: Optional[float] = None
    limit: Optional[int] = 20
    offset: Optional[int] = 0
```

**Rank Programs Tool Schema**:
```python
class RankProgramsArguments(BaseModel):
    country_name: Optional[str] = None
    institution_name: Optional[str] = None
    max_tuition: Optional[float] = None
    ranking_method: Optional[str] = "popularity"  # "popularity", "cost_effectiveness", "engagement"
    limit: Optional[int] = 10
```

### 3. Database Query Implementation

**Purpose**: Execute PostgreSQL queries based on MCP tool parameters

**Programs List Query**:
- Joins programs, countries, and institutions tables
- Applies ILIKE filters for text searches
- Supports pagination with LIMIT and OFFSET
- Returns structured program data with engagement metrics

**Rank Programs Query**:
- Uses dynamic scoring formulas based on ranking method
- Popularity: `total_views + (total_impressions * 0.1)`
- Engagement: `ctr * 100`
- Cost-effectiveness: `(total_views / tuition) * 1000`
- Orders results by calculated ranking score

## Components and Interfaces

### 1. Data Loading Pipeline

**Purpose**: ETL process to load Parquet data into PostgreSQL

**Implementation Details** (from notebooks):
- Loads country, institution, and program data from specific Parquet files
- Handles data type conversions and JSON serialization for complex fields
- Implements foreign key mapping between countries, institutions, and programs
- Uses batch inserts with conflict resolution for data updates

**Key Methods**:
```python
def load_country_data(parquet_path: str) -> pd.DataFrame
def load_institution_data(parquet_path: str) -> pd.DataFrame  
def load_program_data(parquet_path: str) -> pd.DataFrame
def insert_countries(df: pd.DataFrame, conn: psycopg2.Connection)
def insert_institutions(df: pd.DataFrame, conn: psycopg2.Connection)
def insert_programs(df: pd.DataFrame, conn: psycopg2.Connection)
```

### 2. Program Discovery Engine

**Purpose**: Core business logic for program search, filtering, and ranking

**Interfaces**:
```python
class ProgramDiscoveryEngine:
    def search_programs(
        self,
        country: Optional[str] = None,
        institution_type: Optional[str] = None,
        max_tuition: Optional[float] = None,
        duration_range: Optional[Tuple[int, int]] = None,
        limit: int = 20
    ) -> List[ProgramResult]
    
    def rank_programs_by_engagement(
        self, 
        programs: List[Program],
        weight_ctr: float = 0.4,
        weight_views: float = 0.3,
        weight_cost: float = 0.3
    ) -> List[RankedProgram]
    
    def get_program_recommendations(
        self,
        user_preferences: Dict[str, Any]
    ) -> List[ProgramRecommendation]
```

### 3. Database Access Layer

**Purpose**: Manages PostgreSQL connections, query execution, and data mapping

**Implementation Details** (from notebooks):
- Uses psycopg2 for PostgreSQL connectivity
- Implements connection pooling and environment-based configuration
- Handles complex data types (JSONB, arrays) and foreign key relationships
- Provides query builders for dynamic filtering and sorting

**Key Components**:
```python
class DatabaseManager:
    def __init__(self, connection_params: Dict[str, str])
    def get_connection(self) -> psycopg2.Connection
    def execute_query(self, query: str, params: Dict) -> List[Dict]
    def execute_batch(self, query: str, data: List[Dict]) -> None
    
class QueryBuilder:
    def build_program_search_query(self, filters: Dict) -> Tuple[str, Dict]
    def build_analytics_query(self, metric_type: str) -> str
    def build_ranking_query(self, criteria: Dict) -> str
```

### 4. MCP Protocol Handlers

**Purpose**: Implement MCP tools, resources, and prompts for program discovery

**Tools** (2 functions that DO things):
- `programs_list`: Search and filter educational programs with multiple criteria (country, institution, program name, budget)
- `rank_programs`: Rank programs by popularity, engagement, or cost-effectiveness using different scoring algorithms

**Resources** (1 reference guide):
- `usage_guide`: Static help document explaining available tools, parameters, and usage examples

**Prompts** (1 formatting template):
- `program_summary`: Template for creating user-friendly program summaries and recommendations

### 5. Analytics Engine

**Purpose**: Generate insights and statistics from the educational data

**Capabilities**:
- Country-level program distribution and engagement metrics
- Institution rankings by type and performance
- Tuition analysis by region and program duration
- Trend analysis and comparative statistics

## Data Models

### Core Data Models

```python
@dataclass
class Country:
    country_id: int
    name: str
    num_institutes: int
    total_programs: int
    avg_ctr: float
    total_views: int
    total_impressions: int
    top_programs: List[Dict[str, Any]]

@dataclass
class Institution:
    institution_id: int
    name: str
    country_id: int
    country_name: str
    institution_type: str
    ctr: float
    total_views: int
    total_impressions: int

@dataclass
class Program:
    program_id: int
    name: str
    institution_id: int
    institution_name: str
    country_id: int
    country_name: str
    duration_months: int
    tuition: Optional[float]
    ctr: float
    total_views: int
    total_impressions: int

@dataclass
class ProgramRecommendation:
    program: Program
    score: float
    ranking_factors: Dict[str, float]
    recommendation_reason: str
```

### MCP Response Models

```python
@dataclass
class SearchResult:
    programs: List[Program]
    total_count: int
    filters_applied: Dict[str, Any]
    execution_time_ms: int

@dataclass
class AnalyticsResult:
    metric_type: str
    data: Dict[str, Any]
    generated_at: datetime
    data_freshness: datetime
```

## Data Loading Strategy

Based on the notebook implementations:

### 1. Parquet File Processing
- **Country Data**: Loads from `gold_country_program_summary` with JSON handling for top_programs
- **Institution Data**: Loads from `gold_institute_engagement` with country mapping
- **Program Data**: Loads from `gold_program_engagement` with institution and country relationships

### 2. Data Transformation
- Converts numpy arrays to Python lists for JSON serialization
- Maps string-based foreign keys to integer IDs
- Handles missing data and creates new country/institution records as needed
- Implements data validation and type conversion

### 3. Database Loading
- Uses batch inserts with `execute_batch` for performance
- Implements upsert logic with `ON CONFLICT` clauses
- Maintains referential integrity through proper foreign key handling
- Includes timestamp tracking for data freshness

## Error Handling

### Database Connection Management
- Connection pooling with automatic retry for transient failures
- Environment-based configuration with validation
- Graceful degradation when database is unavailable
- Transaction rollback on data loading errors

### Data Quality Assurance
- Schema validation during Parquet loading
- Foreign key constraint handling with automatic relationship creation
- Data type validation and conversion error handling
- Duplicate detection and resolution strategies

## Performance Optimization

### Query Performance
- Optimized indexes on frequently filtered columns (country, institution_type, tuition, duration)
- Composite indexes for common query patterns
- JSONB indexing for top_programs searches
- Query plan analysis and optimization

### Caching Strategy
- In-memory caching for frequently accessed country and institution data
- Query result caching for common search patterns
- Cache invalidation on data updates
- Redis integration for distributed caching (future enhancement)

### Data Loading Performance
- Batch processing for large datasets
- Parallel loading of independent data sources
- Incremental updates for changed records only
- Connection pooling for concurrent operations

## Testing Strategy

### Data Pipeline Testing
- Unit tests for Parquet loading and transformation functions
- Integration tests with sample data from actual gold layer files
- Data quality validation tests
- Performance benchmarks for loading operations

### MCP Server Testing
- Protocol compliance testing against MCP specification
- End-to-end testing with real database connections
- Load testing for concurrent user scenarios
- Error handling and recovery testing

### Database Testing
- Schema migration testing
- Query performance testing with realistic data volumes
- Foreign key constraint validation
- Data integrity testing across all operations
##
 JSON-RPC Communication Protocol

### How JSON-RPC Works in MCP Server

**1. Claude Desktop call tool:**
Instead of calling `programs_list()` directly, Claude sends a JSON message:

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "programs_list",
    "arguments": {
      "country_name": "Germany",
      "max_tuition": 15000
    }
  },
  "id": 123
}
```

**2.  MCP server receives this and:**
- Parses the JSON message
- Calls actual `programs_list()` function
- Gets the results from database

**3. The MCPserver sends back the results:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "programs": [
      {"program_name": "Engineering", "tuition": 12000, ...},
      {"program_name": "Computer Science", "tuition": 14000, ...}
    ],
    "count": 25
  },
  "id": 123
}
```

### Why use JSON-RPC?

1. **Different Languages**: Claude (written in one language) can call Python server
2. **Different Processes**: They run as separate programs
3. **Standardized**: Everyone knows how JSON-RPC works
4. **Simple**: Just JSON messages back and forth

### In this case:
- **Claude Desktop** = JSON-RPC Client
- **MCP Server** = JSON-RPC Server
- **Communication** = JSON messages over stdin/stdout (like a pipe)

It's basically a way to make function calls between different programs feel like regular function calls!

## Development and Testing

### Local Development with MCP Inspector
```bash
uv run mcp dev ./src/server.py
```

This command:
- Starts your MCP server in development mode
- Launches the MCP Inspector web interface
- Allows you to test tools, resources, and prompts interactively
- Shows the actual JSON-RPC messages being exchanged

### Production with Claude Desktop
```bash
uv --directory /Users/vee/Desktop/univacity_mcp run src/server.py
```

This command is used by Claude Desktop to:
- Launch your MCP server as a subprocess
- Establish stdin/stdout JSON-RPC communication
- Enable real-time program discovery conversations