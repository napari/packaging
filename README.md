# packaging - conda-based napari installers

[![tests](https://github.com/napari/packaging/actions/workflows/tests.yml/badge.svg)](https://github.com/napari/packaging/actions/workflows/tests.yml)
[![tests_ui](https://github.com/napari/packaging/actions/workflows/tests_ui.yml/badge.svg)](https://github.com/napari/packaging/actions/workflows/tests_ui.yml)

**Important: This repo is used by napari core maintainers.**

## Description

This repository stores the tools (CI pipelines and helper scripts) needed to create **conda-based**
napari installers for Linux, macOS and Windows. It uses the [constructor](https://github.com/conda/constructor)
tool which allows [constructing an installer](https://conda.github.io/constructor/) for a collection
of conda packages.

## Documentation

You can find more information in the following resources:

* [Napari docs about packaging](https://napari.org/dev/developers/coredev/packaging.html)
* [Napari docs about creating installers using this repo and the constructor tool](https://napari.org/dev/developers/coredev/packaging.html#installers)
* [NAP-2: Distributing napari with conda-based packaging](https://napari.org/stable/naps/2-conda-based-packaging.html)

## Usage

### Quickstart

This is how to build an installer for the latest napari release. We assume that `napari/napari` and `napari/packaging` will be cloned as siblings to `napari/` and `napari-packaging`, respectively:

```bash
git clone https://github.com/napari/napari.git napari  # skip if cloned already
cd napari
git checkout <latest-tag>  # only needed for some resources like images, not the code itself
cd ..
git clone https://github.com/napari/packaging.git napari-packaging
cd napari-packaging
conda env create -n napari-packaging-installers --file environments/ci_installers_environment.yml
conda activate napari-packaging-installers
pip install -e ../napari --no-deps
CONSTRUCTOR_PYTHON_VERSION="3.11" python build_installers.py --location ../napari
# Installers will be generated under `_work/`.
```

For any other versions, it's probably easier to [run a `workflow_dispatch` trigger on `.github/workflows/make_bundle_conda.yml`](https://github.com/napari/packaging/actions/workflows/make_bundle_conda.yml).

### Locally built packages

napari installers are created from conda packages _exclusively_, using `constructor`. This means that we need to have conda packages for the napari version we want to distribute. We get those from conda channels: `conda-forge`, `napari`, `napari/label/nightly`, or our own local channel.

Our Github workflows rely on conda-forge feedstock scripts to have the closes possible setup, but for debugging installers we can take a few shortcuts. We only need to know which version we have cloned:

```bash
conda activate napari-packaging-installers
CONSTRUCTOR_USE_LOCAL=1 python build_installers.py --version
# e.g. 0.6.5dev18+gc9111b7bb
```

Now, let's edit the `recipe.yaml` file so it points to our cloned version:

```diff
 context:
   name: napari
-  version: "REPLACE_ME"
+  version: "0.6.5dev18+gc9111b7bb"
   python_min: "3.10"
   build_number: 0

 recipe:
   name: ${{ name|lower }}
   version: ${{ version }}

 source:
-  # This section has been patched from the original conda-forge feedstock
-  # so it uses the mounted volume of the cloned repo in a Docker image
-  - path: /home/conda/feedstock_root/napari-source
+  - path: ../../napari
```

Now build the recipe, making sure packages are generated in `_work/packages/`:

```bash
conda create -n rattler-build rattler-build
conda activate rattler-build
CONDA_BLD_PATH=_work/packages/ rattler-build build --recipe conda-recipe/
```

> Tip: You may skip tests with `--test=skip`

The installers can now be built from the local packages with:

```bash
conda activate napari-packaging-installers
CONSTRUCTOR_USE_LOCAL=1 CONDA_BLD_PATH=_work/packages/ CONSTRUCTOR_PYTHON_VERSION="3.11" python build_installers.py --location ../napari
```

The artifacts will be available in `_work/`.
