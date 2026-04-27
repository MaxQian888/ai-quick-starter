# act Local Simulation

Use this file when the task is to run GitHub Actions locally with Docker rather than only generate or edit workflow YAML.

## Official references

- Usage guide: `https://nektosact.com/usage/index.html`
- Runners guide: `https://nektosact.com/usage/runners.html`

## What to assume from current docs

- Running `act` without an explicit event name defaults to `push`.
- Use `-W` with a workflow file or workflow directory to narrow execution.
- Use `-j` to run a single job.
- Use `-e <event.json>` when the workflow depends on event payload fields.
- Use `--secret-file` for secrets, `--env-file` for environment variables, and `--var-file` if repository variables are needed outside this skill.
- Use `-P <runner>=<image>` to override runner images.
- `--action-offline-mode` helps avoid unnecessary pulls when local images or action clones are already present.

## Runner reality

From the current runners guide:

- `ubuntu-latest` defaults to a small image unless overridden.
- Default runner images are intentionally incomplete and may not match GitHub-hosted runners perfectly.
- Higher-fidelity images exist, but they are heavier and slower.

Practical default:

- Start with the default image for quick feedback.
- Switch to `catthehacker/ubuntu:act-latest` or a more specific image through `-P` when tool availability is the blocker.
- Do not claim parity with GitHub-hosted runners unless the local image and workflow requirements are actually close enough.

## act command patterns

Run the default validation path:

```bash
act push -W .github/workflows/ci.yml
```

Run one job:

```bash
act pull_request -W .github/workflows/ci.yml -j lint
```

Run with explicit event payload and secret file:

```bash
act workflow_dispatch -W .github/workflows/ci.yml --secret-file .secrets -e event.json
```

Override runner image and architecture:

```bash
act push -W .github/workflows/ci.yml -P ubuntu-latest=catthehacker/ubuntu:act-latest --container-architecture linux/amd64
```

## Safety rules for this skill

- Prefer `act` for validation workflows, not publish or deploy paths.
- If the workflow relies on `${{ secrets.* }}` and no secret file is provided, keep the run blocked instead of pretending local simulation is complete.
- If the workflow contains unsupported or private `uses:` steps, do not silently ignore them.
- If local simulation is partial, say exactly which jobs or steps ran and which were skipped.
- If Docker or `act` is missing, fall back only to reproducible `run:` steps and keep the claim narrow.
