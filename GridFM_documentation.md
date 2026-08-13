## Documentation Guidelines

Use this document to record important discussions and findings from work with Claude Code across both GridFM repositories:

- `gridfm-datakit`
- `gridfm-graphkit`

- Write in simple, clear language.
- Do not use em dashes.
- Summarize the key findings, decisions, changes, and open questions.
- Organize information under clear headings.
- Keep related information together.
- Identify the repository for every change, finding, decision, and commit.
- Commit work regularly in small, atomic commits. Each commit should contain one logical change and leave the repository in a usable state.
- After each commit, record the repository name, commit number or short hash, and a one-line summary in the commit log below. Use these identifiers when referring to changes in the rest of the document.
- Periodically review and reorganize the document so it remains a useful overview. Do not simply append new information to the end.

## Background reading (pulled 2026-08-13)

Repository: `gridfm-datakit`

The links listed in `context.md` were pulled and saved under
`docs/references/`. The two arXiv papers were saved as PDF. The blog post, the
Hugging Face and GitHub org pages, and the LF Energy project page were saved as
notes in `docs/references/web_sources_summary.md`, since they are web pages, not
papers. The Joule perspective paper could not be pulled. Cell Press returned
HTTP 403 Forbidden, the article is behind a paywall.

Files saved:
- `docs/references/genco_arxiv_2608.09921.pdf`
- `docs/references/datakit_arxiv_2512.14658.pdf`
- `docs/references/web_sources_summary.md`

### GENCO (IBM Research)

GENCO, short for Geometric Neural Corrective Solver, is an open source neural
model that analyzes power grids. It uses a graph transformer with corrective
layers and physics decoders, and scales to grids up to 10,000 buses. One model
handles power flow, optimal power flow, and state estimation, tasks that are
normally solved with separate tools. Claimed speedups are up to 30x over AC
solvers for power flow and up to 85x over interior point solvers for
optimization. It was validated on Hydro-Quebec's real 1,200 bus transmission
network. The GridFM Development Framework that supports it includes open
datasets with 4 million instances across 6 topologies.

### gridfm-datakit paper

Title: "gridfm-datakit-v1: A Python Library for Scalable and Realistic Power
Flow and Optimal Power Flow Data Generation." This is the paper for this
repository. It describes three gaps the library fills in existing data
generation tools: limited scenario diversity, datasets restricted to feasible
operating points, and inflexible generator cost functions. It compares the
library against OPFData, OPF-Learn, PGLearn, and PF-Delta.

### GridFM on Hugging Face and GitHub

The GridFM organization on Hugging Face is affiliated with LF Energy and has
published 31 datasets, mainly OPF data built on IEEE test cases (case14 through
case2000) and PFDelta task data. No public models are listed yet.

The GridFM organization on GitHub hosts two repositories: `gridfm-datakit`
(this repository, data generation) and `gridfm-graphkit` (foundation model
training and inference).

### OpenGridFM and LF Energy

OpenGridFM is the umbrella project under LF Energy, a Linux Foundation project.
Its stated goal is to enable foundation models for power grids with a
significant computation speed advantage over classical tools. `gridfm-datakit`
and `gridfm-graphkit` are its two repositories.

### Open question

The Joule perspective paper has not been read. It needs to be accessed manually
through a subscription or institutional access, since automated fetching is
blocked.

## Commit Log

Record completed work in this format:

| Repository | Commit | Summary |
| --- | --- | --- |
| `<repository>` | `<short hash>` | Brief description of the logical change |