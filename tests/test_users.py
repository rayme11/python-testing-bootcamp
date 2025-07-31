def test_sample_user_fixture(sample_user):
    assert sample_user["username"] == "test_user"
    assert sample_user["email"] == "test@example.com"
