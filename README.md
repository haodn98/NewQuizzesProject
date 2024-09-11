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
![image](https://github.com/user-attachments/assets/88bfe3b4-6365-416f-aaff-c59d928af84b)
![image](https://github.com/user-attachments/assets/dcf0070e-c733-476f-b270-4c884899a1f4)
![image](https://github.com/user-attachments/assets/7f6959f2-953a-4709-970b-d7e79fed32bc)


