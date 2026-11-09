'use strict';
require('dotenv').config({ path: require('node:path').join(__dirname, '.env') });
const express = require('express');
const mysql = require('mysql2');
const cors = require('cors');

function createApp(db) {
    const app = express();
    app.use(cors());
    app.use(express.json({ limit: '16kb' }));
    const validId = (req, res, next) => {
        const id = Number(req.params.id);
        if (!Number.isSafeInteger(id) || id <= 0) return res.status(400).json({ success: false, message: 'ID deve ser um inteiro positivo' });
        req.playerId = id;
        next();
    };
    const validName = (req, res, next) => {
        const nome = req.body?.nome;
        if (typeof nome !== 'string' || !nome.trim() || nome.trim().length > 255) {
            return res.status(400).json({ success: false, message: 'nome deve conter de 1 a 255 caracteres' });
        }
        req.playerName = nome.trim();
        next();
    };
    const query = (res, sql, params, done) => {
        db.query(sql, params, (err, rows) => {
            if (err) {
                console.error('Erro MySQL:', err.code || err.message);
                return res.status(503).json({ success: false, message: 'Banco de dados indisponivel' });
            }
            done(rows);
        });
    };
    const missing = res => res.status(404).json({ success: false, message: 'Player não encontrado' });
    app.get('/health', (req, res) => query(res, 'SELECT 1 AS ok', [], () => res.json({ success: true, database: 'connected' })));
    app.get('/player', (req, res) => query(res, 'SELECT id, nome, moedas FROM player ORDER BY id', [], rows => res.json(rows)));
    app.get('/player/:id', validId, (req, res) => query(res, 'SELECT id, nome, moedas FROM player WHERE id = ?', [req.playerId], rows => rows.length ? res.json(rows[0]) : missing(res)));
    app.post('/player/insertPlayer', validName, (req, res) => query(res, 'INSERT INTO player (nome) VALUES (?)', [req.playerName], result => res.status(201).json({ success: true, message: 'Player inserido com sucesso', insertId: result.insertId, id: result.insertId, nome: req.playerName })));
    app.delete('/player/deletePlayer/:id', validId, (req, res) => query(res, 'DELETE FROM player WHERE id = ?', [req.playerId], result => result.affectedRows ? res.json({ success: true, message: 'Player deletado com sucesso' }) : missing(res)));
    app.put('/player/updatePlayer/:id', validId, validName, (req, res) => query(res, 'UPDATE player SET nome = ? WHERE id = ?', [req.playerName, req.playerId], result => result.affectedRows ? res.json({ success: true, message: 'Player atualizado com sucesso' }) : missing(res)));
    app.post('/player/coins/:id', validId, (req, res) => {
        const quantidade = req.body?.quantidade;
        if (!Number.isInteger(quantidade) || quantidade <= 0 || quantidade > 2147483647) {
            return res.status(400).json({ success: false, message: 'Quantidade de moedas invalida' });
        }
        query(
            res,
            'INSERT INTO player (id, nome, moedas) VALUES (?, ?, ?) ON DUPLICATE KEY UPDATE moedas = moedas + ?',
            [req.playerId, 'Jogador local', quantidade, quantidade],
            () => res.json({ success: true })
        );
    });
    app.use((err, req, res, next) => {
        if (err.type === 'entity.parse.failed') return res.status(400).json({ success: false, message: 'JSON invalido' });
        if (err.type === 'entity.too.large') return res.status(413).json({ success: false, message: 'Corpo da requisicao muito grande' });
        console.error(err.message);
        res.status(500).json({ success: false, message: 'Erro interno' });
    });
    return app;
}
function start() {
    for (const key of ['DB_HOST', 'DB_USER', 'DB_NAME']) {
        if (!process.env[key]) throw new Error(`Defina ${key} no arquivo .env (veja .env.example)`);
    }
    const db = mysql.createPool({ host: process.env.DB_HOST, port: Number(process.env.DB_PORT || 3306), user: process.env.DB_USER, password: process.env.DB_PASSWORD || '', database: process.env.DB_NAME, connectionLimit: 5, connectTimeout: 5000 });
    const server = createApp(db).listen(Number(process.env.PORT || 3000), '127.0.0.1', () => console.log(`API em http://127.0.0.1:${server.address().port}`));
    server.on('error', err => { console.error(err.message); db.end(); process.exitCode = 1; });
    const shutdown = () => server.close(() => db.end());
    process.once('SIGINT', shutdown);
    process.once('SIGTERM', shutdown);
    return server;
}
if (require.main === module) {
    try { start(); } catch (err) { console.error(err.message); process.exitCode = 1; }
}
module.exports = { createApp, start };
