import type { ParsedRepo } from '@/types';

const API_URL = import.meta.env.VITE_GITINGEST_API ?? 'https://gitingest.com/api/ingest';

export function splitRepoInputs(raw: string): string[] {
  return raw.split(/[\n,\s]+/).map((x) => x.trim()).filter(Boolean);
}

export function parseRepoInput(raw: string): ParsedRepo | null {
  const t = raw.trim().replace(/\/$/, '');
  const url = t.match(/^https?:\/\/github\.com\/([^/]+)\/([^/\s]+)(?:\/tree\/([^\s/]+))?/i);
  if (url) return { url: `https://github.com/${url[1]}/${url[2]}`, owner: url[1], name: url[2], branch: url[3] };
  const short = t.match(/^([^/\s]+)\/([^@\s]+)(?:@([^\s]+))?$/);
  if (short) return { url: `https://github.com/${short[1]}/${short[2]}`, owner: short[1], name: short[2], branch: short[3] };
  return null;
}

export type Digest = { summary: string; tree: string; content: string; tokenEstimate: number; fileCount: number };

export async function fetchRepoDigest(repo: ParsedRepo, signal?: AbortSignal): Promise<Digest> {
  const res = await fetch(API_URL, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url: repo.url, branch: repo.branch }), signal });
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`);
  const d = await res.json() as { summary: string; tree: string; content: string };
  const tk = d.summary.match(/Estimated tokens:\s*([\d.]+)([km]?)/i); const fv = d.summary.match(/Files analyzed:\s*(\d+)/i);
  const tokenEstimate = tk ? Number(tk[1]) * (tk[2]?.toLowerCase() === 'k' ? 1e3 : tk[2]?.toLowerCase() === 'm' ? 1e6 : 1) : 0;
  return { ...d, tokenEstimate: Math.round(tokenEstimate), fileCount: fv ? Number(fv[1]) : 0 };
}

export const toMarkdown = (r: ParsedRepo, d: Digest) => `# ${r.owner}/${r.name}${r.branch ? `@${r.branch}` : ''}\n\n${d.summary}\n\n## Directory Structure\n\n\
\
${d.tree}\n\
\
\n## Code Digest\n\n${d.content}\n`;
