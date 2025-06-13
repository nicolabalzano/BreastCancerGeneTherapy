# Gene Research Platform - Docker Setup

Questo progetto include tre servizi containerizzati:
- **Frontend**: App Flask per la ricerca PubMed e interfaccia utente
- **Backend**: API per le predizioni di geni con machine learning
- **Cheshire Cat**: Sistema LLM per analisi avanzate

## 🚀 Avvio Rapido

### 1. Prerequisiti
- Docker installato
- Docker Compose installato

### 2. Configurazione variabili d'ambiente
Il progetto usa un file `.env` centralizzato nella directory root:

```bash
# Copia il template e modifica con le tue API keys
cp .env.example .env
```

**Configurazione minima richiesta nel file `.env`:**
```env
# OBBLIGATORIO per Cheshire Cat
DEEPSEEK_TOKEN=your-deepseek-token-here

# Porte dei servizi (opzionale, usa i default se non specificato)
FRONTEND_PORT=5000
BACKEND_PORT=5001
CHESHIRE_CAT_PORT=1865

# URLs interni (normalmente non modificare)
CHESHIRE_CAT_URL=http://cheshire-cat-core:80
BACKEND_API_URL=http://backend:5000

# Chiave di sicurezza (cambia in produzione)
SECRET_KEY=your-secure-secret-key
```

**API Keys opzionali per altri provider LLM:**
```env
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
GOOGLE_API_KEY=your-google-api-key
# ... vedi .env.example per la lista completa
```

### 3. Avvio dei servizi
```bash
# Dalla directory root del progetto
docker-compose up -d
```

### 4. Verifica dei servizi
- **Frontend**: http://localhost:5000
- **Backend API**: http://localhost:5001
- **Cheshire Cat**: http://localhost:1865

## ⚙️ Configurazione Variabili d'Ambiente

### 📋 Variabili principali

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `DEEPSEEK_TOKEN` | - | **OBBLIGATORIO** - Token API per DeepSeek |
| `FRONTEND_PORT` | 5000 | Porta per il frontend Flask |
| `BACKEND_PORT` | 5001 | Porta per l'API backend |
| `CHESHIRE_CAT_PORT` | 1865 | Porta per Cheshire Cat |
| `FLASK_ENV` | production | Modalità Flask (production/development) |
| `FLASK_DEBUG` | 0 | Debug Flask (0/1) |
| `SECRET_KEY` | - | Chiave segreta per Flask |
| `MAX_CONTENT_LENGTH` | 500000000 | Limite upload file (500MB) |

### 🔐 API Keys supportate

- **DeepSeek**: `DEEPSEEK_TOKEN` (obbligatorio)
- **OpenAI**: `OPENAI_API_KEY`
- **Anthropic**: `ANTHROPIC_API_KEY`
- **Google Gemini**: `GOOGLE_API_KEY`
- **Cohere**: `COHERE_API_KEY`
- **HuggingFace**: `HUGGINGFACE_API_KEY`
- **Azure OpenAI**: `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_VERSION`

### 🌐 URLs interni (Docker network)

- `CHESHIRE_CAT_URL=http://cheshire-cat-core:80`
- `BACKEND_API_URL=http://backend:5000`

**Nota**: Non modificare gli URL interni a meno che non cambi i nomi dei servizi Docker.

### 💻 Modalità sviluppo

Per attivare la modalità sviluppo, modifica nel file `.env`:
```env
FLASK_ENV=development
FLASK_DEBUG=1
```

Oppure usa il comando:
```bash
.\manage.ps1 dev  # Windows
./manage.sh dev   # Linux/Mac
```

## 📋 Comandi Utili

### Costruire e avviare tutti i servizi
```bash
docker-compose up --build -d
```

### Vedere i logs
```bash
# Tutti i servizi
docker-compose logs -f

# Solo il frontend
docker-compose logs -f frontend

# Solo il backend
docker-compose logs -f backend

# Solo Cheshire Cat
docker-compose logs -f cheshire-cat-core
```

### Fermare i servizi
```bash
docker-compose down
```

### Rimuovere tutto (inclusi volumi)
```bash
docker-compose down -v
```

### Ricostruire un singolo servizio
```bash
# Ricostruire solo il frontend
docker-compose build frontend
docker-compose up -d frontend

# Ricostruire solo il backend
docker-compose build backend
docker-compose up -d backend
```

## 🔧 Sviluppo

### Modalità sviluppo con hot reload
Per modifiche al codice senza ricostruire:

```bash
# Ferma i servizi
docker-compose down

# Monta i volumi per lo sviluppo
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### Debug
```bash
# Accedere al container frontend
docker exec -it gene_research_frontend bash

# Accedere al container backend
docker exec -it gene_prediction_backend bash
```

## 🌐 Porte dei Servizi

| Servizio | Porta Host | Porta Container | URL |
|----------|------------|-----------------|-----|
| Frontend | 5000 | 5000 | http://localhost:5000 |
| Backend | 5001 | 5000 | http://localhost:5001 |
| Cheshire Cat | 1865 | 80 | http://localhost:1865 |

## 📁 Struttura Volumi

- `./frontend/uploads` → `/app/uploads` (Frontend uploads)
- `./backendPrediction/assets` → `/app/assets` (Modelli ML)
- `./LLM/static` → `/app/cat/static` (Cheshire Cat static files)
- `./LLM/plugins` → `/app/cat/plugins` (Cheshire Cat plugins)
- `./LLM/data` → `/app/cat/data` (Cheshire Cat data)

## 🔧 Troubleshooting

### Problema: Container non si avvia
```bash
# Controlla i logs
docker-compose logs [service-name]

# Verifica lo stato
docker-compose ps
```

### Problema: Porta già in uso
Modifica le porte nel `docker-compose.yml`:
```yaml
ports:
  - "5002:5000"  # Cambia la porta host
```

### Problema: Permessi file
```bash
# Aggiusta i permessi
sudo chown -R $USER:$USER ./
```

### Ricostruire da zero
```bash
# Ferma tutto e rimuovi immagini
docker-compose down
docker system prune -a

# Ricostruisci
docker-compose up --build -d
```
