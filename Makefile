include make-compose.mk

install:
	poetry install

build:
	poetry build

lint:
	poetry run flake8 paymaster

package-install:
	python3 -m pip install --user dist/*.whl

test:
	poetry run pytest -v

test-coverage:
	poetry run pytest --cov=paymaster --cov-report xml

pre-commit:
	poetry run pre-commit run --all-files

mypy-check:
	poetry run mypy --namespace-packages tests paymaster

complexity-check:
	poetry run flake8 --max-cognitive-complexity=5 $(file)

start-app:
	poetry run uvicorn --host=0.0.0.0:5000 paymaster.main:app

.PHONY: test paymaster install lint build
