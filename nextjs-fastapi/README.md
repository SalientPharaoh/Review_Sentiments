# Sentiment Analysis API Documentation

## Table of Contents

- [Sentiment Analysis API Documentation](#sentiment-analysis-api-documentation)
  - [Table of Contents](#table-of-contents)
  - [1. Introduction](#1-introduction)
  - [2. Setup and Installation](#2-setup-and-installation)
    - [Prerequisites](#prerequisites)
    - [Installation Steps](#installation-steps)
  - [3. API Endpoints](#3-api-endpoints)
    - [POST /analyze\_file](#post-analyze_file)
    - [POST /analyze\_batch](#post-analyze_batch)
  - [4. Code Structure](#4-code-structure)
  - [5. Key Components](#5-key-components)
    - [Environment Variables](#environment-variables)
    - [FastAPI Application](#fastapi-application)
    - [Groq Client](#groq-client)
    - [Pydantic Models](#pydantic-models)
  - [6. Sentiment Analysis Process](#6-sentiment-analysis-process)
    - [Key Functions](#key-functions)
      - [analyze\_sentiments\_batch](#analyze_sentiments_batch)
      - [process\_chunk](#process_chunk)
      - [process\_reviews](#process_reviews)
  - [7. Error Handling and Logging](#7-error-handling-and-logging)
  - [8. Performance Considerations](#8-performance-considerations)
  - [9. Security Considerations](#9-security-considerations)
  - [10. Deployment](#10-deployment)
  - [11. Limitations and Future Improvements](#11-limitations-and-future-improvements)
  - [12. Troubleshooting](#12-troubleshooting)
  - [13. API Reference](#13-api-reference)
    - [SentimentResponse Model](#sentimentresponse-model)
    - [ReviewBatch Model](#reviewbatch-model)
  - [14. Running FrontEnd](#14-running-frontend)

## 1. Introduction

This Sentiment Analysis API is a FastAPI-based application that leverages the Groq API to analyze the sentiment of text reviews. The API can process reviews from uploaded CSV or XLSX files or as a batch of text inputs. It categorizes sentiments as positive, negative, or neutral, and provides sentiment scores along with top comments for each category.

## 2. Setup and Installation

### Prerequisites

- Python 3.7+
- FastAPI
- Pandas
- Groq API access
- Other dependencies (see `requirements.txt`)

### Installation Steps

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the project root with the following content:

   ```bash
   GROQ_API_KEY=your_groq_api_key_here
   ```

## 3. API Endpoints

### POST /analyze_file

Analyzes sentiments from a file upload (CSV or XLSX).

**Request:**

- Method: POST
- Content-Type: multipart/form-data
- Body: File upload (CSV or XLSX)

**Response:**

```json
{
  "positive": 0.6,
  "negative": 0.3,
  "neutral": 0.1,
  "top_positive": ["Great product!", "Excellent service", "Highly recommended"],
  "top_negative": ["Poor quality", "Terrible experience", "Would not buy again"],
  "top_neutral": ["Average", "It's okay", "Neither good nor bad"]
}
```

### POST /analyze_batch

Analyzes sentiments from a batch of text reviews.

**Request:**

- Method: POST
- Content-Type: application/json
- Body:

  ```json
  {
    "reviews": ["Great product!", "Poor quality", "Average experience"]
  }
  ```

**Response:**
Same format as /analyze_file

## 4. Code Structure

The application is structured as follows:

- **Imports and Setup**: Initial imports, environment variable loading, and logger setup.
- **FastAPI App Initialization**: Setting up the FastAPI application with CORS middleware.
- **Model Definitions**: Pydantic models for request and response structures.
- **Utility Functions**: Token counting and review chunking.
- **Core Logic**: Functions for sentiment analysis using the Groq API.
- **API Endpoints**: File upload and batch processing endpoints.

## 5. Key Components

### Environment Variables

The application uses `python-dotenv` to load environment variables:

```python
from dotenv import load_dotenv
load_dotenv()
```

### FastAPI Application

The main FastAPI application is initialized with CORS middleware:

```python
app = FastAPI(title="Optimized Sentiment Analysis API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)
```

### Groq Client

The Groq client is initialized using the API key from environment variables:

```python
groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
```

### Pydantic Models

Two main Pydantic models are defined:

1. `SentimentResponse`: Defines the structure of the API response.
2. `ReviewBatch`: Defines the structure for batch review requests.

## 6. Sentiment Analysis Process

The sentiment analysis process involves several steps:

1. **Tokenization**: The `num_tokens_from_string` function calculates the number of tokens in a given string.

2. **Chunking**: Large batches of reviews are split into smaller chunks to fit within the model's token limit.

3. **Sentiment Analysis**: Each chunk is processed using the Groq API with a specific prompt structure.

4. **Result Aggregation**: Results from all chunks are combined, and top comments are extracted.

### Key Functions

#### analyze_sentiments_batch

This function orchestrates the entire sentiment analysis process:

```python
async def analyze_sentiments_batch(reviews: List[str], max_retries: int = 5) -> List[Tuple[str, float]]:
    # Implementation details...
```

#### process_chunk

This function sends a chunk of reviews to the Groq API and processes the response:

```python
async def process_chunk(chunk: List[str]) -> List[Tuple[str, float]]:
    # Implementation details...
```

#### process_reviews

This function processes the results and prepares the final response:

```python
async def process_reviews(reviews: List[str]) -> Dict[str, any]:
    # Implementation details...
```

## 7. Error Handling and Logging

The application uses Python's `logging` module for error tracking and debugging:

```python
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

Errors are logged at various points in the code, especially during API calls and file processing.

## 8. Performance Considerations

- **Chunking**: Reviews are processed in chunks to optimize API usage and handle large datasets.
- **Asynchronous Processing**: The application uses `asyncio` for non-blocking I/O operations.
- **Retry Mechanism**: A retry mechanism with exponential backoff is implemented for API call failures.

## 9. Security Considerations

- **CORS**: Currently set to allow all origins (`"*"`). In production, this should be restricted.
- **API Key**: Stored as an environment variable to prevent exposure in the code.
- **Input Validation**: FastAPI provides automatic request validation based on the Pydantic models.

## 10. Deployment

To run the application:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

For production deployment, consider using a process manager like Gunicorn with Uvicorn workers.

## 11. Limitations and Future Improvements

- Implement more granular error handling and user feedback.
- Add caching mechanism for repeated analyses.
- Implement user authentication and rate limiting.
- Expand sentiment analysis to include more detailed categories or emotion detection.

## 12. Troubleshooting

Common issues and their solutions:

- **API Key Issues**: Ensure the `GROQ_API_KEY` is correctly set in the `.env` file.
- **File Upload Errors**: Check file format and size limitations.
- **Rate Limiting**: The application implements retries, but persistent rate limit errors may require reducing request frequency.

## 13. API Reference

### SentimentResponse Model

```python
class SentimentResponse(BaseModel):
    positive: float
    negative: float
    neutral: float
    top_positive: List[str]
    top_negative: List[str]
    top_neutral: List[str]
```

### ReviewBatch Model

```python
class ReviewBatch(BaseModel):
    reviews: List[str]
```

## 14. Running FrontEnd

```bash
cd nextjs-fastapi
```


```bash
npm install
```

```bash
npm run dev
```
