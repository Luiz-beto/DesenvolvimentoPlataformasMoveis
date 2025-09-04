-- ===================================================================
-- Banco e charset
-- ===================================================================
CREATE DATABASE IF NOT EXISTS loja_grid
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE loja_grid;

-- ===================================================================
-- Usuários
-- ===================================================================
CREATE TABLE IF NOT EXISTS usuarios (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nome_usuario VARCHAR(50) NOT NULL UNIQUE,
  senha_hash VARCHAR(255) NOT NULL,
  papel ENUM('admin','usuario') NOT NULL DEFAULT 'usuario',
  criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Admin padrão: admin / admin123
INSERT INTO usuarios (nome_usuario, senha_hash, papel)
SELECT 'admin', 'pbkdf2:sha256:260000$UkKTnImrrrClOxX1$b33692a6e2ef3027006edc52a2a7e67faed3b5cbbb43df0c38cdc73ff7a555d6', 'admin'
WHERE NOT EXISTS (SELECT 1 FROM usuarios WHERE nome_usuario='admin');

-- ===================================================================
-- Produtos (com upload de imagem; sem URL)
-- ===================================================================
CREATE TABLE IF NOT EXISTS produtos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nome VARCHAR(120) NOT NULL,
  descricao TEXT,
  preco DECIMAL(10,2) NOT NULL DEFAULT 0,
  -- Upload de imagem
  imagem MEDIUMBLOB NULL,           -- conteúdo do arquivo
  imagem_nome VARCHAR(255) NULL,    -- nome original (ex: foto.jpg)
  imagem_mime VARCHAR(100) NULL,    -- ex: image/jpeg, image/png
  imagem_tamanho INT UNSIGNED NULL, -- bytes
  criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_produtos_nome (nome)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- (Opcional) Exemplos sem imagem
INSERT INTO produtos (nome, descricao, preco)
SELECT * FROM (
  SELECT 'Produto A','Descrição do produto A', 99.90 UNION ALL
  SELECT 'Produto B','Descrição do produto B',149.90 UNION ALL
  SELECT 'Produto C','Descrição do produto C', 59.90 UNION ALL
  SELECT 'Produto D','Descrição do produto D',199.90
) AS t
WHERE NOT EXISTS (SELECT 1 FROM produtos);

-- ===================================================================
-- Banners (apenas imagem)
-- ===================================================================
CREATE TABLE IF NOT EXISTS banners (
  id INT AUTO_INCREMENT PRIMARY KEY,
  imagem MEDIUMBLOB NOT NULL,     -- arquivo binário do banner
  imagem_nome VARCHAR(255) NULL,  -- nome original
  imagem_mime VARCHAR(100) NOT NULL,
  criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===================================================================
-- Contatos (nome, telefone, email, foto)
-- ===================================================================
CREATE TABLE IF NOT EXISTS contatos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nome VARCHAR(120) NOT NULL,
  telefone VARCHAR(40) NOT NULL,
  email VARCHAR(200) NULL,
  foto MEDIUMBLOB NULL,            -- foto do contato
  foto_nome VARCHAR(255) NULL,
  foto_mime VARCHAR(100) NULL,
  criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_contatos_nome (nome),
  INDEX idx_contatos_telefone (telefone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
