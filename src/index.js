const RENDER_URL_BASE = 'https://univacity-mcp.onrender.com';

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // Handle MCP SSE endpoint
    if (url.pathname === '/sse' || url.pathname === '/stream') {
      const targetUrl = RENDER_URL_BASE + '/sse' + url.search;
      
      try {
        const upstreamResponse = await fetch(targetUrl, {
          method: 'GET',
          headers: { Accept: 'text/event-stream' },
        });

        return new Response(upstreamResponse.body, {
          status: upstreamResponse.status,
          headers: {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
          },
        });
      } catch (err) {
        return new Response('Error: ' + err.message, { status: 500 });
      }
    }
    
    // Fallback SSE endpoint
    if (url.pathname === '/sse-fallback') {
      const stream = new ReadableStream({
        start(controller) {
          // Send MCP initialization
          const initMessage = {
            jsonrpc: '2.0',
            method: 'initialize',
            params: {
              protocolVersion: '2024-11-05',
              capabilities: {
                tools: {},
                resources: {},
                prompts: {}
              },
              clientInfo: {
                name: 'EduMatch MCP Server',
                version: '1.0.0'
              }
            }
          };
          
          controller.enqueue(new TextEncoder().encode(`data: ${JSON.stringify(initMessage)}\n\n`));
          
          // Send tools list
          const toolsMessage = {
            jsonrpc: '2.0',
            method: 'tools/list',
            result: {
              tools: [
                {
                  name: 'programs_list',
                  description: 'Search and filter educational programs',
                  inputSchema: {
                    type: 'object',
                    properties: {
                      program_name: { type: 'string' },
                      country_name: { type: 'string' },
                      institution_name: { type: 'string' },
                      max_tuition: { type: 'number' },
                      limit: { type: 'number', default: 20 },
                      offset: { type: 'number', default: 0 }
                    }
                  }
                },
                {
                  name: 'rank_programs',
                  description: 'Get ranked program recommendations',
                  inputSchema: {
                    type: 'object',
                    properties: {
                      country_name: { type: 'string' },
                      institution_name: { type: 'string' },
                      max_tuition: { type: 'number' },
                      ranking_method: { type: 'string', default: 'popularity' },
                      limit: { type: 'number', default: 10 }
                    }
                  }
                }
              ]
            }
          };
          
          controller.enqueue(new TextEncoder().encode(`data: ${JSON.stringify(toolsMessage)}\n\n`));
        }
      });

      return new Response(stream, {
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
          'Access-Control-Allow-Origin': '*'
        },
      });
    }

    // Handle MCP tool calls by proxying to FastAPI
    if (url.pathname === '/tools/call') {
      const body = await request.json();
      const toolName = body.params?.name;
      const toolArgs = body.params?.arguments || {};
      
      let endpoint = '';
      if (toolName === 'programs_list') {
        endpoint = '/programs';
      } else if (toolName === 'rank_programs') {
        endpoint = '/rank';
      } else {
        return new Response(JSON.stringify({
          jsonrpc: '2.0',
          id: body.id,
          error: { code: -32601, message: 'Method not found' }
        }), { headers: { 'Content-Type': 'application/json' } });
      }
      
      try {
        const response = await fetch(RENDER_URL_BASE + endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(toolArgs)
        });
        
        const result = await response.json();
        
        return new Response(JSON.stringify({
          jsonrpc: '2.0',
          id: body.id,
          result: { content: [{ type: 'text', text: JSON.stringify(result) }] }
        }), { headers: { 'Content-Type': 'application/json' } });
      } catch (err) {
        return new Response(JSON.stringify({
          jsonrpc: '2.0',
          id: body.id,
          error: { code: -32603, message: err.message }
        }), { headers: { 'Content-Type': 'application/json' } });
      }
    }

    // Normal proxy fallback
    const targetUrl = RENDER_URL_BASE + url.pathname + url.search;
    try {
      const response = await fetch(targetUrl, {
        method: request.method,
        headers: request.headers,
        body: request.body,
      });

      return new Response(response.body, {
        status: response.status,
        headers: response.headers,
      });
    } catch (err) {
      return new Response('Error connecting to Render MCP server: ' + err.message, {
        status: 500,
      });
    }
  },
};