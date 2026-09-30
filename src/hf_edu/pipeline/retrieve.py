"""Step 2: ClinicalContext -> one RetrievalQuery per topic -> KnowledgeStore.

The orchestrator (this code), not the LLM, decides what to query.
"""
from hf_edu.kb import KnowledgeStore
from hf_edu.schemas import (
    CORE_TOPICS,
    TRIGGER_TOPICS,
    ClinicalContext,
    RetrievalQuery,
    RetrievedChunk,
    Topic,
    TriggerCode,
)


def triggers_for_topic(context: ClinicalContext, topic: Topic) -> list[TriggerCode]:
    return [t for t in context.active_triggers() if topic in TRIGGER_TOPICS.get(t, ())]


def query_text_for_topic(context: ClinicalContext, topic: Topic) -> str:
    parts: list[str] = []
    if topic == Topic.DIET:
        parts += [i.text for i in context.diet_instructions]
    elif topic == Topic.ACTIVITY:
        parts += [i.text for i in context.activity_instructions]
    elif topic == Topic.MEDICATION:
        parts += [m.name for m in context.discharge_medications]
    elif topic == Topic.FOLLOWUP:
        parts += [i.text for i in context.followup]
    return " ".join(parts)


def build_queries(
    context: ClinicalContext, top_k: int, topics: tuple[Topic, ...] = CORE_TOPICS
) -> list[RetrievalQuery]:
    """Per topic: one general query, plus one trigger query if the topic has active triggers.

    Separate queries keep trigger-specific chunks from crowding out general guidance
    (e.g. hyperkalemia chunks pushing out low-sodium diet chunks).
    """
    queries = []
    for topic in topics:
        text = query_text_for_topic(context, topic) or None
        queries.append(RetrievalQuery(topic=topic, query_text=text, language="ko", top_k=top_k))
        if triggers := triggers_for_topic(context, topic):
            queries.append(
                RetrievalQuery(topic=topic, triggers=triggers, query_text=text, language="ko", top_k=top_k)
            )
    return queries


def retrieve(store: KnowledgeStore, queries: list[RetrievalQuery]) -> dict[Topic, list[RetrievedChunk]]:
    """Run queries and merge per topic: trigger-matched chunks first, then general; no duplicates."""
    merged: dict[Topic, dict[str, RetrievedChunk]] = {}
    for query in queries:
        bucket = merged.setdefault(query.topic, {})
        for hit in store.search(query):
            bucket.setdefault(hit.chunk.chunk_id, hit)
    return {
        topic: sorted(hits.values(), key=lambda h: (not h.matched_triggers, -h.score, h.chunk.chunk_id))
        for topic, hits in merged.items()
    }
