# HeaderProof
[![HeaderProof CI](https://github.com/TayfurYldz/headerproof/actions/workflows/ci.yml/badge.svg)](https://github.com/TayfurYldz/headerproof/actions/workflows/ci.yml)
HeaderProof is an evidence-gated active scanner for CORS, CSRF, response splitting, cache poisoning, and content reflection.

It prints findings only after a detector-specific technical proof gate passes. Run evidence is stored under `${XDG_STATE_HOME:-~/.local/state}/headerproof/runs/`.

## Install
```bash
curl -fsSL https://raw.githubusercontent.com/TayfurYldz/headerproof/main/install.sh | sh
docker run --rm ghcr.io/tayfuryldz/headerproof:latest --version
```

## Run
```bash
headerproof example.com
subfinder -silent | httpx -silent | headerproof -silent
headerproof example.com -severity high,medium -o findings.jsonl
```

Output is one grep-friendly line per verified finding:
```text
[response_splitting_crlf_candidate] [high] [reproduced] https://example.com/path
```
Use `-json` for JSONL, `-sarif` for SARIF, and `-v` for compact proof notes. Results use stdout; operational messages use stderr.
Exit codes: `0` no verified finding, `1` verified finding present, `2` scan error.

[Terminal recording](docs/headerproof-demo.cast)

## Scope
| Tool | Primary role |
|---|---|
| HeaderProof | Header/cache proof-gated verification |
| Nuclei | General template-driven scanning |
| Corsy | CORS-focused testing |
| ffuf | Web fuzzing and content discovery |

Docs: [Architecture](docs/ARCHITECTURE.md) · [Testing](docs/TESTING.md) · [Project proof](docs/PROJECT_PROOF.md) · [Discovery](docs/DISCOVERY.md) · [Configuration](docs/CONFIGURATION.md) · [PyPI](docs/PYPI.md) · [Roadmap](docs/ROADMAP.md) · [Contributing](CONTRIBUTING.md) · [Community](https://github.com/TayfurYldz/headerproof/discussions)

Python 3.10+ · MIT · authorized testing only.
