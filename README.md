## Step Functions CI/CD (GitHub Actions)

This repo includes a branch-driven Step Functions CI/CD pipeline:

- **`cert` branch**: deploys to **cert** AWS environment
- **`prod` branch**: deploys to **prod** AWS environment (typically gated by GitHub Environment approvals)

It supports **create**, **update**, and **delete** of state machines based on changes under `stepfunctions/`.

### Workflow diagram

```mermaid
flowchart TD
  dev[Developer changes<br/>stepfunctions/** or scripts/**] --> pr[Open PR]
  pr --> validatePR[CI: Validate<br/>- jq manifest/env/definitions<br/>- render templates (cert)<br/>- JSON parse check]
  validatePR --> prmerge{PR merged?}

  prmerge -->|No| stop1[Stop]
  prmerge -->|Yes → merge to cert| certPush[Push/Merge to cert branch]
  prmerge -->|Yes → merge to prod| prodPush[Push/Merge to prod branch]

  certPush --> diffCert[Detect changes<br/>DEPLOY: added/modified/renamed defs<br/>DELETE: removed/renamed-away defs]
  diffCert --> oidcCert[Configure AWS creds (OIDC)<br/>Assume AWS_ROLE_TO_ASSUME_CERT]
  oidcCert --> deployCert[Create/Update loop<br/>render ASL → create/update-state-machine<br/>tag-resource + logging/tracing]
  oidcCert --> deleteCert[Delete loop<br/>delete-state-machine for removed workflows]

  prodPush --> diffProd[Detect changes<br/>DEPLOY + DELETE]
  diffProd --> gateProd[GitHub Environment: prod<br/>required reviewers (approval gate)]
  gateProd --> oidcProd[Configure AWS creds (OIDC)<br/>Assume AWS_ROLE_TO_ASSUME_PROD]
  oidcProd --> deployProd[Create/Update loop<br/>render ASL → create/update-state-machine<br/>tag-resource + logging/tracing]
  oidcProd --> deleteProd[Delete loop<br/>delete-state-machine for removed workflows]

  manual[workflow_dispatch<br/>inputs: environment=cert|prod<br/>mode=changed|all] --> selectManual[Select definitions<br/>changed: diff-based<br/>all: deploy all (no deletes)]
  selectManual --> gateManual{environment == prod?}
  gateManual -->|Yes| gateProd
  gateManual -->|No| oidcCert
```
