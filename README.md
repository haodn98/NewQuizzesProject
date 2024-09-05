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

Endpoints screen list:
![image](https://github.com/user-attachments/assets/763d2a78-044a-496e-a5e9-30c1060374da)
![image](https://github.com/user-attachments/assets/de457588-f39c-49f0-ad8f-003abbf85ef0)
