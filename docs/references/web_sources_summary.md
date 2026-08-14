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

## Other grid/power-system foundation model projects (pulled 2026-08-14)

Found while checking whether GridFM (IBM/ETH/Hydro-Quebec, LF Energy) and GridSFM
(Microsoft) are the only two grid foundation model efforts. They are not. Five more
papers pulled and saved:

### LUMINA (two companion papers, Argonne National Laboratory)

The closest direct sibling to GridFM. Authors overlap directly: Kibaek Kim (Argonne)
is a co-author on both LUMINA papers and on the `gridfm-datakit-v1` paper read earlier
in this session. Also involves Emory University and Sogang University.

- `docs/references/lumina_methods_arxiv_2603.04300.pdf`: "LUMINA: Foundation Models
  for Topology Transferable ACOPF" (Li, Memon, Jin, Fenu, Song, Sharma, Gasana, H.
  Kim, Zhao, K. Kim, published as an ICLR 2026 conference paper). Asks what design
  principles a foundation model needs when its predictions must satisfy hard physical
  constraints, using AC-OPF as the test case. Through controlled experiments across
  architectures, training objectives, and system diversity, the paper derives three
  design trade-offs: learning physics-invariant representations while still respecting
  system-specific constraints, optimizing accuracy while keeping solutions feasible,
  and staying reliable in high-impact, tight-margin operating regimes. Releases the
  LUMINA framework, meaning data processing and training pipelines, for reproducible
  research on this kind of model.
- `docs/references/lumina_bench_arxiv_2605.02133.pdf`: "LUMINA: A Grid Foundation
  Model for Benchmarking AC Optimal Power Flow Surrogate Learning" (Jin, Song, Memon,
  Li, Fenu, H. Kim, Zhao, K. Kim). The companion benchmark paper. Introduces
  LUMINA-Bench, a benchmark suite covering multi-topology pretraining, transfer, and
  adaptation for AC-OPF surrogates, evaluating both uniform and diverse architectures
  across single and multi-network scenarios, on both predictive accuracy and physical
  constraint adherence. Open-sourced the data processing, training, and evaluation
  tools.

### CANOS (Google DeepMind)

`docs/references/canos_arxiv_2403.17660.pdf`: "CANOS: A Fast and Scalable Neural
AC-OPF Solver Robust To N-1 Perturbations" (Piloto, Liguori, Madjiheurem, Zgubic,
Lovett, Tomlinson, Elster, Apps, Witherspoon). Not self-branded a foundation model, but
the key precursor both GridFM and the wider field point back to. A GNN-based AC-OPF
solver that predicts within 1 percent of the true cost in 33 to 65 milliseconds,
scales to grids with up to 10000 buses, and is explicitly robust to N-1 topology
perturbations used in security-constrained analysis. Mazzonelli's thesis cites this
directly as the prior work GridFM is positioned against, since CANOS is trained on a
specific topology and not designed to generalize across grid configurations.

### Two papers in a different problem category (electricity time series, not AC-OPF)

Found while searching, worth keeping distinct rather than conflating with the AC-OPF
foundation models above. Both are about learning from electricity time series data
(load, consumption), not about solving power flow or OPF.

- `docs/references/llm_power_systems_arxiv_2312.07044.pdf`: "Large Foundation Models
  for Power Systems" (Huang, Li, Liu, Wang, Chen). Tests whether general-purpose large
  language models like GPT-4 can help with power system tasks (optimal power flow,
  electric vehicle scheduling, knowledge retrieval from engineering reports, situation
  awareness) without any task-specific training. Different approach entirely from
  GridFM/GridSFM/LUMINA, which train dedicated graph models on grid data. This one
  tests off-the-shelf general LLMs on format-free queries.
- `docs/references/powerpm_arxiv_2408.04057.pdf`: "PowerPM: Foundation Model for Power
  Systems" (Tu, Zhang, Zhang, Fu, Zhang, Yang). A foundation model for electricity time
  series specifically, with temporal and hierarchical encoders, pretrained with masked
  time series modeling plus contrastive learning. Evaluated on demand-side management,
  grid stability, and consumer behavior tasks. Not about power flow or OPF.

### Not pulled

A paper titled "PowerGPT: Foundation Model for Power Systems" appears on OpenReview
(id `ntSP0bzr8Y`), possibly close to or overlapping with PowerPM given similar
electricity time series framing, but the OpenReview page is behind a bot-verification
wall that could not be passed automatically, and its arXiv identifier could not be
confirmed. Not pulled, to avoid guessing the wrong paper. Follow the OpenReview link
directly in a browser to check.

## Five more grid foundation model papers (pulled 2026-08-14)

Found by asking, after the first pass above, whether anything was still missing. It
was. This space is moving fast, another pass would likely find more still.

- `docs/references/weather_fm_power_grid_arxiv_2509.25268.pdf`: "A Weather Foundation
  Model for the Power Grid" (Bodnar, Rousseau-Rizzi, Shankar, Merleau, Flampouris,
  Candille, Antic, Miralles, Gupta). Not a power-flow model at all. Fine-tunes a
  1.5 billion parameter weather foundation model (the Generative Forecasting
  Transformer) on Hydro-Quebec's own infrastructure data to forecast five variables
  relevant to grid operations: surface temperature, precipitation, hub height wind
  speed, wind turbine icing risk, and rime ice buildup on power lines. Cuts
  temperature MAE by 15 percent, precipitation MAE by 35 percent, wind speed MAE by
  15 percent, and reaches 0.72 average precision for day ahead rime ice detection,
  a hazard conventional forecasting cannot predict well. Francois Miralles, a
  Hydro-Quebec author, also appears on the Joule perspective paper read earlier in
  this session. Complementary to GridFM, not a competitor: this is weather
  forecasting in service of grid operations, not a power-flow or OPF surrogate.

- `docs/references/mxgps_arxiv_2607.13763.pdf`: "MxGPS: Multiplex Graph Transformers
  for a Power Grid Foundation Model" (Papaioannou, Tsantilas, Giannakakos,
  Michalakopoulos, Pelekis, Marinakis, Aryandoust, Monti, Bessa, Vergara, Cremer,
  Sarmas). A genuine alternative approach to the exact generalization problem GridFM
  and LUMINA both target. Argues that models with low training error often fail badly
  on unseen grid topologies because they encode structure specific to the training
  topologies. Trains multiplex graph transformers jointly on two tasks, static state
  estimation and AC power flow, and shows this joint training discourages
  topology-specific overfitting. On four unseen grid configurations: zero boundary
  violations and only 39 percent performance degradation under topology shift, versus
  190 to 1400 percent degradation for competing models. Uses only 1.6 million
  parameters, far smaller than typical foundation model scale. Worth reading against
  the PG vs PG-TP reproduction attempt recorded in `GridFM_documentation.md`, since it
  reports a much cleaner generalization result on the same class of problem.

- `docs/references/tokamind_power_grid_arxiv_2605.11033.pdf`: "TokaMind for Power
  Grid: Cross-Domain Transfer from Fusion Plasma" (Wu, Lee, Chen). An unusual
  transfer-learning angle: TokaMind is a multi-modal transformer originally trained on
  tokamak fusion plasma data (MAST), and this paper tests whether its learned
  representations transfer to power grid PMU (synchrophasor) data for event
  classification, alongside two industrial degradation datasets as other transfer
  targets. Power grid PMU data was the best match among the domains tested. Reaches
  F1 = 0.837 on a severe-event classification benchmark, and finds that classification
  difficulty is driven by provider-level grid topology, not by model capacity. First
  cross-domain validation of TokaMind outside fusion. Different problem again: PMU
  event/anomaly classification, not power-flow or OPF solving.

- `docs/references/gridmind_arxiv_2509.02494.pdf`: "GridMind: LLMs-Powered Agents for
  Power System Analysis and Operations" (Hongwei Jin, Kibaek Kim, Jonghwan Kwon). A
  third Argonne National Laboratory project in this space, same two authors as
  LUMINA (Jin, Kim). Different paradigm again: not a trained surrogate model, but a
  multi-agent framework that combines LLMs with real engineering solvers, using
  function calls to keep the actual AC-OPF and N-1 contingency analysis numerically
  accurate while letting a user interact in natural language. Tested on IEEE cases.
  Finds smaller LLMs can match larger ones on analytical accuracy while using less
  compute. Positions agentic AI, meaning an LLM that calls real solvers rather than
  approximating them, as a distinct alternative to training a neural surrogate at all.

- `docs/references/differentiable_power_flow_arxiv_2603.28203.pdf`: "Differentiable
  Power-Flow Optimization" (Oz, Hoerter, Phipps, Debus, Streit, Goetz). Not a
  foundation model, included for completeness since it surfaced in the same search.
  Reformulates AC power flow as a differentiable simulation (DPF) so gradients flow
  end to end from physical power mismatches back to the simulation parameters, built
  on PyTorch for GPU acceleration and batching. Positions itself for time series
  analysis, N-1 contingency analysis, and fast screening tools, not for pretraining a
  reusable model. A different technique category from everything else in this list:
  differentiable physics simulation, not learned representation transfer.
