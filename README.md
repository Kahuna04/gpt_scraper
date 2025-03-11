# ChatGPT Scraper

A Python tool that automates interactions with ChatGPT. This script logs in to ChatGPT, sends prompts, collects responses, and exports the conversation to CSV format.

## Features

- Automated login to ChatGPT using undetected_chromedriver
- Send custom prompts and follow-up replies
- Extract and format responses
- Export conversation history to CSV with timestamps
- Command-line interface with flexible options
- Headless browser support for server environments
- Comprehensive logging system

## Requirements

- Python 3.7+
- Chrome browser installed

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/kahuna04/gpt-scraper.git
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up your credentials:
   - Create a `.env` file with your OpenAI credentials:
     ```
     EMAIL=your@email.com
     PASSWORD=yourpassword
     ```

## Usage

### Command Line Interface

```bash
python src/gpt_scraper.py --prompt "Your initial prompt" --reply "Your follow-up reply"
```

### Or with interactive prompts

```bash
python src/gpt_scraper.py
```

### Arguments

- `--email`: OpenAI account email (if not in .env file)
- `--password`: OpenAI account password (if not in .env file)
- `--prompt`: Initial prompt to send to ChatGPT
- `--reply`: Follow-up reply to ChatGPT's response
- `--output`: Specify output CSV filename (default: output/chatgpt_conversation.csv)
- `--headless`: Run in headless browser mode (no UI)
- `--debug`: Enable detailed debug logging
- `--wait-timeout`: Timeout in seconds to wait for responses (default: 120)

## Key Components

- **ChatGPTScraper Class**: Handles browser automation, login, and conversation
- **Logging System**: Comprehensive logging to both console and file
- **Undetected ChromeDriver**: Uses an advanced ChromeDriver to bypass detection
- **CSV Export**: Saves conversations with timestamps for reference

## Security Considerations

- Credentials can be stored in .env file (not committed to version control)
- Interactive password entry is masked
- Temporary user data directory is created and cleaned up after use
- Screenshots of login failures are saved for troubleshooting

## Notes

The ChatGPT web interface may change, requiring updates to the CSS selectors or XPaths. The current implementation is based on the interface as of March 2025.