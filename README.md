# communicabio-server

The API server which process all inbound requests to Communicabio. It also runs other services if necessary.

## Usage

```shell
uvicorn app:app \
    --telegram-token $TELEGRAM_TOKEN \
    --port $PORT \
    --mongodb $MONGO_URL
    --metric-api $BERT_URL \
    --dialog-api $DIALOG_URL \
```

## Deployment to GCP

```shell
PROJECT_ID=communicabio
IMAGE=api-server

gcloud builds submit --tag gcr.io/$PROJECT_ID/$IMAGE
```

### Setting up Telegram webhooks...

```shell
TOKEN=...
curl -X POST \
     --header "Content-Type: application/json" \
     -d '{"url": "https://communicabio-server-b7e3qu3u4a-uc.a.run.app/webhooks/telegram/$TOKEN"}' \
     'https://api.telegram.org/bot$TOKEN/setWebhook'
```

## Github Actions

See https://github.com/GoogleCloudPlatform/github-actions/tree/master/example-workflows/cloud-run .
