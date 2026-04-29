# GitIngest – AI Agent Integration Guide

Turn any Git repository into a prompt-ready text digest. GitIngest fetches, cleans, and formats source code so AI agents and LLMs can reason over complete projects programmatically.

**For AI Agents**: Use CLI or Python package. Web UI is for human interaction only.

---

## 1. Installation

```bash
# CLI (recommended)
pipx install gitingest
pip install gitingest

# Python package
python -m venv gitingest-env && source gitingest-env/bin/activate
pip install gitingest
pip install gitingest[server]    # self-hosting
pip install gitingest[dev,server] # development

# Verify
gitingest --version
python -c "from gitingest import ingest; print('OK')"
```

---

## 2. Quick-Start

| Method | Best for | One-liner |
|--------|----------|-----------|
| **CLI** | Scripts, automation | `gitingest https://github.com/user/repo  -o - \| your-llm` |
| **Python** | Code integration | `from gitingest import ingest; s,t,c = ingest('url')` |
| **URL Hack** | Quick scrape | Replace `github.com` → `gitingest.com` |
| **Web UI** | Human use only | Not for agents |

---

## 3. Output Format

Three plain-text sections optimized for LLM consumption:

- **Summary** — repo name, file count, token estimate
- **Directory Structure** — hierarchical tree
- **File Contents** — each file wrapped in `=====\nFILE: path\n=====\n<content>`

```python
from gitingest import ingest
summary, tree, content = ingest("https://github.com/octocat/Hello-World ")
full_context = f"{summary}\n\n{tree}\n\n{content}"
```

```bash
gitingest https://github.com/octocat/Hello-World  -o - | your_llm_processor
```

---

## 4. CLI Integration

```bash
# Pipe to AI system
gitingest https://github.com/user/repo  -o - | your_ai_processor

# Filter by type
gitingest https://github.com/user/repo  -i "*.py" -i "*.md" -s 102400 -o -

# Exclude noise
gitingest https://github.com/user/repo  -e "node_modules/*" -e "*.log" -e "dist/*" -o -

# Private repos
export GITHUB_TOKEN="ghp_your_token"
gitingest https://github.com/user/private-repo  -t $GITHUB_TOKEN -o -

# Branch + save to file
gitingest https://github.com/user/repo  -b main -o analysis.txt
```

**Key flags**: `-s` max-size · `-i` include-pattern · `-e` exclude-pattern · `-b` branch · `-t` token · `-o` output (`-` = stdout)

---

## 5. Python Package

```python
from gitingest import ingest, ingest_async
import asyncio

# Synchronous
summary, tree, content = ingest("https://github.com/user/repo ")

# Async batch
async def batch(urls):
    return await asyncio.gather(*[ingest_async(u) for u in urls])

# With filtering
summary, tree, content = ingest(
    "https://github.com/user/repo ",
    max_file_size=51200,
    include_patterns=["*.py", "*.js"],
    exclude_patterns=["node_modules/*", "*.lock", "dist/*"],
)
```

---

## 6. Error Handling & Private Repos

```python
from gitingest import ingest
from gitingest.utils.exceptions import GitIngestError
import os, time

def robust_ingest(url, retries=3):
    for i in range(retries):
        try:
            return ingest(url)
        except GitIngestError as e:
            if i == retries - 1:
                return None, None, f"Failed: {e}"
            time.sleep(2 ** i)

def ingest_private(url):
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN required")
    return ingest(url, token=token)
```

---

## 7. Use-Case Reference

| Use Case | Method | Example |
|----------|--------|---------|
| Code Review Bot | Python async | `await ingest_async(pr_repo)` |
| Docs Generator | CLI filter | `gitingest repo -i "*.py" -i "*.md" -o -` |
| Vuln Scanner | Python batch | Parallel ingest + analysis |
| Vector DB index | CLI + embed | `gitingest repo -o - \| embed \| store` |
| AI coding assistant | Python | Load repo context into conversation |
| Dependency audit | CLI exclude | `gitingest repo -e "node_modules/*" -e "*.lock" -o -` |
| Security audit | CLI + limits | `gitingest repo -i "*.py" -i "*.js" -s 204800 -o -` |

---

## 8. Self-Hosting

```bash
pip install gitingest[server]
uvicorn gitingest.server:app --host 0.0.0.0 --port 8000 --reload
```

`.env.local`:

```
VITE_GITINGEST_API=http://localhost:8000/api/ingest
```

---

## 9. Development & Deployment

```bash
# Dev
git clone https://github.com/your-org/code-nestor  && cd code-nestor
npm install && npm run dev   # → http://localhost:5173
npx tsc --noEmit             # type-check
npm run build                # → dist/

# Vercel
npm i -g vercel && vercel deploy

# Docker
docker build -t code-nestor . && docker run -p 8080:80 code-nestor
```

`Dockerfile`:

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

`netlify.toml` (for SPA routing):

```toml
[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

---

## 10. Resources

- **Web UI**: https://gitingest.com 
- **GitHub**: https://github.com/coderamp-labs/gitingest 
- **PyPI**: https://pypi.org/project/gitingest/ 
- **Discord**: https://discord.gg/zerRaGK9EC
