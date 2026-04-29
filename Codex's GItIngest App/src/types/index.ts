export type RepoStatus = 'idle' | 'loading' | 'success' | 'error';
export interface ParsedRepo { url: string; owner: string; name: string; branch?: string; }
export interface RepoEntry extends ParsedRepo { id: string; status: RepoStatus; error?: string; summary?: string; tree?: string; content?: string; tokenEstimate?: number; fileCount?: number; }
