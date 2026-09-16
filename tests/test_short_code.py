

from app.services.short_code import generate_short_code, ALPHABET, LENGTH


def test_generate_short_code_length():
    
    code = generate_short_code()
    assert len(code) == LENGTH


def test_generate_short_code_uses_alphabet():
    
    code = generate_short_code()
    for char in code:
        assert char in ALPHABET


def test_generate_short_code_is_unique():
    
    codes = {generate_short_code() for _ in range(100)}
    # All 100 should be unique (collision probability is astronomically low)
    assert len(codes) == 100
