import json
from openai import OpenAI
from app.agents.email_agent import handle_list_emails, handle_send_email
from app.agents.calendar_agent import handle_calendar
from app.memory.db import get_recent_interactions, save_interaction

client = OpenAI()

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_emails",
            "description": "Fetch and summarize the user's latest inbox emails.",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "integer",
                        "description": "Number of emails to fetch (default 5).",
                        "default": 5,
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send an email on the user's behalf. Requires explicit confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email address."},
                    "subject": {"type": "string", "description": "Email subject line."},
                    "body": {"type": "string", "description": "Email body text."},
                },
                "required": ["to", "subject", "body"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_calendar",
            "description": "Get today's calendar events for the user.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]

REQUIRES_CONFIRMATION = {"send_email"}

SYSTEM_PROMPT = """You are Pankaj Pandey's personal AI assistant (JARVIS). You're helpful, friendly, and knowledgeable about Pankaj's professional background. You can also read emails, send emails, and check calendar events using the provided tools. For send_email, always call the tool so the user can confirm before sending.

ABOUT PANKAJ PANDEY:
A dedicated Full Stack Developer with 3+ years of professional experience in designing, developing, and deploying scalable digital solutions. Proficient in crafting seamless user experiences and robust backend systems for diverse applications.

EDUCATION:
1. Bachelor of Technology in Computer Science - RGPV University Bhopal (2018-2022), CGPA: 8.59
2. High Secondary - Blooms Academy (2017-2018), 61% GPA
3. High School - Blooms Academy (2015-2016), 71% GPA

PROFESSIONAL EXPERIENCE:
1. Software Engineer Full Stack at Optimeleon AI Pvt. Limited (Mar 2025 - Present)
   - Built AI/LLM-integrated web apps, web scraping systems (reduced manual effort by 75%), background job processing (improved tracking by 100%), user dashboards (increased engagement by 30%)
   - Tech: Next.js, React, TypeScript, Python, PostgreSQL, Docker, Kubernetes, Azure, Redis, Langchain, OpenAI API, Playwright, ClickHouse

2. Software Engineer Full Stack at Wisflux Private Limited (Sep 2022 - Feb 2025)
   - Led full-stack apps, built DSP/SSP platforms for DOOH advertising, micro-services architecture
   - Tech: Angular, React, Node.js, TypeScript, Nest.js, PostgreSQL, Docker, Kubernetes, AWS

3. Software Engineer Intern at UPCRED (Oct 2021 - Dec 2021) - Influencer Marketing, React, animations
4. Full Stack Developer Intern at SkyHype (Jun 2021 - Sep 2021) - Web apps, bug fixes, React

TECHNICAL SKILLS:
- Frontend: React (90%), Next.js (85%), TypeScript (85%), Tailwind CSS (90%), HTML/CSS (95%), JavaScript (90%)
- Backend: Node.js (85%), Express (85%), MongoDB (80%), PostgreSQL (75%), REST APIs (90%), GraphQL (75%)
- DevOps: Git (90%), Docker (80%), AWS (75%), Linux (85%), CI/CD (80%), Jest (85%)
- Additional: AWS/Azure/GCP, Kubernetes, ClickHouse, Langchain, OpenAI API, Inngest, Playwright, Prisma, Sequelize, PostHog

FEATURED PROJECTS:
1. Marketing SaaS Platform - Next.js 14, Tailwind, Framer Motion | https://marketing-saas.pankajpandey.dev
2. E-commerce Dashboard - React, Node.js, MongoDB, Express, Redux | full-stack admin with real-time analytics
3. Scalable Chat Application - WebSocket, AI, React, Socket.io | real-time chat with smart AI responses
4. Video Transcoder - React, Node.js, Socket.io | video processing and optimization

FORMATTING GUIDELINES:
- Use **bold** for important terms, technologies, companies, and achievements
- Use bullet points for listing multiple items
- Highlight metrics in bold (e.g., **75% reduction**, **30% increase**)
- Keep responses concise but informative (2-4 sentences for simple questions)
- Be conversational, enthusiastic, and professional
"""


def _build_messages(text: str) -> list[dict]:
    history = get_recent_interactions(limit=6)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for item in history:
        messages.append({"role": "user", "content": item["user_input"]})
        messages.append({"role": "assistant", "content": item["response"]})
    messages.append({"role": "user", "content": text})
    return messages


async def handle_user_input(text: str) -> dict:
    messages = _build_messages(text)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )

    choice = response.choices[0]

    if choice.finish_reason == "tool_calls":
        tool_call = choice.message.tool_calls[0]
        fn_name = tool_call.function.name
        fn_args = json.loads(tool_call.function.arguments)

        if fn_name in REQUIRES_CONFIRMATION:
            return {
                "status": "needs_confirmation",
                "action": fn_name,
                "args": fn_args,
                "message": (
                    f"I'm about to send an email to {fn_args.get('to')} "
                    f"with subject \"{fn_args.get('subject')}\". "
                    "Reply with /confirm to proceed or /cancel to abort."
                ),
            }

        if fn_name == "list_emails":
            result = await handle_list_emails(fn_args.get("max_results", 5))
        elif fn_name == "get_calendar":
            result = await handle_calendar(text)
        else:
            result = "Unknown tool called."

        save_interaction(text, result, intent=fn_name)
        return {"status": "ok", "response": result}

    text_response = choice.message.content or "I can help with email and calendar."
    save_interaction(text, text_response, intent="general")
    return {"status": "ok", "response": text_response}


async def execute_confirmed_action(action: str, args: dict) -> dict:
    if action == "send_email":
        result = await handle_send_email(args["to"], args["subject"], args["body"])
        save_interaction(
            f"[confirmed] send_email to {args['to']}",
            result,
            intent="send_email",
        )
        return {"status": "ok", "response": result}
    return {"status": "error", "response": "Unknown action."}