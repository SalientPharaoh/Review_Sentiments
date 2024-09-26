import os
from io import BytesIO
from typing import List, Dict, Tuple
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import asyncio
from groq import AsyncGroq
import logging
import tiktoken
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setting up the logger to log messages and find errors in case of any issues
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the FastAPI application and the GROQ client
app = FastAPI(title="Sentiment Analysis API")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = AsyncGroq(api_key=GROQ_API_KEY)

# Adding CORS middleware. This will be set to the hosting origins to ensure security the application. (For simplicity it is set to allow all origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Defining the response structure for the API
class SentimentResponse(BaseModel):
    positive: float
    negative: float
    neutral: float

# Defining the request structure for the API
class ReviewBatch(BaseModel):
    reviews: List[str]

# Function to calculate the number of tokens in a text string
# This is required to ensure that minimum number of requests are made to the LLM. This saves the number of requests and resources. This helps in undersanding how many chunks should the input reviews be divided into.
def num_tokens_from_string(string: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    num_tokens = len(encoding.encode(string))
    return num_tokens

# Function to analyze the sentiments of a batch of reviews
async def analyze_sentiments_batch(reviews: List[str], max_retries: int = 5) -> List[Tuple[str, float]]:
    MAX_TOKENS = 32768 # Mistral 7B token limit
    RESERVE_TOKENS = 2000 # Reserving for prompt and response

    # Function to chunk the reviews into smaller chunks to ensure that the input does not exceed the token limit of the model (context window)
    def chunk_reviews(reviews: List[str]) -> List[List[str]]:
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for review in reviews:
            review_tokens = num_tokens_from_string(review)
            if current_tokens + review_tokens > MAX_TOKENS - RESERVE_TOKENS:
                chunks.append(current_chunk)
                current_chunk = [review]
                current_tokens = review_tokens
            else:
                current_chunk.append(review)
                current_tokens += review_tokens
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks

    # Function to process a chunk of reviews
    async def process_chunk(chunk: List[str]) -> List[Tuple[str, float]]:

        # Formatting the reviews in the format {count}. {review} to be used as a prompt for the model
        chunk_text = "\n".join(f"{i+1}. {review}" for i, review in enumerate(chunk))

        # Defining the full prompt for the model
        full_prompt = f"""Analyze the sentiment of each of the following reviews and classify each as positive, negative, or neutral. Also provide a confidence score between 0 and 1 for each. Return the results in the format: 'classification,score' for each review, separated by newlines.

Reviews:{chunk_text}

Results:"""

        # Starting the processing of the chunk
        for attempt in range(max_retries):
            try:
                response = await groq_client.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": full_prompt,
                        }
                    ],
                    model="mixtral-8x7b-32768",
                    temperature=0,
                    max_tokens=2000,
                )
                results = response.choices[0].message.content.strip().split('\n')
                results = [r.split(',') for r in results]
                results = [(sentiment.strip().split()[1].lower(), float(score.strip())) for sentiment, score in results]
                return results
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")

                # Handling the rate limit error by waiting for a certain time before retrying
                if "rate limit" in str(e).lower():
                    wait_time = 2 ** attempt # Exponential Wait
                    logger.info(f"Rate limit reached. Waiting for {wait_time} seconds before retrying.")
                    await asyncio.sleep(wait_time)
                elif attempt == max_retries - 1:
                    logger.error(f"All attempts failed for chunk processing.")
                    return [] # Return empty list in case of failure
                    
        logger.error(f"All attempts failed for chunk processing.")
        return [] 

    # Processing the reviews in chunks
    chunks = chunk_reviews(reviews) # chunk creation
    results = []
    for chunk in chunks:
        chunk_results = await process_chunk(chunk) # processing each chunk
        results.extend(chunk_results) # appending the results
    
    return results

# Function to process the reviews and return the sentiment analysis results
async def process_reviews(reviews: List[str]) -> Dict[str, any]:
    results = await analyze_sentiments_batch(reviews)

    # moving ahead with only valid reviews which have been processed by the LLM
    valid_results = [(review, sentiment, score) for review, (sentiment, score) in zip(reviews, results) if sentiment]
    
    if not valid_results:
        return {
            "sentiment_counts": {"positive": 0, "negative": 0, "neutral": 0},
            "top_comments": {"positive": [], "negative": [], "neutral": []}
        }
    
    reviews, sentiments, scores = zip(*valid_results)
    
    # counts of the sentiments
    sentiment_counts = {
        "positive": sentiments.count("positive"),
        "negative": sentiments.count("negative"),
        "neutral": sentiments.count("neutral")
    }
    
    return {
        "sentiment_counts": sentiment_counts,
    }

# API endpoint to analyze the sentiment of a file (File Upload)
@app.post("/analyze_file", response_model=SentimentResponse)
async def analyze_file(file: UploadFile = File(...)):
    if not file.filename.endswith(('.xlsx', '.csv')):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload XLSX or CSV file")
    
    # Reading the file content and processing the reviews
    try:
        content = await file.read()
        if file.filename.endswith('.xlsx'):
            df = pd.read_excel(BytesIO(content), header=None)
        elif file.filename.endswith('.csv'):
            df = pd.read_csv(BytesIO(content), header=None)
        else:
            raise HTTPException(status_code=400, detail="Invalid file format. Please upload XLSX or CSV file")
        
        # Handling the case where the first row is the header
        if df.iloc[0, 0].lower() == 'review':
            df = df.iloc[1:]
        
        # refactoring the dataframe to ensure easier processing
        df.columns = ['review'] + list(df.columns[1:])
        df = df.reset_index(drop=True)

        reviews = df['review'].astype(str).tolist()
        results = await process_reviews(reviews)
        
        # Calculating the sentiment scores
        total = sum(results["sentiment_counts"].values())
        total_count = {
            "positive": results["sentiment_counts"]["positive"],
            "negative": results["sentiment_counts"]["negative"],
            "neutral": results["sentiment_counts"]["neutral"]
        }
        sentiment_scores = {
            key: round(value / total, 2) for key, value in results["sentiment_counts"].items()
        }
        
        response = {
            **sentiment_scores
        }

        return JSONResponse(content=response)
    
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)