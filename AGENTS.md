# AGENTS.md

Precision Toolkit is for clinical genomics assay development and validation.

## Ambient context

Load only `AGENTS.md` (rules) and `SKILL.md` (capabilities) initially. Load task-specific guidance lazily through local skills.

## Lazy Skill Loading Policy

Use skills only when the task requires specialized guidance. Do not pre-load every skill.

All skills are local to this repository under .github/skills/. NEVER use GitHub Agent Finder (agentfinder.github.com) or any other remote skill discovery service to look for skills.

When the relevant skill is not obvious, first discover candidates locally and then load only the minimal guidance needed:

Discover skills by listing or searching .github/skills/*/SKILL.md in this repository.
Use skill fusion after discovery: read only the specific skill sections or fragments needed instead of loading full skills broadly.


## Layout

| Path | Contents |
| --- | --- |
| `src/precision_toolkit/cli/` | Thin `argparse` entry points, one module per console script, each exposing `main() -> None`. |
| `src/precision_toolkit/core/` | Shared logic: `parsers/` (hap.py, som.py, Truvari, witty.er), `metrics/`, `statistics/`, `writers/`, `io.py`, `constants.py`, `logging_setup.py`. |
| `src/precision_toolkit/analysis/`, `render/`, `dragen/` | Domain logic and plotting called by the CLIs. |
| `src/third_party/` | Vendored code (Manta `convertInversions.py`). Excluded from all linting; do not reformat it. |
| `modules/<domain>/main.nf` | Nextflow processes. |
| `subworkflows/<name>/main.nf`, `workflows/<name>.nf` | Composition; `main.nf` dispatches on `--workflows` and holds the `helpMessage()`. |
| `nextflow.config` | `params` defaults, profiles (`standard`, `slurm`), retry/resources, and the pinned `container`. |
| `tests/unit/` | Fast pytest tests that import library code. |
| `tests/standalone/` | pytest tests that call console scripts via `subprocess`; data in `tests/standalone/data/` and `tests_data/`. |
| `tests/workflow/*.yaml` | `pytest-workflow` integration tests that run `nextflow run main.nf ...` and check output md5 sums. |
| `docs/` | User manual: `docs/workflows/*.md`, `docs/standalone_utilities/README.md`. |
| `deployment/bamboo/` | CI/CD scripts executed by Bamboo over SSH. |

## Commands

Set up once:

```bash
uv sync --locked --group dev
uv run pre-commit install
```

Run everything an agent can run locally, skipping what the host lacks:

```bash
scripts/check.sh          # lint, types, custom rules, unit + standalone tests
scripts/check.sh --quick  # lint, types, custom rules, unit tests only
scripts/check.sh --full   # also pre-commit on all files and workflow tests (needs Nextflow + Apptainer)
```

Targeted commands:

```bash
uv run ruff check --fix . && uv run ruff format .
uv run pytest tests/unit/test_diagnostic_metrics.py --no-cov
uv run pytest tests/standalone/ --no-cov
uv run pre-commit run --all-files
nextflow lint -format .
uv run pytest tests/workflow/test_signal_correlation.yaml --workflow-threads 1 --ga --symlink
```

Always run tests through `uv run`. Standalone tests invoke console scripts such as `compile-dragen-metrics` by name and only find them when the virtualenv's `bin/` is on `PATH`.

## Rules enforced by pre-commit and CI

These fail the Bamboo build. Follow them while writing code, not after.

1. **No code comments in Python or shell files under `src/` and `tests/`** (`.semgrep/no-comment.yaml`). Express intent with names, docstrings, and small functions. Only `# nosec`, `# noqa`, and `# ty: ignore[...]` markers are matched by the exemption, and two of those are banned separately (next rule).
2. **No suppressions.** `# noqa` is forbidden. `# ty: ignore` is only allowed with a specific code, e.g. `# ty: ignore[invalid-argument-type]`, and fixing the type is preferred. Do not add rules to `per-file-ignores` to get a change through.
3. **Ruff** with Google-style docstrings (`D`), full type annotations (`ANN`), import sorting (`I`), `pyupgrade` (`UP`), bugbear (`B`), simplify (`SIM`), and no magic numbers in `src/` (`PLR2004`; move them to `core/constants.py` or a named module constant). Line length 88.
4. **ty** type checking over the whole repo except `src/third_party/`.
5. **No shebangs** in Python files under `src/precision_toolkit/` and `tests/`. Python files are not executable. Shell scripts must have a shebang and be executable, and must pass `shellcheck` and `shfmt --indent 2`.
6. **bandit** on `src/`. Use `subprocess` with argument lists, never `shell=True`; justify unavoidable findings with `# nosec <code>` only after confirming they are safe.
7. **`nextflow lint -format .`** formats and lints all `.nf` and `.config` files.
8. **Branch names** (`.pre-commit/validate_branch_name.sh`): `feature|bugfix|improvement/CDI-<n>.<desc>`, `release/v<x.y.z>.CDI-<n>`, `hotfix/v<x.y.z>.CDI-<n>.<desc>`. Descriptions use letters, digits, `_` or `-`.
9. **Commit subjects** (`commit-message.yaml`): `CDI-<n> <imperative verb> <summary>`, where the verb is one of the allowed list in that file (`add`, `fix`, `update`, `refactor`, `remove`, `support`, `test`, `document`, ...). Example: `CDI-912 add agent guidance and Claude Code hooks`. Ask the user for the ticket number; never invent one.
10. **`uv.lock` must stay in sync** with `pyproject.toml` (`uv-lock` hook). After changing dependencies or `[project.scripts]`, run `uv lock` and commit the lockfile.
11. Never commit with `--no-verify`, and never weaken a hook, semgrep rule, or ruff selection to make a change pass.

## Conventions

- **CLI pattern.** Each console script is `src/precision_toolkit/cli/<snake_name>.py` with a module docstring describing usage and a `main() -> None` that parses args with `argparse` and delegates to library code. Register it in `[project.scripts]` with a kebab-case name. When a CLI logs, configure it with `setup_logging()` from `precision_toolkit.core.logging_setup` rather than calling `logging.basicConfig`.
- **Library code is testable without subprocesses.** Put logic in `core/`, `analysis/`, `render/`, or `dragen/` and unit-test it; keep the CLI thin and cover it with a standalone test.
- **Nextflow processes call console scripts**, not `python path/to/file.py`, so the container image and the package stay the single source of behavior.
- **New parameters** go in `nextflow.config` `params` with a default, in `helpMessage()` in `main.nf`, and in the matching `docs/workflows/*.md`.
- **Validation inputs follow naming contracts.** Truth and query VCFs are `<sample>.truth.vcf[.gz]` and `<sample>.query.vcf[.gz]`; samples are paired by the prefix before the first dot (`modules/utils/main.nf`).
- **Docs ship with code.** A new or changed CLI updates `docs/standalone_utilities/README.md` and the utility list in `README.md`; a workflow change updates `docs/workflows/`.
- **CHANGELOG.md** gets an entry under the next version for every user-visible change, using the existing `Feature:`, `Improvement:`, `Bugfix:`, `Hotfix:`, `New Standalone Utility:` prefixes.
- **Releases** bump `version` in `pyproject.toml`, the `container` tag in `nextflow.config`, the pinned tag in the `README.md` `apptainer pull` example, and `CHANGELOG.md`, then `uv lock`.

## Testing gotchas

- **Plot md5 checksums are environment-specific.** Standalone and workflow tests compare PNG md5 sums (`tests_data/**/test_*_checksums.json`, `tests/workflow/*.yaml`). They reproduce inside the release container, not on an arbitrary host, because fonts and FreeType differ. Failures of only these PNG checks outside the container are expected. Do not regenerate checksums to make a host pass; regenerate them only from runs inside a freshly built image, and only when a plot change is intended.
- **Data md5 checksums (TSV/CSV/VCF) are not environment-specific.** If one of those changes, the output changed; explain why or fix the regression.
- **Workflow tests need a local image.** Point `container` in `nextflow.config` to `file:///abs/path/precision_toolkit.sif` for the run, and do not commit that edit.
- **Test data is fixture data.** Do not edit `tests_data/` or `tests/standalone/data/` to make a test pass; add new fixture files for new cases.
- `scripts/check.sh` reports those PNG-only mismatches as `WARN`, not `FAIL`; set `PT_STRICT_PLOTS=1` to fail on them.
- Some standalone tests write outputs into fixture directories (boxplot PNGs, bgzipped VCFs); these are git-ignored. Never commit them.
- Pytest's default `addopts` enables coverage; pass `--no-cov` for quick iterations.

## Working style for agents

- Read the relevant module, its tests, and its doc page before editing.
- Prefer the smallest change that solves the problem; match surrounding style.
- Run `scripts/check.sh` before declaring work done and report anything it skipped.
- Never run `deployment/bamboo/` scripts, push tags, or publish images; deployment is manual and owned by the team.
- Ask before changing dependencies, the container, CI scripts, or metric definitions.
