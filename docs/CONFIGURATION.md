# Configuration

HeaderProof keeps the normal command line small. Optional repeated probe inputs belong in `headerproof.yaml` in the current working directory.

```yaml
origins:
  - https://origin.example
headers:
  - X-Custom-Cache-Key
request_headers:
  X-Test-Context: authorized-lab
rate_limit: 5
timeout: 2.5
severity: high,medium
```

Supported keys are `origins`, `headers`, `request_headers`, `concurrency`, `rate_limit`, `timeout`, `severity`, `oob_api`, and `oob_domain`. Request-header values are used at runtime but are never copied into run metadata.

Command-line values override matching config values. `HEADERPROOF_OOB_API` and `HEADERPROOF_OOB_DOMAIN` override OOB values from the file.
