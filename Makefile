# Build, package, test, and clean
PROJECT=nene
PYTEST_ARGS=--cov-config=../.coveragerc --cov-report=term-missing --cov=$(PROJECT) --doctest-modules -v --pyargs
BLACK_FILES=setup.py $(PROJECT)
FLAKE8_FILES=setup.py $(PROJECT)


install:
	pip install --no-deps -e .

test:
	pytest $(PYTEST_ARGS) $(PROJECT)

format:
	black $(BLACK_FILES)

check:
	black --check $(BLACK_FILES)
	flake8 $(FLAKE8_FILES)

clean:
	find . -name "*.pyc" -exec rm -v {} \;
	find . -name "*.orig" -exec rm -v {} \;
	find . -name ".coverage.*" -exec rm -v {} \;
	rm -rvf build dist MANIFEST *.egg-info __pycache__ .coverage .cache .pytest_cache $(PROJECT)/_version.py
