from . import db 
from datetime import datetime
from sqlalchemy import Column, Integer, String, LargeBinary

class VaultEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entry_type = db.Column(db.String(20)) #file or folder
    name = db.Column(db.String(120)) #name of file/folder
    passphrase_enc = db.Column(db.Text)  # encrypted passphrase
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<VaultEntry {self.name}>'
    
