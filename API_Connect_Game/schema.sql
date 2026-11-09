CREATE DATABASE IF NOT EXISTS connect_game CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE connect_game;
CREATE TABLE IF NOT EXISTS player (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    moedas INT UNSIGNED NOT NULL DEFAULT 0
);

-- Adiciona a coluna para bancos criados pela versão anterior da atividade.
SET @coin_migration = IF(
    EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'player' AND COLUMN_NAME = 'moedas'
    ),
    'SELECT 1',
    'ALTER TABLE player ADD COLUMN moedas INT UNSIGNED NOT NULL DEFAULT 0'
);
PREPARE coin_migration FROM @coin_migration;
EXECUTE coin_migration;
DEALLOCATE PREPARE coin_migration;