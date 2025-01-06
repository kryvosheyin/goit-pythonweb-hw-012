Project must contain .env file with params

```
POSTGRES_DB=postgres
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_PORT=5432
POSTGRES_HOST=localhost

REDIS_HOST=redis
REDIS_PORT=6379

DB_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}
JWT_SECRET=secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_SECONDS=3600

MAIL_USERNAME=s
MAIL_PASSWORD=
MAIL_FROM=
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
MAIL_FROM_NAME=Example email
MAIL_STARTTLS=True
MAIL_SSL_TLS=False
USE_CREDENTIALS=True
VALIDATE_CERTS=True

CLD_NAME=
CLD_API_KEY=
CLD_API_SECRET=
```

To run the application use the following commands

```
poetry install

poetry shell

poetry add sphinx -G dev

make html

docker compose up --build

alembic upgrade head

pytest --cov=src tests/ --cov-report=html


```

Access to swagger : http://localhost:8000/docs

![alt text](image.png)
