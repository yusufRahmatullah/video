clean:
	@autopep8 -air .
	@radon cc -s --min C .
	@radon mi --min B .
dep:
	pip install -r requirements.txt
dep-test:
	pip install -r requirements-text.txt
run: clean
	python main.py
