# tests/test_users.py
def test_sample_user_fixture(sample_user):
    assert sample_user["role"] == "admin"
