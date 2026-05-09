import json
import logging
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import anthropic

from .tools import TOOLS
from .agent import execute_tool
from .guardrails import validate_message

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are CivicLens, an AI assistant for exploring public safety and civic incident data in New York City.

You help users query real NYC incident data — 311 complaints, crime reports, MTA alerts — using plain English.
When users ask questions, use your tools to fetch real data and provide accurate, factual answers.

Guidelines:
- Always use tools to get real data before answering factual questions
- For complex requests, chain multiple tools (search → aggregate → summarize)
- Present results clearly: counts, trends, notable patterns
- If no data is found, say so — don't invent incidents
- Keep responses concise and actionable
- Responsible AI: don't speculate about individuals, don't amplify fear"""

MAX_TOOL_ROUNDS = 5


class ChatView(APIView):
    """Single-turn: user message → Claude → tool calls → final answer."""

    def post(self, request):
        message = request.data.get("message", "")
        history = request.data.get("history", [])

        valid, error = validate_message(message)
        if not valid:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        messages = list(history) + [{"role": "user", "content": message}]
        tool_calls_log = []

        for _ in range(MAX_TOOL_ROUNDS):
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )

            if response.stop_reason == "end_turn":
                text = next((b.text for b in response.content if hasattr(b, "text")), "")
                return Response({"response": text, "tool_calls": tool_calls_log})

            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})
                tool_results = []

                for block in response.content:
                    if block.type == "tool_use":
                        logger.info("Tool call: %s(%s)", block.name, block.input)
                        result = execute_tool(block.name, block.input)
                        tool_calls_log.append({"tool": block.name, "input": block.input, "result_summary": str(result)[:200]})
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result),
                        })

                messages.append({"role": "user", "content": tool_results})

        return Response({"response": "Reached maximum reasoning steps.", "tool_calls": tool_calls_log})


class AgentView(APIView):
    """Agentic mode: Claude autonomously chains tools for complex multi-step queries."""

    def post(self, request):
        task = request.data.get("task", "")
        valid, error = validate_message(task)
        if not valid:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        agent_system = SYSTEM_PROMPT + "\n\nYou are in AGENT MODE. Break complex tasks into steps, use multiple tools in sequence, and produce a comprehensive final report."

        messages = [{"role": "user", "content": task}]
        tool_calls_log = []

        for round_num in range(MAX_TOOL_ROUNDS):
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=agent_system,
                tools=TOOLS,
                messages=messages,
            )

            if response.stop_reason == "end_turn":
                text = next((b.text for b in response.content if hasattr(b, "text")), "")
                return Response({"report": text, "steps": round_num + 1, "tool_calls": tool_calls_log})

            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})
                tool_results = []

                for block in response.content:
                    if block.type == "tool_use":
                        result = execute_tool(block.name, block.input)
                        tool_calls_log.append({"step": round_num + 1, "tool": block.name, "input": block.input})
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result),
                        })

                messages.append({"role": "user", "content": tool_results})

        return Response({"report": "Agent reached step limit.", "tool_calls": tool_calls_log})
