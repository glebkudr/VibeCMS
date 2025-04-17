############################
# 1. FRONTEND BUILD STAGE  #
############################
FROM node:20-alpine AS frontend-builder

# Рабочая директория = admin_app/frontend
WORKDIR /app/admin_app/frontend

# 1. package.json + lock → npm ci
COPY admin_app/frontend/package*.json ./
RUN npm ci

# 2. исходники фронта
COPY admin_app/frontend/ ./

# 3. shared/ нужен для алиаса @shared
COPY shared/ /app/shared/

# 4. production‑build
RUN npm run build


############################
# 2. PYTHON RUNTIME STAGE  #
############################
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Python‑deps
COPY admin_app/requirements.txt ./admin_app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r ./admin_app/requirements.txt

# Backend‑код + shared‑модуль + generator
COPY admin_app/ ./admin_app/
COPY shared/    ./shared/
COPY generator/ ./generator/

# Статика фронта, собранная на предыдущей стадии
COPY --from=frontend-builder /app/admin_app/static/admin_dist \
                             ./admin_app/static/admin_dist

EXPOSE 8000
CMD ["uvicorn", "admin_app.main:app", "--host", "0.0.0.0", "--port", "8000"]