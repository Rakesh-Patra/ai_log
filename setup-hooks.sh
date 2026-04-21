#!/bin/bash
# setup-hooks.sh — Install Git pre-commit hooks for this project
# Run once after cloning: bash setup-hooks.sh

set -e

echo "════════════════════════════════════════════"
echo "  DevSecOps Git Hook Setup"
echo "════════════════════════════════════════════"

# ── 1. Native fallback pre-commit hook ───────────────────────
HOOK_FILE=".git/hooks/pre-commit"

cat > "$HOOK_FILE" << 'HOOK'
#!/bin/bash
# Native Git pre-commit — minimal secret detector (fallback if pre-commit not installed)

echo "🔍 Running pre-commit security checks..."

# Block common secret-looking patterns in staged diff
PATTERNS=(
  "AWS_SECRET_ACCESS_KEY\s*="
  "PRIVATE KEY"
  "BEGIN RSA PRIVATE"
  "password\s*=\s*['\"][^'\"]{6,}"
  "AIza[0-9A-Za-z-_]{35}"
)

FOUND=0
for pattern in "${PATTERNS[@]}"; do
  if git diff --cached | grep -qiP "$pattern"; then
    echo "❌ BLOCKED: Possible secret detected matching pattern: $pattern"
    FOUND=1
  fi
done

if [ "$FOUND" -eq 1 ]; then
  echo ""
  echo "💡 If this is a false positive, use: git commit --no-verify"
  echo "   But ONLY if you are certain no real secret is being committed."
  exit 1
fi

echo "✅ No secrets detected. Commit allowed."
exit 0
HOOK

chmod +x "$HOOK_FILE"
echo "✅ Native pre-commit hook installed at $HOOK_FILE"

# ── 2. Install pre-commit tool (if available) ─────────────────
if command -v pre-commit &>/dev/null; then
  echo "✅ pre-commit found. Installing hooks from .pre-commit-config.yaml..."
  pre-commit install
  pre-commit autoupdate
  echo "✅ pre-commit hooks installed (Gitleaks + detect-private-key + yamllint)"
else
  echo "⚠️  pre-commit not installed. To get full Gitleaks protection, run:"
  echo "    pip install pre-commit"
  echo "    pre-commit install"
  echo "    pre-commit autoupdate"
fi

echo ""
echo "════════════════════════════════════════════"
echo "  Setup complete! Your commits are protected."
echo "  To scan git history manually:"
echo "    gitleaks detect --config custom-rules.toml"
echo "════════════════════════════════════════════"
