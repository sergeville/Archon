# Fix Archon MCP Connection - Step by Step Guide

## What's Wrong
Claude is trying to connect to Archon MCP on port 3737 (the web UI), but the actual MCP server is running on port 8051.

## Follow These Steps

### Step 1: Close Claude Completely
1. Quit Claude desktop app (Cmd+Q or Claude menu → Quit Claude)
2. Make sure it's fully closed (check Activity Monitor if unsure)

### Step 2: Edit the Configuration File

Open Terminal and run this command:

```bash
open -a TextEdit ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

Or if you prefer VS Code:

```bash
code ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

### Step 3: Find and Update the Archon Configuration

Look for the section that mentions "archon". It will look something like this:

```json
{
  "mcpServers": {
    "archon": {
      "command": "uvx",
      "args": ["--from", "mcp", "mcp-client-stdio", "http://localhost:3737/sse"],
      "env": {
        "ARCHON_MCP_URL": "http://localhost:3737"
      }
    }
  }
}
```

**Change BOTH instances of 3737 to 8051:**

```json
{
  "mcpServers": {
    "archon": {
      "command": "uvx",
      "args": ["--from", "mcp", "mcp-client-stdio", "http://localhost:8051/sse"],
      "env": {
        "ARCHON_MCP_URL": "http://localhost:8051"
      }
    }
  }
}
```

### Step 4: Save and Close the File

- In TextEdit: File → Save (or Cmd+S)
- Close the editor

### Step 5: Restart Claude

1. Open Claude desktop app again
2. Go to Settings → Developer → Local MCP servers
3. Check that the archon server now shows as "Connected" (green) instead of showing an error

## Verify It's Working

Once Claude restarts, you should see:
- ✅ Archon server status: Connected
- ✅ No "Server disconnected" error
- ✅ The port should now show as 8051

## Troubleshooting

### If the file doesn't exist:
The config file might be in a different location. Try:
```bash
find ~/Library -name "claude_desktop_config.json" 2>/dev/null
```

### If you still see errors after changing:
1. Make sure you saved the file
2. Make sure Claude is completely closed before editing
3. Check that Docker is running: `docker ps | grep archon-mcp`
4. Verify the MCP server is healthy: `curl http://localhost:8051/health`

### If the archon-mcp container isn't running:
```bash
cd /Users/sergevilleneuve/Documents/Archon
docker compose up -d archon-mcp
```

## Quick Verification Commands

After making the change, you can verify everything is working:

```bash
# Check if MCP server is running
docker ps | grep archon-mcp

# Test MCP server health
curl http://localhost:8051/health

# Should return something like: {"success":true,"health":{"status":"healthy"}}

# Check MCP server logs
docker compose logs archon-mcp --tail 50

# Check for tool registration
docker compose logs archon-mcp | grep "registered"
```

## Full Validation Report

For a comprehensive validation of your MCP setup, including all available tools and their status, see: [`archon-mcp-validation-report.md`](./archon-mcp-validation-report.md)

This report includes:

- Configuration validation
- Server health status
- Complete list of all MCP tools
- Tool registration verification
- Active tool usage logs
- Troubleshooting reference

---

**Note:** Keep this file open in another window so you can reference it while Claude is closed!
