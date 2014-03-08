help:
	@echo "make help      - Show this text"
	@echo "make dev-env   - Install all dependencies and development tools"
	@echo "make docs      - Build the html documentation"
	@echo "make view-docs - View the html documentation"

dev-env:
	pip install -r requirements/dev.txt
	pip install -e .

docs:
	make -C docs html

view-docs: docs
	open docs/_build/html/index.html

.PHONY: help dev-env docs view-docs
