WORKDIR = HOMEWORK_BOT
style:
    black -S -l 79 $(WORKDIR)
    isort $(WORKDIR)
    flake8 $(WORKDIR)
