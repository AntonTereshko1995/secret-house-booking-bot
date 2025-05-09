FROM python:3.10
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

ENV HOST 0.0.0.0
ENV PORT 8080
EXPOSE 8080
CMD ["python", "src/main.py"]
# CMD ["python", "--bind", "0.0.0.0:8080", "--host", "0.0.0.0", "--port", "8080", "src/main.py"]
