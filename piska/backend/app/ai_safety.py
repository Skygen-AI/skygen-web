from __future__ import annotations

import re
from typing import Dict, Any, List, Tuple
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SafetyPolicy:
    """AI-powered safety analysis for task actions"""

    # Dangerous patterns
    CRITICAL_PATTERNS = [
        r'rm\s+-rf\s+/',
        r'format\s+[c-z]:',
        r'del\s+/[qsf]',
        r'shutdown\s+/[srf]',
        r'mkfs\.',
        r'dd\s+if=/dev/zero',
    ]

    HIGH_RISK_PATTERNS = [
        r'sudo\s+rm',
        r'chmod\s+777',
        r'curl.*\|\s*sh',
        r'wget.*\|\s*bash',
        r'regedit\s+/s',
        r'net\s+user.*password',
    ]

    SENSITIVE_PATHS = [
        '/etc/passwd', '/etc/shadow', '/boot/',
        'C:\\Windows\\System32', 'C:\\Program Files',
        '/System/', '/Library/Keychains/',
    ]

    @classmethod
    def analyze_actions(cls, actions: List[Dict[str, Any]]) -> Tuple[RiskLevel, List[str]]:
        """Analyze list of actions and return risk level + reasons"""
        max_risk = RiskLevel.LOW
        reasons = []

        for action in actions:
            risk, action_reasons = cls._analyze_single_action(action)
            if cls._risk_priority(risk) > cls._risk_priority(max_risk):
                max_risk = risk
            reasons.extend(action_reasons)

        return max_risk, reasons

    @classmethod
    def _analyze_single_action(cls, action: Dict[str, Any]) -> Tuple[RiskLevel, List[str]]:
        action_type = action.get('type', '')
        params = action.get('params', {})
        reasons = []

        # File operations
        if action_type == 'file_delete':
            path = params.get('path', '')
            if any(sensitive in path for sensitive in cls.SENSITIVE_PATHS):
                return RiskLevel.CRITICAL, [f"Deleting sensitive path: {path}"]
            if path.startswith('/') or path.endswith('*'):
                return RiskLevel.HIGH, [f"Dangerous delete pattern: {path}"]

        # Shell commands
        elif action_type == 'shell':
            command = params.get('command', '')

            # Check critical patterns
            for pattern in cls.CRITICAL_PATTERNS:
                if re.search(pattern, command, re.IGNORECASE):
                    return RiskLevel.CRITICAL, [f"Critical command detected: {command}"]

            # Check high risk patterns
            for pattern in cls.HIGH_RISK_PATTERNS:
                if re.search(pattern, command, re.IGNORECASE):
                    return RiskLevel.HIGH, [f"High-risk command: {command}"]

            # Network operations with pipes
            if '|' in command and ('curl' in command or 'wget' in command):
                return RiskLevel.HIGH, ["Remote code execution via pipe"]

            # Default policy: any shell command requires approval as a precaution
            return RiskLevel.HIGH, ["Shell command requires approval"]

        # Network operations
        elif action_type == 'network_request':
            url = params.get('url', '')
            if any(domain in url for domain in ['pastebin.com', 'bit.ly', 'tinyurl.com']):
                reasons.append("Suspicious URL shortener/paste site")
                return RiskLevel.MEDIUM, reasons

        return RiskLevel.LOW, reasons

    @staticmethod
    def _risk_priority(risk: RiskLevel) -> int:
        return {"low": 1, "medium": 2, "high": 3, "critical": 4}[risk.value]

    @classmethod
    def requires_approval(cls, risk: RiskLevel) -> bool:
        """Determine if risk level requires manual approval"""
        return risk in (RiskLevel.HIGH, RiskLevel.CRITICAL)

    @classmethod
    def should_block(cls, risk: RiskLevel) -> bool:
        """Determine if action should be blocked entirely"""
        return risk == RiskLevel.CRITICAL
