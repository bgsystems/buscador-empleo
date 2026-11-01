FROM python@sha256:6d43704baacd1bfbe7c295d7f13079d5d8104ed33568873133f8fc69980419df

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DB_PATH=/state/ofertas.db \
    CV_PATH=/profile/cv.txt \
    PREFERENCIAS_PATH=/profile/preferencias.txt

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && mkdir /state \
    && chown 1000:1000 /state
COPY buscador/ buscador/
COPY scraper/ scraper/
COPY test_buscador.py .

USER 1000:1000
RUN python test_buscador.py
CMD ["python", "-m", "buscador"]
