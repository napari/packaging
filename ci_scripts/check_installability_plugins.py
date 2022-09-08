#!/usr/bin/env python

"""
Check if all Hub-listed plugins can be installed together with latest napari

Environment variables that affect the script:

- CONDA_SUBDIR: Platform to do checks against (linux-64, osx-64, etc)
- PYTHON_VERSION: Which Python version we are testing against
"""

from argparse import ArgumentParser
from collections import defaultdict
from functools import lru_cache
from subprocess import run, PIPE
import json
import os
import sys
import time

from conda.models.version import VersionOrder
import requests

NPE2API_CONDA = "https://npe2api.vercel.app/api/conda"


@lru_cache
def _latest_napari_on_conda_forge():
    r = requests.get("https://api.anaconda.org/package/conda-forge/napari")
    r.raise_for_status()
    return r.json()["latest_version"]


@lru_cache
def _all_plugin_names():
    r = requests.get(NPE2API_CONDA)
    r.raise_for_status()
    return r.json()


@lru_cache
def _latest_plugin_version(name):
    r = requests.get(f"{NPE2API_CONDA}/{name}")
    time.sleep(0.1)
    if r.ok:
        return r.json()["latest_version"]


def _check_if_latest(pkg):
    failures = []
    name, version = pkg["name"], pkg["version"]
    if name == "napari":
        latest_v = _latest_napari_on_conda_forge()
    else:
        latest_v = _latest_plugin_version(name)
    if latest_v:
        if VersionOrder(version) < VersionOrder(latest_v):
            failures.append(f"{name}=={version} is not the latest version ({latest_v})")
    else:
        failures.append(f"Warning: Could not check version for {name}=={version}")
    return failures


@lru_cache
def _patched_environment():
    platform = os.environ.get("CONDA_SUBDIR")
    if not platform:
        return
    env = os.environ.copy()
    if platform.startswith("linux-"):
        env.setdefault("CONDA_OVERRIDE_LINUX", "1")
        env.setdefault("CONDA_OVERRIDE_GLIBC", "2.17")
        env.setdefault("CONDA_OVERRIDE_CUDA", "11.2")
    elif platform.startswith("osx-"):
        env.setdefault("CONDA_OVERRIDE_OSX", "11.2")
    elif platform.startswith("win-"):
        env.setdefault("CONDA_OVERRIDE_WIN", "1")
    return env


def _solve(*args):
    command = [
        "micromamba",
        "create",
        "-n",
        "notused",
        "--dry-run",
        "-c",
        "conda-forge",
        "--json",
        # we only process truthy args
        *(arg for arg in args if arg),
    ]
    resp = run(command, stdout=PIPE, stderr=PIPE, text=True, env=_patched_environment())
    try:
        return json.loads(resp.stdout)
    except json.JSONDecodeError:
        print("Command:", command)
        print("Output:", resp.stdout)
        raise


def _cli():
    p = ArgumentParser()
    p.add_argument("--all", action="store_true")
    return p.parse_args()


def main():
    pyver = os.environ.get(
        "PYTHON_VERSION", f"{sys.version_info.major}.{sys.version_info.minor}"
    )
    python_spec = f"python={pyver}"
    napari_spec = f"napari={_latest_napari_on_conda_forge()}=*pyside*"
    plugin_names = _all_plugin_names()
    plugin_specs = []
    for _, conda_name in plugin_names.items():
        if conda_name is not None:
            plugin_specs.append(conda_name.replace("/", "::"))

    args = _cli()
    if args.all:
        tasks = [(python_spec, napari_spec, *plugin_specs)]
    else:
        # We add an empty string plugin to test for just napari with no plugins
        tasks = [
            (python_spec, napari_spec, plugin_spec)
            for plugin_spec in ("", *plugin_specs)
        ]

    failures = defaultdict(list)
    n_tasks = len(tasks)
    names_to_check = {"napari", *plugin_names}
    for i, task in enumerate(tasks, 1):
        print(f"Task {i:4d}/{n_tasks}:", *task)
        result = _solve(*task)
        if result["success"] is True:
            # Even if the solver is able to find a solution
            # it doesn't mean it's a valid one because metadata
            # can have errors!
            for pkg in result["actions"]["LINK"]:
                if pkg["name"] in names_to_check:
                    # 1) We should have obtained the latest version
                    #    of the plugin. If not, metadata is faulty!
                    maybe_failures = _check_if_latest(pkg)
                    if maybe_failures:
                        failures[task].extend(maybe_failures)
                elif pkg["name"].lower().startswith("pyqt"):
                    # 2) We want pyside only. If pyqt lands in the env
                    #    it was pulled by the plugin or its dependencies.
                    failures[task].append(
                        f"Solution includes {pkg['name']}=={pkg['version']}"
                    )
        else:
            failures[task].extend(result["solver_problems"])
    print("-" * 20)
    for task, failure_list in failures.items():
        print("Installation attempt for", *task, "has errors!")
        print("Reasons:")
        for failure in failure_list:
            print(" - ", failure)
        print("-" * 20)

    return len(failures)


if __name__ == "__main__":
    sys.exit(main())
