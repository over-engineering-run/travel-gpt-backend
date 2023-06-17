FROM --platform=linux/amd64 python:3.11.3-slim-buster
LABEL maintainer="tainvecs@gmail.com"


# env
ENV BACKEND_ROOT="/backend"
ENV DEBIAN_FRONTEND=noninteractive
ENV PIPENV_VENV_IN_PROJECT=1


# init apt for psql and gcc
RUN apt-get update && \
    apt-get install --no-install-recommends -y libpq-dev gcc python-dev


# init backend api
WORKDIR $BACKEND_ROOT
ADD . $BACKEND_ROOT


# install requirements
RUN python -m pip install --upgrade pip
RUN python -m pip install pipenv
RUN python -m pipenv install


# expose port for backend app
expose 5000

ENTRYPOINT ["python", "-m", "pipenv", "run", "python", "$BACKEND_ROOT/src/servers/server_runner.py"]
