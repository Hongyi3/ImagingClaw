# Reference Stack

ClawImaging should sit above, not replace, the strongest existing domain libraries.

## Cross-domain inverse problems

### DeepInverse
Use for:
- learned inverse methods
- modular forward operators
- deep inverse benchmarks

### ODL
Use for:
- operator-centric prototyping
- variational inverse problems
- tomography-adjacent operator abstractions

### SCICO
Use for:
- JAX-based optimization and computational imaging
- differentiable operator work
- GPU/TPU-accelerated inverse methods

### Pyxu
Use for:
- scalable computational imaging pipelines
- out-of-core and hardware-agnostic operator workflows

## CT / tomography

### ASTRA
Use for:
- performant GPU tomography primitives
- reference analytic and iterative baselines

### CIL
Use for:
- tomographic preprocessing and reconstruction workflows
- challenging or non-standard tomography cases

## MRI

### BART
Use for:
- command-line and library-based MRI reconstruction baselines
- classical and optimization-heavy MRI pipelines

### SigPy
Use for:
- Python-first iterative MRI work
- sampling, preconditioners, and fast prototyping

## Coherent imaging

### PtyPy
Use for:
- end-to-end ptychography workflows
- reconstruction plus visualization

### Ptychography 4.0
Use for:
- modern public ptychography implementations and datasets
- reconstruction infrastructure in that ecosystem

## Adapter rule

Adapters should:
- keep imports lazy
- expose a stable internal interface
- document license and version assumptions
- avoid leaking backend-specific design into the core API
