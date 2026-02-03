# Streamlit Port and Theme Configuration

**Date:** 2026-02-03
**Status:** Approved

## Overview

Add static Streamlit configuration to set the default port to 8560 and force dark mode theme.

## Motivation

Users need a consistent port configuration and theme without having to pass CLI arguments each time they run the application.

## Design

### Configuration File

Create `.streamlit/config.toml` with:

```toml
[server]
port = 8560

[theme]
base = "dark"

[browser]
gatherUsageStats = false
```

**Rationale:**
- Port 8560 as default (instead of Streamlit's 8501)
- Dark theme forced for consistent UI experience
- Usage stats disabled for privacy
- Static config file checked into git for team consistency

### Location

`.streamlit/config.toml` at repository root. Streamlit automatically reads this file on startup.

### Documentation Updates

Update `CLAUDE.md` configuration section to document:
- Location of Streamlit config file
- Default port setting
- Theme configuration
- How to override via CLI if needed

## Implementation

1. Create `.streamlit/` directory
2. Create `.streamlit/config.toml` with settings above
3. Update `CLAUDE.md` documentation
4. Commit changes

## Alternatives Considered

**Dynamic .env generation:** Generate config from .env PORT variable at runtime. Rejected as unnecessarily complex for a simple static setting.

**Wrapper script:** Create run.sh to pass port as CLI argument. Rejected in favor of native Streamlit config system.

## Trade-offs

**Pros:**
- Simple, leverages Streamlit's native config
- One file to edit for port changes
- Consistent across all users
- No code changes needed

**Cons:**
- Port setting is not in .env with other environment variables
- Users must edit .toml to change port (not a .env variable)
