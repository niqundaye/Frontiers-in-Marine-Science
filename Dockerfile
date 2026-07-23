FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg

WORKDIR /artifact

COPY requirements.txt requirements-dev.txt pyproject.toml README.md ./
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements-dev.txt

COPY . .
RUN python -m pip install --no-cache-dir --no-deps -e .

CMD ["python", "scripts/reviewer_quick_check.py"]
