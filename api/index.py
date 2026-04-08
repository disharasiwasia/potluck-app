from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
import string
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi.responses import HTMLResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    database_url = os.environ.get("POSTGRES_URL")
    if not database_url:
        raise HTTPException(status_code=500, detail="Database URL is not configured. Please link a Postgres database in Vercel.")
    conn = psycopg2.connect(database_url)
    return conn

def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS potlucks (
                group_no TEXT PRIMARY KEY,
                group_name TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS participants (
                id SERIAL PRIMARY KEY,
                group_no TEXT REFERENCES potlucks(group_no),
                name TEXT,
                phone TEXT,
                status TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id SERIAL PRIMARY KEY,
                group_no TEXT REFERENCES potlucks(group_no),
                participant_id INTEGER REFERENCES participants(id),
                category TEXT,
                name TEXT
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        print("Database init skipped or failed:", e)

# On cold start we ensure tables exist
init_db()

# Models
class ParticpantCreate(BaseModel):
    name: str 
    phone: str

class StatusUpdate(BaseModel):
    status: str

class ItemCreate(BaseModel):
    participant_id: int
    category: str
    name: str

class ItemUpdate(BaseModel):
    name: str

class PotluckUpdate(BaseModel):
    group_name: str

def generate_group_no():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

@app.post("/api/potlucks")
def create_potluck(user: ParticpantCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    group_no = generate_group_no()
    
    cursor.execute('INSERT INTO potlucks (group_no, group_name) VALUES (%s, %s)', (group_no, "New Potluck Group"))
    cursor.execute('INSERT INTO participants (group_no, name, phone, status) VALUES (%s, %s, %s, %s) RETURNING id', 
                   (group_no, user.name, user.phone, 'coming'))
    participant_id = cursor.fetchone()[0]
    
    conn.commit()
    conn.close()
    return {"group_no": group_no, "participant_id": participant_id}

@app.post("/api/potlucks/{group_no}/join")
def join_potluck(group_no: str, user: ParticpantCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM potlucks WHERE group_no = %s', (group_no,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Potluck not found")
        
    cursor.execute('SELECT id, name FROM participants WHERE group_no = %s AND phone = %s', (group_no, user.phone))
    existing = cursor.fetchone()
    
    if existing:
        participant_id = existing[0]
        if existing[1] != user.name:
             cursor.execute('UPDATE participants SET name = %s WHERE id = %s', (user.name, participant_id))
    else:
        cursor.execute('INSERT INTO participants (group_no, name, phone, status) VALUES (%s, %s, %s, %s) RETURNING id', 
                       (group_no, user.name, user.phone, 'coming'))
        participant_id = cursor.fetchone()[0]
    
    conn.commit()
    conn.close()
    return {"participant_id": participant_id}

@app.get("/api/potlucks/{group_no}")
def get_dashboard(group_no: str):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('SELECT group_no, group_name FROM potlucks WHERE group_no = %s', (group_no,))
    potluck = cursor.fetchone()
    if not potluck:
        conn.close()
        raise HTTPException(status_code=404, detail="Potluck not found")
        
    cursor.execute('SELECT id, name, phone, status FROM participants WHERE group_no = %s', (group_no,))
    participants = list(cursor.fetchall())
    
    cursor.execute('SELECT i.id, i.category, i.name as item_name, i.participant_id, p.name as participant_name FROM items i JOIN participants p ON i.participant_id = p.id WHERE i.group_no = %s', (group_no,))
    items = list(cursor.fetchall())
    
    conn.close()
    return {
        "group_name": potluck["group_name"],
        "participants": participants, 
        "items": items
    }

@app.put("/api/participants/{participant_id}/status")
def update_status(participant_id: int, update: StatusUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE participants SET status = %s WHERE id = %s', (update.status, participant_id))
    conn.commit()
    conn.close()
    return {"success": True}

@app.post("/api/potlucks/{group_no}/items")
def add_item(group_no: str, item: ItemCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO items (group_no, participant_id, category, name) VALUES (%s, %s, %s, %s) RETURNING id',
                   (group_no, item.participant_id, item.category, item.name))
    item_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return {"id": item_id}

@app.put("/api/items/{item_id}")
def update_item(item_id: int, item: ItemUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE items SET name = %s WHERE id = %s', (item.name, item_id))
    conn.commit()
    conn.close()
    return {"success": True}

@app.put("/api/potlucks/{group_no}/name")
def update_group_name(group_no: str, update: PotluckUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE potlucks SET group_name = %s WHERE group_no = %s', (update.group_name, group_no))
    conn.commit()
    conn.close()
    return {"success": True}
