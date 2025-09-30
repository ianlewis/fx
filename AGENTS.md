# AGENTS.md

This file provides guidance to coding agents when working with code in
this repository.

## Common Commands

### Build and Development

- `make all` - Run all tests and build the site
- `make build` - Build the static API site files
- `make install` - Install the package in the local venv
- `make serve` - Serve the API locally (after building)
- `make update` - Update API data from sources (fetches latest exchange rates)

### Testing

- `make test` - Run all linters and tests
- `make unit-tests` - Run unit tests only (`python3 -m unittest discover .`)

### Code Quality

- `make lint` - Run all linters (ruff, markdownlint, yamllint, actionlint, etc.)
- `make ruff` - Run Python linter/type checker
- `make format` - Format all files (Python, JSON, Markdown, YAML)
- `make py-format` - Format Python files only

### Individual Linters

- `make actionlint` - Lint GitHub Actions workflows
- `make markdownlint` - Lint Markdown files
- `make yamllint` - Lint YAML files
- `make textlint` - Lint text content

### Protobuf

- `make protoc` - Compile protobuf files to Python

### Environment Setup

The project uses both Python virtual environment (.venv) and Node.js for tooling.
Make targets automatically handle dependency installation.

## Architecture

### Core Components

- **fx.main** - CLI entrypoint with subcommands (update, build)
- **fx.provider** - Abstract base class for exchange rate providers
- **fx.mufg** - MUFG Bank provider implementation (primary source)
- **fx.quote** - Exchange rate quote data structures
- **fx.currency** - Currency definitions and validation
- **fx.build** - Static site generation for API endpoints
- **fx.update** - Data fetching and persistence logic

### Data Flow

1. **Update phase**: `fx update` fetches exchange rates from MUFG and stores in Protocol
   Buffers format in `data/` directory
2. **Build phase**: `fx build` processes stored data to generate static JSON API files
   in `_site/v1/` directory
3. **Serve phase**: Static files served via HTTP server or deployed to CDN

### Key Files

- **data/** - Raw exchange rate data in Protocol Buffers format
- **\_site/v1/** - Generated static API files (JSON)
- **fx/\*.proto** - Protocol Buffer schemas for data structures
- **fx/\*\_pb2.py** - Generated Python classes from protobuf (don't edit manually)

### Testing Configuration

- Unit tests use Python's built-in unittest framework
- Test files follow `test_*.py` naming convention
- Run individual test: `python3 -m unittest fx.test_mufg`

### Linting Configuration

- **Python**: Uses ruff for linting/formatting, configured in pyproject.toml
- **Protobuf files** (\*\_pb2.py) are excluded from linting
- **Markdown**: markdownlint with custom config
- **YAML**: yamllint with custom config
- **GitHub Actions**: actionlint and zizmor for security

### Development Workflow

1. Make changes to source code
2. Run `make lint` to check code quality
3. Run `make test` to verify functionality
4. Use `make format` to auto-format files
5. Commit with conventional commit format (feat:, fix:, etc.)
