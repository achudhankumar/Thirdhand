FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && python -m playwright install --with-deps --no-shell chromium \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 thirdhand \
    && mkdir -p /app/data && chown thirdhand:thirdhand /app/data
COPY --chown=thirdhand:thirdhand . .
USER thirdhand
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.getenv('PORT','8000')+'/ready',timeout=3)"
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --timeout-graceful-shutdown 260"]
