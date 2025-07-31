import pytest

@pytest.fixture
def sample_user():
    return {
        "id": 1,
        "username": "test_user",
        "email": "test@example.com"
    }

@pytest.fixture(params=[(2, 2, 4), (3, 3, 9), (4, 5, 20)])
def multiply_data(request):
    return request.param

