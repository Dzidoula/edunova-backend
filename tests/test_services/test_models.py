from app.models.user import User
from app.models.document import Document
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.chat_message import ChatMessage
from app.models.progress import Progress
from app.models.pedagogical_memory import PedagogicalMemory


def test_create_full_graph(db_session):
    user = User(username="koffi")
    db_session.add(user)
    db_session.flush()

    doc = Document(
        user_id=user.id,
        title="Cours de fractions",
        subject="Mathématiques",
        document_type="course",
        extracted_text="Une fraction représente...",
    )
    db_session.add(doc)
    db_session.flush()

    chunk = KnowledgeChunk(document_id=doc.id, chunk_index=0, content="Une fraction représente...")
    message = ChatMessage(user_id=user.id, document_id=doc.id, role="user", content="Explique-moi les fractions")
    progress = Progress(user_id=user.id, notion_name="Fractions", subject="Mathématiques")
    memory = PedagogicalMemory(user_id=user.id, memory_type="success", content="A réussi un exercice sur les fractions")

    db_session.add_all([chunk, message, progress, memory])
    db_session.commit()

    assert len(user.documents) == 1
    assert user.documents[0].chunks[0].content.startswith("Une fraction")
    assert progress.mastery == "unknown"
    assert progress.success == 0 and progress.failure == 0
