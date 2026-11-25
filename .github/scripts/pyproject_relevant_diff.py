"""Print a diff of the packaging-relevant parts of napari's pyproject.toml.

Only ``[build-system]`` and the parts of ``[project]`` that affect what
gets installed are compared, so changes to ``[tool.*]`` configuration,
``[dependency-groups]``, metadata (classifiers, urls, ...) or test/docs
extras are not reported.

The output is a unified diff of a JSON rendering of these tables.
Nothing is printed if they are the same in both revisions.

Usage::

    python pyproject_relevant_diff.py --repo path/to/napari BASE HEAD
"""

import argparse
import difflib
import json
import subprocess
import tomllib

IGNORED_PROJECT_KEYS = frozenset(
    {
        'authors',
        'classifiers',
        'description',
        'license-files',
        'readme',
        'urls',
    },
)
IGNORED_EXTRAS = frozenset(
    {
        'build',
        'dev',
        'docs',
        'gallery',
        'release',
        'testing',
        'testing_extra',
    },
)


def read_pyproject(repo: str, rev: str) -> dict:
    """Return the parsed pyproject.toml from ``rev`` of the ``repo``."""
    text = subprocess.run(
        ['git', '-C', repo, 'show', f'{rev}:pyproject.toml'],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return tomllib.loads(text)


def relevant_part(pyproject: dict) -> dict:
    """Return only the tables that matter for the conda recipe."""
    project = {
        key: value
        for key, value in pyproject.get('project', {}).items()
        if key not in IGNORED_PROJECT_KEYS
    }
    project['optional-dependencies'] = {
        name: deps
        for name, deps in project.get('optional-dependencies', {}).items()
        if name not in IGNORED_EXTRAS
    }
    return {
        'build-system': pyproject.get('build-system', {}),
        'project': project,
    }


def render(repo: str, rev: str) -> list[str]:
    data = relevant_part(read_pyproject(repo, rev))
    return json.dumps(data, indent=2, sort_keys=True).splitlines()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        '--repo',
        default='.',
        help='path to the napari git checkout (default: current directory)',
    )
    parser.add_argument('base', help='old revision')
    parser.add_argument('head', help='new revision')
    args = parser.parse_args()

    diff = difflib.unified_diff(
        render(args.repo, args.base),
        render(args.repo, args.head),
        fromfile=f'pyproject.toml ({args.base})',
        tofile=f'pyproject.toml ({args.head})',
        lineterm='',
    )
    for line in diff:
        print(line)


if __name__ == '__main__':
    main()
