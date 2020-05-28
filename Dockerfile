FROM python:3.7-slim

RUN pip install torch==1.5.0+cpu -f https://download.pytorch.org/whl/torch_stable.html
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . /app/
RUN ls /app
RUN python3 -m nltk.downloader 'punkt'

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
RUN echo $PORT
CMD cd /app && ./runme.sh
