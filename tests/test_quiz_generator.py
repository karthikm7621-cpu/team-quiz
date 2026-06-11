import pytest
from quiz_generator import (
    allowed_file,
    extract_text_from_csv,
    extract_text_from_txt,
    build_quiz_prompt,
)


def test_allowed_file_types():
    assert allowed_file('notes.txt')
    assert allowed_file('slides.pdf')
    assert allowed_file('image.png')
    assert allowed_file('photo.JPG')
    assert not allowed_file('archive.zip')


def test_extract_text_from_txt():
    content = 'Hello world!'.encode('utf-8')
    assert extract_text_from_txt(content) == 'Hello world!'


def test_extract_text_from_csv():
    content = 'name,score\nAlice,90\nBob,85'.encode('utf-8')
    output = extract_text_from_csv(content)
    assert 'Alice 90' in output
    assert 'Bob 85' in output


def test_build_quiz_prompt():
    prompt = build_quiz_prompt('Sample text', 5)
    assert 'Generate 5 multiple-choice quiz questions' in prompt
    assert 'Sample text' in prompt
