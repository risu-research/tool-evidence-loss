import fs from 'node:fs';
import http from 'node:http';
import { Readable } from 'node:stream';
import { createMcpHandler, McpServer } from '@modelcontextprotocol/server';
import * as z from 'zod/v4';

const records = JSON.parse(fs.readFileSync(new URL('./cases.json', import.meta.url), 'utf8')).cases;

const handler = createMcpHandler(() => {
  const server = new McpServer({ name: 'runtime-transport-fixture', version: '1.0.0' });
  server.registerTool(
    'query_blockers',
    {
      description: 'Return one frozen model-visible query projection.',
      inputSchema: z.object({ caseId: z.string() }),
    },
    async ({ caseId }) => {
      const rec = records[caseId];
      if (!rec) throw new Error(`Unknown caseId: ${caseId}`);
      return {
        content: [{ type: 'text', text: JSON.stringify(rec.visibleR3) }],
        _meta: { sourceEvidence: rec.sourceEvidence },
      };
    },
  );
  return server;
});

const port = 8765;
const host = '127.0.0.1';
const server = http.createServer(async (req, res) => {
  try {
    if (req.url !== '/mcp') {
      res.statusCode = 404;
      res.end('not found');
      return;
    }
    const chunks = [];
    for await (const chunk of req) chunks.push(chunk);
    const body = Buffer.concat(chunks);
    const init = { method: req.method, headers: req.headers };
    if (req.method !== 'GET' && req.method !== 'HEAD' && body.length > 0) {
      init.body = body;
      init.duplex = 'half';
    }
    const response = await handler.fetch(new Request(`http://${host}:${port}${req.url}`, init));
    res.statusCode = response.status;
    response.headers.forEach((value, key) => res.setHeader(key, value));
    if (!response.body) {
      res.end();
      return;
    }
    Readable.fromWeb(response.body).pipe(res);
  } catch (error) {
    console.error(error?.stack || error);
    if (!res.headersSent) res.statusCode = 500;
    res.end('internal error');
  }
});

server.listen(port, host, () => {
  console.log(`READY http://${host}:${port}/mcp`);
});

async function shutdown() {
  try { await handler.close?.(); } catch {}
  server.close(() => process.exit(0));
  setTimeout(() => process.exit(1), 2000).unref();
}
process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);
