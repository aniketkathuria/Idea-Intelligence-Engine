import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.db import engine, Base
from core import models

Base.metadata.create_all(bind=engine)

print("Database tables created successfully!")