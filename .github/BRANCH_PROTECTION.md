# Branch Protection Setup Guide

This document explains how to enforce CI checks before merging pull requests.

## Overview

The repository now includes a comprehensive CI/CD workflow (`.github/workflows/ci.yml`) that runs:

1. **Tests** - Runs pytest on Python 3.9, 3.10, and 3.11
2. **Code Quality** - Checks formatting (black), linting (flake8, pylint)
3. **Security Scans** - Runs bandit and safety checks for vulnerabilities
4. **Final Gate** - `all-checks-pass` job that requires all checks to succeed

## Enabling Branch Protection

To enforce that CI workflows must pass before merging:

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
- Only passes if ALL jobs succeed
- This is the check you require in branch protection

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

## Maintenance

Periodically review and update:

- Python versions in the matrix
- Security tool versions
- Coverage thresholds
- Required checks in branch protection

---

**Note**: This setup is part of the security improvements for PR #14. All security vulnerabilities have been addressed, and this CI workflow helps prevent new ones from being introduced.
