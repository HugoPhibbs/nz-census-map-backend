FROM python:3.12-slim
WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

RUN pip install gunicorn

CMD ["gunicorn", "-b", "0.0.0.0:8080", "src.app:app"]