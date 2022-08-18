FROM python:3.9

COPY . .

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install system dependencies
RUN apt-get update --allow-releaseinfo-change
RUN apt-get install ffmpeg libsm6 libxext6  -y

# install python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt


# gunicorn
CMD ["gunicorn", "--config", "gunicorn-cfg.py", "run:app"]
