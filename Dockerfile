# Reproducible environment for the COTA study (P1-23).
#
#   docker build -t cota-opt .
#   docker run --rm -v "$PWD/data:/repo/data" cota-opt cota-opt reproduce exp1 --smoke
#
# Raw public inputs are not in the image; mount a data/ folder holding the
# registered files (config/sources.yaml, docs/REPRODUCE.md §0).
FROM python:3.11.15-slim-bookworm

ENV PYTHONHASHSEED=0 \
    OMP_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /repo
COPY requirements-lock.txt pyproject.toml README.md LICENSE ./
COPY LICENSES ./LICENSES
RUN pip install -r requirements-lock.txt
COPY . .
RUN pip install --no-deps -e .

CMD ["cota-opt", "--help"]
