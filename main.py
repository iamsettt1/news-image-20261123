"""news-image-20261123 entry program.

The repository ships the finished front page as ``entry.png`` next to this
file. The harness expects the program to deliver that image at
``entry.png`` inside the output directory: the folder named by the
``MAKEFUN_OUTPUT_DIR`` environment variable when it is set, otherwise
``/output``. The delivery is a straight byte copy, so the two grading
runs produce identical output.
"""

import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "entry.png")
IMAGE_NAME = "entry.png"


def output_dir():
    """Return the directory the harness reads the delivered image from."""
    return os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"


def deliver():
    """Copy the bundled entry.png into the output directory.

    Returns the destination path. Raises FileNotFoundError if the bundled
    image is missing, so a broken repository fails loudly instead of
    delivering nothing.
    """
    if not os.path.isfile(SOURCE):
        raise FileNotFoundError(f"bundled image missing: {SOURCE}")
    dest = os.path.join(output_dir(), IMAGE_NAME)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copyfile(SOURCE, dest)
    return dest


if __name__ == "__main__":
    deliver()
