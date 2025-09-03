FROM python:3.10

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

# Instalar dependências necessárias
RUN apt-get update && \
    apt-get install -y ca-certificates curl jq && \
    update-ca-certificates

# Baixar e instalar o Ngrok
RUN curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null && \
    echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | tee /etc/apt/sources.list.d/ngrok.list && \
    apt update && apt install -y ngrok

WORKDIR /app
COPY . .

