"""Command-line entry point for the Bike Alert project.

This file is intentionally small. In beginner-friendly projects, it is useful
to keep the entry point focused on starting the application and delegate the
real work to modules inside the package.
"""

from bike_alert.app import run


if __name__ == "__main__":
    # This guard means "only run the app when this file is executed directly".
    # It prevents the app from starting by accident when another file imports
    # something from main.py.
    run()
