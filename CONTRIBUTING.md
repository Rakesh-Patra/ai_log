# Contributing to AI-Powered K8s DevSecOps Platform

Thanks for your interest! Here's how to contribute.

## Quick Start

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/ai_log.git
cd ai_log/k8s-kind-voting-app

# 2. Install pre-commit hooks
pip install pre-commit
pre-commit install

# 3. Create a branch
git checkout -b fix/your-fix-description

# 4. Make changes, commit, push
git add .
git commit -m "fix: describe what you fixed"
git push origin fix/your-fix-description

# 5. Open a Pull Request
```

## Rules

1. **Pre-commit hooks must pass** — They run Gitleaks, YAML lint, and Terraform fmt automatically.
2. **No secrets in code** — Use `.env.example` for templates, Vault for real values.
3. **Pin image versions** — Never use `:latest` in K8s manifests.
4. **Add resource limits** — Every K8s deployment needs CPU/memory requests and limits.
5. **Test locally first** — Run `docker compose up` before pushing.

## What We Accept

- 🐛 Bug fixes
- 📖 Documentation improvements
- 🔒 Security hardening
- ♻️ Code deduplication
- 🧪 Test coverage

## What We Don't Accept

- Breaking changes to the CI/CD pipeline without discussion
- Removing security controls
- Adding services that cost money (this is a $0/month project!)

## Code Review

All PRs require review from `@Rakesh-Patra` (see [CODEOWNERS](.github/CODEOWNERS)).

## Questions?

Open an issue or reach out on [LinkedIn](https://linkedin.com/in/rakesh-patra).
