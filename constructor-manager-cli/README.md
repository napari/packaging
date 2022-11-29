# Constructor Manager Commnand line interface

Handle (conda) constructor based bundled applications from the command line.

## Requirements

- conda
- conda-lock
- mamba
- packaging
- requests
- pyyaml

## Installation

This package needs to be installed on the `base` conda environemnt.

```bash
conda install conda-lock mamba packaging requests pyyaml -c conda-forge -y
pip install -e .
```

## Examples

### Check for updates

#### For a given package

```bash
constructor-manager check-updates "napari=0.4.15=*pyside*" -c conda-forge
```

This will check for any updates available for the package named `napari`
taking into account that the current version is `0.4.15`. We are looking for
available version on the `conda-forge` channel.

```json
{
    "available_versions": [
        "0.4.17",
        "0.4.16",
        "0.4.15"
    ],
    "current_version": "0.4.15",
    "latest_version": "0.4.17",
    "previous_version": null,
    "found_versions": [
        "0.4.16",
        "0.4.17"
    ],
    "update": true,
    "installed": true,
    "status": {}
}
```

#### For a given package development versions

```bash
constructor-manager check-updates napari=0.4.15 -c conda-forge -c napari --dev
```

```json
{
    "available_versions": [
        "0.4.17",
        "0.4.17rc8",
        "0.4.17rc5",
        "0.4.17rc4",
        "0.4.17rc4.dev87+g518735b2",
        "0.4.17rc4.dev83+gc9699687",
        "0.4.17rc4.dev80+gaaea9f06",
        "0.4.17rc4.dev79+ge0b7c88a",
        "0.4.17rc4.dev78+gcd5c3147",
        "0.4.17rc4.dev75+gee94c35c",
        "0.4.17rc4.dev74+g8a78b3cc",
        "0.4.17rc4.dev72+g1cc90a74",
        "0.4.17rc4.dev71+g9131b7c2",
        "0.4.17rc4.dev53+gd5ffbacc",
        "0.4.17rc4.dev52+g5cfcc38c",
        "0.4.17rc4.dev51+gb445d2ff",
        "0.4.17rc4.dev47+gec69e693",
        "0.4.17rc4.dev46+g5080ab06",
        "0.4.17rc4.dev44+g8196109b",
        "0.4.17rc4.dev42+gfb81ff62",
        "0.4.17rc4.dev41+ge90c7f88",
        "0.4.17rc4.dev40+ga1ddd475",
        "0.4.17rc4.dev39+gd3b5949c",
        "0.4.17rc4.dev38+gc305b460",
        "0.4.17rc4.dev33+g25669802",
        "0.4.17rc4.dev29+g1f010c5f",
        "0.4.17rc4.dev28+g06a90c74",
        "0.4.17rc4.dev27+gba20158a",
        "0.4.17rc4.dev23+geb26c560",
        "0.4.17rc4.dev22+gf41b51f0",
        "0.4.17rc4.dev20+gd64b351b",
        "0.4.17rc4.dev17+g28e203c2",
        "0.4.17rc4.dev12+g3bf872cb",
        "0.4.17rc4.dev11+g4103d7e5",
        "0.4.17rc4.dev5+g679331ff",
        "0.4.17rc3",
        "0.4.17rc3.dev2+g8bb7e78f",
        "0.4.17rc3.dev1+g4f200dfa",
        "0.4.17rc2",
        "0.4.17rc1",
        "0.4.17rc0",
        "0.4.16",
        "0.4.16rc7",
        "0.4.16rc6",
        "0.4.16rc5",
        "0.4.16rc4",
        "0.4.16rc3",
        "0.4.16rc2",
        "0.4.16rc2.dev305+ga26ac7b8",
        "0.4.16rc2.dev301+gef868fdf",
        "0.4.16rc2.dev300+gbeaa98ef",
        "0.4.16rc2.dev293+g7c7ada86",
        "0.4.16rc2.dev289+gd90a39b8",
        "0.4.16rc2.dev287+g582ef33c",
        "0.4.16rc2.dev286+gfe4dfb7b",
        "0.4.16rc2.dev284+ge65e2ace",
        "0.4.16rc2.dev273+g27a88db5",
        "0.4.16rc2.dev271+ga0a197f0",
        "0.4.16rc2.dev266+g346be6bc",
        "0.4.16rc2.dev260+g74fd219b",
        "0.4.16rc2.dev259+g3c818796",
        "0.4.16rc2.dev258+g32954dea",
        "0.4.16rc2.dev253+g297dfc3d",
        "0.4.16rc2.dev252+gf6bdd623",
        "0.4.16rc2.dev249+g2418a86d",
        "0.4.16rc2.dev247+g29cd6fee",
        "0.4.16rc2.dev245+g392c4bd9",
        "0.4.16rc2.dev239+gc5f173b6",
        "0.4.16rc2.dev233+g457dca40",
        "0.4.16rc2.dev228+g8c302ed7",
        "0.4.16rc2.dev227+ge294c1ed",
        "0.4.16rc2.dev225",
        "0.4.16rc2.dev219",
        "0.4.16rc2.dev217",
        "0.4.16rc2.dev215",
        "0.4.16rc2.dev213",
        "0.4.16rc2.dev212",
        "0.4.16rc2.dev209",
        "0.4.16rc2.dev208",
        "0.4.16rc2.dev204",
        "0.4.16rc2.dev198",
        "0.4.16rc2.dev196",
        "0.4.16rc2.dev194",
        "0.4.16rc2.dev191",
        "0.4.16rc2.dev188",
        "0.4.16rc2.dev184",
        "0.4.16rc2.dev183",
        "0.4.16rc2.dev181",
        "0.4.16rc2.dev180",
        "0.4.16rc2.dev178",
        "0.4.16rc2.dev175",
        "0.4.16rc2.dev172",
        "0.4.16rc2.dev170",
        "0.4.16rc2.dev165",
        "0.4.16rc2.dev162",
        "0.4.16rc2.dev161",
        "0.4.16rc2.dev160",
        "0.4.16rc2.dev158",
        "0.4.16rc2.dev157",
        "0.4.16rc2.dev154",
        "0.4.16rc2.dev153",
        "0.4.16rc2.dev150",
        "0.4.16rc2.dev149",
        "0.4.16rc2.dev143",
        "0.4.16rc2.dev142",
        "0.4.16rc2.dev139",
        "0.4.16rc2.dev137",
        "0.4.16rc2.dev134",
        "0.4.16rc2.dev131",
        "0.4.16rc2.dev126",
        "0.4.16rc2.dev122",
        "0.4.16rc2.dev121",
        "0.4.16rc2.dev119",
        "0.4.16rc2.dev118",
        "0.4.16rc2.dev110",
        "0.4.16rc2.dev107",
        "0.4.16rc2.dev104",
        "0.4.16rc2.dev93",
        "0.4.16rc2.dev81",
        "0.4.16rc2.dev75",
        "0.4.16rc2.dev72",
        "0.4.16rc2.dev70",
        "0.4.16rc2.dev68",
        "0.4.16rc2.dev67",
        "0.4.16rc2.dev66",
        "0.4.16rc2.dev61",
        "0.4.16rc2.dev56",
        "0.4.16rc2.dev47",
        "0.4.16rc2.dev46",
        "0.4.16rc2.dev42",
        "0.4.16rc2.dev40",
        "0.4.16rc2.dev38",
        "0.4.16rc2.dev34",
        "0.4.16rc2.dev33",
        "0.4.16rc2.dev31",
        "0.4.16rc2.dev29",
        "0.4.16rc2.dev28",
        "0.4.16rc2.dev26",
        "0.4.16rc2.dev25",
        "0.4.16rc2.dev23",
        "0.4.16rc2.dev14",
        "0.4.16rc2.dev12",
        "0.4.16rc2.dev11",
        "0.4.16rc2.dev1",
        "0.4.16rc1",
        "0.4.16rc1.dev2",
        "0.4.16rc0",
        "0.4.16.dev110",
        "0.4.16.dev109",
        "0.4.16.dev104",
        "0.4.16.dev101",
        "0.4.16.dev99",
        "0.4.16.dev94",
        "0.4.16.dev87",
        "0.4.16.dev85",
        "0.4.16.dev83",
        "0.4.16.dev79",
        "0.4.16.dev77",
        "0.4.16.dev75",
        "0.4.16.dev69",
        "0.4.16.dev68",
        "0.4.16.dev67",
        "0.4.16.dev66",
        "0.4.16.dev62",
        "0.4.16.dev59",
        "0.4.16.dev58",
        "0.4.16.dev57",
        "0.4.16.dev55",
        "0.4.16.dev54",
        "0.4.16.dev53",
        "0.4.16.dev51",
        "0.4.16.dev48",
        "0.4.16.dev43",
        "0.4.16.dev36",
        "0.4.16.dev33",
        "0.4.16.dev31",
        "0.4.16.dev30",
        "0.4.16.dev28",
        "0.4.16.dev26",
        "0.4.16.dev23",
        "0.4.16.dev19",
        "0.4.16.dev15",
        "0.4.16.dev11",
        "0.4.16.dev8",
        "0.4.16.dev3",
        "0.4.15",
        "0.4.15rc3",
        "0.4.15rc3.dev4",
        "0.4.15rc2.dev118",
        "0.4.15rc2.dev10",
        "0.4.15rc2.dev8",
        "0.4.15rc2.dev7",
        "0.4.15rc1.dev118",
        "0.4.15rc1.dev116",
        "0.4.15.dev159",
        "0.4.15.dev158",
        "0.4.15.dev157",
        "0.4.15.dev151",
        "0.4.15.dev140",
        "0.4.15.dev135",
        "0.4.14",
        "0.4.14.dev109",
        "0.4.14.dev107",
        "0.4.14.dev105",
        "0.4.14.dev104",
        "0.4.14.dev102",
        "0.4.14.dev99",
        "0.4.14.dev96",
        "0.4.14.dev95",
        "0.4.14.dev92",
        "0.4.14.dev86",
        "0.4.14.dev84",
        "0.4.14.dev76",
        "0.4.14.dev73",
        "0.4.13",
        "0.4.13rc4.dev71",
        "0.4.13rc4.dev70",
        "0.4.13rc4.dev69",
        "0.4.13rc4.dev67",
        "0.4.13.dev241",
        "0.4.13.dev239",
        "0.4.13.dev237",
        "0.4.13.dev236",
        "0.4.13.dev224",
        "0.4.13.dev223",
        "0.4.13.dev221",
        "0.4.13.dev219",
        "0.4.13.dev218",
        "0.4.13.dev215",
        "0.4.13.dev203",
        "0.4.13.dev202",
        "0.4.13.dev199",
        "0.4.13.dev195",
        "0.4.13.dev194",
        "0.4.13.dev193",
        "0.4.13.dev191",
        "0.4.13.dev190",
        "0.4.13.dev186",
        "0.4.13.dev172",
        "0.4.13.dev150",
        "0.4.13.dev140",
        "0.4.13.dev139",
        "0.4.13.dev138",
        "0.4.13.dev137",
        "0.4.13.dev118",
        "0.4.13.dev104",
        "0.4.13.dev103",
        "0.4.13.dev102",
        "0.4.13.dev101",
        "0.4.13.dev100",
        "0.4.13.dev90",
        "0.4.13.dev77",
        "0.4.13.dev76",
        "0.4.13.dev75",
        "0.4.13.dev74",
        "0.4.13.dev73",
        "0.4.13.dev72",
        "0.4.13.dev23",
        "0.4.12",
        "0.4.11",
        "0.4.10",
        "0.4.9",
        "0.4.8",
        "0.4.7",
        "0.4.6",
        "0.4.5",
        "0.4.4",
        "0.4.3",
        "0.4.2",
        "0.4.0",
        "0.3.8",
        "0.3.7",
        "0.3.6",
        "0.3.4",
        "0.3.3",
        "0.3.2",
        "0.3.1",
        "0.3.0",
        "0.2.12"
    ],
    "current_version": "0.4.15",
    "latest_version": "0.4.17",
    "previous_version": "0.4.15rc3",
    "found_versions": [
        "0.4.16",
        "0.4.17"
    ],
    "update": true,
    "installed": true,
    "status": {}
}
```

This will check for any updates available for the package named `napari`
including development version taking into account that the current version
is `0.4.15`. We are looking for available version on the `napari` channel.

### Update

TODO

```bash
constructor-manager update "napari=0.4.15=*pyside*" -c conda-forge --plugins-url https://api.napari-hub.org/plugins
constructor-manager update "napari=0.4.16=*pyside*" -c conda-forge --plugins-url https://api.napari-hub.org/plugins
```

```bash
mamba create -n napari-0.4.15 -c conda-forge "napari=0.4.15=*pyside*" affinder blik -y
mamba create -n napari-0.4.16 -c conda-forge "napari=0.4.16=*pyside*" -y
```

```python
{'base_url': 'https://conda.anaconda.org/conda-forge', 'build_number': 0, 'build_string': 'pyhd8ed1ab_0', 'channel': 'conda-forge', 'dist_name': 'zipp-3.10.0-pyhd8ed1ab_0', 'name': 'zipp', 'platform': 'noarch', 'version': '3.10.0'}, {'base_url': 'https://conda.anaconda.org/conda-forge', 'build_number': 0, 'build_string': 'hac89ed1_0', 'channel': 'conda-forge', 'dist_name': 'zlib-ng-2.0.6-hac89ed1_0', 'name': 'zlib-ng', 'platform': 'osx-64', 'version': '2.0.6'}, {'base_url': 'https://conda.anaconda.org/conda-forge', 'build_number': 4, 'build_string': 'hfa58983_4', 'channel': 'conda-forge', 'dist_name': 'zstd-1.5.2-hfa58983_4', 'name': 'zstd', 'platform': 'osx-64', 'version': '1.5.2'}
```

### Update and clean (and maybe launch?)

TODO

### Lock

Create a lock file using `conda-lock` and store it in `<BUNDLE-PREFIX>/var/constructor-manager/state`.

These lock files are usable by the `rollback` command.

```bash
constructor-manager lock "napari=0.4.16=*pyside*" -c conda-forge
```

### Restore

This command will install a specified on a fresh environment, deleting the old environment first.

```bash
constructor-manager restore "napari=0.4.16=*pyside*" -c conda-forge
```
