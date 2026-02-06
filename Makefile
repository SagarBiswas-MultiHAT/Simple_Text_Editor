PYTHON ?= python

.PHONY: install lint format test mypy pyinstaller

install:
	$(PYTHON) -m pip install -e .[dev]

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m isort --check-only .
	$(PYTHON) -m black --check .

format:
	$(PYTHON) -m isort .
	$(PYTHON) -m black .

test:
	$(PYTHON) -m pytest

mypy:
	$(PYTHON) -m mypy tkeditor

pyinstaller:
	$(PYTHON) -m PyInstaller tkeditor.spec
