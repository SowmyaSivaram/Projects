import asyncio
import random
import json
from .BaseClassifier import classify_all_with_rca_async

SAMPLE_LOGS = [
    ("ModernHR", "GET /v2/3454/servers/detail HTTP/1.1 RCODE 404 len: 1583 time: 0.1878400"),
    ("BillingSystem", "System crashed due to drivers errors when restarting the server"),
    ("LegacyCRM", "The 'BulkEmailSender' feature is no longer supported. Use 'EmailCampaignManager' instead."),
    ("BillingSystem", "Denied access attempt on restricted account Account2682"),
    ("ModernHR", "Multiple bad login attempts detected on user 8538 account"),
    ("LegacyCRM", "Case escalation for ticket ID 7324 failed because the assigned support agent is no longer active."),
    ("ModernCRM", "IP 192.168.133.114 blocked due to potential attack")]

async def kafka_producer_simulator():
    while True:
        await asyncio.sleep(random.uniform(1, 5))

async def kafka_consumer_simulator(websocket):
    for source, log_message in SAMPLE_LOGS:
        await asyncio.sleep(random.uniform(1, 2))
        analysis_result = await classify_all_with_rca_async(log_message=log_message, source=source)
        await websocket.send_text(json.dumps({
            "log_message": log_message,
            "analysis": analysis_result,
        }))
    await asyncio.sleep(1)
    await websocket.send_text(json.dumps({"status": "complete"}))