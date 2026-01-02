# Obsidian Web Reader

A web-based Obsidian vault reader that serves your markdown notes over the web. Built with FastAPI (Python) and SvelteKit, with full support for Obsidian-specific syntax.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12+-blue.svg)
![Node](https://img.shields.io/badge/node-20+-green.svg)

## Features

- **Multi-Vault Support** - Switch between multiple Obsidian vaults
- **Vault Management UI** - Add and delete vaults directly from the web interface
- **GitHub Integration** - Clone vaults from GitHub repositories using deploy tokens
- **Auto-Sync** - Automatically pull updates from GitHub at configurable intervals
- **Obsidian Syntax** - Full support for wiki links, embeds, callouts, tags, and more
- **Full-Text Search** - Fast SQLite FTS5-powered search across all notes
- **Markdown Caching** - LRU cache for rendered markdown with automatic invalidation
- **Math Rendering** - LaTeX math with KaTeX
- **Code Highlighting** - Syntax highlighting with Pygments/highlight.js
- **Dark/Light Theme** - Automatic theme detection with manual toggle
- **Password Protection** - Simple authentication to secure your notes
- **Responsive Design** - Works on desktop and mobile devices
- **Docker Ready** - Easy deployment with Docker Compose

## Supported Obsidian Features

| Feature | Status | Syntax |
|---------|--------|--------|
| Wiki Links | ✅ | `[[Note]]`, `[[Note\|Alias]]`, `[[Note#Heading]]` |
| Image Embeds | ✅ | `![[image.png]]` |
| Note Embeds | ✅ | `![[note]]`, `![[note#heading]]` |
| Tags | ✅ | `#tag`, `#nested/tag` |
| Callouts | ✅ | `> [!note]`, `> [!warning]`, etc. |
| YAML Frontmatter | ✅ | `---` block at start |
| Task Lists | ✅ | `- [ ]`, `- [x]` |
| Math (LaTeX) | ✅ | `$inline$`, `$$block$$` |
| Code Blocks | ✅ | Fenced with syntax highlighting |
| Tables | ✅ | Pipe-delimited tables |
| Footnotes | ✅ | `[^1]` references |
| Backlinks | ✅ | Shows notes linking to current note |

### Not Implemented

- Graph View
- Dataview queries
- Canvas files
- Block references (`[[note^block]]`)
- Mermaid diagrams (can be added)

## Quick Start

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/yourusername/obsidian-web-reader.git
cd obsidian-web-reader
```

2. Create vault configuration:
```bash
cp vaults.example.json vaults.json
# Edit vaults.json to point to your vault directories
```

3. Create environment file:
```bash
cp .env.example .env
# Edit .env to set your password and vault path
```

4. Start with Docker Compose:
```bash
docker compose up -d
```

5. Open http://localhost:8000 in your browser (or the port specified in `HOST_PORT`)

### Development Setup

#### Backend

```bash
cd backend

# Install uv if not installed
pip install uv

# Install dependencies
uv sync

# Create environment and vault config
cp env.example .env
cp ../vaults.example.json ../vaults.json
# Edit .env and vaults.json as needed

# Run development server
uv run uvicorn obsidian_reader.main:app --reload
```

#### Frontend

```bash
cd frontend

# Install pnpm if not installed
npm install -g pnpm

# Install dependencies
pnpm install

# (Optional) Create environment config if using custom API URL
cp .env.example .env
# Edit .env if backend runs on different host/port

# Run development server
pnpm dev
```

The frontend runs at http://localhost:5173 and proxies API requests to the backend.

## Configuration

### Environment Variables

Sample environment files are provided:
- `.env.example` - Root config for Docker Compose
- `backend/env.example` - Backend server config
- `frontend/.env.example` - Frontend config (optional)

Copy and customize these files before running the application.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `APP_PASSWORD` | Yes | - | Password for accessing the app |
| `SECRET_KEY` | No | Auto-generated | JWT token signing key (also used for token encryption) |
| `ENV` | No | `production` | `development` or `production` |
| `DEBUG` | No | `false` | Enable debug logging |
| `HOST` | No | `0.0.0.0` | Server bind host |
| `PORT` | No | `8000` | Server bind port |
| `VAULTS_CONFIG` | No | `./vaults.json` | Path to vault config file |
| `VAULTS_DIR` | No | `./vaults` | Directory for cloned vault repositories |
| `DATA_DIR` | No | `./data` | Directory for search indexes |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `1440` | JWT token expiration (24 hours) |
| `CORS_ORIGINS` | No | `localhost:5173` | Allowed CORS origins (comma-separated) |

### Vault Configuration (`vaults.json`)

Vaults can be configured manually via `vaults.json` or added through the web UI:

```json
{
  "vaults": {
    "personal": {
      "path": "/data/vaults/personal",
      "name": "Personal Notes"
    },
    "work": {
      "path": "/data/vaults/work",
      "name": "Work Documentation",
      "repo_url": "https://github.com/user/work-notes",
      "encrypted_token": "gAAAAABl...",
      "refresh_interval_minutes": 60
    }
  },
  "default_vault": "personal"
}
```

#### Vault Configuration Options

| Field | Required | Description |
|-------|----------|-------------|
| `path` | Yes | Local path to the vault directory |
| `name` | Yes | Display name for the vault |
| `repo_url` | No | GitHub repository URL for git-based vaults |
| `encrypted_token` | No | Encrypted deploy token (set via UI) |
| `refresh_interval_minutes` | No | Auto-sync interval (1-1440 minutes) |

### Adding Vaults via UI

1. Click the vault selector in the header
2. Click "Add Vault" button
3. Fill in the form:
   - **Vault Name**: Display name for your vault
   - **Repository URL**: HTTPS URL of your GitHub repository
   - **Deploy Token**: GitHub Personal Access Token or deploy key with read access
   - **Auto-sync** (optional): Enable periodic git pull with interval in minutes

The vault will be cloned to the `vaults` directory and automatically configured.

### GitHub Deploy Tokens

To create a deploy token for read-only access:

1. Go to your GitHub repository → Settings → Secrets and variables → Actions
2. Or create a Personal Access Token at https://github.com/settings/tokens
3. Select only the `repo` scope (or just `read:packages` for private repos)
4. Copy the token and use it when adding the vault

Tokens are encrypted before storage using Fernet symmetric encryption derived from your `SECRET_KEY`.

## Docker Deployment

### Docker Compose Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `APP_PASSWORD` | Yes | - | Password for accessing the app |
| `SECRET_KEY` | No | Auto-generated | JWT token signing key |
| `HOST_PORT` | No | `8000` | Host port for the web interface |
| `VAULTS_PATH` | Yes | - | Path to your vaults directory on the host |

### Production

```bash
# Build and start
docker compose up -d --build

# View logs
docker compose logs -f

# Stop
docker compose down
```

### Development with Docker

```bash
# Start both backend and frontend with hot reload
docker compose -f docker-compose.dev.yml up

# Backend available at http://localhost:8000
# Frontend available at http://localhost:5173
```

## Project Structure

```
obsidian-web-reader/
├── backend/
│   ├── src/obsidian_reader/
│   │   ├── api/            # FastAPI routes
│   │   ├── core/           # Config, auth, security
│   │   ├── models/         # Pydantic schemas
│   │   └── services/       # Vault, markdown, search
│   ├── tests/              # Pytest tests
│   ├── env.example         # Backend env sample
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── lib/
│   │   │   ├── components/ # Svelte components
│   │   │   ├── stores/     # Svelte stores
│   │   │   └── api.ts      # API client
│   │   └── routes/         # SvelteKit routes
│   ├── .env.example        # Frontend env sample
│   └── package.json
├── Dockerfile              # Multi-stage Docker build
├── docker-compose.yml      # Production compose
├── docker-compose.dev.yml  # Development compose
├── .env.example            # Docker Compose env sample
└── vaults.json             # Vault configuration
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/login` | Login with password |
| `POST` | `/api/auth/logout` | Logout |
| `GET` | `/api/auth/me` | Get auth status |
| `GET` | `/api/vaults` | List available vaults |
| `POST` | `/api/vaults/select` | Set active vault |
| `POST` | `/api/vaults/create` | Create vault from GitHub repo |
| `DELETE` | `/api/vaults/{vault_id}` | Delete a vault |
| `POST` | `/api/vaults/{vault_id}/sync` | Trigger manual git pull |
| `GET` | `/api/vault/tree` | Get file tree |
| `GET` | `/api/vault/note/{path}` | Get note content (cached) |
| `GET` | `/api/vault/attachment/{path}` | Get attachment |
| `GET` | `/api/search?q={query}` | Search notes |
| `POST` | `/api/search/reindex` | Rebuild search index |
| `GET` | `/api/cache/stats` | Get markdown render cache stats |
| `POST` | `/api/cache/clear` | Clear markdown render cache |
| `GET` | `/api/health` | Health check |

## Running Tests

```bash
cd backend

# Install test dependencies
uv sync

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=obsidian_reader --cov-report=html
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Obsidian](https://obsidian.md) for the amazing note-taking app
- [FastAPI](https://fastapi.tiangolo.com) for the excellent Python web framework
- [SvelteKit](https://kit.svelte.dev) for the reactive frontend framework
- [Tailwind CSS](https://tailwindcss.com) for utility-first styling

