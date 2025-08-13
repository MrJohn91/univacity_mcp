# Requirements Document

## Introduction

This feature implements a local Model Context Protocol (MCP) server that serves as a Program Discovery Assistant for educational programs. The server leverages pre-aggregated gold-layer educational analytics stored in a PostgreSQL database to help students, counselors, and AI agents discover and evaluate study programs based on preferences such as country, institution, tuition, duration, and engagement metrics.

The MCP server reads data directly from PostgreSQL, which is pre-loaded and maintained externally from Parquet files. The system provides intelligent program recommendations, interactive query capabilities, and analytics insights based on engagement metrics like click-through rates, views, and impressions.

## Requirements

### 1. Programs List Tool - Search and Filtering

**User Story:** As a user (student/counselor), I want to search programs by specific criteria, so that I can find study programs that match my preferences for country, institution, program name, and cost.

#### Acceptance Criteria

1. WHEN a user calls the programs_list tool with country_name filter THEN the system SHALL return programs available in specified countries
2. WHEN a user calls the programs_list tool with institution_name filter THEN the system SHALL return programs from specified institutions
3. WHEN a user calls the programs_list tool with max_tuition filter THEN the system SHALL return programs within the specified tuition range
4. WHEN a user calls the programs_list tool with program_name filter THEN the system SHALL return programs matching the specified name pattern
5. WHEN multiple filters are applied THEN the system SHALL return programs matching all specified criteria with proper pagination using limit and offset

### 2. Rank Programs Tool - Scoring and Ranking

**User Story:** As an AI agent, I want to score and rank programs for personalized recommendations, so that I can provide users with the most relevant and high-quality program suggestions.

#### Acceptance Criteria

1. WHEN the rank_programs tool is called with "popularity" method THEN the system SHALL rank programs using total views and impressions
2. WHEN the rank_programs tool is called with "engagement" method THEN the system SHALL rank programs using click-through rates (CTR)
3. WHEN the rank_programs tool is called with "cost_effectiveness" method THEN the system SHALL rank programs by views per tuition cost
4. WHEN filters are provided THEN the system SHALL apply country, institution, and cost filters before ranking
5. WHEN returning ranked results THEN the system SHALL include ranking score and method used

### 3. Usage Guide Resource - Reference Documentation

**User Story:** As an AI agent, I want to access usage documentation, so that I can understand available tools and provide accurate guidance to users.

#### Acceptance Criteria

1. WHEN the usage_guide resource is accessed THEN the system SHALL provide descriptions of all available tools
2. WHEN accessing the usage guide THEN the system SHALL include key filter options and examples for each tool
3. WHEN viewing the guide THEN the system SHALL explain data insights including metrics and cost information
4. WHEN referencing the guide THEN the system SHALL provide practical examples of tool usage
5. WHEN using the guide THEN the system SHALL help AI agents understand program data structure

### 4. Program Summary Prompt - User-Friendly Output

**User Story:** As an AI agent, I want to generate user-friendly summaries and recommendations, so that I can present program information in an accessible and engaging format.

#### Acceptance Criteria

1. WHEN the program_summary prompt is used THEN the system SHALL provide a structured template for program presentations
2. WHEN generating summaries THEN the system SHALL include key program details (name, institution, country, duration, tuition)
3. WHEN creating recommendations THEN the system SHALL explain engagement metrics in user-friendly terms
4. WHEN summarizing multiple programs THEN the system SHALL provide total counts and key insights
5. WHEN generating output THEN the system SHALL maintain a helpful and informative tone

### 4. Analytics and Insights Tool

**User Story:** As a user, I want to access quick statistics and insights from the education dataset, so that I can understand trends and make informed decisions about study destinations and programs.

#### Acceptance Criteria

1. WHEN requesting country analytics THEN the system SHALL return most popular countries by views and program count
2. WHEN requesting tuition insights THEN the system SHALL provide average tuition by region and program type
3. WHEN requesting institution analytics THEN the system SHALL return top institutions by engagement metrics
4. WHEN requesting program trends THEN the system SHALL show most viewed and highest CTR programs
5. WHEN generating insights THEN the system SHALL provide comparative statistics and trend analysis

### 5. Interactive Query Processing

**User Story:** As an AI agent, I want to process dynamic user queries with natural language parameters, so that I can translate user preferences into database queries and return relevant results.

#### Acceptance Criteria

1. WHEN processing field of study queries THEN the system SHALL map user interests to relevant program categories
2. WHEN handling location preferences THEN the system SHALL support country, region, and city-level filtering
3. WHEN interpreting budget constraints THEN the system SHALL convert currency and apply appropriate tuition filters
4. WHEN processing duration preferences THEN the system SHALL handle various time formats and academic calendar systems
5. WHEN queries return no results THEN the system SHALL suggest alternative criteria or similar options

### 6. Data Freshness and Quality Management

**User Story:** As a system administrator, I want to ensure data quality and freshness, so that users receive accurate and up-to-date program information.

#### Acceptance Criteria

1. WHEN the server starts THEN it SHALL establish connection to PostgreSQL with data validation checks
2. WHEN data is refreshed externally THEN the system SHALL detect updates and invalidate relevant caches
3. WHEN data quality issues are detected THEN the system SHALL log warnings and exclude problematic records
4. WHEN serving stale data THEN the system SHALL include data freshness indicators in responses
5. WHEN database connectivity fails THEN the system SHALL gracefully degrade using cached data with appropriate warnings

### 7. Multi-Language and Localization Support

**User Story:** As a global user, I want program information presented in my preferred language and cultural context, so that I can better understand and evaluate international study options.

#### Acceptance Criteria

1. WHEN requesting localized content THEN the system SHALL translate program names and descriptions where available
2. WHEN displaying costs THEN the system SHALL convert currencies and provide local context
3. WHEN showing duration THEN the system SHALL adapt to local academic calendar systems
4. WHEN generating recommendations THEN the system SHALL consider cultural preferences and educational systems
5. WHEN localization data is unavailable THEN the system SHALL provide clear indicators and fallback to English

### 8. Performance and Scalability

**User Story:** As a system user, I want fast and reliable responses to my queries, so that I can efficiently explore and compare educational programs.

#### Acceptance Criteria

1. WHEN processing simple queries THEN the system SHALL respond within 500ms
2. WHEN handling complex multi-filter queries THEN the system SHALL respond within 2 seconds
3. WHEN serving concurrent requests THEN the system SHALL maintain performance for up to 50 simultaneous users
4. WHEN caching is enabled THEN the system SHALL achieve 80%+ cache hit rate for repeated queries
5. WHEN system load is high THEN the system SHALL implement graceful degradation and queue management

## MCP Server Components (MVP)

### Tools (2 functions that DO things)

1. **`programs_list`** - Searches database for educational programs with filters (country, budget, institution, program name) with pagination support
2. **`rank_programs`** - Ranks programs by popularity, engagement, or cost-effectiveness using different scoring algorithms

### Resources (1 reference guide)

1. **`usage_guide`** - Static help document explaining what tools are available and how to use them, including examples and data insights

### Prompts (1 formatting template)

1. **`program_summary`** - Template telling AI assistants how to nicely format program recommendations for users with structured output

## Technical Notes

The MCP server implements a Program Discovery Assistant architecture using PostgreSQL for efficient querying of educational program data. The system focuses on user experience through intelligent filtering, scoring algorithms, and natural language processing capabilities. Data is maintained externally from Parquet files, ensuring the MCP server always serves current analytics while providing fast, scalable access to program information for students and counselors worldwide.

## Claude Desktop Integration

### 9. Claude Desktop Client Integration

**User Story:** As a user, I want to access the EduMatch program discovery features directly through Claude Desktop, so that I can get personalized study program recommendations in a conversational interface.

#### Acceptance Criteria

1. WHEN Claude Desktop is configured with the EduMatch MCP server THEN the system SHALL be accessible through the "edumatch" server name
2. WHEN a user asks Claude about study programs THEN Claude SHALL be able to call the programs_list and rank_programs tools
3. WHEN Claude needs guidance THEN it SHALL access the usage_guide resource for tool documentation
4. WHEN Claude presents program recommendations THEN it SHALL use the program_summary prompt template for consistent formatting
5. WHEN the MCP server is running THEN Claude Desktop SHALL maintain a persistent connection for real-time program queries

### Client Configuration

The MCP server is configured in Claude Desktop with the following settings:

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

### MCP Protocol Interaction Flow

**How Claude Desktop communicates with the EduMatch MCP Server:**

1. **Server Discovery**: Claude Desktop connects to the MCP server via the configured command and establishes a JSON-RPC connection
2. **Capability Exchange**: Claude requests available tools, resources, and prompts from the server
3. **Resource Access**: Claude can call `mcp://usage_guide` to understand available functionality
4. **Tool Execution**: Claude makes JSON-RPC calls to execute tools with parameters
5. **Prompt Templates**: Claude can request prompt templates to format responses consistently

**User Experience Flow:**

1. **User Query**: "Find engineering programs in Germany under $15,000"
2. **Claude MCP Call**: `GET mcp://usage_guide` to understand available tools
3. **Claude MCP Call**: `tools/call programs_list` with parameters `{country_name: "Germany", max_tuition: 15000, program_name: "engineering"}`
4. **Server Response**: Database query results returned via MCP protocol
5. **Claude MCP Call**: `prompts/get program_summary` to get formatting template
6. **Claude Response**: Formats results using the template and presents to user

## Development Commands

### Local Development
```bash
uv run mcp dev ./src/server.py
```

### Production with Claude Desktop
```bash
uv --directory /Users/vee/Desktop/univacity_mcp run src/server.py
```