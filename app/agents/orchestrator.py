import json
from openai import OpenAI
from app.agents.email_agent import handle_list_emails, handle_send_email
from app.agents.calendar_agent import handle_calendar
from app.memory.db import get_recent_interactions, save_interaction
from app.tools.system import open_url, search_google, open_youtube, open_app, control_music

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
    {
        "type": "function",
        "function": {
            "name": "open_url",
            "description": "Open any URL or website in the default browser.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to open."},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search Google for a query and open results in the browser.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query."},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_youtube",
            "description": "Open YouTube, optionally searching for a video or topic.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Optional search query on YouTube."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": "Launch a desktop application by name (e.g. Spotify, VS Code, Slack, Chrome).",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "The application name to open."},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "control_music",
            "description": "Control music playback — play, pause, next track, previous track, or toggle on Spotify or Apple Music.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["play", "pause", "next", "previous", "toggle"],
                        "description": "The playback action.",
                    },
                    "service": {
                        "type": "string",
                        "enum": ["spotify", "apple_music"],
                        "description": "Music service to control. Defaults to spotify.",
                    },
                },
                "required": ["action"],
            },
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

FOLLOW-UP & CLARIFICATION RULES:
- If a request is ambiguous or missing key details, ask a short clarifying question BEFORE calling any tool.
  Examples:
  - "Play music" → ask "What would you like to listen to, and on Spotify or Apple Music?"
  - "Send an email" → ask "Who should I send it to, and what's the message?"
  - "Open YouTube" → ask "Would you like me to search for something specific on YouTube?"
  - "Search for something" → ask "What would you like me to search for?"
- Keep follow-up questions short, friendly, and to the point (one question at a time).
- Once you have enough info, proceed with the tool call without asking again.
- Remember context from earlier in the conversation — don't ask for info the user already provided.
"""


def _build_messages(text: str, session_id: str = "default") -> list[dict]:
    history = get_recent_interactions(limit=10, session_id=session_id)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for item in history:
        messages.append({"role": "user", "content": item["user_input"]})
        messages.append({"role": "assistant", "content": item["response"]})
    messages.append({"role": "user", "content": text})
    return messages


async def handle_user_input(text: str, session_id: str = "default") -> dict:
    messages = _build_messages(text, session_id=session_id)

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
            save_interaction(text, f"[awaiting confirmation] {fn_name}", intent=fn_name, session_id=session_id)
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
        elif fn_name == "open_url":
            result = open_url(fn_args["url"])
        elif fn_name == "search_web":
            result = search_google(fn_args["query"])
        elif fn_name == "open_youtube":
            result = open_youtube(fn_args.get("query"))
        elif fn_name == "open_app":
            result = open_app(fn_args["name"])
        elif fn_name == "control_music":
            result = control_music(fn_args["action"], fn_args.get("service", "spotify"))
        else:
            result = "Unknown tool called."

        save_interaction(text, result, intent=fn_name, session_id=session_id)
        return {"status": "ok", "response": result}

    text_response = choice.message.content or "I'm here to help!"
    save_interaction(text, text_response, intent="general", session_id=session_id)
    return {"status": "ok", "response": text_response}


async def execute_confirmed_action(action: str, args: dict, session_id: str = "default") -> dict:
    if action == "send_email":
        result = await handle_send_email(args["to"], args["subject"], args["body"])
        save_interaction(
            f"[confirmed] send_email to {args['to']}",
            result,
            intent="send_email",
            session_id=session_id,
        )
        return {"status": "ok", "response": result}
    return {"status": "error", "response": "Unknown action."}