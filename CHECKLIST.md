# Master Plan Checklist: NeuroCognitive Architecture (NCA) - Production Readiness

**Goal:** Finalize the NCA project, ensuring it meets production quality standards regarding code quality, testing, documentation, and overall robustness.

---

## Phase 1: Code Review & Refinement

-   [X] **Task 1.1: Static Analysis Execution**
    -   [X] Step 1.1.1: Execute `ruff check` across the `src/neuroca` directory. (Completed, 4486 issues found)
    -   [X] Step 1.1.2: Attempt auto-fixing Ruff issues (`ruff check --fix`). (Completed, 3066 fixed, 1327 remaining)
    -   [X] Step 1.1.3: Re-execute `ruff check` to document remaining issues. (Completed, 1327 issues documented in previous output)
    -   [X] Step 1.1.4: Execute `mypy` across the `src/neuroca` directory. (Completed, 2212 errors found)
    -   [X] Step 1.1.5: Document identified type checking issues. (Completed, documented in previous output)
    -   [X] Step 1.1.6: Update Knowledge Graph: Add nodes/observations for static analysis tools and initial findings. (Completed)
-   [ ] **Task 1.2: Linting Issue Resolution (Targeted: B008 in dependencies.py)**
    -   [X] Step 1.2.1: Prioritize remaining documented `ruff` issues. (Completed - Focusing on B008 in dependencies.py)
    -   [X] Step 1.2.2: Address `B008` errors in `src/neuroca/api/dependencies.py`: (Completed)
        -   [X] Step 1.2.2.1: Verify target file state (`Get-Content src/neuroca/api/dependencies.py`). (Completed)
        -   [X] Step 1.2.2.2: Implement fixes for `B008` errors according to FastAPI best practices (using dependency injection correctly). (Completed via # noqa)
        -   [X] Step 1.2.2.3: Verify fixes with `ruff check src/neuroca/api/dependencies.py`. (Completed)
        -   [X] Step 1.2.2.4: Update Knowledge Graph: Mark B008 issues resolved for this file, update file node state. (Completed)
    -   [ ] Step 1.2.3: Address remaining high-priority Ruff issues (TBD after B008 resolution).
-   [ ] **Task 1.3: Type Checking Issue Resolution**
    -   [ ] Step 1.3.1: Prioritize documented `mypy` issues.
    -   [ ] Step 1.3.2: For each high-priority issue:
        -   [ ] Step 1.3.2.1: Verify target file state (`Get-Content`).
        -   [ ] Step 1.3.2.2: Implement fix (add/correct type hints).
        -   [ ] Step 1.3.2.3: Verify fix with `mypy` on the specific file.
        -   [ ] Step 1.3.2.4: Update Knowledge Graph: Mark issue resolved, update file node state.
-   [ ] **Task 1.4: Code Modularity & Size Review**
    -   [ ] Step 1.4.1: Identify Python files in `src/neuroca` exceeding 500 lines.
    -   [ ] Step 1.4.2: For each identified file:
        -   [ ] Step 1.4.2.1: Analyze potential for modular refactoring.
        -   [ ] Step 1.4.2.2: If refactoring is beneficial, define sub-modules/classes.
        -   [ ] Step 1.4.2.3: Plan refactoring steps (create new files, move code).
        -   [ ] Step 1.4.2.4: Update this checklist with specific refactoring tasks/steps.
        -   [ ] Step 1.4.2.5: Update Knowledge Graph: Add planned refactoring details.
-   [ ] **Task 1.5: Configuration Review**
    -   [ ] Step 1.5.1: Review `src/neuroca/config/settings.py` and environment-specific files (`production.py`, `development.py`, etc.).
    -   [ ] Step 1.5.2: Verify sensitive information handling (e.g., use of environment variables via `.env.example`).
    -   [ ] Step 1.5.3: Ensure production settings are appropriate (logging levels, debug flags off).
    -   [ ] Step 1.5.4: Update Knowledge Graph: Add nodes/observations for configuration files and settings.

## Phase 2: Testing & Validation

-   [ ] **Task 2.1: Test Coverage Analysis**
    -   [ ] Step 2.1.1: Execute `pytest` with coverage reporting (`--cov=src/neuroca`).
    -   [ ] Step 2.1.2: Analyze coverage report to identify gaps.
    -   [ ] Step 2.1.3: Document areas with insufficient coverage.
    -   [ ] Step 2.1.4: Update Knowledge Graph: Add coverage metric state.
-   [ ] **Task 2.2: Unit Test Enhancement**
    -   [ ] Step 2.2.1: Prioritize documented coverage gaps for unit tests.
    -   [ ] Step 2.2.2: For each high-priority gap:
        -   [ ] Step 2.2.2.1: Design new unit test cases.
        -   [ ] Step 2.2.2.2: Verify target test file state (`Get-Content`).
        -   [ ] Step 2.2.2.3: Implement new unit tests in the appropriate `tests/unit/` file.
        -   [ ] Step 2.2.2.4: Verify new tests pass (`pytest <test_file_path>`).
        -   [ ] Step 2.2.2.5: Update Knowledge Graph: Add new test nodes, link to code units.
-   [ ] **Task 2.3: Integration Test Enhancement**
    -   [ ] Step 2.3.1: Prioritize documented coverage gaps for integration tests.
    -   [ ] Step 2.3.2: For each high-priority gap:
        -   [ ] Step 2.3.2.1: Design new integration test cases (consider component interactions, API endpoints, database interactions).
        -   [ ] Step 2.3.2.2: Verify target test file state (`Get-Content`).
        -   [ ] Step 2.3.2.3: Implement new integration tests in the appropriate `tests/integration/` file.
        -   [ ] Step 2.3.2.4: Verify new tests pass (`pytest <test_file_path>`).
        -   [ ] Step 2.3.2.5: Update Knowledge Graph: Add new test nodes, link to components/endpoints.
-   [ ] **Task 2.4: Full Test Suite Execution**
    -   [ ] Step 2.4.1: Execute the complete test suite (`pytest`).
    -   [ ] Step 2.4.2: Analyze results for any failures.
    -   [ ] Step 2.4.3: If failures occur:
        -   [ ] Step 2.4.3.1: Perform root cause analysis (using KG if helpful).
        -   [ ] Step 2.4.3.2: Create new checklist items under Phase 1 or relevant section to address the failure.
        -   [ ] Step 2.4.3.3: Halt this task until fixes are implemented and verified.
    -   [ ] Step 2.4.4: Confirm all tests pass.
    -   [ ] Step 2.4.5: Update Knowledge Graph: Mark overall test state as PASSED.

## Phase 3: Documentation Review

-   [ ] **Task 3.1: Docstring Review**
    -   [ ] Step 3.1.1: Review docstrings in `src/neuroca` for completeness and clarity (modules, classes, functions).
    -   [ ] Step 3.1.2: Identify missing or inadequate docstrings.
    -   [ ] Step 3.1.3: For each identified issue:
        -   [ ] Step 3.1.3.1: Verify target file state (`Get-Content`).
        -   [ ] Step 3.1.3.2: Add/update docstring.
        -   [ ] Step 3.1.3.3: Update Knowledge Graph: Update file node documentation status.
-   [ ] **Task 3.2: Project Documentation Review (`docs/`)**
    -   [ ] Step 3.2.1: Review `README.md` for accuracy and completeness (installation, usage).
    -   [ ] Step 3.2.2: Review `docs/index.md` and other Markdown files for consistency and clarity.
    -   [ ] Step 3.2.3: Verify architecture diagrams (`docs/architecture/diagrams/`) reflect the current state.
    -   [ ] Step 3.2.4: Check API documentation (`docs/api/`) against implementation.
    -   [ ] Step 3.2.5: Identify documentation gaps or inaccuracies.
    -   [ ] Step 3.2.6: Create specific checklist items to address documentation issues.
-   [ ] **Task 3.3: Documentation Generation (Optional - if using Sphinx/MkDocs)**
    -   [ ] Step 3.3.1: Generate documentation using the configured tool (e.g., `mkdocs build`).
    -   [ ] Step 3.3.2: Review generated documentation for errors or rendering issues.

## Phase 4: Dependency Management

-   [ ] **Task 4.1: Dependency Audit**
    -   [ ] Step 4.1.1: Review `pyproject.toml` for listed dependencies.
    -   [ ] Step 4.1.2: Check for outdated dependencies (`poetry show --outdated`).
    -   [ ] Step 4.1.3: Check for known security vulnerabilities in dependencies (e.g., using `poetry check` or external tools like `safety`).
    -   [ ] Step 4.1.4: Document findings.
    -   [ ] Step 4.1.5: Update Knowledge Graph: Add dependency nodes and vulnerability status.
-   [ ] **Task 4.2: Dependency Updates (If Necessary)**
    -   [ ] Step 4.2.1: Plan updates for critical/vulnerable dependencies.
    -   [ ] Step 4.2.2: For each update:
        -   [ ] Step 4.2.2.1: Update version in `pyproject.toml`.
        -   [ ] Step 4.2.2.2: Run `poetry lock` and `poetry install`.
        -   [ ] Step 4.2.2.3: Re-run full test suite (Task 2.4) to ensure compatibility.
        -   [ ] Step 4.2.2.4: Update Knowledge Graph: Update dependency node version.

## Phase 5: Knowledge Graph Population

-   [ ] **Task 5.1: Final Knowledge Graph Synthesis**
    -   [ ] Step 5.1.1: Systematically parse `src/neuroca` directory structure and files.
    -   [ ] Step 5.1.2: Create/update KG nodes for all modules, classes, functions, and key relationships (imports, calls, inheritance).
    -   [ ] Step 5.1.3: Create/update KG nodes for API endpoints defined in `src/neuroca/api/routes/`.
    -   [ ] Step 5.1.4: Create/update KG nodes for database schemas/repositories defined in `src/neuroca/db/`.
    -   [ ] Step 5.1.5: Link test cases (`tests/`) to the corresponding code units in the KG.
    -   [ ] Step 5.1.6: Verify KG consistency against the final codebase state.

## Phase 6: Final Verification & Sign-off

-   [ ] **Task 6.1: Pre-Commit Hook Check**
    -   [ ] Step 6.1.1: Ensure `.pre-commit-config.yaml` is configured correctly.
    -   [ ] Step 6.1.2: Run pre-commit hooks on all files (`pre-commit run --all-files`).
    -   [ ] Step 6.1.3: Address any issues identified by hooks.
-   [ ] **Task 6.2: Final Checklist Review**
    -   [ ] Step 6.2.1: Review this entire checklist.
    -   [ ] Step 6.2.2: Confirm all preceding tasks and steps are marked as complete.
-   [ ] **Task 6.3: Production Readiness Declaration**
    -   [ ] Step 6.3.1: Based on successful completion of all phases, declare the project ready for production deployment consideration.

---
*This checklist serves as the authoritative guide. All steps involving file modification require prior file state verification (`Get-Content`). Knowledge Graph updates occur after significant milestones.*
