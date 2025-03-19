FROM python:3.13-slim

WORKDIR /uploader

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod -R 755 /uploader

ENV FLASK_SECRET_KEY=dev-key-change-in-production

EXPOSE 5000

CMD ["python3", "app.py"]