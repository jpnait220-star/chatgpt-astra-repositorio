"""Install DuckCapture dependencies using the official Python interpreter."""

from scripts.bootstrap import main

if __name__ == "__main__":
    raise SystemExit(main(install_only=True))
