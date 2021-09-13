# Build, package, test, and clean
PROJECT=nene

install:
	pip install --no-deps -e .

test:
	pytest $(PYTEST_ARGS) $(PROJECT)

format:
	@echo "Formatting import order with isort..."
	@echo
	@isort .
	@echo
	@echo "Formatting code with black..."
	@echo
	@black .
	@echo
	@echo "Done!"

check:
	@echo "Checking black code formatting..."
	@echo
	@black --check .
	@echo
	@echo "Linting with flake8..."
	@echo
	@flake8 .
	@echo
	@echo "Done!"

clean:
	find . -name "*.pyc" -exec rm -v {} \;
	find . -name "*.orig" -exec rm -v {} \;
	find . -name ".coverage.*" -exec rm -v {} \;
	rm -rvf build dist MANIFEST *.egg-info __pycache__ .coverage .cache .pytest_cache $(PROJECT)/_version.py
