# Developer Guides - Table of Contents

## Overview

This directory contains comprehensive developer documentation for the Turnkey Coach Tools codebase. These guides are designed to help both new and experienced developers understand the architecture, contribute effectively, and maintain the codebase.

**Current Version**: v1.5+ with multi-workspace management, bulk sync, workout deletion, and metrics programming.

## Purpose

These guides serve multiple purposes:

1. **Onboarding**: Help new developers get up to speed quickly
2. **Reference**: Provide detailed documentation for specific components
3. **Knowledge Transfer**: Preserve architectural decisions and patterns
4. **AI-Assisted Development**: Enable AI agents to work effectively with minimal context

## Guide Organization

The guides are organized by topic, progressing from high-level architecture to specific implementation details:

## Metric References

- [METRICS_GUIDE.md](../METRICS_GUIDE.md) — canonical metric catalog, API payloads, and usage guidelines
- [METRICS_IN_MARKUP.md](../METRICS_IN_MARKUP.md) — how metrics map into the markup language and uploader expectations

### [01-Architecture-Overview.md](./01-Architecture-Overview.md)

**High-level system architecture, design patterns, and module organization**

**Topics Covered**:
- System architecture diagram and component overview
- Module organization (15 modules: core, tools, supporting)
- Multi-workspace architecture (v1.5+)
- Data flow patterns (authentication, workspace selection, workout history, feed aggregation, bulk sync)
- Nutrition & metrics routing through dual calendars
- Metric catalog integration and tooling
- Design patterns (incremental caching, background refresh, headless mode, workspace isolation)
- Directory structure (workspace-aware runtime directories: `~/Turnkey-{workspace}/`)
- Error handling strategy
- Performance optimizations (parallel sync, ThreadPoolExecutor)
- Security considerations (workspace-isolated credentials)
- Extension points for adding new features

**Best For**:
- Understanding the overall system structure
- Identifying where specific functionality lives
- Planning new features or modifications
- Getting a mental model of how components interact

**Key Sections**:
- Component diagrams (15 modules with line counts)
- Workspace selection flow (new in v1.5)
- Authentication flow
- Workout history flow
- Feed aggregation flow
- Bulk sync flow (new in v1.5)
- Smart sync with deletion detection (new in v1.5)
- Nutrition & metrics flow
- Workspace-aware file system structure

---

### [02-API-Client-and-Authentication.md](./02-API-Client-and-Authentication.md)

**API integration, authentication system, token management, and shared utilities**

**Topics Covered**:
- API configuration and base URL
- Token-based authentication flow (workspace-aware)
- Token caching and expiry handling
- Stored credentials with encryption (per workspace)
- Legacy token scanning and migration
- Client management (fetching client list)
- Workout history management with incremental caching
- Smart sync with deletion detection (v1.5+)
- Workout deletion operations (single and batch)
- Exercise database management (with exercise types)
- Metric catalog access
- Headless mode functions for bulk operations
- Shared utility functions (text cleaning, screen clearing)
- Error handling patterns for API requests
- Best practices for API integration

**Best For**:
- Working with API endpoints
- Understanding authentication mechanisms
- Implementing new API calls
- Debugging authentication issues
- Understanding caching strategies

**Key Sections**:
- Workspace-aware authentication flow
- Token cache structure (per workspace)
- Smart sync with deletion detection algorithm
- Workout deletion operations (single and batch)
- Exercise list management (with type information)
- Metric catalog access
- Headless mode pattern
- Error handling patterns

---

### [03-Feed-Tool-Deep-Dive.md](./03-Feed-Tool-Deep-Dive.md)

**Unified feed implementation, the most complex module in the codebase**

**Topics Covered**:
- Feed tool architecture and components (886 lines - largest module)
- Data flow and initialization
- Caching system (messages, workouts index, feed cache)
- Incremental update strategies
- Comment extraction and alias ID system
- Background data refresh with threading
- Headless mode for bulk sync (v1.5+)
- Display system and styling
- Search functionality
- Navigation system (command-based and vim-like modes)
- User interactions (posting messages, replying to comments)
- Exporting and opening in editor
- Performance optimizations

**Best For**:
- Understanding the feed aggregation system
- Debugging feed-related issues
- Adding new feed features
- Understanding threading patterns
- Learning incremental caching techniques

**Key Sections**:
- Feed initialization flow
- Incremental update algorithms
- Background threading model
- Headless mode implementation
- Search and navigation implementation
- Alias ID system for comment replies

---

### [04-PR-Analysis-Tools.md](./04-PR-Analysis-Tools.md)

**Personal record analysis tools for tracking client strength progress**

**Topics Covered**:
- Estimated PR analyzer (pr_tool.py)
- Actual PR viewer (actual_prs_tool.py)
- Wendler 1RM formula implementation
- Workout history processing algorithms
- Main lifts vs other lifts organization
- Wilks score calculation for powerlifting
- Date range filtering
- Display formatting and styling
- Comparison: Estimated vs Actual PRs
- Use cases for each tool

**Best For**:
- Understanding PR calculation logic
- Adding new strength metrics
- Debugging PR analysis issues
- Implementing new formulas (Brzycki, Epley, etc.)
- Understanding the difference between estimated and actual PRs

**Key Sections**:
- Wendler formula implementation
- Workout processing algorithm
- Wilks score calculation
- Tool comparison table
- Use case examples

---

### [05-Workout-Management.md](./05-Workout-Management.md)

**Workout formatting, parsing, uploading, and AI-assisted planning**

**Topics Covered**:
- Workout formatting to custom markup (format_tool.py)
- Workout parsing from text files (upload_tool.py)
- Browse history functionality
- Set parsing patterns (time-based, RPE, percentage, weight, bodyweight)
- Fuzzy exercise name matching
- Unit detection (lbs/kg)
- Nutrition calendar workflow and dual-calendar routing
- Metric ingestion via `@metric` lines and catalog validation
- Upload workflow
- Dry-run validation flow for markup files
- AI chat tool with context loading
- LLM provider integration (OpenAI/xAI)
- Editing AI responses in text editor
- Direct upload of AI-generated workouts

**Best For**:
- Understanding workout data transformations
- Working with the markup language
- Adding new set types or formats
- Debugging upload issues
- Extending AI chat functionality

**Key Sections**:
- Markup formatting rules
- Nutrition workflow checklists
- Set parsing regex patterns
- Fuzzy matching implementation
- AI chat context assembly
- Upload workflow

---

### [06-Data-Formats-and-Caching.md](./06-Data-Formats-and-Caching.md)

**Comprehensive documentation of all data formats, file structures, and caching strategies**

**Topics Covered**:
- Workspace-aware file system structure (`~/Turnkey-{workspace}/`)
- Global settings file (`~/.turnkey_coach_settings.json`)
- All data format specifications:
  - Authentication token cache (per workspace)
  - User settings (global + workspace registry)
  - Exercise list (per workspace)
  - Workout cache (per client per workspace)
  - Workout index (per client per workspace)
  - Messages cache (per client per workspace)
  - Feed cache (per client per workspace)
- Caching strategies (time-based, date-based, timestamp-based, ID-based)
- Data transformation patterns
- UTF-8 handling with encoding_utils (141 lines)
- Best practices for file I/O
- Troubleshooting cache issues

**Best For**:
- Understanding data structures
- Working with cache files
- Debugging data format issues
- Implementing new cache systems
- Ensuring UTF-8 compatibility

**Key Sections**:
- Workspace directory structure
- Global settings format
- Complete JSON structure examples (all cache types)
- Caching strategy comparisons
- Data transformation pipelines
- UTF-8 encoding utilities
- Cache lifecycle management

---

### [07-Development-Setup.md](./07-Development-Setup.md)

**Setup instructions, development workflows, and contribution guidelines**

**Topics Covered**:
- Prerequisites and installation
- Virtual environment setup
- First-run workspace setup (v1.5+)
- Project structure (15 modules with line counts)
- Workspace management for developers
- Development workflow and branching strategy
- Code style guidelines (PEP 8)
- Documentation standards (docstrings)
- Testing strategies (manual and automated, workspace-aware)
- Debugging techniques
- Common development tasks:
  - Adding new tools (workspace-aware)
  - Adding API endpoints (with headless mode)
  - Extending the markup parser
  - Adding configuration options
  - Adding workspace-aware features
- Contributing guidelines
- Pull request process
- Performance optimization (parallel operations)
- Security considerations (workspace isolation)
- Deployment and release process

**Best For**:
- Setting up development environment
- Understanding contribution workflow
- Learning coding standards
- Finding debugging techniques
- Planning new features

**Key Sections**:
- Installation steps
- First-run workspace setup
- Workspace management guide
- Code style guide
- Testing checklist (including workspace testing)
- Common development tasks
- Workspace-aware feature development
- Contributing guidelines
- Troubleshooting (workspace issues)

---

## How to Use These Guides

### For New Developers

**Recommended Reading Order**:
1. [01-Architecture-Overview.md](./01-Architecture-Overview.md) - Start here for the big picture
2. [07-Development-Setup.md](./07-Development-Setup.md) - Set up your environment
3. [02-API-Client-and-Authentication.md](./02-API-Client-and-Authentication.md) - Understand core functionality
4. Topic-specific guides as needed for your work

### For Experienced Developers

**Quick Reference**:
- Jump directly to the relevant guide for your task
- Use guide cross-references to navigate related topics
- Refer to code location references (e.g., `api_client.py:131-135`)

### For AI Agents

These guides are structured to be consumed by AI agents with limited context windows:
- Each guide is self-contained with minimal cross-dependencies
- Code examples include file locations and line numbers
- Clear section headings enable quick navigation
- Comprehensive but concise explanations

**Context Management Strategy**:
- Load only the relevant guide(s) for the current task
- Use TOC.md to identify which guides are needed
- Cross-references point to specific guides when deeper knowledge is required

## Guide Maintenance

### Keeping Guides Up-to-Date

When making code changes:

1. **Update relevant guides** if architecture or patterns change
2. **Update line number references** if code moves significantly
3. **Add new sections** for new features or components
4. **Update code examples** to match current implementation
5. **Cross-reference new guides** in related documents

### Adding New Guides

If the codebase grows significantly:

1. Create new guide following existing naming pattern: `##-Topic-Name.md`
2. Add entry to this TOC.md with summary
3. Add cross-references from related guides
4. Follow existing guide structure (Purpose, Topics, Key Sections, etc.)

## Quick Reference by Task

### I want to...

**...understand how the system works overall**
→ [01-Architecture-Overview.md](./01-Architecture-Overview.md)

**...add a new API endpoint**
→ [02-API-Client-and-Authentication.md](./02-API-Client-and-Authentication.md)
→ [07-Development-Setup.md](./07-Development-Setup.md) (Common Development Tasks)

**...modify the feed tool**
→ [03-Feed-Tool-Deep-Dive.md](./03-Feed-Tool-Deep-Dive.md)

**...add a new PR calculation formula**
→ [04-PR-Analysis-Tools.md](./04-PR-Analysis-Tools.md)

**...add support for a new set type**
→ [05-Workout-Management.md](./05-Workout-Management.md) (Extending the Markup Parser)

**...understand how caching works**
→ [06-Data-Formats-and-Caching.md](./06-Data-Formats-and-Caching.md)

**...set up my development environment**
→ [07-Development-Setup.md](./07-Development-Setup.md)

**...debug an encoding issue**
→ [06-Data-Formats-and-Caching.md](./06-Data-Formats-and-Caching.md) (UTF-8 Handling)

**...contribute code**
→ [07-Development-Setup.md](./07-Development-Setup.md) (Contributing Guidelines)

**...understand the markup language**
→ [05-Workout-Management.md](./05-Workout-Management.md)
→ `../markup.md` (Language Specification)

## Additional Resources

### In This Repository
- `../README.md` - User-facing documentation
- `../markup.md` - Markup language specification
- `../requirements.txt` - Python dependencies
- Code files themselves - Heavily commented for inline reference

### External Resources
- [Python Documentation](https://docs.python.org/3/)
- [Rich Library Docs](https://rich.readthedocs.io/)
- [Requests Library Docs](https://requests.readthedocs.io/)
- [PEP 8 Style Guide](https://pep8.org/)

## Document Metadata

**Created**: 2025-10-11
**Last Updated**: 2025-10-16
**Maintained By**: Development Team
**Total Guides**: 7 core guides + 2 metric references
**Total Documentation Lines**: ~6,500+ lines across all guides
**Codebase**: 15 modules, ~6,800+ lines of Python
**Current Version**: v1.5+ (multi-workspace architecture)

## Feedback and Improvements

These guides are living documents. If you find:
- Outdated information
- Missing coverage
- Confusing explanations
- Broken references

Please contribute improvements via pull request or create an issue.

---

**Happy coding!**
