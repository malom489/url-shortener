from app.services.auth import  hash_password ,verify_password
def test_hash_password_produces_hash():
    plain="securepass123"
    hashed=hash_password(plain)
    assert hashed!= plain
    assert len(hashed)>50
def test_verify_password_correct():
    plain = "securepass123"
    hashed = hash_password(plain)
    assert verify_password(plain, hashed) is True   
def test_password_is_incorrect():
    hashed = hash_password("correct")
    assert verify_password("wrong", hashed) is False
    
def test_the_same_password_diff_hashes():
    plain = 'securepass123'
    hash1 = hash_password(plain)
    hash2 = hash_password(plain)
    assert hash1 != hash2
    assert verify_password(plain, hash1) is True  
    assert verify_password(plain, hash2) is True