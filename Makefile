.PHONY: help install install-dev data features train evaluate lint format test clean

VENV ?= ~/virtualenvs/alys
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

help:
	@echo "Targets:"
	@echo "  install       Install core package into the venv"
	@echo "  install-dev   Install with dev + notebook + mf extras"
	@echo "  data          Build cleaned dataset from raw Spotify export"
	@echo "  features      Build track/behavioral/genre feature tables"
	@echo "  train         Train recommender models"
	@echo "  evaluate      Evaluate models vs. Spotify + baselines"
	@echo "  lint          Ruff lint"
	@echo "  format        Ruff format"
	@echo "  test          Run pytest"
	@echo "  clean         Remove caches and build artifacts"

install:
	$(PIP) install -e .

install-dev:
	$(PIP) install -e ".[dev,notebook,mf]"

data:
	$(PY) scripts/build_dataset.py

features:
	$(PY) scripts/build_features.py

train:
	$(PY) scripts/train_models.py

evaluate:
	$(PY) scripts/evaluate.py

lint:
	$(VENV)/bin/ruff check .

format:
	$(VENV)/bin/ruff format .

test:
	$(VENV)/bin/pytest

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name '*.egg-info' -prune -exec rm -rf {} +
