from app import build_fallback_chat_reply


def test_fallback_chat_reply_is_contextual():
    reply = build_fallback_chat_reply(
        "pls help me regarding my career",
        ["python", "sql"],
        "Data Scientist",
    )

    assert "Data Scientist" in reply
    assert "python" in reply.lower()
    assert "sql" in reply.lower()
