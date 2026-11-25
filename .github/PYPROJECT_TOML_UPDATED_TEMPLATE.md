---
title: "`pyproject.toml` was updated ({{ env.PYPROJECT_TOML_TODAY }})"
assignees:
  - jni
  - czaki
  - psobolewskiPhD
---

The file [`pyproject.toml`](https://github.com/napari/napari/blob/main/pyproject.toml) (see [history](https://github.com/napari/napari/commits/main/pyproject.toml)) was modified in `napari/napari` in a way that may affect packaging (`[build-system]`, or install-related parts of `[project]` such as dependencies, runtime extras, `requires-python` or entry points). Changes to `[tool.*]`, `[dependency-groups]`, project metadata and test/docs extras are not reported. This might mean the conda-recipe in `napari/packaging` needs adjusting! Please check!

Calculated diff (of a JSON rendering of the relevant tables):

```diff
{{ env.PYPROJECT_TOML_CHANGES }}
```

cc @jni, @czaki, @psobolewskiPhD, @TimMonko
