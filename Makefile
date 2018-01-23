
venv: 
	python3 -m venv .venv

dev: venv
	.venv/bin/pip3 install -r requirements-dev.txt
	.venv/bin/pip3 install -r requirements.txt
	.venv/bin/pip3 install -e .

clean:
	rm -rf .venv
		