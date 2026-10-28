-- ============================================================
-- Urban Mobility Flow Analysis - Database Schema
-- ============================================================

CREATE DATABASE ColetaTransporte;
GO

USE ColetaTransporte;
GO

-- 1. Real-time bus positions (SPTrans)
CREATE TABLE Coleta_SPTrans (
    id                  INT PRIMARY KEY IDENTITY(1,1),
    prefixo             VARCHAR(20),
    latitude            FLOAT,
    longitude           FLOAT,
    linha_codigo        INT,
    data_hora_sptrans   DATETIME,
    data_hora_coleta    DATETIME DEFAULT GETDATE()
);

-- 2. Google Places (geocoding + Place IDs)
CREATE TABLE Coleta_Google (
    id                  INT PRIMARY KEY IDENTITY(1,1),
    latitude            FLOAT,
    longitude           FLOAT,
    endereco_completo   VARCHAR(MAX),
    place_id            VARCHAR(255)
);

ALTER TABLE Coleta_Google
ADD CONSTRAINT UQ_PlaceID UNIQUE (place_id);
GO

-- 3. Google Places popularity / ratings
CREATE TABLE Coleta_Google_Popularidade (
    id                  INT PRIMARY KEY IDENTITY(1,1),
    place_id            VARCHAR(255),
    nota_media          FLOAT,
    total_avaliacoes    INT,
    faixa_preco         INT,
    data_consulta       DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_Google_Pop FOREIGN KEY (place_id) REFERENCES Coleta_Google(place_id)
);
GO

-- 4. Aggregated social network metrics
CREATE TABLE Coleta_Sociais_Agregados (
    id                  INT PRIMARY KEY IDENTITY(1,1),
    plataforma          VARCHAR(50),
    ano                 INT,
    metrica             VARCHAR(100),
    valor               FLOAT,
    data_importacao     DATETIME DEFAULT GETDATE()
);

-- 5. Relationship between transport and social engagement
CREATE TABLE Coleta_Interacao_SocialTransporte (
    id                  INT PRIMARY KEY IDENTITY(1,1),
    sptrans_id          INT,
    sociais_id          INT,
    impacto_estimado    FLOAT,
    descricao_evento    VARCHAR(255),
    data_relacao        DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_SPTrans FOREIGN KEY (sptrans_id) REFERENCES Coleta_SPTrans(id),
    CONSTRAINT FK_Sociais FOREIGN KEY (sociais_id) REFERENCES Coleta_Sociais_Agregados(id)
);

-- 6. Historical social check-ins (Gowalla, Brightkite, etc.)
CREATE TABLE Coleta_Checkins (
    id                  INT PRIMARY KEY IDENTITY(1,1),
    user_id             VARCHAR(50),
    latitude            FLOAT,
    longitude           FLOAT,
    checkin_time        DATETIME,
    location_id         VARCHAR(50),
    data_importacao     DATETIME DEFAULT GETDATE()
);
GO
