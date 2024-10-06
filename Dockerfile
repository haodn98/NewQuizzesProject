FROM python:3.11

ENV DOCKER_ENV=1

RUN mkdir /quizzesproject
WORKDIR /quizzesproject

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .

RUN chmod a+x docker/*.sh

ENTRYPOINT ["docker/app.sh"]