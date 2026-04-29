import { useState } from "react";
import { Download, Copy, Check, ChevronDown, ChevronUp, FolderTree, FileCode2, Files } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { buildMarkdown, type GitIngestResult } from "@/lib/gitingest";
import { downloadFile, copyToClipboard } from "@/lib/utils";
import type { ParsedRepo } from "@/types";

interface DigestResultProps { repo: ParsedRepo; result: GitIngestResult; }

export function DigestResult({ repo, result }: DigestResultProps) {
  const [treeOpen, setTreeOpen] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);

  const repoLabel = `${repo.owner}/${repo.name}${repo.branch ? `@${repo.branch}` : ""}`;
  const safeFilename = repoLabel.replace(/[/@]/g, "-");

  function handleCopy(section: "all" | "tree" | "content") {
    copyToClipboard(buildMarkdown(repo, result, section)).then(() => {
      setCopied(section);
      setTimeout(() => setCopied(null), 2000);
    });
  }

  function handleDownload(section: "all" | "tree" | "content") {
    const suffix = section === "tree" ? "tree" : section === "content" ? "digest" : "full";
    downloadFile(`${safeFilename}-${suffix}.md`, buildMarkdown(repo, result, section));
  }

  const tokens = result.tokenEstimate >= 1000
    ? `${(result.tokenEstimate / 1000).toFixed(1)}k tokens`
    : `${result.tokenEstimate} tokens`;

  return (
    <Card className="mb-4">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3 flex-wrap">
          <div>
            <CardTitle className="text-base font-mono">{repoLabel}</CardTitle>
            <div className="flex items-center gap-2 mt-1.5">
              <Badge variant="secondary"><Files className="w-3 h-3 mr-1" />{result.fileCount} files</Badge>
              <Badge variant="outline">{tokens}</Badge>
            </div>
          </div>
          <div className="flex gap-2 flex-wrap">
            <Button size="sm" variant="outline" onClick={() => handleCopy("all")}>
              {copied === "all" ? <Check /> : <Copy />}{copied === "all" ? "Copied" : "Copy all"}
            </Button>
            <Button size="sm" variant="outline" onClick={() => handleDownload("all")}><Download />Full digest</Button>
            <Button size="sm" variant="outline" onClick={() => handleDownload("tree")}><FolderTree />Tree</Button>
            <Button size="sm" variant="outline" onClick={() => handleDownload("content")}><FileCode2 />Code</Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <pre className="text-xs text-muted-foreground bg-muted/40 rounded-md p-3 mb-3 whitespace-pre-wrap font-mono">
          {result.summary}
        </pre>
        <button
          className="flex w-full items-center justify-between text-sm font-medium py-2 hover:text-primary transition-colors"
          onClick={() => setTreeOpen((o) => !o)}
        >
          <span className="flex items-center gap-1.5"><FolderTree className="w-4 h-4" /> Directory structure</span>
          {treeOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
        {treeOpen && (
          <pre className="text-xs bg-muted/40 rounded-md p-3 overflow-x-auto font-mono leading-relaxed">
            {result.tree}
          </pre>
        )}
      </CardContent>
    </Card>
  );
}
