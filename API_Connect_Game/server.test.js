'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { createApp } = require('./server');

test('HTTP: CRUD, validacao, JSON e erros de banco', async () => {
    let nextId = 1;
    const players = new Map();
    let offline = false;
    const db = { query(sql, args, cb) {
        if (offline) return cb({ code: 'ECONNREFUSED' });
        if (sql.startsWith('SELECT 1')) return cb(null, [{ ok: 1 }]);
        if (sql.includes('ON DUPLICATE KEY')) { const [id, nome, q] = args; const p = players.get(id); if (p) p.moedas += q; else players.set(id, { id, nome, moedas: q }); return cb(null, { affectedRows: 1 }); }
        if (sql.startsWith('INSERT')) { const id = nextId++; players.set(id, { id, nome: args[0] }); return cb(null, { insertId: id }); }
        if (sql.startsWith('DELETE')) return cb(null, { affectedRows: Number(players.delete(args[0])) });
        if (sql.startsWith('UPDATE')) { const p = players.get(args[1]); if (p) p.nome = args[0]; return cb(null, { affectedRows: Number(!!p) }); }
        return cb(null, sql.includes('WHERE') ? (players.has(args[0]) ? [players.get(args[0])] : []) : [...players.values()]);
    } };
    const server = createApp(db).listen(0, '127.0.0.1');
    await new Promise(resolve => server.once('listening', resolve));
    const base = `http://127.0.0.1:${server.address().port}`;
    const req = async (path, method = 'GET', body) => {
        const response = await fetch(base + path, { method, headers: { 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body) });
        return { status: response.status, data: await response.json() };
    };
    try {
        assert.equal((await req('/health')).status, 200);
        assert.deepEqual((await req('/player')).data, []);
        assert.equal((await req('/player/1')).status, 404);
        for (const id of ['0', '-1', 'abc', '1.2', '9007199254740992']) assert.equal((await req('/player/' + id)).status, 400);
        for (const nome of [undefined, '', ' ', ['Bruno'], 123, 'a'.repeat(256)]) assert.equal((await req('/player/insertPlayer', 'POST', { nome })).status, 400);
        const created = await req('/player/insertPlayer', 'POST', { nome: ' Bruno "Jogador" ç ' });
        assert.equal(created.status, 201);
        assert.equal(created.data.insertId, 1);
        assert.equal((await req('/player/1')).data.nome, 'Bruno "Jogador" ç');
        assert.equal((await req('/player')).data.length, 1);
        assert.equal((await req('/player/updatePlayer/1', 'PUT', { nome: 'Novo nome' })).data.success, true);
        assert.equal((await req('/player/1')).data.nome, 'Novo nome');
        assert.equal((await req('/player/deletePlayer/1', 'DELETE', {})).data.success, true);
        assert.equal((await req('/player/deletePlayer/1', 'DELETE', {})).status, 404);
        assert.equal((await req('/player/updatePlayer/1', 'PUT', { nome: 'X' })).status, 404);
        assert.equal((await fetch(base + '/player/insertPlayer', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{' })).status, 400);
        for (const quantidade of [undefined, 0, -1, 1.5, '3']) assert.equal((await req('/player/coins/7', 'POST', { quantidade })).status, 400);
        const coleta1 = await req('/player/coins/7', 'POST', { quantidade: 2 });
        assert.equal(coleta1.status, 200);
        assert.equal(coleta1.data.success, true);
        assert.equal(coleta1.data.moedas, 2);
        const coleta2 = await req('/player/coins/7', 'POST', { quantidade: 5 });
        assert.equal(coleta2.data.moedas, 7);
        assert.equal(coleta2.data.mensagem, 'Coleta registrada no banco! +5 moeda(s). Total de Jogador local no MySQL: 7');
        offline = true;
        assert.equal((await req('/health')).status, 503);
        assert.equal((await req('/player/coins/7', 'POST', { quantidade: 1 })).status, 503);
    } finally { await new Promise(resolve => server.close(resolve)); }
});
