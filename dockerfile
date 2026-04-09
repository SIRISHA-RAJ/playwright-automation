FROM mcr.microsoft.com/playwright/python:v1.43.0-jammy
WORKDIR /app
COPY . .
ENV PYTHONPATH=/app
RUN pip install -r requirements.txt
RUN playwright install --with-deps
# Default command to run
CMD ["pytest", "-v", "-s", "--html=reports/report.html"]
# CMD ["pytest", "-v", "--html=reports/report.html"]
