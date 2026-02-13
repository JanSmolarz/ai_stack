#FROM python:3.11-slim
#WORKDIR /app
#COPY requirements.txt .
#RUN pip install --no-cache-dir -r requirements.txt
#COPY . .
#CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
# ----------------------------------------------------------------------
# -------------------------------
# Obraz bazowy
# -------------------------------
FROM python:3.11-slim

# -------------------------------
# Zmienne środowiskowe
# -------------------------------
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# -------------------------------
# Katalog roboczy
# -------------------------------
WORKDIR /app

# -------------------------------
# Zależności systemowe
# -------------------------------
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# -------------------------------
# Instalacja zależności Python
# -------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# -------------------------------
# Kopiowanie projektu
# -------------------------------
COPY . .

# -------------------------------
# Porty
# -------------------------------
EXPOSE 8015
EXPOSE 8501

# -------------------------------
# Komenda startowa (DEMO)
# -------------------------------
CMD sh -c "uvicorn app:app --host 0.0.0.0 --port 8015 & \
           streamlit run ui.py --server.port 8501 --server.address 0.0.0.0"
