import sqlite3
from datetime import datetime
from pathlib import Path
import pandas as pd

DB = Path('data/financeplustech.db')
DB.parent.mkdir(exist_ok=True)


def conn():
    return sqlite3.connect(DB)


def init_db():
    c = conn()
    sql = c.cursor()
    sql.execute('CREATE TABLE IF NOT EXISTS clienti (id INTEGER PRIMARY KEY AUTOINCREMENT, denominazione TEXT, piva TEXT, sede TEXT, attivita TEXT, pec TEXT, amministratore TEXT, telefono TEXT, email TEXT, data_creazione TEXT)')
    sql.execute('CREATE TABLE IF NOT EXISTS collaboratori (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, cognome TEXT, cellulare TEXT, email TEXT, data_creazione TEXT)')
    sql.execute('CREATE TABLE IF NOT EXISTS documenti (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_id INTEGER, categoria TEXT, nome_file TEXT, percorso_locale TEXT, cloud_provider TEXT, cloud_id TEXT, data_upload TEXT)')
    sql.execute('CREATE TABLE IF NOT EXISTS richieste (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_id INTEGER, data TEXT, canale TEXT, oggetto TEXT, stato TEXT, semaforo TEXT, data_creazione TEXT)')
    sql.execute('CREATE TABLE IF NOT EXISTS mail (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_id INTEGER, data_mail TEXT, direzione TEXT, stato TEXT, responsabile TEXT, mittente_destinatario TEXT, oggetto TEXT, testo TEXT, allegato TEXT, data_creazione TEXT)')
    sql.execute('CREATE TABLE IF NOT EXISTS valutazioni (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_id INTEGER, score INTEGER, rating TEXT, fido_stimato REAL, giudizio TEXT, ricavi TEXT, mol TEXT, utile TEXT, cash_flow TEXT, indice_indebitamento TEXT, data_creazione TEXT)')
    c.commit(); c.close()


def df(q, params=()):
    c = conn(); out = pd.read_sql_query(q, c, params=params); c.close(); return out


def run(q, params=()):
    c = conn(); cur = c.cursor(); cur.execute(q, params); c.commit(); x = cur.lastrowid; c.close(); return x


def now():
    return datetime.now().isoformat()


def insert_cliente(a,b,c,d,e,f,g,h):
    return run('INSERT INTO clienti (denominazione,piva,sede,attivita,pec,amministratore,telefono,email,data_creazione) VALUES (?,?,?,?,?,?,?,?,?)', (a,b,c,d,e,f,g,h,now()))


def insert_collaboratore(a,b,c,d):
    return run('INSERT INTO collaboratori (nome,cognome,cellulare,email,data_creazione) VALUES (?,?,?,?,?)', (a,b,c,d,now()))


def insert_documento(a,b,c,d,e,f):
    return run('INSERT INTO documenti (cliente_id,categoria,nome_file,percorso_locale,cloud_provider,cloud_id,data_upload) VALUES (?,?,?,?,?,?,?)', (a,b,c,d,e,f,now()))


def insert_richiesta(a,b,c,d,e,f):
    return run('INSERT INTO richieste (cliente_id,data,canale,oggetto,stato,semaforo,data_creazione) VALUES (?,?,?,?,?,?,?)', (a,b,c,d,e,f,now()))


def insert_mail(a,b,c,d,e,f,g,h,i):
    return run('INSERT INTO mail (cliente_id,data_mail,direzione,stato,responsabile,mittente_destinatario,oggetto,testo,allegato,data_creazione) VALUES (?,?,?,?,?,?,?,?,?,?)', (a,b,c,d,e,f,g,h,i,now()))


def insert_valutazione(a,b,c,d,e,f='',g='',h='',i='',j=''):
    return run('INSERT INTO valutazioni (cliente_id,score,rating,fido_stimato,giudizio,ricavi,mol,utile,cash_flow,indice_indebitamento,data_creazione) VALUES (?,?,?,?,?,?,?,?,?,?,?)', (a,b,c,d,e,f,g,h,i,j,now()))


def list_clienti(): return df('SELECT * FROM clienti ORDER BY id DESC')
def get_cliente(i):
    x = df('SELECT * FROM clienti WHERE id=?', (i,)); return None if x.empty else x.iloc[0]
def list_collaboratori(): return df('SELECT * FROM collaboratori ORDER BY id DESC')
def list_documenti(cliente_id=None): return df('SELECT * FROM documenti WHERE cliente_id=? ORDER BY id DESC', (cliente_id,)) if cliente_id else df('SELECT * FROM documenti ORDER BY id DESC')
def list_richieste(cliente_id=None): return df('SELECT * FROM richieste WHERE cliente_id=? ORDER BY id DESC', (cliente_id,)) if cliente_id else df('SELECT * FROM richieste ORDER BY id DESC')
def list_mail(cliente_id=None): return df('SELECT * FROM mail WHERE cliente_id=? ORDER BY id DESC', (cliente_id,)) if cliente_id else df('SELECT * FROM mail ORDER BY id DESC')
def list_valutazioni(cliente_id=None): return df('SELECT * FROM valutazioni WHERE cliente_id=? ORDER BY id DESC', (cliente_id,)) if cliente_id else df('SELECT * FROM valutazioni ORDER BY id DESC')
