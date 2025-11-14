# Branch Protection Setup Guide

This document explains how to enforce CI checks before merging pull requests.

## 🚦 Current CI Status: Informational Mode

**The CI is currently configured to provide feedback without blocking PRs.**

- ✅ CI runs on all pull requests
- ✅ Shows test, lint, and security scan results
- ⚠️ Does NOT block merges if checks fail (intentional for gradual rollout)
- 💡 Easy to switch to strict mode later (see below)

This allows you to review CI results and fix any issues before enforcing strict checks.

## Overview

The repository includes a comprehensive CI/CD workflow (`.github/workflows/ci.yml`) that runs:

1. **Tests** - Runs pytest on Python 3.9, 3.10, and 3.11 (skips PyAudio in CI)
2. **Code Quality** - Checks formatting (black), linting (flake8, pylint)
3. **Security Scans** - Runs bandit and safety checks for vulnerabilities
4. **Final Gate** - `All CI Checks Passed` job that verifies all checks completed

## Enabling Branch Protection (Optional but Recommended)

To enforce that CI workflows must pass before merging:

**Note:** This is optional initially. You can review CI results first, then enable this later.

### Step 1: Navigate to Repository Settings

1. Go to your GitHub repository
2. Click on **Settings** (top menu)
3. Click on **Branches** (left sidebar)

### Step 2: Add Branch Protection Rule

1. Click **Add rule** or **Add branch protection rule**
2. In **Branch name pattern**, enter: `main`

### Step 3: Configure Required Checks

Enable the following settings:

- ✅ **Require a pull request before merging**
  - Optional: Require approvals (1 or more)
  - ✅ Dismiss stale pull request approvals when new commits are pushed

- ✅ **Require status checks to pass before merging**
  - ✅ Require branches to be up to date before merging
  - In the search box, add these required checks:
    - `All CI Checks Passed`
    - `Test (Python 3.9)`
    - `Test (Python 3.10)`
    - `Test (Python 3.11)`
    - `Code Quality & Linting`
    - `Security Checks`

- ✅ **Require conversation resolution before merging**
  - Ensures all review comments are addressed

- ✅ **Do not allow bypassing the above settings**
  - Applies to administrators too (recommended for security)

### Step 4: Additional Recommended Settings

- ✅ **Require linear history** - Prevents merge commits, keeps history clean
- ✅ **Require signed commits** - Ensures commit authenticity
- ⚠️ **Lock branch** - Only for very stable releases

### Step 5: Save Changes

Click **Create** or **Save changes** at the bottom.

## What Happens After Setup

Once enabled:

1. **All PRs must pass CI** - GitHub will block merging until all checks pass
2. **Status checks are visible** - You'll see ✅ or ❌ on PRs
3. **Merge button disabled** - Until requirements met
4. **Better code quality** - Automated enforcement of standards

## CI Workflow Details

### Tests Job
- Runs on Ubuntu with Python 3.9, 3.10, 3.11
- Installs system dependencies (portaudio)
- Runs pytest with coverage reporting
- Uploads coverage reports

### Lint Job
- Checks code formatting with `black`
- Runs `flake8` for syntax and style issues
- Runs `pylint` for code quality
- Continues even if warnings found (but reports them)

### Security Job
- Scans code with `bandit` for security issues
- Checks dependencies with `safety` for known vulnerabilities
- Uploads security reports as artifacts
- Flags issues for review

### Final Gate Job
- Waits for all other jobs to complete
- Currently passes if jobs complete (even with errors)
- In strict mode, only passes if ALL jobs succeed
- This is the check you require in branch protection

## 🔧 Switching to Strict Mode

Once you've reviewed CI results and fixed any issues, make enforcement strict:

### Option 1: Enforce via Branch Protection (Recommended)

Follow "Enabling Branch Protection" above to require the `All CI Checks Passed` check.
This blocks merges even in informational mode if jobs are cancelled.

### Option 2: Make CI Workflow Strict

Edit `.github/workflows/ci.yml` line 140:

**Current (informational):**
```yaml
if [[ "${{ needs.test.result }}" != "cancelled" && \
```

**Change to (strict):**
```yaml
if [[ "${{ needs.test.result }}" == "success" && \
```

This makes the final gate require all jobs to succeed, not just complete.

### Recommended Approach

1. Start with Option 1 (branch protection only)
2. Monitor CI results for a few PRs
3. Fix any recurring issues
4. Then enable Option 2 for stricter enforcement

## Testing the CI Workflow

To test the workflow:

```bash
# Make any change to a Python file
echo "# test" >> test_file.py

# Commit and push to a branch
git checkout -b test-ci-workflow
git add test_file.py
git commit -m "Test CI workflow"
git push -u origin test-ci-workflow
```

Then create a PR on GitHub and watch the checks run!

## Troubleshooting

### Checks not appearing?
- Ensure the workflow file is in `main` branch
- Check Actions tab for workflow runs
- Verify workflow syntax with: `yamllint .github/workflows/ci.yml`

### Checks failing?
- Click "Details" next to failed check
- Review the logs
- Fix issues and push new commit

### Can't merge even though checks pass?
- Verify branch protection is configured correctly
- Check that branch is up-to-date with base branch
- Ensure all conversations are resolved

## Security Benefits

Enforcing CI checks provides:

- ✅ **Automated security scanning** - Catches vulnerabilities early
- ✅ **Code quality enforcement** - Maintains standards
- ✅ **Test coverage** - Reduces bugs
- ✅ **Audit trail** - All changes reviewed and tested
- ✅ **Prevents accidental merges** - Human errors caught

## Known Limitations

Current CI setup has these known limitations:

1. **PyAudio skipped in CI** - Audio library requires compilation, skipped for faster CI
2. **Informational mode** - Tests run but don't block (by design for gradual rollout)
3. **No audio tests** - Tests requiring audio hardware will need mocking

These are acceptable tradeoffs for initial rollout. Can be improved over time.

## Maintenance

Periodically review and update:

- Python versions in the matrix (currently 3.9, 3.10, 3.11)
- Security tool versions (bandit, safety)
- Coverage thresholds (if enforced in future)
- Required checks in branch protection
- Switch from informational to strict mode when ready

## Next Steps

1. ✅ CI is now running on all PRs (informational mode)
2. 📊 Review CI results on next few PRs
3. 🔧 Fix any recurring issues identified
4. 🔒 Enable branch protection when ready
5. 💪 Switch to strict mode for full enforcement

---

**Note**: This CI/CD setup is part of the security improvements for PR #14. All security vulnerabilities have been addressed, and this workflow helps prevent new ones from being introduced. The gradual rollout approach (informational → enforced) ensures a smooth transition without blocking development.
