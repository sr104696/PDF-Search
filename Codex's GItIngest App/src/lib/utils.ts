export const id = () => crypto.randomUUID();
export async function copy(text: string) { await navigator.clipboard.writeText(text); }
export function download(filename: string, content: string) {
  const blob = new Blob([content], { type: 'text/markdown' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = filename; a.click(); URL.revokeObjectURL(a.href);
}
