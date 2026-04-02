.PHONY: install lint typecheck test clean

install:
	pip install -e ".[dev]"

lint:
	ruff check src/ tests/
	ruff format --check src/ tests/

typecheck:
	mypy src/image_analysis/

test:
	pytest --cov=src/image_analysis --cov-report=term-missing

clean:
	rm -rf .pytest_cache htmlcov .coverage .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
