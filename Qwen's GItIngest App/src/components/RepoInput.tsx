import { useState, useCallback } from "react";
import { Loader2, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";
import { splitRepoInputs, parseRepoInput } from "@/lib/gitingest";
import { generateId } from "@/lib/utils";
import type { RepoEntry } from "@/types";

interface RepoInputProps {
  onSubmit: (entries: RepoEntry[]) => void;
  isLoading: boolean;
}

export function RepoInput({ onSubmit, isLoading }: RepoInputProps) {
  const [value, setValue] = useState("");
  const tokens = splitRepoInputs(value);
  const validCount = tokens.filter((t) => parseRepoInput(t) !== null).length;

  const handleSubmit = useCallback(() => {
    const entries: RepoEntry[] = tokens
      .map((raw) => {
        const parsed = parseRepoInput(raw);
        if (!parsed) return null;
        return {
          id: generateId(),
          rawInput: raw,
          url: parsed.url,
          owner: parsed.owner,
          name: parsed.name,
          branch: parsed.branch,
          status: "idle" as const,
        };
      })
      .filter((e): e is RepoEntry => e !== null);
    if (entries.length > 0) onSubmit(entries);
  }, [tokens, onSubmit]);

  const label =
    tokens.length === 0
      ? "No URLs yet"
      : validCount === 0
      ? `${tokens.length} token${tokens.length > 1 ? "s" : ""} — none recognised`
      : `${validCount} repo${validCount > 1 ? "s" : ""} ready`;

  return (
    <Card className="mb-6">
      <CardContent className="p-6">
        <label className="text-sm font-medium mb-2 block">
          GitHub repo URLs{" "}
          <span className="text-muted-foreground font-normal">(one per line, comma- or space-separated)</span>
        </label>
        <Textarea
          className="font-mono text-sm min-h-32"
          placeholder={"https://github.com/coderamp-labs/gitingest \nhttps://github.com/magarcia/gitingest \nowner/repo@branch"}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey) && !isLoading && validCount > 0)
              handleSubmit();
          }}
        />
        <div className="flex items-center justify-between mt-4 flex-wrap gap-3">
          <div className="text-sm text-muted-foreground">{label}</div>
          <Button onClick={handleSubmit} disabled={isLoading || validCount === 0}>
            {isLoading ? <><Loader2 className="animate-spin" />Generating…</> : <><Sparkles />Generate digests</>}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
