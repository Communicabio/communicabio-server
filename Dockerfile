FROM python:3.7-slim

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . /app/

CMD cd /app && uvicorn app:app
#    --metric-api $BERT_URL \
#    --dialog-api $DIALOG_URL \
