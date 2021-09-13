# Build, package, test, and clean
PROJECT=nene

install:
	pip install --no-deps -e .

test:
	pytest $(PYTEST_ARGS) $(PROJECT)

format:
	isort .
	black .

check:
	black --check .
	flake8 .

clean:
	find . -name "*.pyc" -exec rm -v {} \;
	find . -name "*.orig" -exec rm -v {} \;
	find . -name ".coverage.*" -exec rm -v {} \;
	rm -rvf build dist MANIFEST *.egg-info __pycache__ .coverage .cache .pytest_cache $(PROJECT)/_version.py
