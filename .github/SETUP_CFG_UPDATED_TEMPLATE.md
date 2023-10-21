---
title: "`setup.cfg` was updated ({{ env.SETUP_CFG_TODAY }})"
assignees: jaimergp
---

The file `setup.cfg` was modified in `napari/napari`. This might mean the conda-recipe in
`napari/packaging` needs adjusting! Please check!

Calculated diff:

```diff
{{ env.SETUP_CFG_CHANGES }}
```

cc @jaimergp
