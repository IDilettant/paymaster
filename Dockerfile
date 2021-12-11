FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

WORKDIR /usr/src/app
COPY . /usr/src/app

RUN python -m pip install poetry
RUN make install

EXPOSE 5000
