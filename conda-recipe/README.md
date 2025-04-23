This folder is a patched copy of the conda-forge/napari-feedstock `recipe/`
directory:
- The `source` section points to a local source, not a PyPI tarball.
- The `outputs` section might be different too to accommodate changes happening
  during development (e.g. new dependency was added.)

Use this link to see what happened in `napari/napari:pyproject.toml`, compared
to last release:

    https://github.com/napari/napari/compare/v${VERSION_HERE}...main

and look for `pyproject.toml` in the Files tab.

You can also check the changes locally using git. For example, to check the
changes since v0.5.6, make sure you have the latest main branch then use the
command:

    git diff v0.5.6..HEAD pyproject.toml

The point of having a local copy is to be able to update it while developing
the next release, without needing to publish the changes on conda-forge. On
releases, the recipe contents here must be synced with conda-forge (mostly the
`outputs` section).

If changes occur on conda-forge (e.g. changes required by new infra), the
contents of `recipe/` must be synced here!
