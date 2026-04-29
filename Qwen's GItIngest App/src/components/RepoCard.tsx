import { Loader2, AlertCircle, XCircle } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { DigestResult } from "@/components/DigestResult";
import type { RepoEntry, ParsedRepo } from "@/types";

interface RepoCardProps { entry: RepoEntry; onRemove: (id: string) => void; }

export function RepoCard({ entry, onRemove }: RepoCardProps) {
  const repoLabel = `${entry.owner}/${entry.name}${entry.branch ? `@${entry.branch}` : ""}`;

  if (entry.status === "loading") {
    return (
      <Card className="mb-4">
        <CardContent className="flex items-center gap-3 p-6">
          <Loader2 className="w-5 h-5 animate-spin text-primary" />
          <span className="text-sm font-mono text-muted-foreground">
            Fetching <strong className="text-foreground">{repoLabel}</strong>…
          </span>
        </CardContent>
      </Card>
    );
  }

  if (entry.status === "error") {
    return (
      <Card className="mb-4 border-destructive/40">
        <CardContent className="flex items-start justify-between gap-3 p-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-destructive mt-0.5 shrink-0" />
            <div>
              <p className="text-sm font-mono font-medium">{repoLabel}</p>
              <p className="text-xs text-muted-foreground mt-1">{entry.error}</p>
            </div>
          </div>
          <button className="text-muted-foreground hover:text-foreground transition-colors"
            onClick={() => onRemove(entry.id)} aria-label="Dismiss">
            <XCircle className="w-5 h-5" />
          </button>
        </CardContent>
      </Card>
    );
  }

  if (entry.status === "success" && entry.summary !== undefined) {
    const repo: ParsedRepo = { url: entry.url, owner: entry.owner, name: entry.name, branch: entry.branch };
    const result = {
      summary: entry.summary!,
      tree: entry.tree!,
      content: entry.content!,
      tokenEstimate: entry.tokenEstimate ?? 0,
      fileCount: entry.fileCount ?? 0,
    };
    return <DigestResult repo={repo} result={result} />;
  }

  return null;
}
