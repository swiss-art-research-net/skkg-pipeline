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

# Install Apache Jena / RIOT
ARG JENA_VERSION=5.5.0
ARG JENA_SHA512=f9ae68a748e642c6a8175ee25afdfa37ce057ed37e7caf279a8a46ad93284bea808cf14d96bf30b6e4e6a4ddaf30cf5ee9d441f48a9a3d3c9e647a9b71645e0c
RUN wget --no-verbose \
        https://archive.apache.org/dist/jena/binaries/apache-jena-${JENA_VERSION}.tar.gz \
        -O /tmp/jena.tar.gz && \
    echo "${JENA_SHA512}  /tmp/jena.tar.gz" | sha512sum --check - && \
    tar -xzf /tmp/jena.tar.gz -C /opt && \
    ln -s /opt/apache-jena-${JENA_VERSION} /opt/jena && \
    ln -s /opt/jena/bin/riot /usr/local/bin/riot && \
    rm /tmp/jena.tar.gz

ENV JENA_HOME=/opt/jena
ENV PATH="${JENA_HOME}/bin:${PATH}"

# COPY x3ml service
COPY x3ml/java/bin/ /java/bin/

# Define volumes and working directory
VOLUME /data
VOLUME /mapping
WORKDIR /scripts

# Entry point
COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]