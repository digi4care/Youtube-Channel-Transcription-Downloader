# Git Workflow Guide - Enterprise Best Practices

## Overview

Deze gids volgt de workflow die grote tech bedrijven gebruiken (Google, Facebook, Microsoft, etc.)

---

## 🔥 Complete Workflow - Van Feature tot Production

### **Fase 1: Voorbereiding (Setup)**

#### 1.1 Sync met Main Branch

```bash
# Switch naar main
git checkout main

# Haal laatste wijzigingen op
git pull origin main

# Check je status
git status
```

#### 1.2 Maak Feature Branch

```bash
# Maak en switch naar nieuwe branch
git checkout -b feature/your-feature-name

# Tip: Gebruik deze branch naming conventions:
# - feature/     = Nieuwe features
# - bugfix/      = Bug fixes
# - hotfix/      = Urgent productie fixes
# - chore/       = Onderhoud/cleanup
# - refactor/    = Code herstructurering
```

---

### **Fase 1.5: PLANNING (CRITICAL STEP)**

⚠️ **STOP!** - Grote bedrijven plannen ALTIJD eerst voordat ze code schrijven

#### 1.3 Define Problem & Solution

```markdown
# Feature Plan: Your Feature Name

## Problem
What problem are we solving?
Why does this matter?

## Solution
How will we solve it?
What approach will we take?

## Technical Design
- What files need to change?
- What functions/modules affected?
- What data structures?
- What interfaces?

## Testing Strategy
- How will we test this?
- Unit tests needed?
- Integration tests?
- Edge cases to consider?

## Rollout Plan
- Backward compatibility?
- Migration required?
- Documentation updates?
```

#### 1.4 Create Feature Plan Document

```bash
# Create plan document
touch FEATURE_PLAN_FEATURE_NAME.md

# Template structure:
# 1. Overview
# 2. Problem Statement
# 3. Technical Design
# 4. Changes Required
# 5. Testing Plan
# 6. Examples
# 7. Backward Compatibility
# 8. Migration Path
# 9. Rollout Plan
# 10. Approval Required
```

#### 1.5 Get Approval

- [ ] Stakeholder/Team lead approval
- [ ] Architecture review (if complex)
- [ ] Security review (if needed)
- [ ] **ONLY THEN:** Proceed to development

---

### **Fase 2: Development**

#### 2.1 Implement Based on Plan

- ✅ Follow the approved plan exactly
- ✅ Write code
- ✅ Test je wijzigingen
- ✅ Run linting/formatters

#### 2.2 Review Je Eigen Code

```bash
# Bekijk wat je hebt gewijzigd
git diff

# Bekijk staged wijzigingen
git diff --staged
```

#### 2.3 Commit Best Practices

```bash
# Stage specifieke files (NIET altijd git add .)
git add file1.py file2.py

# Commit met goede message (zie commit conventions hieronder)
git commit -m "feat: add user authentication module

- Implement JWT token validation
- Add password hashing with bcrypt
- Create login/logout endpoints

Fixes #123"
```

#### 2.4 Push Naar Remote

```bash
# Push je branch
git push origin feature/your-feature-name
```

---

### **Fase 3: Pull Request (Code Review)**

#### 3.1 Open PR op GitHub

**Via CLI:**

```bash
gh pr create --title "feat: add user authentication" --body "$(cat <<'EOF'
## Summary
Brief description of what this PR does

## Changes
- Added JWT authentication
- Created login/logout endpoints
- Added password hashing

## Testing
- Unit tests passing
- Manual testing completed

## Checklist
- [ ] Code reviewed
- [ ] Tests added
- [ ] Documentation updated
EOF
)"
```

**Via GitHub Web:**

- Ga naar: `https://github.com/username/repo/compare`
- Selecteer je branch
- Klik "Create Pull Request"

#### 3.2 PR Beschrijving Template

```markdown
## Summary
What does this PR do? (1-2 sentences)

## Type of Change
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change (fix or feature that causes existing functionality to not work as expected)
- [ ] Documentation update

## Changes Made
- Bullet point 1
- Bullet point 2
- Bullet point 3

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Screenshots (if applicable)

## Checklist
- [ ] My code follows the style guidelines
- [ ] I have performed a self-review
- [ ] I have commented complex code
- [ ] I have updated documentation
- [ ] My changes generate no new warnings

## Related Issues
Closes #123
```

---

### **Fase 4: Code Review Process**

#### 4.1 Reviewer Checklist

**Voor Reviewers:**

- [ ] Code is leesbaar en begrijpelijk
- [ ] Follows project conventions
- [ ] Tests zijn geschreven
- [ ] Geen security issues
- [ ] Performance impact is acceptable
- [ ] Documentation is updated

#### 4.2 Op PR Commenteren

```markdown
✅ **Looks good!** Ready to merge.

⚠️ **Minor issue:** Please fix variable naming on line 42.

🔴 **Major issue:** This breaks backwards compatibility. Please revert.

💡 **Suggestion:** Could we also handle edge case X here?
```

#### 4.3 Revisions Naar PR

```bash
# Maak nieuwe commits voor wijzigingen
git add .
git commit -m "fix: address review comments

- Renamed variable to be more descriptive
- Added null check for edge case"

# Push de wijzigingen (PR updated automatisch)
git push origin feature/your-feature-name
```

---

### **Fase 5: Merge & Cleanup**

#### 5.1 Merge Strategies

Option A: **Merge Commit (Standaard)**

```bash
# Via GitHub UI - klik "Merge pull request"
# Maakt een merge commit: "Merge branch 'feature/...' into main"
```

Option B: **Squash and Merge (Aanbevolen)**

```bash
# Via GitHub UI - klik dropdown → "Squash and merge"
# All commits worden 1 commit
# Commit message = PR title
```

Option C: **Rebase (Voor historici)**

```bash
# Via GitHub UI - klik dropdown → "Rebase and merge"
# Behoudt alle commits maar verplaatst ze naar main
```

#### 5.2 Cleanup Na Merge

```bash
# Switch naar main
git checkout main

# Pull gemergede changes
git pull origin main

# Delete lokale branch
git branch -d feature/your-feature-name

# Delete remote branch (optioneel)
git push origin --delete feature/your-feature-name
```

---

## 📋 Commit Message Conventions

### Format: `type: short description`

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes (formatting, no logic)
- `refactor`: Code restructuring without changing behavior
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Maintenance tasks, dependencies
- `ci`: CI/CD changes
- `build`: Build system changes

**Examples:**

```bash
feat: add user authentication system
fix: resolve race condition in queue processor
docs: update API documentation for v2
refactor: simplify error handling logic
perf: optimize database queries with indexes
test: add integration tests for payment flow
chore: update dependencies to latest versions
```

**Beste Practices:**

- ✅ Use imperative mood ("add" not "added")
- ✅ Keep subject line under 50 chars
- ✅ Capitalize first letter
- ✅ No period at end
- ✅ Describe WHAT and WHY, not HOW

---

## 🔄 Daily Workflow

### Start je dag

```bash
git checkout main
git pull origin main
git checkout your-feature-branch
git rebase main  # Optional: keep history clean
```

### Eind van de dag

```bash
git add .
git commit -m "feat: progress on authentication"
git push origin your-feature-branch
```

---

## 🚨 Emergency Fixes (Hotfix)

```bash
# Maak hotfix branch van production (main)
git checkout -b hotfix/critical-bug-fix

# Fix it fast!
git add .
git commit -m "hotfix: prevent null pointer in payment processor

Fixes production issue #456"

# Push en maak urgent PR
git push origin hotfix/critical-bug-fix
```

---

## 🛠️ Useful Commands Cheat Sheet

```bash
# Basics
git status                    # Check current status
git log --oneline            # View commit history
git branch                   # List branches
git branch -a                # List all branches (remote + local)

# Switching
git checkout main            # Switch to main
git checkout -b new-branch   # Create + switch to new branch
git switch -                 # Switch to previous branch

# Staging & Committing
git add file.py              # Stage specific file
git add .                    # Stage all changes
git commit -m "message"      # Commit staged changes
git commit --amend           # Edit last commit

# Pushing & Pulling
git push origin branch       # Push to remote
git pull origin main         # Pull from main
git fetch                    # Update remote refs
git rebase main              # Rebase on main

# Undoing
git restore file.py          # Discard unstaged changes
git restore --staged file.py # Unstage file
git revert HEAD              # Create revert commit
git reset --hard HEAD        # ⚠️ DANGER: Hard reset

# Stashing
git stash                    # Save changes temporarily
git stash list               # List stashes
git stash pop                # Apply last stash
```

---

## 📚 Resources

- [Git Documentation](https://git-scm.com/doc)
- [GitHub Flow](https://docs.github.com/en/get-started/using-github/github-flow)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Pro Git Book (Free)](https://git-scm.com/book)

---

## ✨ Pro Tips

1. **Pull Before Push** - Altijd eerst syncen met main
2. **Small PRs** - Kleinere PRs = snellere reviews
3. **Descriptive Names** - Goede branch/commit namen
4. **Test First** - Schrijf tests voordat je code
5. **Review Own Code** - Bekijk je eigen code voordat je een PR maakt
6. **Use .gitignore** - Commit nooit secrets, node_modules, build files
7. **Atomic Commits** - 1 commit = 1 logische verandering
8. **Rebase for Clean History** - Gebruik rebase in plaats van merge voor feature branches

---

**Remember:** Grote bedrijven gebruiken deze workflow omdat het:

- ✅ Code quality waarborgt
- ✅ Knowledge sharing stimuleert
- ✅ Bugs voorkomt
- ✅ Onboarding makkelijker maakt
- ✅ Production stability garandeert
