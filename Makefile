.PHONY: run test check export

run:
	python3 -m fourth_down

test:
	python3 -m unittest discover -s tests -v

check: test
	python3 -m fourth_down --check
	python3 -m compileall -q fourth_down scripts cloud

export:
	python3 -m scripts.export_artifacts
