# Sentiment Analysis API Documentation

## Table of Contents

1. [Introduction](#introduction)
2. [Setup](#setup)
3. [API Endpoints](#api-endpoints)
4. [Code Structure](#code-structure)
5. [Key Functions](#key-functions)
6. [Error Handling](#error-handling)
7. [Deployment](#deployment)
8. [Limitations and Future Improvements](#limitations-and-future-improvements)

## Introduction

This documentation covers a FastAPI-based Sentiment Analysis API that uses the Groq API to analyze the sentiment of text reviews. The API can process reviews from uploaded CSV or XLSX files and return sentiment scores (positive, negative, neutral) for the analyzed content.

## Setup

### Prerequisites

- Python 3.7+
- FastAPI
- Pandas
- Groq API access
- Other dependencies listed in `requirements.txt`

### Environment Setup

1. Clone the repository
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up a `.env` file in the project root with the following content:

   ```bash
   GROQ_API_KEY=your_groq_api_key_here
   ```

## API Endpoints

### POST /analyze_file

Analyzes sentiments from a file upload.

- **Input**: CSV or XLSX file containing reviews
- **Output**: JSON with sentiment scores

  ```json
  {
    "positive": 0.6,
    "negative": 0.3,
    "neutral": 0.1
  }
  ```

## Code Structure

- **FastAPI App Initialization**: Sets up the FastAPI application with CORS middleware
- **Model Definitions**: Pydantic models for request/response structures
- **Utility Functions**: Token counting, review chunking
- **Core Logic**: Sentiment analysis using Groq API
- **API Endpoint**: File upload and processing

### Key Functions

#### `num_tokens_from_string(string: str) -> int`

Calculates the number of tokens in a given string using the GPT-3.5-turbo tokenizer.

##### `analyze_sentiments_batch(reviews: List[str], max_retries: int = 5) -> List[Tuple[str, float]]`

Processes a batch of reviews, chunking them if necessary, and sends them to the Groq API for sentiment analysis.

#### `process_chunk(chunk: List[str]) -> List[Tuple[str, float]]`

Processes a single chunk of reviews, formatting them into a prompt for the Groq API and parsing the response.

#### `process_reviews(reviews: List[str]) -> Dict[str, any]`

Orchestrates the sentiment analysis process and compiles the results.

## Error Handling

- File format validation
- Groq API rate limiting with exponential backoff
- General exception catching and logging

## Deployment

1. Ensure all environment variables are set
2. Run the FastAPI application:

   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

## Limitations and Future Improvements

1. Currently only supports file uploads, could be extended to accept direct text input
2. Error handling could be more granular
3. Could implement caching to improve performance for repeated analyses
4. Sentiment analysis could be expanded to include more detailed categories or emotion detection

## Security Considerations

1. CORS is currently set to allow all origins (`"*"`). In a production environment, this should be restricted to specific allowed origins.
2. API key is stored in an environment variable, which is a good practice. Ensure the `.env` file is not committed to version control.
3. Input validation could be strengthened to prevent potential injection attacks.

---

For any issues or feature requests, please open an issue in the project repository.
