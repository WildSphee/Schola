# Schola

## Student-Centric Hub for Online Learning Assistant

Schola is a Telegram chatbot designed to assist students in their learning journey. Leveraging OpenAI's language models, Schola allows students to select their subject, take a picture of a question or ask questions directly, and receive detailed answers along with the correct page numbers and references.

## Features

- **Subject Selection**: Choose your subject of interest to get tailored assistance.
- **Interactive Q&A**: Ask questions via text or by sending a picture of the problem.
- **Smart Responses**: Get detailed answers powered by OpenAI's language models.
- **References**: Receive page numbers and references for deeper understanding.

## Installation

### Prerequisites

- **Python 3.10+**
- **Poetry**: Dependency management tool. [Install Poetry](https://python-poetry.org/docs/#installation)

### Clone the Repository

```bash
git clone https://github.com/yourusername/schola.git
cd schola
```

### Set Up the Environment

#### Install Dependencies

Use Poetry to install all dependencies:

```bash
poetry install
```

This command will create a virtual environment and install all required packages specified in `pyproject.toml`.

#### Environment Variables

Create a `.env` file in the root directory to store your environment variables:

```env
OPENAI_API_KEY=your_openai_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

Replace `your_openai_api_key` and `your_telegram_bot_token` with your actual keys.

## Running the Bot

Start the Telegram bot with:

```bash
poetry run python bot.py
```

## Development

### Linting and Type Checking

Ensure your code adheres to the project's style guidelines.

#### Run Linting Scripts

Execute the linting script:

```bash
sh scripts/lint.sh
```

This script utilizes `ruff` for linting and `mypy` for type checking.

### Dependencies

Development dependencies are managed under the `[tool.poetry.group.dev.dependencies]` section in `pyproject.toml`.

## Project Structure

```
schola/
├── bot.py
├── pyproject.toml
├── README.md
├── scripts/
│   └── lint.sh
└── .env
```

## Scripts

- **Linting**: `sh scripts/lint.sh` - Runs code linting and type checks.

## Dependencies

- **Python 3.10+**
- **openai**: ^1.47.1
- **requests**: ^2.32.3
- **python-dotenv**: ^1.0.1
- **python-telegram-bot**: ^21.6

## Contact

Developed by Reagan  
Email: [rrr.chanhiulok@gmail.com](mailto:rrr.chanhiulok@gmail.com)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to the OpenAI community for continual support.
- Inspired by the need for accessible educational resources.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## Troubleshooting

If you encounter issues:

- Ensure all environment variables are correctly set in the `.env` file.
- Verify that dependencies are properly installed with `poetry install`.
- Check that your Python version is 3.10 or higher.

## Future Improvements

- Add unit tests for better reliability.
- Expand subject coverage.
- Implement voice input capabilities.

```

**Happy Learning!**
