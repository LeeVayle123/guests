-- Script d'initialisation pour la table guests
CREATE TABLE IF NOT EXISTS guests (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nom VARCHAR(255),
  postnom VARCHAR(255),
  prenom VARCHAR(255),
  telephone VARCHAR(50),
  table_assignee VARCHAR(100),
  nombre_places INT DEFAULT 1,
  a_confirme BOOLEAN DEFAULT FALSE,
  statut VARCHAR(100),
  secret_code VARCHAR(255),
  secret_used BOOLEAN DEFAULT FALSE,
  INDEX idx_guests_table (table_assignee)
);

-- Table pour représenter les tables de réception
CREATE TABLE IF NOT EXISTS tables (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) UNIQUE,
  capacity INT DEFAULT 8,
  description VARCHAR(255)
);
+
+-- Table pour stocker les souhaits du livre d'or
+CREATE TABLE IF NOT EXISTS wishes (
+  id INT AUTO_INCREMENT PRIMARY KEY,
+  guest_name VARCHAR(255),
+  content TEXT,
+  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
+);
