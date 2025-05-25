import uvicorn
from main import app  # Assuming main.py is in the same directory

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)