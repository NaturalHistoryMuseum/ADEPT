# ADEPT evaluation bundle
Open adept_evaluation.ipynb in Jupyter and run all cells from this folder. Requires Python 3.9+ and pandas. The notebook includes executed outputs and generates supplementary CSV and LaTeX tables plus full metrics and discrepancy reports in results/.

The data are the revised reference and prediction CSVs supplied by Ben Hartley. This is evaluation on development material, not a held-out test. Blank reference values mean no relevant information. Four previously unreadable Gymnadenia measurement cells are blank in the supplied revised file and count as negatives; use explicit exclusions if they remain unscorable. See the notebook for all matching rules.

For Overleaf, add \usepackage{longtable} to the preamble, upload results/supplementary_per_trait.tex, and use \input{supplementary_per_trait.tex}. NA means a metric is undefined. Rates are 0 to 1. No botanical trait synonyms are merged. No changes were made to the supplied input values.
