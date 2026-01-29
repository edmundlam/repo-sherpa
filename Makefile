.PHONY: install run clean help

install:
	uv sync

run:
	uv run python src/main.py

clean:
	rm -rf .venv

help:
	@echo "Available targets:"
	@echo "  install  - Install dependencies and create virtual environment"
	@echo "  run      - Run the bot"
	@echo "  clean    - Remove virtual environment"
	@echo "  help     - Show this help message"
