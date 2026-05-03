---
name: pre-deploy
description: Validate build, environment, and dependencies before deployment
---

# Pre-Deploy Workflow

Run before any deployment to production. All checks must pass.

## Execution

Spawn `deploy-checker` (which absorbs the prior `env-validator`, `dep-auditor`, and `infra-auditor` roles):

| Agent | Focus |
|-------|-------|
| `deploy-checker` | Build validation, bundle size, production config, environment variables, secrets detection, dependencies, vulnerabilities, license compliance, infrastructure config |

## Gate Check

After the agent completes:
- **All checks pass** -> "Ready to deploy"
- **Any check fails** -> "BLOCKED - Fix first" with specific blockers listed

## Expected Output

```markdown
# Pre-Deploy Checklist

## Status: READY / BLOCKED

### Build Validation (deploy-checker)
- [x] Production build succeeds
- [x] Bundle size acceptable
- [x] No build warnings

### Environment (deploy-checker)
- [x] All required vars set
- [x] No secrets in code
- [x] Production config valid

### Dependencies (deploy-checker)
- [x] No critical vulnerabilities
- [x] No high vulnerabilities

## Deployment Decision
READY TO DEPLOY / BLOCKED - Fix issues
```
