---
title: "`pyproject.toml` was updated ({{ env.PYPROJECT_TOML_TODAY }})"
assignees: jaimergp
---

The file `pyproject.toml` was modified in `napari/napari`. This might mean the conda-recipe in
`napari/packaging` needs adjusting! Please check!

Calculated diff:

```diff
{{ env.PYPROJECT_TOML_CHANGES }}
```

cc @jaimergp
