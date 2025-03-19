# Terminal Retrieval Agent

A system for retrieving and extracting terminal information from various harbor websites.

## Overview

This project consists of several components that work together to search for, process, and extract terminal information for harbors:

- `InternetSearchEngine`: Searches the web for relevant sources about harbor terminals
- `WebsiteProcessor`: Processes website content to extract relevant information
- `TerminalInfoExtractor`: Uses AI to extract structured terminal data from website content
- `TerminalRetrievalAgent`: Coordinates the complete workflow

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Configure Azure OpenAI credentials:
   - Update the `config.json` file with your Azure OpenAI API key and endpoint

## Usage

Run the test script to retrieve information about Hamburg harbor terminals:

```bash
python test.py
```

Or create your own script:

```python
from TerminalRetrievalAgent import TerminalRetrievalAgent

agent = TerminalRetrievalAgent('Your Harbor Name')
results = agent.start()
```

## Features

- Smart content targeting to find relevant sections
- Large content handling with chunking
- Deduplication of terminal information
- Rate limiting handling with exponential backoff