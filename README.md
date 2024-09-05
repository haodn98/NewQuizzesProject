Getting Started

Install dependencies:

    $ pip install -r requirements.txt

Start FastAPI process:

    $ uvicorn app.main:app --reload    

Open local API docs http://localhost:8000/docs#/

docker-compose run 

    docker-compose up -d --build

Alembic migration create:

    alembic revision --autogenerate -m "some migration"

Migrations use: 
    
    alembic upgrade head

Migrations downgrade
    
    alembic downgrade -1

