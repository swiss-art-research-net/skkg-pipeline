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

# Install Python packages
RUN pip install --no-cache-dir \
    chardet \
    date-parser-sari \
    lxml \
    urllib3 \
    requests \
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
    semantic-field-definition-generator \
    pyexistdb \
    pyduktape2 \
    python-decouple \
    requests-toolbelt

# Install x3ml Mapping engine
RUN mkdir -p /libs /java/bin /x3ml /scripts /data /mapping
RUN wget https://github.com/isl/x3ml/releases/download/2.2.0/x3ml-engine-2.2.0-exejar.jar -O /libs/x3ml-engine-exejar.jar

# COPY x3ml service
COPY x3ml/java/bin/ /java/bin/

# Install task runner (http://taskfile.dev)
RUN sh -c "$(curl -sSL https://taskfile.dev/install.sh)" -- -d

# Install AWS CLI
RUN pip --no-cache-dir install --upgrade awscli

# Define volumes and working directory
VOLUME /data
VOLUME /mapping
WORKDIR /scripts

# Entry point
ENTRYPOINT ["java", "-Xms512m", "-Xmx1024m", "-cp", "/libs/x3ml-engine-exejar.jar:/java/bin", "X3MLEngineService"]
