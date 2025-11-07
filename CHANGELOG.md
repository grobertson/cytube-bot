# Changelog

## [Monolithic Refactor] - 2025-10-29

### Major Restructuring

This release represents a complete architectural overhaul of the cytube-bot project, transforming it from an installable Python package into a monolithic application structure.

#### Added
- **New Directory Structure**:
  - `lib/` - Core CyTube interaction library (formerly `cytube_bot_async/`)
  - `bots/` - Bot implementations (formerly `examples/`)
  - `common/` - Shared utilities for bot development

- **Python Path Hack**:
  - All bot files now include automatic path detection
  - Bots can be run from any directory without manual PYTHONPATH setup
  - Uses `Path(__file__).parent.parent.parent` to locate project root
  
- **Updated Documentation**:
  - Comprehensive README with quick start guide
  - API reference documentation
  - Bot development guide
  - Future roadmap including LLM integration plans

- **Modern Dependency Management**:
  - `requirements.txt` for direct pip installation
  - Removed Poetry/setuptools complexity
  
#### Changed
- **Import Paths**: All imports updated from `cytube_bot_async` to `lib`
- **Bot Structure**: Bots now import directly from local `lib` and `common` modules
- **Configuration**: Simplified bot configuration and startup
- **Development Workflow**: No need to reinstall package after changes

#### Removed
- Package installation files (`setup.py`, `pyproject.toml`, `MANIFEST.in`)
- Poetry lock file
- Old documentation structure
- Original `cytube_bot_async/` and `examples/` directories (archived in `_old/`)

#### Fixed
- Markov bot missing `_load_markov()` and `_save_markov()` methods
- Markov bot incorrect text attribute access
- Unused imports and parameters across bot implementations
- Python 3.8+ async compatibility issues

### Migration Guide

For existing users of the old package structure:

1. **Update imports**:
   ```python
   # Old
   from cytube_bot_async import Bot, MessageParser
   
   # New
   from lib import Bot, MessageParser
   from common import get_config, Shell
   ```

2. **Move bot files**: Place your custom bots in the `bots/` directory

3. **Install dependencies**: `pip install -r requirements.txt`

### Future Plans

- LLM chat integration (OpenAI, Anthropic, etc.)
- Advanced playlist management features
- Web dashboard for bot monitoring
- Plugin system for extensibility
- Multi-channel support
- Enhanced AI-powered features

### Technical Details

**Python Version**: Requires Python 3.8 or higher

**Core Dependencies**:
- websockets >= 12.0
- requests >= 2.32.3
- markovify >= 0.9.4 (for markov bot)

**Breaking Changes**: This is a complete architectural change. The old package-based approach is no longer supported. All development should use the new monolithic structure.

---

## Previous Versions

Historical changelog entries for the package-based versions have been archived. This represents a fresh start with a new development philosophy focused on simplicity and ease of customization.
