FROM python:3.12-slim

# .pyc yozilmaydi, loglar buferlanmasdan darhol chiqadi (docker compose logs).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Avval faqat requirements: kod o'zgarganda kutubxonalar qatlami keshdan olinadi.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN chmod +x entrypoint.sh

# Ilova root bo'lmagan foydalanuvchi nomidan ishlaydi; staticfiles'ga yozish huquqi kerak.
RUN useradd --create-home --uid 1000 app && mkdir -p staticfiles && chown -R app:app /app
USER app

EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]
