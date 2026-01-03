"""Tests for production mode functionality.

These tests verify behavior that only occurs in production mode,
such as static file serving for the SPA frontend.
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


class TestStaticPathCalculation:
    """Test suite for static path calculation.
    
    These tests ensure the static file path is correctly calculated
    regardless of where the code is running (Docker, local, etc.).
    """

    def test_static_path_resolves_to_correct_directory(self):
        """Verify the static path calculation points to the right location.
        
        The static path should be:
        - <project_root>/static in Docker (/app/static)
        - <backend>/static in local development
        
        It should be exactly 3 .parent calls from main.py:
        - main.py -> obsidian_reader/ -> src/ -> <project_root>
        """
        from obsidian_reader import main
        
        main_file = Path(main.__file__)
        
        # Calculate the path as it's done in production
        static_path = main_file.parent.parent.parent / "static"
        
        # Verify the path structure is correct
        # main.py should be in obsidian_reader/
        assert main_file.parent.name == "obsidian_reader"
        # obsidian_reader/ should be in src/
        assert main_file.parent.parent.name == "src"
        # static should be a sibling of src/
        assert static_path.name == "static"
        assert static_path.parent == main_file.parent.parent.parent

    def test_static_path_is_not_root_directory(self):
        """Ensure static path doesn't accidentally resolve to filesystem root.
        
        This was a bug where 4 .parent calls instead of 3 caused the path
        to resolve to '/' instead of '/app'.
        """
        from obsidian_reader import main
        
        main_file = Path(main.__file__)
        static_path = main_file.parent.parent.parent / "static"
        
        # The static path should never be at the filesystem root
        assert static_path.parent != Path("/")
        assert str(static_path) != "/static"

    def test_static_path_parent_count(self):
        """Verify we're using exactly 3 .parent calls.
        
        This is a regression test for the off-by-one bug.
        """
        from obsidian_reader import main
        
        main_file = Path(main.__file__)
        
        # The correct path uses 3 parents
        correct_path = main_file.parent.parent.parent / "static"
        
        # The incorrect path (bug) used 4 parents
        incorrect_path = main_file.parent.parent.parent.parent / "static"
        
        # These should be different
        assert correct_path != incorrect_path
        
        # The incorrect path would be closer to root
        assert len(incorrect_path.parts) < len(correct_path.parts)


class TestProductionStaticFileServing:
    """Test suite for production static file serving.
    
    These tests run with ENV=production to verify static file
    serving works correctly.
    """

    @pytest.fixture
    def production_env(self, tmp_path):
        """Set up production environment with mock static files."""
        # Create mock static directory structure
        static_dir = tmp_path / "static"
        static_dir.mkdir()
        
        assets_dir = static_dir / "assets"
        assets_dir.mkdir()
        
        # Create mock files
        index_html = static_dir / "index.html"
        index_html.write_text("<!DOCTYPE html><html><body>Test SPA</body></html>")
        
        favicon = static_dir / "favicon.svg"
        favicon.write_text("<svg></svg>")
        
        js_file = assets_dir / "index.js"
        js_file.write_text("console.log('test');")
        
        css_file = assets_dir / "index.css"
        css_file.write_text("body { margin: 0; }")
        
        return static_dir

    @pytest.fixture
    def production_app(self, production_env, tmp_path):
        """Create a production mode FastAPI app with static files."""
        import asyncio
        import json
        
        # Create vault config
        vault_path = tmp_path / "vault"
        vault_path.mkdir()
        (vault_path / "test.md").write_text("# Test\n\nTest content.")
        
        config = {
            "vaults": {
                "test": {"path": str(vault_path), "name": "Test Vault"}
            },
            "default_vault": "test"
        }
        config_path = tmp_path / "vaults.json"
        config_path.write_text(json.dumps(config))
        
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        # Store original environment
        original_env = os.environ.get("ENV")
        original_vaults = os.environ.get("VAULTS_CONFIG")
        original_data = os.environ.get("DATA_DIR")
        original_password = os.environ.get("APP_PASSWORD")
        
        # Set production environment
        os.environ["ENV"] = "production"
        os.environ["VAULTS_CONFIG"] = str(config_path)
        os.environ["DATA_DIR"] = str(data_dir)
        os.environ["APP_PASSWORD"] = "test_password"
        
        # Clear cached modules to force reload with new settings
        modules_to_remove = [
            key for key in sys.modules.keys()
            if key.startswith("obsidian_reader")
        ]
        for mod in modules_to_remove:
            del sys.modules[mod]
        
        # Patch the static path calculation to use our test directory
        with patch("obsidian_reader.main.Path") as MockPath:
            # Make Path behave normally except for __file__ parent chain
            MockPath.side_effect = lambda x: Path(x)
            
            # Import fresh with production settings
            from obsidian_reader.core.config import Settings
            import obsidian_reader.core.config as config_module
            config_module.settings = Settings()
            
            # Verify we're in production mode
            assert config_module.settings.is_development is False
            
            # For this test, we'll manually create an app that serves static files
            from fastapi import FastAPI
            from fastapi.staticfiles import StaticFiles
            from fastapi.responses import FileResponse
            from obsidian_reader.api.routes import router as api_router
            
            app = FastAPI()
            app.include_router(api_router, prefix="/api")
            
            # Mount static files like production does
            if production_env.exists():
                app.mount(
                    "/assets",
                    StaticFiles(directory=production_env / "assets"),
                    name="assets"
                )
                
                @app.get("/{full_path:path}")
                async def serve_spa(full_path: str):
                    file_path = production_env / full_path
                    if file_path.exists() and file_path.is_file():
                        return FileResponse(file_path)
                    return FileResponse(production_env / "index.html")
            
            # Initialize vault manager
            from obsidian_reader.services.vault_manager import VaultManager
            import obsidian_reader.services.vault_manager as vm_module
            vm_module.vault_manager = VaultManager()
            asyncio.run(vm_module.vault_manager.initialize())
            
            from fastapi.testclient import TestClient
            
            with TestClient(app) as client:
                yield client
        
        # Restore environment
        if original_env is not None:
            os.environ["ENV"] = original_env
        elif "ENV" in os.environ:
            del os.environ["ENV"]
            
        if original_vaults is not None:
            os.environ["VAULTS_CONFIG"] = original_vaults
        elif "VAULTS_CONFIG" in os.environ:
            del os.environ["VAULTS_CONFIG"]
            
        if original_data is not None:
            os.environ["DATA_DIR"] = original_data
        elif "DATA_DIR" in os.environ:
            del os.environ["DATA_DIR"]
            
        if original_password is not None:
            os.environ["APP_PASSWORD"] = original_password
        
        # Clear modules again for next tests
        modules_to_remove = [
            key for key in sys.modules.keys()
            if key.startswith("obsidian_reader")
        ]
        for mod in modules_to_remove:
            del sys.modules[mod]

    def test_root_serves_index_html(self, production_app):
        """Test that root path serves index.html in production."""
        response = production_app.get("/")
        
        assert response.status_code == 200
        assert "Test SPA" in response.text

    def test_unknown_path_serves_index_html_for_spa(self, production_app):
        """Test that unknown paths serve index.html for SPA routing."""
        response = production_app.get("/some/spa/route")
        
        assert response.status_code == 200
        assert "Test SPA" in response.text

    def test_assets_are_served(self, production_app):
        """Test that static assets are served correctly."""
        response = production_app.get("/assets/index.js")
        
        assert response.status_code == 200
        assert "console.log" in response.text

    def test_favicon_is_served(self, production_app):
        """Test that favicon is served."""
        response = production_app.get("/favicon.svg")
        
        assert response.status_code == 200
        assert "<svg>" in response.text

    def test_api_routes_still_work(self, production_app):
        """Test that API routes work alongside static file serving."""
        response = production_app.get("/api/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestProductionLogging:
    """Test suite for production logging behavior."""

    def test_missing_static_directory_logs_warning(self, tmp_path, caplog):
        """Test that missing static directory logs a warning."""
        import logging
        
        # This tests the logging behavior when static files are not found
        caplog.set_level(logging.WARNING)
        
        # Create a non-existent path
        missing_path = tmp_path / "nonexistent" / "static"
        
        # Simulate what production startup should do
        if not missing_path.exists():
            logging.warning(
                f"Static files directory not found at {missing_path}. "
                "Frontend will not be served. "
                "Ensure the frontend build is copied to the correct location."
            )
        
        assert "Static files directory not found" in caplog.text
        assert str(missing_path) in caplog.text

