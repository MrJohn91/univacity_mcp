const RENDER_URL_BASE = 'https://univacity-mcp.onrender.com';

addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  const url = new URL(request.url);
  const path = url.pathname;

  // Handle OPTIONS for CORS preflight
  if (request.method === 'OPTIONS') {
    return new Response(null, {
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': '*'
      }
    });
  }

  // Handle SSE / MCP Inspector endpoints
  if (path === '/sse' || path === '/stream') {
    try {
      const upstreamResponse = await fetch(RENDER_URL_BASE + path + url.search, {
        method: 'GET',
        headers: { Accept: 'text/event-stream' },
      });

      const newHeaders = new Headers(upstreamResponse.headers);
      newHeaders.set('Access-Control-Allow-Origin', '*');
      newHeaders.set('Cache-Control', 'no-cache');
      newHeaders.set('Connection', 'keep-alive');
      newHeaders.set('Content-Type', 'text/event-stream');

      return new Response(upstreamResponse.body, {
        status: upstreamResponse.status,
        headers: newHeaders,
      });
    } catch (err) {
      return new Response('Error: ' + err.message, { status: 500 });
    }
  }

  // Fallback SSE stream with MCP init (optional)
  if (path === '/sse-fallback') {
    const stream = new ReadableStream({
      start(controller) {
        const initMessage = {
          jsonrpc: '2.0',
          method: 'initialize',
          params: {
            protocolVersion: '2024-11-05',
            capabilities: { tools: {}, resources: {}, prompts: {} },
            clientInfo: { name: 'EduMatch MCP Server', version: '1.0.0' }
          }
        };
        controller.enqueue(new TextEncoder().encode(`data: ${JSON.stringify(initMessage)}\n\n`));

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

  // Handle MCP tool calls
  if (path === '/tools/call') {
    if (request.method !== 'POST') {
      return new Response(JSON.stringify({
        jsonrpc: '2.0',
        error: { code: -32600, message: 'Invalid request method, use POST' }
      }), { headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' } });
    }

    let body;
    try {
      body = await request.json();
    } catch (err) {
      return new Response(JSON.stringify({
        jsonrpc: '2.0',
        error: { code: -32700, message: 'Invalid JSON body' }
      }), { headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' } });
    }

    const toolName = body.params?.name;
    const toolArgs = body.params?.arguments || {};
    let endpoint = '';
    if (toolName === 'programs_list') endpoint = '/programs';
    else if (toolName === 'rank_programs') endpoint = '/rank';
    else return new Response(JSON.stringify({
      jsonrpc: '2.0',
      id: body.id,
      error: { code: -32601, message: 'Method not found' }
    }), { headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' } });

    try {
      const resp = await fetch(RENDER_URL_BASE + endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(toolArgs)
      });
      const result = await resp.json();
      return new Response(JSON.stringify({ jsonrpc: '2.0', id: body.id, result }), {
        headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
      });
    } catch (err) {
      return new Response(JSON.stringify({
        jsonrpc: '2.0',
        id: body.id,
        error: { code: -32603, message: err.message }
      }), { headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' } });
    }
  }

  // Fallback proxy for all other requests
  try {
    const resp = await fetch(RENDER_URL_BASE + path + url.search, {
      method: request.method,
      headers: request.headers,
      body: request.body
    });
    const newHeaders = new Headers(resp.headers);
    newHeaders.set('Access-Control-Allow-Origin', '*');
    return new Response(resp.body, { status: resp.status, headers: newHeaders });
  } catch (err) {
    return new Response('Error connecting to Render MCP server: ' + err.message, { status: 500 });
  }
}