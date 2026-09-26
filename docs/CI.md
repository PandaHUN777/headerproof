# CI consumption

HeaderProof keeps findings on stdout and operational messages on stderr so pipelines can consume machine output without stripping progress text.

## Machine output

Use JSONL for streaming consumers:

    headerproof -l urls.txt -json > findings.jsonl

Use SARIF 2.1.0 for code-scanning consumers:

    headerproof -l urls.txt -sarif > headerproof.sarif

Operational scan messages remain on stderr. `-silent` suppresses operational output while retaining finding lines on stdout.

## Exit codes

| Code | Meaning |
|---:|---|
| 0 | Scan completed with no verified technical findings |
| 1 | Scan completed with one or more verified technical findings |
| 2 | Scan failed or completed with scan errors |
| 130 | Interrupted by the operator |

Exit code 1 is a finding result, not a scanner failure. CI wrappers should decide whether findings fail a workflow based on their own policy.

## GitHub Action

The independently versioned action is available as `TayfurYldz/headerproof-action@v1`. Its `version` input selects the scanner release separately; by default it installs the latest published HeaderProof binary. Set `fail-on-findings: "false"` to retain exit-code `1` as an action output without failing the workflow step.
