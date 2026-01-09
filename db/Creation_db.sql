--Data base created in postgresql
DROP TABLE IF EXISTS videos;
DROP TYPE IF EXISTS cefr_enum;
DROP TYPE IF EXISTS sub_source_enum;

CREATE TYPE cefr_enum AS ENUM ('A1', 'A2', 'B1', 'B2', 'C1', 'C2');
CREATE TYPE sub_source_enum AS ENUM ('manual', 'generated', 'none');

CREATE TABLE videos (
    video_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    channel_name TEXT,
    topics TEXT[],         
    accents TEXT[],       
    content_types TEXT[],   

    level cefr_enum,       
    wpm INTEGER,           
    subtitle_source sub_source_enum, 

    -- Datos extra de la IA
    ai_analysis JSONB,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

--Creamos los índices para que las búsquedas sean instantáneas
CREATE INDEX idx_topics ON videos USING GIN (topics);
CREATE INDEX idx_accents ON videos USING GIN (accents);
CREATE INDEX idx_types ON videos USING GIN (content_types);
CREATE INDEX idx_level_wpm ON videos (level, wpm);