"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestAuthEndpoints:
    """Test suite for authentication endpoints."""

    def test_login_success(self, test_client: TestClient):
        """Test successful login."""
        response = test_client.post(
            "/api/auth/login",
            json={"password": "test_password"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, test_client: TestClient):
        """Test login with wrong password."""
        response = test_client.post(
            "/api/auth/login",
            json={"password": "wrong_password"}
        )

        assert response.status_code == 401
        assert "Incorrect password" in response.json()["detail"]

    def test_auth_status_unauthenticated(self, test_client: TestClient):
        """Test auth status when not authenticated."""
        response = test_client.get("/api/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is False

    def test_auth_status_authenticated(self, authenticated_client: TestClient):
        """Test auth status when authenticated."""
        response = authenticated_client.get("/api/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True

    def test_logout(self, authenticated_client: TestClient):
        """Test logout."""
        response = authenticated_client.post("/api/auth/logout")

        assert response.status_code == 200
        assert "Logged out" in response.json()["message"]


class TestVaultEndpoints:
    """Test suite for vault endpoints."""

    def test_list_vaults_unauthenticated(self, test_client: TestClient):
        """Test listing vaults when not authenticated."""
        response = test_client.get("/api/vaults")
        assert response.status_code == 401

    def test_list_vaults(self, authenticated_client: TestClient):
        """Test listing vaults."""
        response = authenticated_client.get("/api/vaults")

        assert response.status_code == 200
        data = response.json()
        assert "vaults" in data
        assert len(data["vaults"]) >= 1
        assert data["vaults"][0]["id"] == "test"

    def test_select_vault(self, authenticated_client: TestClient):
        """Test selecting a vault."""
        response = authenticated_client.post(
            "/api/vaults/select",
            json={"vault_id": "test"}
        )

        assert response.status_code == 200

    def test_select_nonexistent_vault(self, authenticated_client: TestClient):
        """Test selecting a non-existent vault."""
        response = authenticated_client.post(
            "/api/vaults/select",
            json={"vault_id": "nonexistent"}
        )

        assert response.status_code == 404

    def test_get_file_tree(self, authenticated_client: TestClient):
        """Test getting file tree."""
        # First select a vault
        authenticated_client.post(
            "/api/vaults/select",
            json={"vault_id": "test"}
        )

        response = authenticated_client.get("/api/vault/tree")

        assert response.status_code == 200
        data = response.json()
        assert "tree" in data
        assert len(data["tree"]) > 0

    def test_get_note(self, authenticated_client: TestClient):
        """Test getting a note."""
        # First select a vault
        authenticated_client.post(
            "/api/vaults/select",
            json={"vault_id": "test"}
        )

        response = authenticated_client.get("/api/vault/note/test_note")

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Note"
        assert "content_html" in data
        assert len(data["tags"]) > 0

    def test_get_nonexistent_note(self, authenticated_client: TestClient):
        """Test getting a non-existent note."""
        authenticated_client.post(
            "/api/vaults/select",
            json={"vault_id": "test"}
        )

        response = authenticated_client.get("/api/vault/note/nonexistent")

        assert response.status_code == 404

    def test_get_note_with_special_characters_in_path(self, authenticated_client: TestClient):
        """Test getting a note with dashes and spaces in the filename.
        
        This tests the URL encoding/decoding of paths with special characters.
        The frontend encodes each path segment individually, preserving slashes.
        """
        authenticated_client.post(
            "/api/vaults/select",
            json={"vault_id": "test"}
        )

        # URL encode the path properly - encode each segment but keep slashes
        # This simulates what the frontend does with encodePathForUrl
        response = authenticated_client.get(
            "/api/vault/note/subfolder/note-with-dashes%20-%20test%201"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Note With Dashes"
        assert "content_html" in data

    def test_get_note_with_unencoded_special_characters(self, authenticated_client: TestClient):
        """Test getting a note with unencoded special characters in the filename.
        
        FastAPI's path converter should handle both encoded and unencoded paths.
        """
        authenticated_client.post(
            "/api/vaults/select",
            json={"vault_id": "test"}
        )

        # Test with unencoded path (spaces directly in URL)
        response = authenticated_client.get(
            "/api/vault/note/subfolder/note-with-dashes - test 1"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Note With Dashes"

    def test_get_attachment(self, authenticated_client: TestClient):
        """Test getting an attachment."""
        authenticated_client.post(
            "/api/vaults/select",
            json={"vault_id": "test"}
        )

        response = authenticated_client.get("/api/vault/attachment/attachments/test.png")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"


class TestSearchEndpoints:
    """Test suite for search endpoints."""

    def test_search_unauthenticated(self, test_client: TestClient):
        """Test search when not authenticated."""
        response = test_client.get("/api/search?q=test")
        assert response.status_code == 401

    def test_search(self, authenticated_client: TestClient):
        """Test searching notes."""
        # Select vault first
        authenticated_client.post(
            "/api/vaults/select",
            json={"vault_id": "test"}
        )

        response = authenticated_client.get("/api/search?q=callout")

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data

    def test_search_empty_query(self, authenticated_client: TestClient):
        """Test search with empty query."""
        authenticated_client.post(
            "/api/vaults/select",
            json={"vault_id": "test"}
        )

        response = authenticated_client.get("/api/search?q=")

        assert response.status_code == 200
        data = response.json()
        assert data["results"] == []

    def test_reindex(self, authenticated_client: TestClient):
        """Test reindexing search."""
        authenticated_client.post(
            "/api/vaults/select",
            json={"vault_id": "test"}
        )

        response = authenticated_client.post("/api/search/reindex")

        assert response.status_code == 200
        assert "Indexed" in response.json()["message"]


class TestHealthEndpoint:
    """Test suite for health endpoint."""

    def test_health_check(self, test_client: TestClient):
        """Test health check endpoint."""
        response = test_client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

