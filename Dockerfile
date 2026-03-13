FROM python:3.9

WORKDIR /app

COPY . .

RUN pip install bcrypt redis

CMD ["python", "server/server.py"]