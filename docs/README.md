# repo-sherpa Documentation

Welcome to the repo-sherpa documentation. This multi-bot Slack service provides AI-powered assistance for git repositories.

## Quick Links

- [Main README](../README.md) - Project overview and quick start
- [Setup Guide](setup.md) - Configure your Slack apps
- [Development Guide](development.md) - Local development and contributing
- [Deployment Guide](deployment.md) - Production deployment
- [Architecture Guide](architecture.md) - System design and internals

## Documentation by Topic

### Getting Started

1. **[Project README](../README.md)** - Start here for project overview, features, and quick start guide
2. **[Slack App Setup](setup.md)** - Step-by-step instructions for configuring Slack apps per bot

### For Developers

3. **[Development Guide](development.md)** - Local development setup, testing, debugging, and contribution workflow
   - Development environment setup
   - Project structure overview
   - Testing strategy
   - Code style guidelines
   - Pull request process

### For Operators

4. **[Deployment Guide](deployment.md)** - Production deployment and operations
   - System requirements
   - Environment configuration
   - Deployment options (systemd, Docker)
   - Monitoring and logging
   - Security hardening
   - Scaling considerations

### For Architects

5. **[Architecture Guide](architecture.md)** - System design and component interactions
   - High-level architecture
   - Request flow diagrams
   - Component details
   - Session management
   - Error handling
   - Performance characteristics

## Common Tasks

### I want to...

**...set up repo-sherpa for the first time**
→ Start with [Project README](../README.md), then [Slack App Setup](setup.md)

**...run repo-sherpa locally for development**
→ See [Development Guide - Development Setup](development.md#development-setup)

**...deploy repo-sherpa to production**
→ Follow [Deployment Guide](deployment.md)

**...understand how repo-sherpa works**
→ Read [Architecture Guide](architecture.md)

**...contribute to repo-sherpa**
→ See [Development Guide - Contributing](development.md#contributing)

**...troubleshoot an issue**
→ Check [Deployment Guide - Troubleshooting](deployment.md#troubleshooting) or [Setup Guide - Troubleshooting](setup.md#troubleshooting)

**...add a new bot**
→ Follow [Slack App Setup](setup.md) to create a new Slack app, then add it to `bot_config.yaml`

**...configure timeouts or emojis**
→ Edit `bot_config.yaml` (see [Project README - Configuration Reference](../README.md#configuration-reference))

## Documentation Structure

```
docs/
├── README.md              # This file - documentation index
├── setup.md               # Slack app configuration guide
├── development.md         # Development and contribution guide
├── deployment.md          # Production deployment and operations
└── architecture.md        # System architecture and design
```

## Key Concepts

### Multi-Bot Architecture
repo-sherpa runs multiple independent bot instances from a single process. Each bot:
- Serves a specific git repository
- Has its own Slack app and tokens
- Maintains separate session contexts

### Session Management
The system maintains Claude Code session IDs per Slack thread, enabling multi-turn conversations. Sessions are stored in-memory and persist only during the bot's runtime.

### Async Processing
Requests are handled asynchronously via ThreadPoolExecutor, with visual feedback provided through emoji reactions.

## Support

For questions or issues:
- Check the relevant documentation above
- Search [GitHub Issues](https://github.com/yourusername/repo-sherpa/issues)
- Open a new issue with details

## Documentation Conventions

- **Code blocks**: Show commands or configuration
- **Mermaid diagrams**: Visualize architecture and flows
- **Tables**: Compare options or list requirements
- **Checklists**: Track completion of multi-step processes
