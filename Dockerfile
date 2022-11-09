FROM python:3.11

ENV USER_HOME='/home/python'
RUN groupadd --gid 1001 python && \
    useradd --uid 1001 --gid python --shell /usr/bin/nologin --create-home --home-dir ${USER_HOME} python && \
    chown -R python:python ${USER_HOME}
USER python
WORKDIR ${USER_HOME}
ENV PATH="${USER_HOME}/.local/bin:/bin:/sbin:/usr/bin:/usr/local/bin"

COPY requirements.txt .
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["/usr/local/bin/python", "bot.py"]
