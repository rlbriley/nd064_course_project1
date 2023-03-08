FROM python:3.8
# Maintainer label is deprecated.
LABEL maintainer="Richard L. Briley Jr." \
      org.opencontainers.image.authors="Richard L. Briley Jr." \
      org.opencontainers.image.version="v1.0.1" \
      org.opencontainers.image.url="" \
      org.opencontainers.image.documentation="" \
      org.opencontainers.image.source="https://github.com/rlbriley/nd064_course_1" \
      org.opencontainers.image.vendor="None" \
      version="v1.0.1"
COPY ./techtrends /app
WORKDIR /app
EXPOSE 3111:3111
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 CMD wget http://localhost:3111/healthz
RUN pip install -r requirements.txt
RUN python3 /app/init_db.py
CMD [ "python", "app.py" ]