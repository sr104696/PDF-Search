import { useState, useCallback, useMemo } from "react";
import { Github } from "lucide-react";
import { RepoInput } from "@/components/RepoInput";
import { RepoCard } from "@/components/RepoCard";
import { fetchRepoDigest } from "@/lib/gitingest";
import type { RepoEntry } from "@/types";

const MAX_CONCURRENT_REQUESTS = 3;

export default function App() {
  const [results, setResults] = useState<RepoEntry[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleRemove = useCallback((id: string) => {
    setResults((prev) => prev.filter((r) => r.id !== id));
  }, []);

  const handleSubmit = useCallback(async (entries: RepoEntry[]) => {
    setIsLoading(true);
    const loadingEntries = entries.map((e) => ({ ...e, status: "loading" as const }));
    setResults(loadingEntries);

    // Process requests with concurrency limit to avoid rate limiting
    const processWithConcurrency = async (
      items: typeof loadingEntries,
      concurrencyLimit: number
    ) => {
      const results: typeof loadingEntries = [];
      const executing: Promise<void>[] = [];

      for (const entry of items) {
        const promise = (async () => {
          try {
            const result = await fetchRepoDigest({
              url: entry.url,
              owner: entry.owner,
              name: entry.name,
              branch: entry.branch,
            });
            results.push({ ...entry, status: "success" as const, ...result });
          } catch (err) {
            results.push({
              ...entry,
              status: "error" as const,
              error: err instanceof Error ? err.message : "Unknown error",
            });
          } finally {
            executing.splice(executing.indexOf(promise), 1);
          }
        })();

        results.push(entry); // Placeholder
        executing.push(promise);
        if (executing.length >= concurrencyLimit) {
          await Promise.race(executing);
        }
      }

      await Promise.all(executing);
      return results;
    };

    try {
      const updated = await processWithConcurrency(loadingEntries, MAX_CONCURRENT_REQUESTS);
      setResults(updated);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const stats = useMemo(() => {
    const success = results.filter((r) => r.status === "success").length;
    const errors = results.filter((r) => r.status === "error").length;
    const loading = results.filter((r) => r.status === "loading").length;
    return { success, errors, loading, total: results.length };
  }, [results]);

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/30">
      <div className="mx-auto max-w-5xl px-4 py-12">
        <header className="mb-10">
          <div className="flex items-center gap-3 mb-4">
            <div className="rounded-xl bg-primary/10 p-2.5">
              <Github className="h-6 w-6 text-primary" aria-hidden="true" />
            </div>
            <h1 className="text-3xl font-bold tracking-tight">GitIngest</h1>
          </div>
          <p className="text-muted-foreground max-w-2xl">
            Paste one or many GitHub repo URLs. Get a compact{" "}
            <strong>directory tree</strong> Markdown and a{" "}
            <strong>compressed code digest</strong> Markdown for each — perfect
            for feeding to LLMs.
          </p>
        </header>

        <RepoInput onSubmit={handleSubmit} isLoading={isLoading} />

        {results.length > 0 && (
          <section>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-medium text-muted-foreground">
                Results ({stats.total})
              </h2>
              <div className="flex gap-2 text-xs">
                {stats.loading > 0 && (
                  <span className="text-primary">{stats.loading} loading</span>
                )}
                {stats.success > 0 && (
                  <span className="text-green-600">{stats.success} success</span>
                )}
                {stats.errors > 0 && (
                  <span className="text-destructive">{stats.errors} errors</span>
                )}
              </div>
            </div>
            {results.map((entry) => (
              <RepoCard key={entry.id} entry={entry} onRemove={handleRemove} />
            ))}
          </section>
        )}

        <footer className="text-center text-sm text-muted-foreground mt-12">
          Tip: GitHub anonymous API allows ~60 requests per hour. Large monorepos
          may hit caps and produce partial digests.
        </footer>
      </div>
    </div>
  );
}
