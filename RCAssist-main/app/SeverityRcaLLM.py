from dotenv import load_dotenv
from groq import Groq
import re
import os
load_dotenv()
groq = Groq(api_key=os.environ.get("GROQ_API_KEY"))
def classify_severity_with_llm(log_message):
    prompt = f'''You are an expert log analysis tool. Classify the severity of the following log message.
The only available severities are: Critical, High, Medium, Low, Informational.
Your response MUST be a single word from that list and nothing else.

Here are some examples of how to classify logs:
- Log: "IP 192.168.133.114 blocked due to potential attack" -> Severity: Critical
- Log: "System crashed due to kernel panic" -> Severity: Critical
- Log: "Failed to connect to database master node" -> Severity: High
- Log: "API returned 404 not found error" -> Severity: Medium
- Log: "User login successful" -> Severity: Informational

Classify This Log:
- Log: "{log_message}"
- Severity:'''
    try:
        chat_completion = groq.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.0,
            max_tokens=10
        )
        severity = chat_completion.choices[0].message.content.strip().replace(".", "")
        return severity
    except Exception as e:
        print(f"Error getting severity from LLM: {e}")
        return "Unclassified"

def classify_with_llm(log_msg):
    prompt = f'''Classify the log message into one of these categories:
    Workflow Error, Deprecation Warning.
    If you can't figure out a category, use "Unclassified".
    Put the category inside <category> </category> tags.
    Log message: {log_msg}'''
    chat_completion = groq.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.1-8b-instant",
        temperature=0.5
    )
    content = chat_completion.choices[0].message.content
    match = re.search(r'<category>(.*)</category>', content, flags=re.DOTALL)
    if match:
        return match.group(1).strip()
    return "Unclassified"

def get_root_cause_and_action(log_message, error_type):
    try:
        chat_completion = groq.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at analyzing application logs. Based on the log message and its error type, provide a likely root cause and a concrete recommended action for a developer to take."
                },
                {
                    "role": "user",
                    "content": f"Log Message: \"{log_message}\"\nError Type: \"{error_type}\"\n\nProvide the 'Likely Root Cause' and a 'Recommended Action'."
                }
            ],
            model="llama-3.1-8b-instant",
        )
        response_text = chat_completion.choices[0].message.content
        root_cause = "Could not determine."
        action = "Manual investigation required."
        if "Likely Root Cause:" in response_text:
            root_cause = response_text.split("Likely Root Cause:")[1].split("Recommended Action:")[0].strip()
        if "Recommended Action:" in response_text:
            action = response_text.split("Recommended Action:")[1].strip()
        return root_cause, action
    except Exception as e:
        print(f"Error getting RCA from LLM: {e}")
        return "LLM analysis failed.", "Manual investigation required."