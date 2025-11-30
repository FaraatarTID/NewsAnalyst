# Streamlit Interface Walkthrough

I have added a Streamlit interface to the News Analyst app, allowing you to run market analysis and view results in a web browser.

## Changes Made

1.  **Installed Streamlit**: Added `streamlit` to the environment.
2.  **Created `streamlit_app.py`**: A new entry point for the application that provides a web UI.
    - Reuses the existing services (`RSSService`, `BraveSearchService`, `AIService`, etc.).
    - Allows entering a custom topic.
    - Displays analysis results with expandable details.
    - Shows progress and statistics.

## How to Run

To start the Streamlit interface, run the following command in your terminal:

```bash
streamlit run streamlit_app.py
```

This will open a new tab in your default web browser with the application.

## Features

- **Custom Topic**: You can enter a specific topic (e.g., "Tire Recycling in Iran") to override the default configuration.
- **Real-time Progress**: The app shows the status of each step (Collection, Enrichment, Analysis).
- **Interactive Results**: Click on an article to expand and read the AI-generated summary.
- **Priority Highlighting**: High-priority articles are marked with 🔥.
