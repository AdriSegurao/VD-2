# Data Visualization Second Practical Work

**Authors:** Pablo Rodríguez Elvira, Adrián Segura Onorato

Interactive visualizations of the Simpsons scripts dataset using Altair and Jupyter Notebook.

## Setup

Install the required packages before running the notebooks:

```bash
pip install -r requirements.txt
```

> `vegafusion` and `vl-convert-python` are required for Altair to handle large datasets (chart 4 uses line-level data with ~76k rows that exceeds Altair's default row limit).

## Usage

Run the notebooks in this order:

1. **`simpsons_data_processing.ipynb`** — cleans the raw CSV files and produces the four output datasets.
2. **`charts.ipynb`** — loads the processed datasets and renders the interactive charts.

## Data

Place the raw CSV files in the project root before running the processing notebook:

- `simpsons_script_lines.csv`
- `simpsons_episodes.csv`

## Charts

| # | Title | Description |
|---|-------|-------------|
| 1 | Word Count Distribution by Character | Total words spoken per character, filterable by season |
| 2 | Word Count Evolution Across Seasons | Words per season per character, bar and line views |
| 3 | Word Distribution Comparison by Season | Two-character grouped bar comparison across episodes of a season, with season-level boxplots |
| 4 | Word Distribution Comparison by Episode | Two-character scatter plot across the episode timeline, with episode-level boxplots |
| 5 | Sentence Count Distribution by Character | Total sentences spoken per character |
