# Change Control Process

## 1. Purpose

Define the process for managing changes to the validated software system, ensuring all modifications are documented, reviewed, and approved before implementation.

## 2. Scope

This process applies to all changes to:
- Source code (backend, frontend, pipelines)
- Configuration files
- Database schema
- Deployment infrastructure
- Documentation

## 3. Change Categories

| Category | Description | Approval Required |
|----------|-------------|-------------------|
| Emergency | Critical bug fix for patient safety | Post-hoc approval within 24h |
| Major | New feature, architecture change | Full review cycle |
| Minor | Bug fix, UI improvement | Standard review |
| Documentation | Documentation-only change | Single reviewer |

## 4. Process Flow

```
1. Change Request (CR) Submitted
   └─> Issue created in GitHub with template

2. Impact Assessment
   └─> Developer identifies affected components
   └─> Traceability matrix updated

3. Approval
   └─> Reviewers assigned based on category
   └─> PR review and approval

4. Implementation
   └─> Code changes on feature branch
   └─> Unit tests written/updated

5. Verification
   └─> CI tests pass
   └─> Manual testing if required
   └─> Regression assessment

6. Release
   └─> Release record completed
   └─> Version tag created
   └─> Deployment executed

7. Post-Release Monitoring
   └─> Monitor for issues
   └─> Update validation records
```

## 5. Roles and Responsibilities

| Role | Responsibilities |
|------|-----------------|
| Requester | Submit CR, provide justification |
| Developer | Implement change, write tests |
| Reviewer | Review code, approve/reject |
| Quality | Verify validation compliance |
| Manager | Final approval for major changes |

## 6. Records

All change records are maintained in:
- GitHub Issues (change requests)
- GitHub Pull Requests (implementation)
- docs/validation/ (validation documents)
- CHANGELOG.md (release history)

## 7. Audit Trail

- Git history provides immutable audit trail
- Audit log system captures all operational changes
- PR reviews are recorded permanently
