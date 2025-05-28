# AI-Driven Lead Generator (bang2sampl)

Generates lead URLs via Google Custom Search API and sends them to Bang3 for scraping, with backup to CSV.

## Requirements

- requests
- pymongo
- transformers
- python-dotenv

## Setup

1. Copy `.env.example` to `.env` and set:
   - `GOOGLE_API_KEY`
   - `GOOGLE_CX`
   - (`BANG3_API_URL`, `MONGO_URI` are optional with defaults)

## Build

    docker build -t bang2sampl .

## Run

    docker run --rm --env-file .env bang2sampl