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

from tqdm import tqdm
from conda.models.version import VersionOrder
import requests

NPE2API_CONDA = "https://npe2api.vercel.app/api/conda"


@lru_cache
def latest_napari_on_conda_forge():
    r = requests.get("https://api.anaconda.org/package/conda-forge/napari")
    r.raise_for_status()
    return r.json()["latest_version"]


@lru_cache
def all_plugin_names():
    r = requests.get(NPE2API_CONDA)
    r.raise_for_status()
    return r.json()


@lru_cache
def latest_version(name):
    r = requests.get(f"{NPE2API_CONDA}/{name}")
    r.raise_for_status()
    time.sleep(0.1)
    return r.json()["latest_version"]


@lru_cache
def patched_environment():
    platform = os.environ.get("CONDA_SUBDIR")
    if not platform:
        return
    env = os.environ.copy()
    if platform.startswith("linux-"):
        env.setdefault("CONDA_OVERRIDE_GLIBC", "2.17")
        env.setdefault("CONDA_OVERRIDE_CUDA", "11.2")
    elif platform.startswith("osx-"):
        env.setdefault("CONDA_OVERRIDE_OSX", "11.2")
    return env


def solve(*args):
    command = [
        "micromamba",
        "create",
        "-n",
        "notused",
        "--dry-run",
        "-c",
        "conda-forge",
        "--json",
        *args,
    ]
    resp = run(command, stdout=PIPE, stderr=PIPE, text=True, env=patched_environment())
    try:
        return json.loads(resp.stdout)
    except json.JSONDecodeError:
        print("Command:", command)
        print("Output:", resp.stdout)
        raise


def cli():
    p = ArgumentParser()
    p.add_argument("--all", action="store_true")
    return p.parse_args()


def main():
    pyver = os.environ.get(
        "PYTHON_VERSION", f"{sys.version_info.major}.{sys.version_info.minor}"
    )
    python_spec = f"python={pyver}"
    napari_spec = f"napari={latest_napari_on_conda_forge()}=*pyside*"
    plugin_names = all_plugin_names()
    plugin_specs = []
    for _, conda_name in plugin_names.items():
        if conda_name is not None:
            plugin_specs.append(conda_name.replace("/", "::"))

    args = cli()
    if args.all:
        tasks = [(python_spec, napari_spec, *plugin_specs)]
    else:
        tasks = [
            (python_spec, napari_spec, plugin_spec) for plugin_spec in plugin_specs
        ]

    failures = defaultdict(list)
    n_tasks = len(tasks)
    for i, task in enumerate(tasks, 1):
        print(f"Task {i:4d}/{n_tasks}:", *task)
        result = solve(*task)
        if result["success"] is True:
            for pkg in result["actions"]["LINK"]:
                if pkg["name"] in plugin_names:
                    pkg_latest_version = latest_version(pkg["name"])
                    if VersionOrder(pkg["version"]) < VersionOrder(pkg_latest_version):
                        failures[task].append(
                            f'{pkg["name"]}=={pkg["version"]} '
                            f"is not the latest version ({pkg_latest_version})"
                        )
                elif pkg["name"].lower().startswith("pyqt"):
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
