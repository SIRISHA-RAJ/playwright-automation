FROM mcr.microsoft.com/playwright/python:v1.43.0-jammy
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install --with-deps
COPY . .
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
CMD ["pytest", "-v", "-s", "--html=reports/report.html"]
