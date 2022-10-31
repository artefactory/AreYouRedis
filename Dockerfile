FROM python:3.9

WORKDIR ./
COPY ./ ./

RUN python3 -m pip install --upgrade pip setuptools wheel
RUN pip install pip-tools

RUN pip-compile ./requirements.in
RUN pip install -r ./requirements.txt
RUN pip install -e .

CMD ["sh", "./entrypoint.sh"]