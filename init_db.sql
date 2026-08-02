-- ============================================================
-- SCRIPT DE CRÉATION ET D'INITIALISATION DE LA BASE DE DONNÉES
-- Projet: Invitation Mariage / Réception
-- Compatible avec Supabase & PostgreSQL
-- ============================================================

-- 1. Table des Invités (guests)
CREATE TABLE IF NOT EXISTS guests (
  id BIGSERIAL PRIMARY KEY,
  nom VARCHAR(255) NOT NULL,
  postnom VARCHAR(255),
  prenom VARCHAR(255) NOT NULL,
  telephone VARCHAR(50),
  table_assignee VARCHAR(100),
  nombre_places INT DEFAULT 1,
  a_confirme BOOLEAN DEFAULT FALSE,
  statut VARCHAR(100) DEFAULT 'Invité',
  secret_code VARCHAR(255),
  secret_used BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Index pour accélérer la recherche des invités par nom et code secret
CREATE INDEX IF NOT EXISTS idx_guests_table ON guests(table_assignee);
CREATE INDEX IF NOT EXISTS idx_guests_secret_code ON guests(UPPER(secret_code));
CREATE INDEX IF NOT EXISTS idx_guests_search ON guests(UPPER(nom), UPPER(postnom), LOWER(prenom));


-- 2. Table des Tables de Réception (tables)
CREATE TABLE IF NOT EXISTS tables (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(100) UNIQUE NOT NULL,
  capacity INT DEFAULT 8,
  description VARCHAR(255),
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);


-- 3. Table du Livre d'Or (wishes)
CREATE TABLE IF NOT EXISTS wishes (
  id BIGSERIAL PRIMARY KEY,
  guest_name VARCHAR(255) NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_wishes_created_at ON wishes(created_at DESC);


-- 4. Insertion des tables par défaut (VIP + Tables 1 à 10)
INSERT INTO tables (name, capacity, description) VALUES
  ('Table VIP', 8, 'Table pour les invités d''honneur'),
  ('Table 1', 8, 'Table 1'),
  ('Table 2', 8, 'Table 2'),
  ('Table 3', 8, 'Table 3'),
  ('Table 4', 8, 'Table 4'),
  ('Table 5', 8, 'Table 5'),
  ('Table 6', 8, 'Table 6'),
  ('Table 7', 8, 'Table 7'),
  ('Table 8', 8, 'Table 8'),
  ('Table 9', 8, 'Table 9'),
  ('Table 10', 8, 'Table 10')
ON CONFLICT (name) DO NOTHING;


-- 5. Exemples d'invités (Optionnel - à exécuter si vous voulez des données de test)
-- INSERT INTO guests (nom, postnom, prenom, telephone, table_assignee, nombre_places, secret_code, statut) VALUES
--   ('KABONGO', 'MUTOMBO', 'Jean', '+243810000001', 'Table VIP', 2, 'VIP2026', 'VIP'),
--   ('KANKU', 'ILUNGA', 'Sarah', '+243820000002', 'Table 1', 1, 'SARAH2026', 'Invité');
