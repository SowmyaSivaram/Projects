import pandas as pd
import asyncio
from .RegexClassifier import classify_with_regex
from .BertClassifier import classify_with_bert
from .SeverityRcaLLM import (
    classify_with_llm,
    get_root_cause_and_action,
    classify_severity_with_llm
)

async def classify_all_with_rca_async(log_message: str, source: str):
    return await asyncio.to_thread(classify_all_with_rca, [(source, log_message)])

def classify_all_with_rca(logs):
    results = []
    non_error_labels = [
        "User Action", "System Notification", "HTTP Status",
        "Resource Usage", "Deprecation Warning"
    ]
    for source, log_msg in logs:
        target_label = classify_log(source, log_msg)
        analysis = {
            "error_type": target_label,
            "severity": "N/A",
            "suggested_root_cause": "N/A",
            "suggested_action": "N/A"
        }
        if target_label not in non_error_labels:
            analysis["severity"] = classify_severity_with_llm(log_msg)
            root_cause, action = get_root_cause_and_action(log_msg, target_label)
            analysis["suggested_root_cause"] = root_cause
            analysis["suggested_action"] = action
        results.append(analysis)
    if len(results) == 1:
        return results[0]
    return results

def classify_log(source, log_msg):
    if source == "LegacyCRM":
        label = classify_with_llm(log_msg)
    else:
        label = classify_with_regex(log_msg)
        if not label:
            label = classify_with_bert(log_msg)
    return label

async def classify_csv(df: pd.DataFrame):
    tasks = [classify_all_with_rca_async(log, source) for source, log in zip(df["source"], df["log_message"])]
    classification_results = await asyncio.gather(*tasks)
    results_df = pd.DataFrame(classification_results)
    output_df = pd.concat([df, results_df], axis=1)
    return output_df