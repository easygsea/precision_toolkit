# Copilot Git safety hook

[`git-safety.json`](./git-safety.json) registers a `preToolUse` hook for Copilot
CLI and Copilot in the cloud, plus the VS Code-compatible `PreToolUse` event. It
calls [`block-dangerous-git.sh`](./scripts/block-dangerous-git.sh) before shell
commands execute.

The script blocks these Git command families:

- `git push`, including forced pushes.
- `git reset --hard`.
- `git clean -f` and `git clean -fd`.
- `git branch -D`.
- `git checkout .` and `git restore .`.

Normal inspection commands such as `git status`, `git diff`, and `git log`, as
well as non-destructive Git workflows, continue through Copilot's normal
permission flow.

To test the policy without running a blocked command:

```bash
printf '%s' \
  '{"toolName":"bash","toolArgs":"{\"command\":\"git status --short\"}"}' \
  | .github/hooks/scripts/block-dangerous-git.sh

printf '%s' \
  '{"toolName":"bash","toolArgs":"{\"command\":\"git push\"}"}' \
  | .github/hooks/scripts/block-dangerous-git.sh
```

The first command exits successfully. The second writes a block reason to
standard error and exits with status 2, which denies the tool call. A malformed
payload is denied the same way rather than continuing without the policy check.

Blocked operations must be run manually outside Copilot after reviewing the
repository state. Repository-level hook files must be merged to the default
branch before Copilot in the cloud uses them.
