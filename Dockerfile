FROM python:3.13.7-alpine3.22

RUN mkdir /data
VOLUME /data
WORKDIR /data

RUN pip install discord.py
