FROM python:3.10-slim

WORKDIR /app

RUN pip install --no-cache-dir requests pymongo transformers python-dotenv

COPY bang2sampl.py .

CMD ["python", "bang2sampl.py"]