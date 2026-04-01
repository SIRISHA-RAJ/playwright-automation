FROM mcr.microsoft.com/playwright/python:v1.43.0-jammy

WORKDIR /app

COPY . .

ENV PYTHONPATH=/app
RUN pip install -r requirements.txt
RUN playwright install

CMD ["pytest", "-v"]