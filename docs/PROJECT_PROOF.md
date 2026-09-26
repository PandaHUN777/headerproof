# Project proof

HeaderProof documentation separates reproducible project evidence from claims about real-world impact.

## Terminal recording

`headerproof-demo.cast` is a short asciinema v2 recording of HeaderProof against a controlled localhost fixture. It demonstrates the stable CLI/output contract only:

```text
$ headerproof http://127.0.0.1:37297/demo -silent -severity high
[response_splitting_crlf_candidate] [high] [reproduced] http://127.0.0.1:37297/demo
```

The recording is not presented as a real bug-bounty finding. Tests parse the cast as JSON, require the localhost target, and pin the compact finding shape so documentation cannot silently drift away from the CLI contract.

## Tool scope comparison

The README comparison describes primary roles, not a quality ranking:

| Tool | Primary role |
|---|---|
| HeaderProof | Header/cache proof-gated verification |
| Nuclei | General template-driven scanning |
| Corsy | CORS-focused testing |
| ffuf | Web fuzzing and content discovery |

HeaderProof's row describes this repository. The other rows intentionally stay at the level stated by those projects' public documentation rather than claiming feature parity or superiority.

## Real finding case study

A real-world case study is intentionally not published until there is a finding from an explicitly permitted program that can be disclosed safely.

A future case study must include:
- the program or authorization basis, redacted when required;
- the affected behavior without target-identifying secrets;
- the exact HeaderProof finding type and evidence state;
- the minimum redacted request/response evidence needed to support the claim;
- what remained unverified at scan time;
- disclosure/publication permission or a public disclosure reference.

Do not convert a controlled fixture, DVWA case, synthetic example, or unverified public target into a "real finding" example.
