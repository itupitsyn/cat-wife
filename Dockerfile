FROM python:latest

ADD bot.py .

RUN pip install requests python-dotenv python-telegram-bot

CMD ["python", "./bot.py"]

