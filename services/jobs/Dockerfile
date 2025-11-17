FROM python:3.8

# Install system dependencies
RUN apt-get -qq update && \
    apt-get -q -y upgrade && \
    apt-get install -y \
        sudo \
        curl \
        wget \
        locales \
        parallel \
        time \
        default-jre \
        default-jdk \
        python3-distutils \
        openjdk-17-jre \
        openjdk-17-jdk \
        raptor2-utils \
        jq && \
    locale-gen en_US.UTF-8 && \
    rm -rf /var/lib/apt/lists/*

ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8

# Set the timezone
RUN ln -sf /usr/share/zoneinfo/Europe/Zurich /etc/localtime
ENV TZ=Europe/Zurich

# Install Python packages
RUN pip install --no-cache-dir \
    chardet \
    date-parser-sari \
    lxml \
    urllib3 \
    requests \
    deepl \
    edtf \
    tqdm \
    rdflib \
    sari-field-definitions-generator \
    sparqlwrapper \
    PyYAML \
    Pillow \
    pytz \
    pyshacl \
    pandas \
    semantic-field-definition-generator==1.4.1 \
    prometheus_client \
    pyexistdb \
    pyduktape2 \
    python-decouple \
    requests-toolbelt

# Install x3ml Mapping engine
RUN mkdir -p /libs /java/bin /x3ml /scripts /data /mapping
RUN wget https://github.com/isl/x3ml/releases/download/2.2.0/x3ml-engine-2.2.0-exejar.jar -O /libs/x3ml-engine-exejar.jar

# Install task runner (http://taskfile.dev)
RUN sh -c "$(curl -sSL https://taskfile.dev/install.sh)" -- -d

# Install AWS CLI
RUN pip --no-cache-dir install --upgrade awscli

# COPY x3ml service
COPY x3ml/java/bin/ /java/bin/

# Define volumes and working directory
VOLUME /data
VOLUME /mapping
WORKDIR /scripts

# Entry point
COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]