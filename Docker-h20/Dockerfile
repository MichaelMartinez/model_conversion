# Use the specified base image
FROM nvidia/cuda:11.6.2-cudnn8-devel-ubuntu20.04
ENV DEBIAN_FRONTEND=noninteractive

# Install Python 3.10 and set it as the default
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository -y ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.10 python3.10-distutils python3.10-dev && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1

# Install pip
RUN apt-get install -y wget git && \
    wget https://bootstrap.pypa.io/get-pip.py && \
    python3.10 get-pip.py && \
    rm get-pip.py

# Set the working directory
WORKDIR /app

# Clone the repository
RUN git clone https://github.com/h2oai/h2o-llmstudio.git /app

# Install required packages and dependencies
RUN pip install --upgrade pip \
    && pip install pipenv==2022.10.4 \
    && pipenv install --python 3.10 \
    && pipenv run pip install deps/h2o_wave-nightly-py3-none-manylinux1_x86_64.whl --force-reinstall

# Set environment variables for Wave and HF_HOME
ENV H2O_WAVE_MAX_REQUEST_SIZE=25MB \
    H2O_WAVE_NO_LOG=True \
    H2O_WAVE_PRIVATE_DIR="/download/@/app/output/download" \
    HF_HOME="/app/HF_CACHE"

# Create the HF_CACHE directory
RUN mkdir -p /app/HF_CACHE

# Expose the Wave server's port
EXPOSE 10101

# Start the Wave server
CMD ["pipenv", "run", "wave", "run", "app"]