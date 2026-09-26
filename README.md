# HeaderProof
[![HeaderProof CI](https://github.com/TayfurYldz/headerproof/actions/workflows/ci.yml/badge.svg)](https://github.com/TayfurYldz/headerproof/actions/workflows/ci.yml)
HeaderProof is an evidence-gated active scanner for CORS, CSRF, response splitting, cache poisoning, and content reflection.

It only prints findings that pass a detector-specific technical proof gate. Full evidence for every run is stored under `${XDG_STATE_HOME:-~/.local/state}/headerproof/runs/`.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/TayfurYldz/headerproof/main/install.sh | sh
```

## Run

```bash
headerproof example.com
headerproof -l urls.txt -c 16 -rl 5
subfinder -silent | httpx -silent | headerproof -silent
headerproof example.com -severity high,medium -o findings.jsonl
```

Default terminal output is one grep-friendly line per verified finding:

```text
[response_splitting_crlf_candidate] [high] [reproduced] https://example.com/path
```

Use `-json` for JSONL findings and `-v` for compact proof notes. Results go to stdout; operational messages go to stderr.

Exit codes: `0` no verified finding, `1` verified finding present, `2` scan error.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Evidence and testing](docs/TESTING.md)
- [Roadmap](docs/ROADMAP.md)
- [Contributing](CONTRIBUTING.md)

Python 3.10+ · MIT · authorized testing only.
