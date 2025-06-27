---
title: "`pyproject.toml` was updated ({{ env.PYPROJECT_TOML_TODAY }})"
assignees:
  - jni
  - czaki
  - psobolewskiPhD
---

The file [`pyproject.toml`](https://github.com/napari/napari/blob/main/pyproject.toml) (see [history](https://github.com/napari/napari/commits/main/pyproject.toml)) was modified in `napari/napari`. This might mean the conda-recipe in `napari/packaging` needs adjusting! Please check!

Calculated diff:

```diff
{{ env.PYPROJECT_TOML_CHANGES }}
```

cc @jni, @czaki, @psobolewskiPhD, @TimMonko
