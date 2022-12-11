WORKDIR = HOMEWORK_BOT

style:
	flake8 $(WORKDIR)
	black -S -l 79 $(WORKDIR)
	isort $(WORKDIR)
