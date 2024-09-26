import os
from io import BytesIO
from typing import List, Dict, Tuple
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pandas as pd
import asyncio
from groq import AsyncGroq
import logging
import tiktoken
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Optimized Sentiment Analysis API")
groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SentimentResponse(BaseModel):
    positive: float
    negative: float
    neutral: float
    top_positive: List[str]
    top_negative: List[str]
    top_neutral: List[str]

class ReviewBatch(BaseModel):
    reviews: List[str]

def num_tokens_from_string(string: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    num_tokens = len(encoding.encode(string))
    return num_tokens

async def analyze_sentiments_batch(reviews: List[str], max_retries: int = 5) -> List[Tuple[str, float]]:
    MAX_TOKENS = 32768 
    RESERVE_TOKENS = 2000

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

    async def process_chunk(chunk: List[str]) -> List[Tuple[str, float]]:
        chunk_text = "\n".join(f"{i+1}. {review}" for i, review in enumerate(chunk))
        full_prompt = f"""Analyze the sentiment of each of the following reviews and classify each as positive, negative, or neutral. Also provide a confidence score between 0 and 1 for each. Return the results in the format: 'classification,score' for each review, separated by newlines.

Reviews:{chunk_text}

Results:"""
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
                if "rate limit" in str(e).lower():
                    wait_time = 2 ** attempt
                    logger.info(f"Rate limit reached. Waiting for {wait_time} seconds before retrying.")
                    await asyncio.sleep(wait_time)
                elif attempt == max_retries - 1:
                    logger.error(f"All attempts failed for chunk processing.")
                    return []
                    
        logger.error(f"All attempts failed for chunk processing.")
        return [] 

    chunks = chunk_reviews(reviews)
    results = []
    for chunk in chunks:
        chunk_results = await process_chunk(chunk)
        results.extend(chunk_results)
    
    return results

async def process_reviews(reviews: List[str]) -> Dict[str, any]:
    results = await analyze_sentiments_batch(reviews)
    valid_results = [(review, sentiment, score) for review, (sentiment, score) in zip(reviews, results) if sentiment]
    
    if not valid_results:
        return {
            "sentiment_counts": {"positive": 0, "negative": 0, "neutral": 0},
            "top_comments": {"positive": [], "negative": [], "neutral": []}
        }
    
    reviews, sentiments, scores = zip(*valid_results)
    
    sentiment_counts = {
        "positive": sentiments.count("positive"),
        "negative": sentiments.count("negative"),
        "neutral": sentiments.count("neutral")
    }
    
    top_comments = {
        "positive": [],
        "negative": [],
        "neutral": []
    }
    
    for review, sentiment, score in valid_results:
        if len(top_comments[sentiment]) < 3:
            top_comments[sentiment].append((review, float(score)))
        elif float(score) > min(s for _, s in top_comments[sentiment]):
            top_comments[sentiment] = sorted(
                top_comments[sentiment] + [(review, float(score))],
                key=lambda x: x[1],
                reverse=True
            )[:3]
    
    return {
        "sentiment_counts": sentiment_counts,
        "top_comments": {k: [r for r, _ in v] for k, v in top_comments.items()}
    }

@app.post("/analyze_file", response_model=SentimentResponse)
async def analyze_file(file: UploadFile = File(...)):
    if not file.filename.endswith(('.xlsx', '.csv')):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload XLSX or CSV file")
    
    try:
        content = await file.read()
        if file.filename.endswith('.xlsx'):
            df = pd.read_excel(BytesIO(content), header=None)
        else:
            df = pd.read_csv(BytesIO(content), header=None)
        
        if df.iloc[0, 0].lower() == 'review':
            df = df.iloc[1:]
        
        df.columns = ['review'] + list(df.columns[1:])
        df = df.reset_index(drop=True)

        reviews = df['review'].astype(str).tolist()
        results = await process_reviews(reviews)
        
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
            **sentiment_scores,
            "top_positive": results["top_comments"]["positive"],
            "top_negative": results["top_comments"]["negative"],
            "top_neutral": results["top_comments"]["neutral"]
        }
        return JSONResponse(content=response)
    
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze_batch", response_model=SentimentResponse)
async def analyze_batch(review_batch: ReviewBatch):
    try:
        reviews = review_batch.reviews
        results = await process_reviews(reviews)
        
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
            **sentiment_scores,
            "top_positive": results["top_comments"]["positive"],
            "top_negative": results["top_comments"]["negative"],
            "top_neutral": results["top_comments"]["neutral"]
        }
        return JSONResponse(content=response)
    
    except Exception as e:
        logger.error(f"Error processing batch: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("./index.html", {"request": request, "title": "Sentiment Analysis API"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)