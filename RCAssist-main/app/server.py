from fastapi import (FastAPI, UploadFile, File, WebSocket, Request, HTTPException)
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import pandas as pd
from io import StringIO
from app.BaseClassifier import classify_csv
from app.KafkaSimulator import kafka_consumer_simulator

load_dotenv()
app = FastAPI(title="RCAssist API")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        await kafka_consumer_simulator(websocket)
    except Exception as e:
        print(f"WebSocket Error: {e}")
    finally:
        print("WebSocket client disconnected.")
@app.post("/classify_csv/")
async def classify_csv_endpoint(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV.")
    contents = await file.read()
    string_io_buffer = StringIO(contents.decode('utf-8'))
    df = pd.read_csv(string_io_buffer)
    result_df = await classify_csv(df)
    output_buffer = StringIO()
    result_df.to_csv(output_buffer, index=False)
    output_buffer.seek(0)
    return StreamingResponse(
        output_buffer,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=result.csv"}
    )