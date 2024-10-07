FROM docker.io/adfreiburg/qlever:latest
USER root
RUN apt update
RUN apt install -y python3 python3-pip

RUN pip install qlever

RUN mkdir /input
RUN mkdir /index

VOLUME ["/input", "/index"]
WORKDIR /index
# Run idling
ENTRYPOINT tail -f /dev/null