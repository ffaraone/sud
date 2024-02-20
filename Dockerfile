FROM python:3.12
RUN apt update && apt install -y vim
RUN bash -c "$(curl -fsSL https://raw.githubusercontent.com/ohmybash/oh-my-bash/master/tools/install.sh)"
COPY . /app
WORKDIR /app
RUN pip install poetry && poetry install
