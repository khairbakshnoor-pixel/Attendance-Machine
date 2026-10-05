from utils.security import LoginLimiter, csv_safe, hash_password, verify_password


def test_password_hash_and_login_rate_limit():
    encoded = hash_password("a-strong-test-password")
    assert "a-strong-test-password" not in encoded
    assert verify_password("a-strong-test-password", encoded)
    assert not verify_password("wrong", encoded)
    assert not verify_password("test", "broken")
    limiter = LoginLimiter()
    for _ in range(5):
        assert not limiter.attempt("wrong", encoded)[0]
    assert not limiter.attempt("a-strong-test-password", encoded)[0]


def test_csv_formula_escaping():
    assert csv_safe("=1+1") == "'=1+1"
    assert csv_safe("  @SUM(A1)").startswith("'")
    assert csv_safe("Ali") == "Ali"
