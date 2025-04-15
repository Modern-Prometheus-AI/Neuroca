# Autonomous LLM Codebase Analysis Prompt for NeuroCognitive Architecture (NCA) v1.0.0

**Date:** 2025-04-14
**Time:** 14:30 UTC+0

---

## Subject: Codebase Analysis Request - NeuroCognitive Architecture (NCA)

---

## Directive Section

This prompt is designed for autonomous, in-depth analysis of the NeuroCognitive Architecture (NCA) codebase, a sophisticated framework enhancing Large Language Models (LLMs) with biologically-inspired cognitive capabilities. The execution mode is strictly sequential and autonomous, adhering to the guidelines in the Code Analysis Quality & Standards Guide located at `./CODEBASE_STANDARDS_REPOSITORY/CODE_ANALYSIS_STANDARDS.md`. Intermediate reporting is disabled; only the final comprehensive report will be provided upon completion of all phases. Progress and findings must be logged internally as per the Analysis Progress Log Protocol. The overall objective is to thoroughly analyze the NCA codebase to understand its architecture, identify strengths, detect potential issues, and provide actionable recommendations for improvement.

---

## Analysis Progress Log Protocol (Internal)

- **Log Location:** `analysis_artifacts/NCA_Analysis_Log.md`
- **Data Points to Log:** Date, Phase/Task, Files/Modules Analyzed, Functions/Classes Mapped, Dependencies Identified, Issues Found (Type, Severity, Location), Verification Checks Performed, Identified Ambiguities/Gaps, Compliance Notes
- **Update Frequency:** After completion and verification of each Task

---

## Hierarchical Execution Blocks

### Phase 1: Scoping & Setup
- [ ] **Phase 1: Scoping & Setup**
  **Objective:** Establish the scope of analysis, set up necessary tools, and gather initial context about the NCA codebase.

  - [ ] **Task 1.1: Define Analysis Scope and Objectives**
    **Task Objective:** Clearly define the boundaries and goals of the NCA codebase analysis.
    - [ ] *Step 1.1.1 [(Rule #S1: SCOPE_DEFINITION)](./CODEBASE_STANDARDS_REPOSITORY/CODE_ANALYSIS_STANDARDS.md#rule-S1):* Identify the primary modules of interest within the NCA codebase, including core, memory, integration, and API components based on project structure in `Neuroca/docs/README.md` and `docs/`.
    - [ ] *Step 1.1.2 [(Rule #S2: OBJECTIVE_CLARITY)](./CODEBASE_STANDARDS_REPOSITORY/CODE_ANALYSIS_STANDARDS.md#rule-S2):* Define specific analysis objectives such as understanding architecture, identifying bottlenecks, and assessing code quality.
    **Internal Success Criteria:**
    - A documented list of target modules and specific analysis objectives exists.
    - Compliance with all referenced Code Analysis Standards Rules.
    **Internal Verification Method:**
    - Verify that the list of target modules aligns with the project structure documentation.
    - Confirm that objectives are specific, measurable, and relevant to the NCA codebase goals.
    - Verify compliance with referenced Code Analysis Standards Rules for this Task and its Steps.
    **Task Completion Review (Internal):**
    - Update internal Analysis Log with defined scope, objectives, and verification status.

  - [ ] **Task 1.2: Gather Initial Documentation and Context**
    **Task Objective:** Collect and review available documentation to build foundational knowledge of the NCA codebase.
    - [ ] *Step 1.2.1 [(Rule #D1: DOC_REVIEW)](./CODEBASE_STANDARDS_REPOSITORY/CODE_ANALYSIS_STANDARDS.md#rule-D1):* Locate and review key documentation files in `Neuroca/docs/` including architecture, components, and data flow descriptions.
    - [ ] *Step 1.2.2 [(Rule #D2: CONTEXT_BUILD)](./CODEBASE_STANDARDS_REPOSITORY/CODE_ANALYSIS_STANDARDS.md#rule-D2):* Summarize the purpose and key features of NCA from `Neuroca/README.md` and other introductory materials.
    **Internal Success Criteria:**
    - A summary of key documentation and context about NCA is documented.
    - Compliance with all referenced Code Analysis Standards Rules.
    **Internal Verification Method:**
    - Check that all relevant documentation files have been accessed and summarized.
    - Validate that the summary accurately reflects the purpose and features of NCA.
    - Verify compliance with referenced Code Analysis Standards Rules for this Task and its Steps.
    **Task Completion Review (Internal):**
    - Update internal Analysis Log with reviewed documents, summary of context, and verification status.

  **Phase Completion Review (Internal):**
  - Review cumulative findings for Phase 1, assess progress against scoping objectives, and update the internal Analysis Log with any correlations or initial insights.

---

### Phase 2: Code Parsing & Static Analysis
- [ ] **Phase 2: Code Parsing & Static Analysis**
  **Objective:** Perform a detailed static analysis of the NCA codebase to identify code structure, quality issues, and initial findings.

  - [ ] **Task 2.1: Static Analysis of Core Module**
    **Task Objective:** Perform static analysis on all relevant source files within the `neuroca/core` module to identify potential code quality issues, complexity hotspots, and adherence to defined coding standards.
    - [ ] *Step 2.1.1 [(Rule #C1: FILE_ID)](./CODEBASE_STANDARDS_REPOSITORY/CODE_ANALYSIS_STANDARDS.md#rule-C1):* Identify all source code files (e.g., `.py`) within the target module path: `Neuroca/src/neuroca/core`.
    - [ ] *Step 2.1.2 [(Rule #C2: LINT_TOOL)](./CODEBASE_STANDARDS_REPOSITORY/CODE_ANALYSIS_STANDARDS.md#rule-C2), [(Rule #C3: STYLE_GUIDE)](./CODEBASE_STANDARDS_REPOSITORY/CODE_ANALYSIS_STANDARDS.md#rule-C3):* Execute the configured linter/static analyzer (e.g., Pylint) using the project-specific configuration against the identified files. Capture all reported issues.
    - [ ] *Step 2.1.3 [(Rule #C4: COMPLEX_TOOL)](./CODEBASE_STANDARDS_REPOSITORY/CODE_ANALYSIS_STANDARDS.md#rule-C4):* If available, run code complexity analysis (e.g., Radon) to calculate metrics like Cyclomatic Complexity for functions/methods. Identify units exceeding thresholds defined in (Rule #C4).
    - [ ] *Step 2.1.4 [(Rule #C5: ISSUE_AGGREGATE)](./CODEBASE_STANDARDS_REPOSITORY/CODE_ANALYSIS_STANDARDS.md#rule-C5):* Aggregate findings from Steps 2.1.2 and 2.1.3. Normalize issue format (File, Line, Rule ID, Severity, Description). Categorize issues based on type (e.g., Style, Bug Risk, Complexity, Security, Performance).
    - [ ] *Step 2.1.5 [(Rule #C6: FALSE_POS_REVIEW)](./CODEBASE_STANDARDS_REPOSITORY/CODE_ANALYSIS_STANDARDS.md#rule-C6):* Perform an initial automated review or apply heuristics to flag potential false positives based on common patterns or suppression comments. Document flagged items.
    **Internal Success Criteria:**
    - A documented list of source files targeted for analysis exists.
    - Linter/static analyzer execution completed successfully; raw output is stored.
    - Complexity metrics (if applicable) are calculated and stored for relevant code units.
    - A consolidated, categorized list of static analysis findings is generated in a structured format (e.g., JSON).
    - Potential false positives are flagged with rationale.
    - Compliance with all referenced Code Analysis Standards Rules.
    **Internal Verification Method:**
    - Verify the analyzed file list correctly reflects the target module.
    - Check static analyzer logs for execution errors or configuration issues.
    - Spot-check a sample of reported issues against the source code to confirm location and validity.
    - Verify complexity scores for high-complexity units seem plausible relative to code structure.
    - Review the format and completeness of the aggregated findings list.
    - Check that flagged false positives have supporting evidence or rationale.
    - Verify compliance with referenced Code Analysis Standards Rules for this Task and its Steps.
    **Task Completion Review (Internal):**
    - Update internal Analysis Log with files analyzed, tools run, summary of findings counts by category/severity, and verification status.

  **Phase Completion Review (Internal):**
  - Review cumulative findings for Phase 2, assess progress against static analysis objectives, check for correlations between different types of findings, and update the internal Analysis Log.

---

### Phase 3: Dependency Mapping
- [ ] **Phase 3: Dependency Mapping**
  **Objective:** Map dependencies within the NCA codebase to understand inter-module relationships and potential coupling issues.

  - [ ] **Task 3.1: Identify Module Dependencies**
    **Task Objective:** Analyze dependencies between major NCA modules such as `core`, `memory`, `integration`, and `api`.
    - [ ] *Step 3.1.1 [(Rule #D1: DEP_ID)](./CODEBASE_STANDARDS_REPOSITORY/CODE_ANALYSIS_STANDARDS.md#rule-D1):* Identify import statements and module references across source files in `Neuroca/src/neuroca/`.
    - [ ] *Step 3.1.2 [(Rule #D2: DEP_GRAPH)](./CODEBASE_STANDARDS_REPOSITORY/CODE_ANALYSIS_STANDARDS.md#rule-D2):* Generate a dependency graph or matrix showing relationships between modules.
    - [ ] *Step 3.1.3 [(Rule #D3: CIRCULAR_DEP)](./CODEBASE_STANDARDS_REPOSITORY/CODE_ANALYSIS_STANDARDS.md#rule-D3):* Detect potential circular dependencies or tight coupling issues.
    **Internal Success Criteria:**
    - A comprehensive list of inter-module dependencies is documented.
    - A dependency graph or matrix is generated.
    - Circular dependencies or coupling issues are identified and documented.
    - Compliance with all referenced Code Analysis Standards Rules.
    **Internal Verification Method:**
    - Cross-check identified dependencies with actual import statements in code.
    - Validate the dependency graph against known module interactions from documentation.
    - Confirm that circular dependency findings are accurate by reviewing code paths.
    - Verify compliance with referenced Code Analysis Standards Rules for this Task and its Steps.
    **Task Completion Review (Internal):**
    - Update internal Analysis Log with dependency findings, graph details, and verification status.

  **Phase Completion Review (Internal):**
  - Review cumulative findings for Phase 3, assess progress against dependency mapping objectives, check for potential architectural issues, and update the internal Analysis Log.

---

### Phase 4: Logic & Flow Analysis
- [ ] **Phase 4: Logic & Flow Analysis**
  **Objective:** Analyze the logic and control flow within critical NCA components, focusing on the three-tiered memory system and LLM integration.

  - [ ] **Task 4.1: Analyze Memory System Logic**
    **Task Objective:** Understand the logic and flow of the three-tiered memory system (Working, Episodic, Semantic) in `neuroca/memory`.
    - [ ] *Step 4.1.1 [(Rule #L1: LOGIC_TRACE)](./CODEBASE_STANDARDS_REPOSITORY/CODE_ANALYSIS_STANDARDS.md#rule-L1):* Trace the flow of data through memory tiers by analyzing key functions and classes in `Neuroca/src/neuroca/memory/`.
    - [ ] *Step 4.1.2 [(Rule #L2: COMPLEXITY_ASSESS)](./CODEBASE_STANDARDS_REPOSITORY/CODE_ANALYSIS_STANDARDS.md#rule-L2):* Assess the complexity of memory management logic, identifying potential bottlenecks or error-prone areas.
    **Internal Success Criteria:**
    - A detailed flow diagram or description of memory system logic is documented.
    - Complexity hotspots or potential issues in memory logic are identified.
    - Compliance with all referenced Code Analysis Standards Rules.
    **Internal Verification Method:**
    - Validate the flow diagram against actual code paths in memory system files.
    - Confirm identified complexity issues by cross-referencing with static analysis results.
    - Verify compliance with referenced Code Analysis Standards Rules for this Task and its Steps.
    **Task Completion Review (Internal):**
    - Update internal Analysis Log with memory system logic findings and verification status.

  **Phase Completion Review (Internal):**
  - Review cumulative findings for Phase 4, assess progress against logic analysis objectives, check for systemic issues in flow, and update the internal Analysis Log.

---

### Phase 5: Quality & Security Assessment
- [ ] **Phase 5: Quality & Security Assessment**
  **Objective:** Evaluate the NCA codebase for quality, performance, and security issues.

  - [ ] **Task 5.1: Security Vulnerability Scan**
    **Task Objective:** Identify potential security vulnerabilities in the NCA codebase, focusing on LLM integration and API components.
    - [ ] *Step 5.1.1 [(Rule #S1: SEC_SCAN)](./CODEBASE_STANDARDS_REPOSITORY/CODE_ANALYSIS_STANDARDS.md#rule-S1):* Scan source files in `Neuroca/src/neuroca/integration/` and `Neuroca/src/neuroca/api/` for common security issues like input validation, authentication flaws, and secrets management.
    - [ ] *Step 5.1.2 [(Rule #S2: SEC_REPORT)](./CODEBASE_STANDARDS_REPOSITORY/CODE_ANALYSIS_STANDARDS.md#rule-S2):* Document identified vulnerabilities with severity, location, and potential mitigation strategies.
    **Internal Success Criteria:**
    - A list of potential security vulnerabilities is documented with details.
    - Compliance with all referenced Code Analysis Standards Rules.
    **Internal Verification Method:**
    - Spot-check reported vulnerabilities against code to confirm accuracy.
    - Verify that all critical areas (integration, API) have been scanned.
    - Verify compliance with referenced Code Analysis Standards Rules for this Task and its Steps.
    **Task Completion Review (Internal):**
    - Update internal Analysis Log with security findings and verification status.

  **Phase Completion Review (Internal):**
  - Review cumulative findings for Phase 5, assess progress against quality and security objectives, prioritize critical issues, and update the internal Analysis Log.

---

### Phase 6: Synthesis & Reporting
- [ ] **Phase 6: Synthesis & Reporting**
  **Objective:** Synthesize all findings into a comprehensive report with actionable recommendations for the NCA codebase.

  - [ ] **Task 6.1: Compile Final Analysis Report**
    **Task Objective:** Create a detailed report summarizing all phases of analysis, key findings, and recommendations.
    - [ ] *Step 6.1.1 [(Rule #R1: REPORT_STRUCTURE)](./CODEBASE_STANDARDS_REPOSITORY/CODE_ANALYSIS_STANDARDS.md#rule-R1):* Organize findings into sections covering architecture overview, code quality, dependencies, logic flow, security, and performance.
    - [ ] *Step 6.1.2 [(Rule #R2: RECOMMENDATIONS)](./CODEBASE_STANDARDS_REPOSITORY/CODE_ANALYSIS_STANDARDS.md#rule-R2):* Provide actionable recommendations for identified issues, prioritizing critical security and performance concerns.
    **Internal Success Criteria:**
    - A comprehensive report is compiled covering all analysis phases.
    - Recommendations are specific, prioritized, and actionable.
    - Compliance with all referenced Code Analysis Standards Rules.
    **Internal Verification Method:**
    - Verify that all phases and findings are represented in the report.
    - Check that recommendations align with identified issues and project goals.
    - Verify compliance with referenced Code Analysis Standards Rules for this Task and its Steps.
    **Task Completion Review (Internal):**
    - Update internal Analysis Log with report completion status and verification details.

  **Phase Completion Review (Internal):**
  - Review the final report for completeness, ensure all objectives are met, and update the internal Analysis Log with final status.

---

## Final Instruction

Begin execution of this prompt immediately, following the strict sequential order of Phases, Tasks, and Steps as outlined. Mark checkboxes as complete (`- [x]`) only after each item meets its Internal Success Criteria and passes verification. Adhere strictly to the guidelines in `./CODEBASE_STANDARDS_REPOSITORY/CODE_ANALYSIS_STANDARDS.md`, ensuring thoroughness and analytical rigor throughout the process. Intermediate reporting is prohibited; only the final report from Phase 6 will be provided externally. Perform a last sweep (*FINAL-CODE-ANALYSIS-SWEEP*) over the entire analysis process and output to ensure quality, accuracy, completeness, proper issue reporting, and identification of analysis limitations.

---

## Contextual Footer

*Instructions generated: 2025-04-14 14:30 UTC+0. Location context: Windows OS, Workspace at c:\git\Neuro-Cognitive-Agent\Neuroca*
