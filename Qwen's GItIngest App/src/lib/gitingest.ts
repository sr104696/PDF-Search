import type { ParsedRepo } from "@/types";

// Accepts: full GitHub URLs, github.com/owner/repo/tree/branch, owner/repo, owner/repo@branch
export function parseRepoInput(raw: string): ParsedRepo | null {
  const trimmed = raw.trim();
  if (!trimmed) return null;

  const urlMatch = trimmed.match(
    /^https?:\/\/github\.com\/([^/]+)\/([^/@\s]+)(?:\/tree\/([^/\s]+))?/
  );
  if (urlMatch) {
    const [, owner, name, branch] = urlMatch;
    return { url: `https://github.com/${owner}/${name}`, owner, name, branch };
  }

  const shortMatch = trimmed.match(/^([^/\s]+)\/([^@\s]+)(?:@([^\s]+))?$/);
  if (shortMatch) {
    const [, owner, name, branch] = shortMatch;
    return { url: `https://github.com/${owner}/${name}`, owner, name, branch };
  }

  return null;
}

export function splitRepoInputs(raw: string): string[] {
  return raw.split(/[\n,\s]+/).map((s) => s.trim()).filter(Boolean);
}

export interface GitIngestResult {
  summary: string;
  tree: string;
  content: string;
  tokenEstimate: number;
  fileCount: number;
}

const API_BASE = (typeof import.meta !== "undefined" && import.meta.env?.VITE_GITINGEST_API)
  ?? "https://gitingest.com/api/ingest";

export async function fetchRepoDigest(
  repo: ParsedRepo,
  signal?: AbortSignal
): Promise<GitIngestResult> {
  const body: Record<string, unknown> = { url: repo.url };
  if (repo.branch) body.branch = repo.branch;

  const res = await fetch(API_BASE, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`GitIngest API error ${res.status}: ${text}`);
  }

  const data = (await res.json()) as { summary: string; tree: string; content: string };

  const tokenMatch = data.summary.match(/Estimated tokens:\s*([\d.]+)([km]?)/i);
  let tokenEstimate = 0;
  if (tokenMatch) {
    const val = parseFloat(tokenMatch[1]);
    const unit = tokenMatch[2].toLowerCase();
    tokenEstimate = unit === "k" ? val * 1000 : unit === "m" ? val * 1_000_000 : val;
  }

  const fileMatch = data.summary.match(/Files analyzed:\s*(\d+)/i);
  const fileCount = fileMatch ? parseInt(fileMatch[1], 10) : 0;

  return { summary: data.summary, tree: data.tree, content: data.content, tokenEstimate, fileCount };
}

export function buildMarkdown(
  repo: ParsedRepo,
  result: GitIngestResult,
  section: "all" | "tree" | "content" = "all"
): string {
  const header = `# ${repo.owner}/${repo.name}${repo.branch ? `@${repo.branch}` : ""}\n\n`;
  if (section === "tree") return `${header}## Directory Structure\n\n\`\`\`\n${result.tree}\n\`\`\`\n`;
  if (section === "content") return `${header}## Code Digest\n\n${result.content}\n`;
  return `${header}${result.summary}\n\n## Directory Structure\n\n\`\`\`\n${result.tree}\n\`\`\`\n\n## Code Digest\n\n${result.content}\n`;
}
