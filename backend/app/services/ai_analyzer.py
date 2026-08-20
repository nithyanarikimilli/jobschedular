import google.generativeai as genai
from app.core.config import settings
import logging
import json
import re

logger = logging.getLogger("smartqueue.analyzer")

def run_rule_based_analyzer(error_message: str, stack_trace: str) -> dict:
    """
    Fallback regex-based analyzer if Gemini API key is missing or fails.
    """
    err_text = f"{error_message} \n {stack_trace}".lower()

    # Network / Timeout patterns
    if any(p in err_text for p in ["timeout", "socket.timeout", "connection timeout", "httperror", "max retries exceeded", "connection refused"]):
        return {
            "failure_reason": "Transient Network / Timeout failure",
            "severity": "MEDIUM",
            "suggested_solution": "Retry the job. Check the external service health and confirm network access routes.",
            "is_temporary": True
        }
    
    # DB Operational patterns
    if any(p in err_text for p in ["operationalerror", "psycopg2.operationalerror", "deadlock", "lock timeout", "connection limit exceeded"]):
        return {
            "failure_reason": "Database connectivity or locking conflict",
            "severity": "MEDIUM",
            "suggested_solution": "Retry the job. Verify PostgreSQL connections count and CPU usage.",
            "is_temporary": True
        }

    # Authentication / Authorization patterns
    if any(p in err_text for p in ["unauthorized", "forbidden", "permission denied", "invalid token", "401", "403"]):
        return {
            "failure_reason": "Authentication or credentials error",
            "severity": "CRITICAL",
            "suggested_solution": "Check and rotate the API keys/passwords used in the job configuration. Do not retry without updating credentials.",
            "is_temporary": False
        }

    # Invalid arguments / coding bugs
    if any(p in err_text for p in ["valueerror", "keyerror", "typeerror", "validationerror", "jsondecodeerror", "syntaxerror"]):
        return {
            "failure_reason": "Invalid arguments or application logic validation error",
            "severity": "HIGH",
            "suggested_solution": "Verify the job payload values. Update input schema validation logic or refactor application code.",
            "is_temporary": False
        }

    # Default fallback
    return {
        "failure_reason": "General Execution Failure",
        "severity": "MEDIUM",
        "suggested_solution": "Review the full execution logs and stack trace to diagnose the issue.",
        "is_temporary": True
    }

def analyze_job_failure(error_message: str, stack_trace: str, logs: str, retry_count: int, duration: float) -> dict:
    """
    Analyzes job failures using Gemini AI, falling back to rule-based analysis if necessary.
    """
    if settings.GEMINI_API_KEY:
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
            You are an expert site reliability engineer (SRE). A background job has failed.
            Analyze the failure details and return a JSON block containing diagnostics.
            
            Error Message: {error_message}
            Stack Trace: {stack_trace}
            Execution Logs: {logs}
            Attempt Number: {retry_count + 1}
            Duration: {duration:.2f} seconds

            Your output must be a single JSON object with EXACTLY the following keys (do not include markdown syntax around JSON):
            {{
                "failure_reason": "string detailing the root cause",
                "severity": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
                "suggested_solution": "clear actionable recommendation to fix the issue",
                "is_temporary": true | false (whether the failure appears to be a transient issue that will resolve on retry)
            }}
            """
            
            response = model.generate_content(prompt)
            text = response.text.strip()
            
            # Clean possible markdown wrap
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
            else:
                data = json.loads(text)
                
            # Verify keys exist
            if all(k in data for k in ["failure_reason", "severity", "suggested_solution", "is_temporary"]):
                return data
                
        except Exception as e:
            logger.warning(f"AI Failure Analyzer via Gemini failed: {e}. Falling back to rule-based analyzer.")
            
    return run_rule_based_analyzer(error_message, stack_trace)
