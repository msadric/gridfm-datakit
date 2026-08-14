# Web sources pulled on 2026-08-13

These sources could not be saved as PDF (blog post, org pages, paywalled article).
Notes below are extracted from a live fetch of each page. The two arXiv papers were
saved as PDF in this same folder: `genco_arxiv_2608.09921.pdf` and
`datakit_arxiv_2512.14658.pdf`.

## IBM Research blog: GENCO neural solver

URL: https://research.ibm.com/blog/gridfm-neural-solver-power-grid

GENCO (Geometric Neural Corrective Solver) is an open source model from IBM Research.
It uses a heterogeneous graph transformer with corrective layers and physics decoders
to analyze power grids up to 10,000 buses. It replaces the usual choice between slow
but accurate AC models and fast but inaccurate DC approximations.

One model handles three tasks that are normally solved separately: power flow, optimal
power flow, and state estimation. Physics informed decoders keep predictions physically
feasible.

Claimed results:
- Up to 30x faster than AC solvers for power flow
- Up to 85x faster than interior point solvers for optimization
- Better accuracy than classical methods for state estimation under sparse measurements
- Validated on Hydro-Quebec's real 1,200 bus transmission network using operational data

The GridFM Development Framework that goes with it provides open datasets (4 million
instances across 6 topologies) and benchmarking tools.

## Hugging Face: gridfm organization

URL: https://huggingface.co/gridfm

Community organization affiliated with LF Energy. 8 team members, 31 datasets
published, no public models listed as of this pull.

Two main dataset collections:
- OPF Data Collection: optimal power flow datasets built on IEEE test cases
  (case14, case30, case57, case118, case500, case2000), ranging from about 27M to 4B
  in size
- PFDelta Data Collection: power flow data organized by task (versions 1.1, 2.2 to 2.3,
  4.1 to 4.3), 20M to 50M in size

Also includes a large specialized dataset, pf_small_case10000_goc, at 13.4B.

## GitHub: gridfm organization

URL: https://github.com/gridfm

Maintains two main Python repositories, both Apache-2.0 licensed:

- gridfm-datakit: generates power flow data to train machine learning and foundation
  models for the electric power grid. 136 stars, 28 forks. Last updated 2026-07-08.
- gridfm-graphkit: trains, finetunes, and lets users interact with a foundation model
  for the electric power grid. 91 stars, 30 forks. Last updated 2026-08-13.

## LF Energy: OpenGridFM project page

URL: https://lfenergy.org/projects/opengridfm/

The page is JavaScript rendered, so only the page metadata could be pulled:

"OpenGridFM is an open source framework to enable emergence of foundation models for
power grids, providing a significant computation speed."

This confirms OpenGridFM is hosted under LF Energy (a Linux Foundation project) as its
umbrella project, with gridfm-datakit and gridfm-graphkit as its repositories.

## Joule perspective paper

URL: https://www.cell.com/joule/fulltext/S2542-4351(24)00470-7

This page returned HTTP 403 Forbidden on fetch. Cell Press blocks automated access and
the full text is likely behind a subscription. Not pulled. Follow the link directly in
a browser to read it.

## Graph foundation model transferability survey (pulled 2026-08-14)

URL: https://arxiv.org/abs/2503.09363
Saved: docs/references/transferability_survey_arxiv_2503.09363.pdf

"Towards Graph Foundation Models: A Transferability Perspective" (Yuxiang Wang, Wenqi
Fan, Suhang Wang, Yao Ma, arXiv:2503.09363, March 2025). A survey, not a new model. It
proposes the first taxonomy that organizes existing Graph Foundation Models (GFMs)
specifically through the lens of transferability, meaning how well a model trained on
one graph domain or task generalizes to another. Graphs vary far more than text or
images in structure, features, and data distribution, which makes transfer harder.

The survey splits GFMs into domain-specific and general-purpose approaches, and maps
out open research directions for improving cross-domain and cross-task generalization.

Relevant here as general background, not GridFM-specific. It is the broader graph-ML
framing of the same generalization problem Mazzonelli's thesis tests empirically for
power grids: zero-shot transfer of a pretrained model to an unseen grid topology (see
`GridFM_documentation.md`, section "Background reading: the origin thesis").
