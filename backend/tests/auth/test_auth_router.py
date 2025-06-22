from unittest.mock import MagicMock, AsyncMock

from fastapi.testclient import TestClient

def test_google_callback(mocker, client: TestClient):
    google_data = {
        'given_name': 'Test',
        'family_name': 'User',
        'email': 'test@example.com',
        'picture': 'foo',
        'is_active': True
    }

    mocker.patch("src.auth.router.oauth.google.authorize_access_token", new=AsyncMock())
    
    mock_response = MagicMock()
    mock_response.json.return_value = google_data
    mocker.patch('src.auth.router.oauth.google.get', new=AsyncMock(return_value=mock_response))

    mock_user = MagicMock(username=google_data['given_name'])
    mocker.patch("src.auth.router.get_object_or_404", new=AsyncMock(return_value=mock_user))

    response = client.get('/auth/google/callback')
    assert response.status_code == 200
    assert 'access_token' in response.json()
    assert 'refresh_token' in response.json()

def test_login(mocker, client: TestClient):
    login_data = {
        'username': 'testuser',
        'password': 'testpassword',
    }

    mocker.patch(
        'src.auth.router.authenticate_user',
        new=AsyncMock(return_value=MagicMock(username='testuser'))
    )

    response = client.post('/auth/token', data=login_data)
    assert response.status_code == 200
    assert 'access_token' in response.json()
    assert 'refresh_token' in response.json()

def test_register(mocker, client: TestClient):
    user_data = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "StrongPassw123%",
        "first_name": "Test",
        "last_name": "User"
    }

    mock_user = MagicMock(username=user_data["username"], email=user_data["email"])
    mocker.patch("src.auth.router.create_user", new=AsyncMock(return_value=mock_user))

    mock_token = MagicMock(uuid="fake-uuid-token")
    mocker.patch("src.auth.router.create_email_activation_token", new=AsyncMock(return_value=mock_token))

    mocker.patch("src.auth.router.send_html_email", new=AsyncMock())

    response = client.post("/auth/register", json=user_data)

    assert response.status_code == 200
    json_response = response.json()
    assert "access_token" in json_response
    assert "refresh_token" in json_response
    assert json_response["token_type"] == "bearer"
