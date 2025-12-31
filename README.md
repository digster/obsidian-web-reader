# Obsidian Web Reader

A web-based Obsidian vault reader that serves your markdown notes over the web. Built with FastAPI (Python) and SvelteKit, with full support for Obsidian-specific syntax.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12+-blue.svg)
![Node](https://img.shields.io/badge/node-20+-green.svg)

## Features

- **Multi-Vault Support** - Switch between multiple Obsidian vaults
- **Obsidian Syntax** - Full support for wiki links, embeds, callouts, tags, and more
- **Full-Text Search** - Fast SQLite FTS5-powered search across all notes
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
echo "APP_PASSWORD=your-secure-password" > .env
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env
echo "VAULTS_PATH=/path/to/your/vaults" >> .env
```

4. Start with Docker Compose:
```bash
docker compose -f docker/docker-compose.yml up -d
```

5. Open http://localhost:8000 in your browser

### Development Setup

#### Backend

```bash
cd backend

# Install uv if not installed
pip install uv

# Install dependencies
uv sync

# Create vault config
cp vaults.example.json vaults.json
# Edit vaults.json

# Run development server
ENV=development APP_PASSWORD=dev uv run uvicorn obsidian_reader.main:app --reload
```

#### Frontend

```bash
cd frontend

# Install pnpm if not installed
npm install -g pnpm

# Install dependencies
pnpm install

# Run development server
pnpm dev
```

The frontend runs at http://localhost:5173 and proxies API requests to the backend.

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `APP_PASSWORD` | Yes | - | Password for accessing the app |
| `SECRET_KEY` | No | Auto-generated | JWT token signing key |
| `ENV` | No | `production` | `development` or `production` |
| `DEBUG` | No | `false` | Enable debug logging |
| `HOST` | No | `0.0.0.0` | Server bind host |
| `PORT` | No | `8000` | Server bind port |
| `VAULTS_CONFIG` | No | `./vaults.json` | Path to vault config file |
| `DATA_DIR` | No | `./data` | Directory for search indexes |

### Vault Configuration (`vaults.json`)

```json
{
  "vaults": {
    "personal": {
      "path": "/data/vaults/personal",
      "name": "Personal Notes"
    },
    "work": {
      "path": "/data/vaults/work",
      "name": "Work Documentation"
    }
  },
  "default_vault": "personal"
}
```

## Docker Deployment

### Production

```bash
# Build and start
docker compose -f docker/docker-compose.yml up -d --build

# View logs
docker compose -f docker/docker-compose.yml logs -f

# Stop
docker compose -f docker/docker-compose.yml down
```

### Development with Docker

```bash
# Start both backend and frontend with hot reload
docker compose -f docker/docker-compose.dev.yml up

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
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── lib/
│   │   │   ├── components/ # Svelte components
│   │   │   ├── stores/     # Svelte stores
│   │   │   └── api.ts      # API client
│   │   └── routes/         # SvelteKit routes
│   └── package.json
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml      # Production
│   └── docker-compose.dev.yml  # Development
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
| `GET` | `/api/vault/tree` | Get file tree |
| `GET` | `/api/vault/note/{path}` | Get note content |
| `GET` | `/api/vault/attachment/{path}` | Get attachment |
| `GET` | `/api/search?q={query}` | Search notes |
| `POST` | `/api/search/reindex` | Rebuild search index |
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

