FROM python:2.7.10

WORKDIR /app
COPY ./ /app

RUN pip install -r requirements.txt
RUN python setup.py
RUN python test.py

EXPOSE 5000
CMD python main.py
