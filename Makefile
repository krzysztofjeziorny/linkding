.PHONY: serve install

serve:
	python manage.py runserver

tasks:
	python manage.py process_tasks

test:
	pytest

format:
	black bookmarks
	black siteroot
	npx prettier bookmarks/frontend --write

install:
	.venv/bin/pip install -r requirements.txt --upgrade