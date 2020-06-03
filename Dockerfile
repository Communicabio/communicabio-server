FROM python:3.7-slim

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . /app/

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
CMD cd /app && python3 ./main.py \
    --telegram-token $TELEGRAM_TOKEN \
    --vk-secret $VK_SECRET \
    --port $PORT \
    --metric-api $BERT_URL \
    --dialog-api $DIALOG_URL \
    --mongodb $MONGO_URL
