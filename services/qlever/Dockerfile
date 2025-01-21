FROM docker.io/adfreiburg/qlever:commit-acb6633
USER root
RUN apt update
RUN apt install -y python3 python3-pip librdf-dev raptor2-utils

RUN mkdir /input
RUN mkdir /index
USER qlever


VOLUME ["/input", "/index"]
WORKDIR /index/skkg
# Run idling
ENTRYPOINT qlever start & tail -f /dev/null