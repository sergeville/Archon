"""
Application management tools for Archon MCP Server.
"""

import json
import logging
import os
import subprocess
import re
from mcp.server.fastmcp import Context, FastMCP

logger = logging.getLogger(__name__)

IDEA_APP_PATH = '/Users/sergevilleneuve/Documents/MyExperiments/idea-capture-web'
IDEA_APP_CMD = 'npm run dev'

def is_process_running(command_pattern):
    """Check if a process with the given command pattern is running."""
    try:
        # Use ps aux and grep to find the process
        output = subprocess.check_output(['ps', 'aux']).decode()
        for line in output.splitlines():
            if command_pattern in line and 'grep' not in line:
                # Extract PID
                parts = line.split()
                if parts:
                    return int(parts[1])
        return None
    except Exception as e:
        logger.error(f'Error checking process status: {e}')
        return None

def register_app_tools(mcp: FastMCP):
    """Register application management tools."""

    @mcp.tool()
    async def start_idea_app(ctx: Context) -> str:
        """
        Start the 'Idea Capture' web application in the background.
        
        This command navigates to the project directory and launches the 
        development server using nohup to ensure it persists.
        """
        if not os.path.exists(IDEA_APP_PATH):
            return json.dumps({'success': False, 'error': f'Project path not found: {IDEA_APP_PATH}'})
            
        existing_pid = is_process_running(IDEA_APP_CMD)
        if existing_pid:
            return json.dumps({
                'success': True, 
                'message': f'Idea Capture app is already running with PID {existing_pid}',
                'pid': existing_pid,
                'url': 'http://localhost:3000'
            })

        try:
            # Command from user memory: nohup npm run dev > dev.log 2>&1 &
            cmd = f'nohup {IDEA_APP_CMD} > dev.log 2>&1 &'
            
            # Start process
            process = subprocess.Popen(
                cmd,
                shell=True,
                cwd=IDEA_APP_PATH,
                preexec_fn=os.setsid # Create new process group
            )
            
            logger.info(f'Started Idea App at {IDEA_APP_PATH} with PID {process.pid}')
            
            return json.dumps({
                'success': True, 
                'message': 'Idea Capture web application starting in background...',
                'pid': process.pid,
                'url': 'http://localhost:3000'
            })
            
        except Exception as e:
            logger.error(f'Failed to start Idea App: {e}')
            return json.dumps({'success': False, 'error': str(e)})

    @mcp.tool()
    async def get_app_status(ctx: Context, app_name: str = 'idea-capture') -> str:
        """
        Check the status of a background application.
        
        Supported apps: 'idea-capture'
        """
        if app_name == 'idea-capture':
            pid = is_process_running(IDEA_APP_CMD)
            if pid:
                return json.dumps({
                    'success': True,
                    'app': 'Idea Capture',
                    'status': 'running',
                    'pid': pid,
                    'url': 'http://localhost:3000'
                })
            else:
                return json.dumps({
                    'success': True,
                    'app': 'Idea Capture',
                    'status': 'stopped'
                })
        else:
            return json.dumps({'success': False, 'error': f'Unknown application: {app_name}'})

    @mcp.tool()
    async def ensure_app_running(ctx: Context, app_name: str = 'idea-capture') -> str:
        """
        Check if an app is running and restart it if it has crashed or stopped.
        """
        if app_name == 'idea-capture':
            pid = is_process_running(IDEA_APP_CMD)
            if pid:
                return json.dumps({
                    'success': True,
                    'message': f'App is healthy (PID {pid})',
                    'status': 'running'
                })
            else:
                logger.warning(f'App {app_name} not running. Attempting auto-restart...')
                # Re-use start_idea_app logic (calling the tool function directly)
                # Note: FastMCP tools are async, so we await
                return await start_idea_app(ctx)
        else:
            return json.dumps({'success': False, 'error': f'Unknown application: {app_name}'})
