FROM python

WORKDIR /project

COPY requirements.txt .

RUN pip3 install --no-cache-dir --upgrade -r requirements.txt

COPY /src /src

ENV PYTHONPATH=/project

CMD ["python", "src/main.py"]
