"""
Main updater entrypoints.

This will running on the base conda environment.
"""

from .defaults import DEFAULT_CHANNEL


def check_for_updates(package_name, channel=DEFAULT_CHANNEL):
    """
    """
    pass


def download_artifacts(package_name, channel=DEFAULT_CHANNEL, location=None):
    """
    """
    pass


def update():
    """
    """
    pass


def remove():
    """
    """
    pass


def clean():
    """
    """
    pass


def state():
    """
    """
    pass




"""
def execute(cmd):
    popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line 
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)

# Example
for path in execute(["locate", "a"]):
    print(path, end="")
"""
