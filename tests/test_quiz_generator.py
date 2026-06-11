from quiz_generator import (
    allowed_file,
    extract_text_from_csv,
    extract_text_from_txt,
    generate_quiz_locally,
)


def test_allowed_file_types() -> None:
    assert allowed_file("notes.txt")
    assert allowed_file("slides.pdf")
    assert allowed_file("image.png")
    assert allowed_file("photo.JPG")
    assert not allowed_file("archive.exe")


def test_extract_text_from_txt() -> None:
    content = b"Hello world!"
    assert extract_text_from_txt(content) == "Hello world!"


def test_extract_text_from_csv() -> None:
    content = b"name,score\nAlice,90\nBob,85"
    output = extract_text_from_csv(content)
    assert "Alice 90" in output
    assert "Bob 85" in output


def test_generate_quiz_locally() -> None:
    text = "Python is a programming language. It was created by Guido van Rossum. Python supports multiple programming paradigms and is widely used."
    questions = generate_quiz_locally(text, 3)
    assert len(questions) >= 1
    assert len(questions) <= 3
    for q in questions:
        assert "points" in q
        assert 1 <= q["points"] <= 3
        assert q["type"] in (
            "MCQ",
            "Very Short Answer",
            "Short Answer",
            "Long Answer",
            "Essay",
        )
