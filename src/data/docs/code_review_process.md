# Code Review Process

## Overview
Every code change to a production repository must go through a pull
request (PR) and receive at least one approval before merging. This
applies to all engineering teams regardless of seniority.

## Steps
1. Author opens a PR with a clear description, linked ticket, and test
   evidence (unit tests passing, screenshots for UI changes).
2. Automated checks run: linting, unit tests, and security scanning.
   A PR cannot be merged if any required check fails.
3. At least one reviewer (two for changes to shared libraries or
   infrastructure code) reviews the diff for correctness, readability,
   and adherence to team style guides.
4. Reviewers leave comments as "blocking" or "non-blocking." Blocking
   comments must be resolved before merge.
5. Once approved and checks pass, the author (or a designated merger)
   squashes and merges the PR into the main branch.

## Review Turnaround
Reviewers are expected to provide initial feedback within one business
day. If a PR is blocked for more than two business days, the author
should escalate in the team's engineering channel.

## Emergency Hotfixes
Hotfixes for production incidents may bypass the standard SLA but still
require at least one reviewer's sign-off before deploying, and a
retroactive full review within 24 hours.
