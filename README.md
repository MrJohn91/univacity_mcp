# EduMatch MCP Server

A Model Context Protocol (MCP) server that provides intelligent educational program recommendations using PostgreSQL as the data backend. The server offers both local MCP protocol support for Claude Desktop integration and cloud-deployed HTTP API endpoints with GitHub OAuth authentication.

## 🏗️ Architecture Overview

### Dual Server Architecture

The project implements a dual-server architecture to support both local MCP protocol and cloud HTTP API access:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Claude Desktop │    │  MCP Inspector   │    │  Web Clients    │
│                 │    │                  │    │                 │
└─────────┬───────┘    └─────────┬────────┘    └─────────┬───────┘
          │                      │                       │
          │ stdio                │ HTTP                  │ HTTP
          │                      │                       │
┌─────────▼───────┐    ┌─────────▼────────┐    ┌─────────▼───────┐
│   server.py     │    │  api_server.py   │    │  api_server.py  │
│  (Local MCP)    │    │  (Local HTTP)    │    │  (Cloud HTTP)   │
│                 │    │                  │    │  + OAuth Auth   │
└─────────┬───────┘    └─────────┬────────┘    └─────────┬───────┘
          │                      │                       │
          └──────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │     PostgreSQL Database   │
                    │   (Local → Cloud Migration)│
                    └───────────────────────────┘
```

### Why Two Servers?

1. **`server.py`** - Pure MCP Protocol Server
   - Direct FastMCP implementation
   - Optimized for Claude Desktop integration
   - Uses stdio transport for local communication
   - No HTTP overhead

2. **`api_server.py`** - HTTP API Wrapper
   - FastAPI web server wrapping MCP functionality
   - Supports HTTP/HTTPS for web access
   - Includes GitHub OAuth authentication
   - Enables cloud deployment and web testing

##  Quick Start

### Prerequisites

- Python 3.8+
- UV package manager
- PostgreSQL database
- GitHub OAuth App (for cloud deployment)

## 📊 Data Analysis & Setup Notebooks

The project includes comprehensive Jupyter notebooks for data exploration, database setup, and data migration:

### Core Data Processing Notebooks

- **`explore_gold_data.ipynb`** - Comprehensive exploration of gold layer datasets
  - **Data Loading**: Loads and analyzes all 4 gold layer Parquet files with automatic file discovery
  - **Dataset Overview**: 5,977 programs across 98 institutions in 26+ countries
  - **Data Quality Analysis**: No missing values found, comprehensive statistical summaries
  - **Engagement Metrics**: CTR ranges from 0.007 to 0.982 (average 0.436), total views up to 915K
  - **Financial Analysis**: Tuition ranges from $0 to $1M+ with detailed cost distribution
  - **Program Diversity**: Duration spans 1-96 months, covering global educational offerings
  - **Complex Data Handling**: Processes nested JSON structures (top_programs arrays) and country arrays
  - **Performance Insights**: Identifies top-performing countries (UK, Portugal, Turkey) by engagement

- **`db_design.ipynb`** - Database schema creation and management
  - **Schema Creation**: Establishes normalized PostgreSQL database with 3 core tables
  - **Relationship Design**: Implements proper foreign key constraints (countries ← institutions ← programs)
  - **Data Type Optimization**: Uses SERIAL for IDs, NUMERIC for precision, JSONB for complex data
  - **Index Strategy**: Creates performance indexes on frequently queried columns (CTR, country, tuition)
  - **Schema Evolution**: Handles column modifications and constraint additions dynamically
  - **JSONB Integration**: Stores complex nested program data (top_programs arrays) efficiently
  - **Connection Management**: Uses environment variables for secure database configuration

### Data Loading Notebooks

- **`country_dataload.ipynb`** - Country data extraction and loading
  - **Data Processing**: Extracts country-level aggregated metrics from Spark-processed Parquet files
  - **JSON Handling**: Converts numpy arrays to JSON-serializable format for top_programs field
  - **Engagement Mapping**: Processes CTR, views, impressions, and country rankings
  - **Data Volume**: Successfully loads 26 countries with complete statistical profiles
  - **Conflict Resolution**: Implements ON CONFLICT DO UPDATE for data refresh scenarios
  - **Data Validation**: Ensures data integrity with proper type conversions and null handling
  - **Performance**: Uses execute_values for efficient batch insertion

- **`institute_dataload.ipynb`** - Institution data processing and insertion
  - **Data Extraction**: Processes institution engagement data with country relationship mapping
  - **Foreign Key Management**: Creates country_id mappings and handles missing country references
  - **Dynamic Data Creation**: Automatically creates missing countries (Ghana, Rwanda, Zimbabwe) during import
  - **Institution Classification**: Processes 98 institutions with PUBLIC/PRIVATE type categorization
  - **Engagement Processing**: Maps CTR, views, impressions, and ranking data for each institution
  - **Data Integrity**: Validates foreign key relationships and handles constraint violations
  - **Batch Processing**: Uses iterative insertion with proper error handling and rollback support

- **`program_dataload.ipynb`** - Individual program data migration
  - **Large-Scale Processing**: Handles the largest dataset with 5,977 individual programs
  - **ID Mapping Complexity**: Converts MongoDB ObjectIDs to PostgreSQL integer foreign keys
  - **Dynamic Relationship Creation**: Creates missing institutions and countries on-the-fly during import
  - **Data Type Handling**: Manages complex conversions (numpy arrays, nullable integers, decimal precision)
  - **Performance Optimization**: Uses execute_batch for efficient bulk insertion (5,969 programs loaded)
  - **Comprehensive Attributes**: Maps program name, duration, tuition, CTR, views, impressions, rankings
  - **Data Cleaning**: Handles null countries (8 programs) and ensures referential integrity
  - **Error Recovery**: Implements transaction rollback and data validation throughout the process

These notebooks collectively migrate data from Spark-processed Parquet files to a normalized PostgreSQL database, ensuring data integrity and establishing proper relationships for the MCP server to query efficiently.

### Local Development

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd univacity_mcp
   uv sync
   ```

2. **Database Setup**
   ```bash
   # Configure database connection in src/config.py
   # Load your educational data into PostgreSQL
   ```

3. **Run Local MCP Server**
   ```bash
   # For Claude Desktop integration
   uv run src/server.py
   
   # For development with MCP Inspector
   uv run mcp dev ./src/server.py
   ```

4. **Run Local HTTP API Server**
   ```bash
   # For web testing and development
   uv run src/api_server.py
   # Server runs on http://localhost:8000
   ```

### Cloud Deployment

The server is deployed on Render with Cloudflare CDN:
- **Production URL**: `https://your-domain.com`
- **MCP Endpoint**: `/streamable`
- **Authentication**: GitHub OAuth required

## 🔐 Authentication & Security

### GitHub OAuth Integration

The cloud deployment uses GitHub OAuth for authentication with restricted access to specific users.

#### How OAuth Works

OAuth is like getting a temporary pass: you prove who you are to GitHub, GitHub gives you a special token, and you use that token to access the MCP server.

**The Process:**
1. **User clicks login** → Gets redirected to GitHub to prove identity
2. **GitHub verifies user** → Sends back a temporary code to our server
3. **Our server exchanges code for token** → Gets a permanent access token from GitHub
4. **Server checks if user is authorized** → Only specific GitHub usernames are allowed access
5. **User uses token** → Can now access MCP tools with the token as proof of identity

1. **Get Authorization Code**
   - User visits: `/auth/github/authorize`
   - Redirected to GitHub to login
   - GitHub returns with authorization code

2. **Exchange Code for Token**
   ```python
   # Server exchanges code for access token
   response = requests.post('https://github.com/login/oauth/access_token', {
       'client_id': GITHUB_CLIENT_ID,
       'client_secret': GITHUB_CLIENT_SECRET, 
       'code': authorization_code
   })
   access_token = response.json()['access_token']
   ```

3. **Use Token for API Access**
   ```bash
   curl -H "Authorization: Bearer ACCESS_TOKEN" \
     https://your-domain.com/streamable
   ```

#### Configuration
- **Authorized Users**: Only specific GitHub usernames can access MCP tools
- **Token Validation**: Each request validates token against GitHub API
- **Automatic Expiry**: Tokens expire and require re-authentication

#### Security Features
- Only authorized GitHub users can access MCP tools
- Token validation against GitHub API
- Secure credential storage (excluded from git)
- Rate limiting and error handling

## 🛠️ MCP Server Components

### Tools (2)
1. **`programs_list`** - Search and filter educational programs
   ```json
   {
     "program_name": "computer science",
     "country_name": "Germany", 
     "max_tuition": 20000,
     "limit": 10
   }
   ```

2. **`rank_programs`** - Rank programs by engagement metrics
   ```json
   {
     "country_name": "Canada",
     "ranking_method": "popularity",
     "limit": 5
   }
   ```

### Resources (1)
1. **`guide://usage`** - Usage guide and documentation
   - Tool descriptions and examples
   - Data insights and metrics explanation
   - Best practices for AI agents

### Prompts (1)
1. **`program_summary`** - Template for user-friendly program presentations
   - Structured output format
   - Engagement metrics translation
   - Consistent recommendation styling

##  Database Architecture

### Local to Cloud Migration

The project evolved from local PostgreSQL to cloud-hosted database:

#### Local Development
```python
# src/config.py - Local configuration
DATABASE_URL = "postgresql://user:password@localhost:5432/univacity_db"
```

#### Cloud Production
```python
# src/config.py - Cloud configuration  
DATABASE_URL = os.environ.get("DATABASE_URL")  # Render PostgreSQL
```

#### Migration Process
1. **Data Export**: Local database dumped to `univacity_db.dump`
2. **Cloud Setup**: Render PostgreSQL instance provisioned
3. **Data Import**: Dump file restored to cloud database
4. **Connection Update**: Environment variables configured
5. **Verification**: Data integrity and performance testing

### Database Schema
```sql
-- Core tables
CREATE TABLE countries (
    country_id SERIAL PRIMARY KEY,
    institute_country VARCHAR(255) UNIQUE
);

CREATE TABLE institutions (
    institution_id SERIAL PRIMARY KEY,
    institution_name VARCHAR(255),
    country_id INTEGER REFERENCES countries(country_id)
);

CREATE TABLE programs (
    program_id SERIAL PRIMARY KEY,
    program_name VARCHAR(255),
    country_id INTEGER REFERENCES countries(country_id),
    institution_id INTEGER REFERENCES institutions(institution_id),
    duration_months INTEGER,
    tuition DECIMAL(10,2),
    ctr DECIMAL(5,4),
    total_views INTEGER,
    total_impressions INTEGER
);
```

## Testing & Development

### MCP Inspector Testing

1. **Install MCP Inspector**
   ```bash
   git clone https://github.com/modelcontextprotocol/inspector.git
   cd inspector
   npm install
   npm start
   ```

2. **Test Local Server**
   ```
   Transport: Streamable HTTP
   URL: http://localhost:8000/streamable
   Auth: Bearer YOUR_GITHUB_TOKEN
   ```

3. **Test Cloud Server**
   ```
   Transport: Streamable HTTP  
   URL: https://your-domain.com/streamable
   Auth: Bearer YOUR_GITHUB_TOKEN
   ```

### Claude Desktop Integration

Configure Claude Desktop to use the local MCP server:

```json
{
  "mcpServers": {
    "edumatch": {
      "command": "/opt/homebrew/bin/uv",
      "args": ["--directory", "/Users/vee/Desktop/univacity_mcp", "run", "src/server.py"]
    }
  }
}
```

## API Endpoints

### MCP Protocol Endpoints
- `POST /` - MCP JSON-RPC handler
- `POST /streamable` - Streamable HTTP transport
- `GET /sse` - Server-Sent Events (legacy)

### OAuth Endpoints
- `GET /auth/github/authorize` - GitHub OAuth authorization
- `POST /auth/github/token` - Token exchange
- `GET /user` - Get authenticated user info
- `GET /callback` - OAuth callback handler

### Utility Endpoints
- `GET /` - Server status
- `POST /programs` - Direct programs endpoint
- `POST /rank` - Direct ranking endpoint
- `GET /usage` - Usage guide

## 🔧 Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:password@host:port/database

# GitHub OAuth (for cloud deployment)
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret

# Server
PORT=8000
```

### File Structure
```
univacity_mcp/
├── src/
│   ├── server.py                    # Pure MCP server (local)
│   ├── api_server.py                # HTTP API wrapper (cloud)
│   ├── config.py                    # Database configuration
│   ├── requirements.txt             # Python dependencies
│   ├── explore_gold_data.ipynb      # Data exploration and analysis
│   ├── db_design.ipynb              # Database schema creation
│   ├── country_dataload.ipynb       # Country data loading
│   ├── institute_dataload.ipynb     # Institution data loading
│   └── program_dataload.ipynb       # Program data loading
├── local_data/                      # Spark-processed data layers
│   ├── bronze/                      # Raw data ingestion
│   ├── silver/                      # Cleaned and validated data
│   └── gold/                        # Business-ready aggregated data
├── .gitignore                       # Excludes test files and secrets
├── README.md                        # This file
└── pyproject.toml                   # UV project configuration
```

## Deployment

### Local Development Commands
```bash
# MCP Server for Claude Desktop
uv run src/server.py

# MCP Server with development tools
uv run mcp dev ./src/server.py

# HTTP API Server for testing
uv run src/api_server.py
```

### Cloud Deployment (Render)
1. **GitHub Integration**: Automatic deployment on push to main
2. **Environment Setup**: Configure DATABASE_URL and OAuth secrets
3. **Build Command**: `uv sync`
4. **Start Command**: `uv run src/api_server.py`

### Cloudflare CDN
- **Origin**: Render deployment
- **CDN URL**: `https://your-domain.com`
- **Benefits**: Global edge caching, DDoS protection, SSL termination

## 🔍 Monitoring & Debugging

### Logs and Debugging
```bash
# Local server logs
uv run src/api_server.py  # Watch console output

# Test authentication
curl -H "Authorization: Bearer TOKEN" \
  https://univacitymcp.nfluncvjohn.workers.dev/user

# Test MCP endpoints
curl -X POST https://your-domain.com/streamable \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}'
```

##  Contributing

1. Fork the repository
2. Create a feature branch
3. Test locally with MCP Inspector
4. Ensure authentication works
5. Submit pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the usage guide resource in the MCP server
2. Test with MCP Inspector for debugging
3. Verify GitHub OAuth token validity
4. Check database connectivity

---

**Built with using FastMCP, FastAPI, and PostgreSQL**