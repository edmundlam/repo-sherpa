.PHONY: install run test clean help

install:
	uv sync

run:
	uv run python src/main.py

test:
	uv run pytest

clean:
	rm -rf .venv

help:
	@echo "Available targets:"
	@echo "  install  - Install dependencies and create virtual environment"
	@echo "  run      - Run the bot"
	@echo "  test     - Run all tests"
	@echo "  clean    - Remove virtual environment"
	@echo "  help     - Show this help message"
