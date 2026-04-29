export type RepoStatus = "idle" | "loading" | "success" | "error";

export interface RepoEntry {
  id: string;
  rawInput: string;
  url: string;
  owner: string;
  name: string;
  branch?: string;
  status: RepoStatus;
  error?: string;
  summary?: string;
  tree?: string;
  content?: string;
  tokenEstimate?: number;
  fileCount?: number;
}

export interface ParsedRepo {
  url: string;
  owner: string;
  name: string;
  branch?: string;
}
