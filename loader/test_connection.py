import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

client = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=8000)
print(client.admin.command("ping"))
print("Connected to MongoDB Atlas")
