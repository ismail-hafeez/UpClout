import os
import sys

# Add project root to path so we can import from src.chatbot.config
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, _project_root)

# Use the SAME config as the CLI model — this is what makes it work well
from src.chatbot.config.groq_config import vector_store, instruction, llm


# ── System prompt with user context (layered on top of the CLI instruction) ──
SYSTEM_PROMPT_TEMPLATE = """
{instruction}

ABOUT THE USER YOU ARE SPEAKING WITH:
- Username: @{username}
- Account Type: {user_type}
- Niche/Category: {niche}
- Location: {location}
- Followers: {followers}
- Following: {following}

You already know this user. Do NOT ask them to introduce themselves. Greet them by name and reference their niche when relevant.
Use occasional owl-related micro-expressions (e.g., "Hoot!", "Wise choice").
"""


def call_model(
    user_message: str,
    conversation_history: list[dict],
    user_context: dict
) -> str:
    """
    Performs RAG retrieval then calls the LLM.
    Mirrors the CLI model's approach exactly — simple similarity search
    on the raw user message, same instruction prompt, same LLM config.

    Args:
        user_message: The current user query
        conversation_history: Full conversation from MongoDB [{role, content}, ...]
        user_context: Dict with username, user_type, niche, location, followers, following

    Returns:
        The AI response text
    """
    # 1. Similarity search — EXACTLY like the CLI model: raw user_input, k=5
    results = vector_store.similarity_search(user_message, k=5)

    context = ""
    for idx, doc in enumerate(results, 1):
        username = doc.metadata.get("username", f"Profile {idx}")
        context += f"[@{username}]: {doc.page_content}\n"

    # 2. Build conversation history string
    history_lines = []
    for m in conversation_history:
        role = "User" if m["role"] == "user" else "Owly"
        history_lines.append(f"{role}: {m['content']}")

    # 3. Build system prompt with user context layered on CLI instruction
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        instruction=instruction,
        username=user_context.get("username", "Unknown"),
        user_type=user_context.get("user_type", "Unknown"),
        niche=user_context.get("niche", "Unknown"),
        location=user_context.get("location", "Unknown"),
        followers=user_context.get("followers", "Unknown"),
        following=user_context.get("following", "Unknown"),
    )

    # 4. Compose prompt — same structure as CLI model
    prompt = (
        f"{system_prompt}\n\n"
        f"Conversation so far:\n"
        + "\n".join(history_lines)
        + f"\n\nContext from Database:\n{context}\n\nUser question: {user_message}\n\nAnswer:"
    )

    # 5. Call the LLM
    response = llm.invoke(prompt)
    answer = response.content if hasattr(response, "content") else str(response)

    return answer

