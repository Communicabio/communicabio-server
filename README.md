# communicabio-server

## Usage

```shell
./main.py \
    --telegram-token TELEGRAM_TOKEN \
    --vk-secret VK_SECRET \
    --port 8080 \
    --metric-api BERT_API \
    --dialog-api DIALOG_API \
    --mongodb MONGO_URL
```


## Deployment to GCP

```shell
PROJECT_ID=stunning-hull-187717
IMAGE=communicabio_server

gcloud builds submit --tag gcr.io/$PROJECT_ID/$IMAGE
```

## Setting up webhooks...

```shell
curl -X POST \
     --header "Content-Type: application/json" \
     -d '{"url": "https://communicabio-server-b7e3qu3u4a-uc.a.run.app/webhooks/telegram/1079728001:AAElKzs3sokX7puQBnerJRbGyJ0acjETXL0"}' \
     'https://api.telegram.org/bot1079728001:AAElKzs3sokX7puQBnerJRbGyJ0acjETXL0/setWebhook'
```
