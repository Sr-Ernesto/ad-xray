# AD-XRAY — Blueprint Revisado (Post-Auditoría)

**Versión:** 2.0 (Revisado por El Fiscal ⚖️)  
**Fecha:** 2026-02-16  
**Estado:** APROBADO CON CAMBIOS

---

## 🎯 Objetivo de FASE 1

> "Validar que podemos detectar COD/Hotmart en 50 competidores sin ser baneados, y que alguien pagaría por esto."

**NO es:** Construir el SaaS final con 10,000 competidores/día.  
**SÍ es:** MVP funcional que demuestre la ventaja competitiva LATAM.

---

## 🏗️ Stack (Simplificado — Todo Python)

| Componente | Tecnología | Justificación |
|-----------|-----------|---------------|
| **API** | FastAPI (Python) | Coherencia con `engine.py`. Sin fricción Node↔Python |
| **Cola** | Celery + Redis | Python-native, Redis ya desplegado |
| **DB** | Supabase (PostgreSQL) | Ya desplegado. Particionamiento por fecha si crece |
| **Scraper** | `engine.py` refactorizado como módulo | Base existente probada |
| **Storage** | MinIO (S3) | Ya desplegado + `uploader_s3.py` existe |
| **Frontend** | Next.js + Tailwind | FASE 2 (no FASE 1) |
| **Deploy** | Docker Compose local → Coolify después | Coolify tiene bugs pendientes |

### ❌ Eliminado de FASE 1
- ~~NestJS~~ → FastAPI
- ~~BullMQ~~ → Celery
- ~~ClickHouse/Timescale~~ → Solo PostgreSQL
- ~~Pinecone~~ → FASE 2+
- ~~OCR/Transcripción~~ → FASE 2+
- ~~10,000 competidores/día~~ → 50 máximo

---

## 📁 Estructura del Proyecto

```
projects/ad-xray/
├── BLUEPRINT.md          # Este archivo
├── api/                  # FastAPI backend
│   ├── main.py           # App entry + routes
│   ├── routes/
│   │   ├── scan.py       # POST /scan endpoint
│   │   └── results.py    # GET /results, GET /results/{id}
│   ├── workers/
│   │   ├── harvester.py  # Celery task: scrape Meta Ads
│   │   ├── inspector.py  # Celery task: COD/Hotmart detector
│   │   └── downloader.py # Celery task: download + upload MinIO
│   ├── models/
│   │   ├── schemas.py    # Pydantic models
│   │   └── database.py   # Supabase/PostgreSQL connection
│   ├── celery_app.py     # Celery config
│   └── requirements.txt
├── db/
│   └── migrations/       # SQL migrations
│       └── 001_initial.sql
├── docker-compose.yml    # Local dev stack
├── Dockerfile
└── tests/
    ├── test_harvester.py
    └── test_inspector.py
```

---

## 📊 Schema de Base de Datos (PostgreSQL/Supabase)

```sql
-- Tabla principal de anuncios
CREATE TABLE ads (
    id BIGINT PRIMARY KEY,              -- ad_archive_id de Meta
    ad_id_internal TEXT,
    page_name TEXT,
    page_id TEXT,
    page_profile_uri TEXT,
    page_profile_picture_url TEXT,
    page_like_count INT,
    page_categories TEXT[],
    
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT true,
    
    body_text TEXT,
    title TEXT,
    cta TEXT,
    cta_type TEXT,
    link_url TEXT,
    link_description TEXT,
    
    publisher_platform TEXT[],
    byline TEXT,
    
    image_url TEXT,
    video_url TEXT,
    card_count INT DEFAULT 0,
    s3_link TEXT,
    
    -- Inspector results
    funnel_type TEXT,           -- 'cod', 'hotmart', 'whatsapp', 'shopify', 'unknown'
    funnel_confidence FLOAT,
    funnel_signals JSONB,      -- {"cod_keywords": [...], "whatsapp_found": true, ...}
    landing_page_url TEXT,     -- URL final después de redirects
    
    -- AI Analysis
    ai_analysis JSONB,
    
    -- Meta
    country TEXT,
    query TEXT,
    scraped_at TIMESTAMPTZ DEFAULT NOW(),
    job_id UUID REFERENCES scrape_jobs(id)
);

-- Jobs de scraping
CREATE TABLE scrape_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query TEXT NOT NULL,
    country TEXT DEFAULT 'CO',
    max_count INT DEFAULT 20,
    status TEXT DEFAULT 'pending',    -- pending, running, completed, failed
    ads_found INT DEFAULT 0,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Competidores para tracking
CREATE TABLE competitors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    page_id TEXT UNIQUE NOT NULL,
    page_name TEXT,
    category TEXT,
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_ads_page_id ON ads(page_id);
CREATE INDEX idx_ads_country ON ads(country);
CREATE INDEX idx_ads_funnel_type ON ads(funnel_type);
CREATE INDEX idx_ads_scraped_at ON ads(scraped_at);
CREATE INDEX idx_jobs_status ON scrape_jobs(status);
```

---

## 🔬 El Inspector (COD/Hotmart Detector)

El diferenciador clave. Lógica de `inspector.py`:

```python
# Señales COD (Pago Contra Entrega)
COD_SIGNALS = {
    "keywords": [
        "pago contra entrega", "contraentrega", "pago al recibir",
        "paga cuando recibas", "COD", "cash on delivery",
        "envío gratis", "sin tarjeta", "pago en efectivo",
        "recibe y paga", "paga al recibir tu pedido"
    ],
    "tech": [
        "tiendanube.com", "vtex.com", "shopify.com",
        "woocommerce", "dropi.co", "lojadoafiliado"
    ],
    "whatsapp": [
        "wa.me/", "api.whatsapp.com", "whatsapp.com/send",
        "wa.link/"
    ]
}

# Señales Hotmart
HOTMART_SIGNALS = {
    "urls": [
        "hotmart.com", "go.hotmart.com", "pay.hotmart.com",
        "kiwify.com", "eduzz.com", "monetizze.com"
    ],
    "keywords": [
        "comprar agora", "inscríbete", "acceso inmediato",
        "garantía de", "días de garantía", "curso online",
        "método comprobado", "clase gratis"
    ]
}
```

### Flujo del Inspector:
1. Toma la `link_url` del anuncio
2. Navega con Playwright (siguiendo redirects)
3. Captura URL final (landing page real)
4. Escanea HTML por señales COD/Hotmart/WhatsApp
5. Clasifica el funnel_type con confidence score
6. Guarda resultados en PostgreSQL

---

## 🚀 Plan de Ejecución

### PRE-FASE 1: Deuda Técnica (Semana 0)
- [ ] **P0:** Test de anti-detección Meta — scrapear 100 anuncios, medir % de 403
- [ ] **P0:** Resolver Coolify `exited:unhealthy` (o decidir Docker Compose directo)
- [ ] **P1:** Configurar logging centralizado (Loki o stdout estructurado)

### FASE 1A: API + DB (Semana 1)
- [ ] Crear schema PostgreSQL en Supabase
- [ ] FastAPI con endpoints básicos (`POST /scan`, `GET /results`)
- [ ] Celery + Redis configurado
- [ ] Refactorizar `engine.py` como módulo importable (no solo CLI)
- [ ] Worker Harvester: ejecuta scraping y guarda en DB

### FASE 1B: Inspector (Semana 2)
- [ ] Worker Inspector: navega landing pages
- [ ] Detección COD (keywords + tech)
- [ ] Detección Hotmart/affiliate (URLs + keywords)
- [ ] Detección WhatsApp
- [ ] Guardar `funnel_type` + `funnel_signals` en DB

### FASE 1C: Pipeline Completo (Semana 3)
- [ ] Worker Downloader: baja assets a MinIO (reusar `uploader_s3.py`)
- [ ] AI Analyzer integrado (reusar `analyzer.py`)
- [ ] Docker Compose para dev local
- [ ] Tests básicos
- [ ] API docs (Swagger auto de FastAPI)

### FASE 1D: Validación (Semana 4)
- [ ] 10 competidores LATAM scrapeados sin ban
- [ ] COD detector: 80%+ accuracy (test manual con 50 anuncios)
- [ ] API responde en <500ms
- [ ] Demo a 3 marketers LATAM → feedback

---

## ⚠️ Límites Operacionales FASE 1

| Parámetro | Límite | Razón |
|-----------|--------|-------|
| Competidores/día | 50 max | Evitar ban de Meta |
| Scrapes/hora | 5 max | Delays de 10+ min entre competidores |
| Proxy | IP residencial (PC1) | Soberanía local |
| Fallback | Apify si >5% de 403 | Plan B documentado |

---

## ✅ Criterios de Éxito FASE 1

- [ ] 10 competidores scrapeados sin ban de IP
- [ ] COD detector funciona con 80%+ accuracy
- [ ] API responde en <500ms (sin carga)
- [ ] 1 usuario beta usa la herramienta 3 veces/semana
- [ ] Pipeline completo: scan → inspect → download → analyze funciona end-to-end

---

## 🔮 FASE 2 (Solo si FASE 1 valida)

- Frontend Next.js + Tailwind
- NestJS como BFF si Next.js lo requiere
- ClickHouse/Timescale para analytics históricas
- Pinecone para búsqueda semántica
- OCR + Transcripción de videos
- Proxies residenciales rotativos
- Escala a 500+ competidores/día
- Auth + multi-tenant

---

## 📋 Código Base Existente (Reusar)

| Archivo | Qué hace | Reusar en |
|---------|----------|-----------|
| `engine.py` | Scraper Meta Ads Library (Playwright + network interception) | Worker Harvester |
| `analyzer.py` | Análisis AI con Gemini | Worker Analyzer |
| `uploader_s3.py` | Download + upload a MinIO | Worker Downloader |
| `uploader.py` | Upload a Google Sheets | Deprecar (reemplazar con DB) |

---

## 🐺 Agentes Asignados

| Tarea | Agente | Modelo |
|-------|--------|--------|
| Spec técnico (este doc) | Roco (orquestador) | claude-opus-4 |
| Auditoría | El Fiscal | claude-sonnet-4-5 |
| Código backend | El Ingeniero (coder) | gemini-3-pro |
| Tests | El Inspector (tester) | gemini-3-flash |
| Deploy | El Lanzador (deployer) | gemini-3-flash |
