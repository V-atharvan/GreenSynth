# Analysis Reproducibility & Provenance

## 1. Provenance Tree
Every statistical result traces directly back to:
$$\text{Result} \rightarrow \text{AnalysisRun} \rightarrow \text{DatasetVersion} \rightarrow \text{Experiment} \rightarrow \text{Sample} \rightarrow \text{Raw/Processed Data}$$

## 2. Reproducibility Metadata
Every analysis run stores analysis method, parameters, dataset version, software version, scientific method version, and random seed (where applicable).
