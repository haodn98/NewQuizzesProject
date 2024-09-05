FROM python:3.11

RUN mkdir /quizzesproject

WORKDIR /quizzesproject

COPY ./requirements.txt .

RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN chmod a+x docker/*.sh

RUN alembic upgrade head

WORKDIR src

CMD gunicorn main:app  --bind=0.0.0.0:8000