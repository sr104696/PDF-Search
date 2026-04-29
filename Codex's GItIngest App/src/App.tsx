import { useMemo, useState } from 'react';
import { parseRepoInput, splitRepoInputs, fetchRepoDigest, toMarkdown } from '@/lib/gitingest';
import { copy, download, id } from '@/lib/utils';
import type { RepoEntry } from '@/types';

export default function App() {
  const [input, setInput] = useState('');
  const [items, setItems] = useState<RepoEntry[]>([]);
  const [loading, setLoading] = useState(false);

  const parsed = useMemo(() => Array.from(new Map(splitRepoInputs(input).map((x) => [x, parseRepoInput(x)]).filter(([, v]) => v).map(([k, v]) => [k, v!])).values()), [input]);

  async function run() {
    setLoading(true);
    const base = parsed.map((p) => ({ ...p, id: id(), status: 'loading' as const }));
    setItems(base);
    const out = await Promise.all(base.map(async (e) => {
      try { const d = await fetchRepoDigest(e); return { ...e, status: 'success' as const, ...d }; }
      catch (err) { return { ...e, status: 'error' as const, error: err instanceof Error ? err.message : String(err) }; }
    }));
    setItems(out); setLoading(false);
  }

  return <div className='container'><h1>Codex’s GitIngest App</h1><p className='muted'>Optimized: deduped inputs, configurable API endpoint, clearer failures.</p>
  <div className='card'><textarea value={input} onChange={(e)=>setInput(e.target.value)} placeholder='owner/repo or https://github.com/owner/repo'/><div className='row'><button disabled={loading || parsed.length===0} onClick={run}>{loading ? 'Generating…' : `Generate (${parsed.length})`}</button></div></div>
  {items.map((e)=><div key={e.id} className='card'><strong>{e.owner}/{e.name}{e.branch?`@${e.branch}`:''}</strong>
    {e.status==='loading' && <p>Loading…</p>}
    {e.status==='error' && <p className='danger'>{e.error}</p>}
    {e.status==='success' && <><p className='muted'>{e.fileCount} files · {e.tokenEstimate} tokens</p><div className='row'><button onClick={()=>copy(toMarkdown(e,e as any))}>Copy</button><button onClick={()=>download(`${e.owner}-${e.name}.md`, toMarkdown(e,e as any))}>Download</button></div><pre>{e.summary}</pre></>}
  </div>)}
  </div>;
}
