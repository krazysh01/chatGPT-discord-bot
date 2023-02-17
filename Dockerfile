FROM ubuntu:latest

ENV PYTHONUNBUFFERED 1
RUN apt-get update && apt-get install -y \
  python3.10 \
  python3-pip

RUN pip install cryptography
COPY ./ /DiscordBot
WORKDIR /DiscordBot
RUN pip3 install -r requirements.txt

CMD ["python3", "main.py"]
