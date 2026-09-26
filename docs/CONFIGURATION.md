# Configuration

HeaderProof keeps the normal command line small. Optional repeated probe inputs belong in `headerproof.yaml` in the current working directory.

```yaml
origins:
  - https://origin.example
headers:
  - X-Custom-Cache-Key
rate_limit: 5
timeout: 2.5
severity: high,medium
```

Supported keys are `origins`, `headers`, `concurrency`, `rate_limit`, `timeout`, `severity`, `oob_api`, and `oob_domain`.

Command-line values override matching config values. `HEADERPROOF_OOB_API` and `HEADERPROOF_OOB_DOMAIN` override OOB values from the file.
