import re

def classify_with_regex(log_msg):
    http_match = re.search(r'HTTP/\d\.\d\"?.*\s(\d{3})', log_msg, re.IGNORECASE)
    if http_match:
        httpStatus = int(http_match.group(1))
        if httpStatus >= 400:
            return "HTTP Error"
        else:
            return "HTTP Status"
    failure_pattern = r'\b(upload|backup|update|cleanup|reboot|generation).*\b(fail|aborted|error)'
    if re.search(failure_pattern, log_msg, re.IGNORECASE):
        return "Operation Failure"
    success_pattern = r'\b(upload|backup|updat|clean|reboot).*\b(success|complet)'
    if re.search(success_pattern, log_msg, re.IGNORECASE):
        return "System Notification"
    other_patterns = {
        'Security Alert': r'\b(failed login|brute force|unauthorized|attack|blocked ip|sql injection|xss|escalation detected)\b',
        'System Crash': r'\b(crash|fatal error|kernel panic|stack trace|segmentation fault)\b',
        'Database Error': r'\b(database error|db connection failed|query failed|deadlock detected)\b',
        'Resource Usage': r'\b(memory limit|disk limit|cpu usage)\b',
        'User Action': r'\b(logged in|logged out|session timed out|user created|account created)\b',
    }
    for label, pattern in other_patterns.items():
        if re.search(pattern, log_msg, re.IGNORECASE):
            return label

    return None