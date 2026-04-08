from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import random
import string
import os
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "potluck.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS potlucks (
            group_no TEXT PRIMARY KEY,
            group_name TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_no TEXT,
            name TEXT,
            phone TEXT,
            status TEXT,
            FOREIGN KEY(group_no) REFERENCES potlucks(group_no)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_no TEXT,
            participant_id INTEGER,
            category TEXT,
            name TEXT,
            FOREIGN KEY(group_no) REFERENCES potlucks(group_no),
            FOREIGN KEY(participant_id) REFERENCES participants(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Models
class ParticpantCreate(BaseModel):
    name: str # Option to update name if same phone is used
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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    group_no = generate_group_no()
    
    # Store potluck
    cursor.execute('INSERT INTO potlucks (group_no, group_name) VALUES (?, ?)', (group_no, "New Potluck Group"))
    
    # Add creator
    cursor.execute('INSERT INTO participants (group_no, name, phone, status) VALUES (?, ?, ?, ?)', 
                   (group_no, user.name, user.phone, 'coming'))
    participant_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    return {"group_no": group_no, "participant_id": participant_id}

@app.post("/api/potlucks/{group_no}/join")
def join_potluck(group_no: str, user: ParticpantCreate):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # check if potluck exists
    cursor.execute('SELECT * FROM potlucks WHERE group_no = ?', (group_no,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Potluck not found")
        
    # Check if participant already exists by phone
    cursor.execute('SELECT id, name FROM participants WHERE group_no = ? AND phone = ?', (group_no, user.phone))
    existing = cursor.fetchone()
    
    if existing:
        participant_id = existing[0]
        if existing[1] != user.name:
             cursor.execute('UPDATE participants SET name = ? WHERE id = ?', (user.name, participant_id))
    else:
        cursor.execute('INSERT INTO participants (group_no, name, phone, status) VALUES (?, ?, ?, ?)', 
                       (group_no, user.name, user.phone, 'coming'))
        participant_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    return {"participant_id": participant_id}

@app.get("/api/potlucks/{group_no}")
def get_dashboard(group_no: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT group_no, group_name FROM potlucks WHERE group_no = ?', (group_no,))
    potluck = cursor.fetchone()
    if not potluck:
        conn.close()
        raise HTTPException(status_code=404, detail="Potluck not found")
        
    cursor.execute('SELECT id, name, phone, status FROM participants WHERE group_no = ?', (group_no,))
    participants = [dict(row) for row in cursor.fetchall()]
    
    # Needs participant_id so frontend can identify ownership
    cursor.execute('SELECT i.id, i.category, i.name as item_name, i.participant_id, p.name as participant_name FROM items i JOIN participants p ON i.participant_id = p.id WHERE i.group_no = ?', (group_no,))
    items = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {
        "group_name": potluck["group_name"],
        "participants": participants, 
        "items": items
    }

@app.put("/api/participants/{participant_id}/status")
def update_status(participant_id: int, update: StatusUpdate):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE participants SET status = ? WHERE id = ?', (update.status, participant_id))
    conn.commit()
    conn.close()
    return {"success": True}

@app.post("/api/potlucks/{group_no}/items")
def add_item(group_no: str, item: ItemCreate):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO items (group_no, participant_id, category, name) VALUES (?, ?, ?, ?)',
                   (group_no, item.participant_id, item.category, item.name))
    item_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"id": item_id}

@app.put("/api/items/{item_id}")
def update_item(item_id: int, item: ItemUpdate):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE items SET name = ? WHERE id = ?', (item.name, item_id))
    conn.commit()
    conn.close()
    return {"success": True}

@app.put("/api/potlucks/{group_no}/name")
def update_group_name(group_no: str, update: PotluckUpdate):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE potlucks SET group_name = ? WHERE group_no = ?', (update.group_name, group_no))
    conn.commit()
    conn.close()
    return {"success": True}

# Mount static files for frontend
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")
