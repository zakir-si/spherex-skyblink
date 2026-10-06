install:
	python -m pip install -r backend/requirements.txt

install-science:
	python -m pip install -r backend/requirements-science.txt

test:
	pytest -q

run:
	uvicorn backend.main:app --reload
