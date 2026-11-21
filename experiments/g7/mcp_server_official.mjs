import fs from 'node:fs';
import { McpServer } from '@modelcontextprotocol/server';
import { StdioServerTransport } from '@modelcontextprotocol/server/stdio';
import * as z from 'zod/v4';

const records = JSON.parse(fs.readFileSync(new URL('./server_cases.json', import.meta.url), 'utf8')).cases;
const server = new McpServer({ name: 's2ai-official-runtime-fixture', version: '1.0.0' });

server.registerTool(
  'query_blockers',
  {
    description: 'Return the frozen model-visible blocker-query projection for one confirmatory case.',
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

await server.connect(new StdioServerTransport());
