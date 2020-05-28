TELEGRAM_TOKEN=1079728001:AAElKzs3sokX7puQBnerJRbGyJ0acjETXL0
VK_SECRET=MBuEG6G4d7SNoQp3xIeU
PORT=8080
BERT_URL=https://bert-service-b7e3qu3u4a-ew.a.run.app
GPT2_URL=http://34.71.136.92
MONGO_URL="mongodb+srv://user:sYI36czIcR3EdQsN@communicabio-aishutin-nwzyf.gcp.mongodb.net/test?retryWrites=true&w=majority"

python3 ./main.py \
    --telegram-token $TELEGRAM_TOKEN \
    --vk-secret $VK_SECRET \
    --port $PORT \
    --metric-api $BERT_URL \
    --dialog-api $GPT2_URL \
    --mongodb $MONGO_URL
