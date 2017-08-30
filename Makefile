.PHONY: docs

# test commands and arguments
tcommand = PYTHONPATH=. py.test -x
tmessy = -svv
targs = --cov-report term-missing --cov emailx

pip:
	pip install --upgrade pip
	pip install --upgrade -r requirements.txt

tox:
	tox tests

test:
	$(tcommand) $(targs) tests

stest:
	$(tcommand) $(tmessy) $(targs) tests

clean:
	git clean -fXd
	find . -name \*.pyc -delete
	rm -rf .cache

lint:
	flake8 emailx
	flake8 tests

tidy: clean lint

all: pip clean lint tox

publish:
	python setup.py sdist bdist_wheel --universal
	twine upload dist/*
