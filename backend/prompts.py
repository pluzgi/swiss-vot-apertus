"""
Prompt Templates for Swiss Voting Assistant
System prompts and context formatting for Apertus LLM
"""

from typing import List, Dict

# System prompt for Swiss voting assistant
SYSTEM_PROMPT_DE = """Du bist ein hilfreicher Assistent für Schweizer Volksabstimmungen.

Deine Aufgabe:
- Informiere objektiv über anstehende Volksinitiativen
- Erkläre Abstimmungsinhalte verständlich
- Präsentiere Argumente von beiden Seiten (Ja/Nein)
- Zitiere offizielle Quellen und Abstimmungsbüchlein
- Bleibe neutral und sachlich

Wichtig:
- Gib keine persönliche Meinung oder Abstimmungsempfehlung ab
- Kennzeichne klar, welche Informationen aus offiziellen Quellen stammen
- Bei Unsicherheit: Verweise auf die offizielle Abstimmungsbroschüre
- Antworte auf Deutsch, Französisch oder Italienisch, je nach Anfrage
"""

SYSTEM_PROMPT_FR = """Tu es un assistant utile pour les votations populaires suisses.

Ta tâche:
- Informer objectivement sur les initiatives populaires à venir
- Expliquer le contenu des votations de manière compréhensible
- Présenter les arguments des deux côtés (Oui/Non)
- Citer les sources officielles et les brochures de vote
- Rester neutre et factuel

Important:
- Ne donne pas d'opinion personnelle ou de recommandation de vote
- Indique clairement quelles informations proviennent de sources officielles
- En cas de doute: référer à la brochure officielle de vote
- Réponds en allemand, français ou italien selon la demande
"""

SYSTEM_PROMPT_IT = """Sei un assistente utile per le votazioni popolari svizzere.

Il tuo compito:
- Informare obiettivamente sulle iniziative popolari in arrivo
- Spiegare il contenuto delle votazioni in modo comprensibile
- Presentare gli argomenti di entrambe le parti (Sì/No)
- Citare fonti ufficiali e opuscoli di voto
- Rimanere neutrale e fattuale

Importante:
- Non dare opinioni personali o raccomandazioni di voto
- Indicare chiaramente quali informazioni provengono da fonti ufficiali
- In caso di dubbio: fare riferimento all'opuscolo ufficiale di voto
- Rispondi in tedesco, francese o italiano a seconda della richiesta
"""

# Language-specific system prompts
SYSTEM_PROMPTS = {
    "de": SYSTEM_PROMPT_DE,
    "fr": SYSTEM_PROMPT_FR,
    "it": SYSTEM_PROMPT_IT
}


def get_system_prompt(language: str = "de") -> str:
    """
    Get system prompt for specified language

    Args:
        language: Language code (de, fr, it)

    Returns:
        System prompt string
    """
    return SYSTEM_PROMPTS.get(language, SYSTEM_PROMPT_DE)


def format_rag_context(
    contexts: List[Dict],
    initiative_metadata: Dict[str, Dict]
) -> str:
    """
    Format RAG contexts and metadata into a prompt

    Args:
        contexts: List of retrieved context dicts
        initiative_metadata: Initiative metadata by vote_id

    Returns:
        Formatted context string
    """
    if not contexts:
        return ""

    parts = ["**Relevante Informationen aus den offiziellen Abstimmungsbüchlein:**\n"]

    # Group by initiative
    by_initiative = {}
    for ctx in contexts:
        vote_id = ctx["metadata"]["vote_id"]
        if vote_id not in by_initiative:
            by_initiative[vote_id] = []
        by_initiative[vote_id].append(ctx)

    # Format each initiative's context
    for vote_id, chunks in by_initiative.items():
        metadata = initiative_metadata.get(vote_id, {})

        # Initiative header
        title = metadata.get("title", chunks[0]["metadata"].get("initiative_title", vote_id))
        date = metadata.get("date", "")
        parts.append(f"\n### Initiative {vote_id}: {title}")

        if date:
            parts.append(f"**Abstimmungsdatum:** {date}")

        # Add context chunks
        parts.append("")
        for chunk in chunks:
            parts.append(chunk["text"])
            parts.append("")

        # Add metadata if available
        if metadata:
            if metadata.get("position_bundesrat"):
                parts.append(f"**Position Bundesrat:** {metadata['position_bundesrat']}")

            if metadata.get("parteiparolen"):
                parts.append("**Parteiparolen:**")
                for parole in metadata["parteiparolen"][:5]:  # Limit to first 5
                    parts.append(f"  - {parole}")

            if metadata.get("pdf_url"):
                parts.append(f"\n**Quelle:** [Offizielles Abstimmungsbüchlein]({metadata['pdf_url']})")

        parts.append("\n---\n")

    return "\n".join(parts)


def create_chat_prompt(
    user_query: str,
    rag_result: Dict = None,
    language: str = "de"
) -> List[Dict[str, str]]:
    """
    Create complete chat prompt with RAG context

    Args:
        user_query: User's question
        rag_result: RAG pipeline result (optional)
        language: Language code

    Returns:
        List of message dicts for Apertus API
    """
    messages = []

    # System prompt
    system_prompt = get_system_prompt(language)
    messages.append({
        "role": "system",
        "content": system_prompt
    })

    # User message with context
    if rag_result and rag_result.get("contexts"):
        context = format_rag_context(
            rag_result["contexts"],
            rag_result.get("initiative_metadata", {})
        )
        user_content = f"{context}\n\n---\n\n**Frage:** {user_query}"
    else:
        user_content = user_query

    messages.append({
        "role": "user",
        "content": user_content
    })

    return messages


def detect_language(text: str) -> str:
    """
    Simple language detection based on keywords

    Args:
        text: Input text

    Returns:
        Language code (de, fr, it)
    """
    text_lower = text.lower()

    # French indicators
    if any(word in text_lower for word in ["quelle", "quel", "quels", "quelles", "qu'est-ce", "votation"]):
        return "fr"

    # Italian indicators
    if any(word in text_lower for word in ["quale", "quali", "che cosa", "votazione"]):
        return "it"

    # Default to German
    return "de"


# Prompt templates for specific tasks
SUMMARIZE_INITIATIVE_TEMPLATE = """Fasse diese Volksinitiative in 2-3 Sätzen zusammen:

Titel: {title}
Datum: {date}

{description}
"""

EXPLAIN_ARGUMENTS_TEMPLATE = """Erkläre die Hauptargumente für und gegen diese Initiative:

Initiative: {title}

Pro-Argumente:
{pro_args}

Contra-Argumente:
{contra_args}
"""

COMPARE_INITIATIVES_TEMPLATE = """Vergleiche diese beiden Volksinitiativen:

Initiative 1: {title1}
{description1}

Initiative 2: {title2}
{description2}

Gemeinsamkeiten und Unterschiede:
"""
