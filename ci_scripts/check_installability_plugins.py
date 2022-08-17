#!/usr/bin/env python

"""
Check if all Hub-listed plugins can be installed together with latest napari
"""

import json
from subprocess import CalledProcessError, check_output, STDOUT

import requests

NPE2API_CONDA = "https://npe2api.vercel.app/api/conda"


def check_output_verbose(*args, **kwargs):
    """
    Check return code of a subprocess, capturing stdout and stderr.
    If an error happened, print both streams, then raise.
    """
    kwargs.pop("stderr", None)
    kwargs.pop("text", None)
    kwargs.pop("universal_newlines", None)
    try:
        return check_output(*args, stderr=STDOUT, text=True, **kwargs)
    except CalledProcessError as exc:
        print("Output:")
        print(exc.stdout)
        raise


def latest_napari_on_conda_forge():
    r = requests.get("https://api.anaconda.org/package/conda-forge/napari")
    r.raise_for_status()
    return r.json()["latest_version"]


def all_plugin_names():
    r = requests.get(NPE2API_CONDA)
    r.raise_for_status()
    return r.json()


def is_latest_version(name, version):
    r = requests.get(f"{NPE2API_CONDA}/{name}")
    r.raise_for_status()
    latest_version = r.json()["latest_version"]
    return version >= latest_version


def solve(specs):
    resp = check_output_verbose(
        [
            "micromamba",
            "create",
            "-n",
            "notused",
            "--dry-run",
            "-c",
            "conda-forge",
            "--json",
            *specs,
        ]
    )
    print(resp)
    return json.loads(resp)


def main():
    specs = [f"napari={latest_napari_on_conda_forge()}"]
    plugin_names = all_plugin_names()
    for _, conda_name in plugin_names.items():
        if conda_name is not None:
            specs.append(conda_name.replace("/", "::"))

    result = solve(specs)
