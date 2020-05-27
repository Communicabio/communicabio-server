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

PROJECT_ID=stunning-hull-187717
IMAGE=communicabio_server
VERSION=1

gcloud builds submit --tag gcr.io/$PROJECT_ID/$IMAGE:$VERSION
