"""
Vercel MCP Connector
=====================
MCP server for Vercel deployments, projects, domains, and environment variables.

Author: ABBI (Adaptive Second Brain Intelligence)
"""

import os
import json
import httpx
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins="*")

VERCEL_TOKEN = os.environ.get("VERCEL_TOKEN", "")
VERCEL_TEAM_ID = os.environ.get("VERCEL_TEAM_ID", "")
BASE_URL = "https://api.vercel.com"

def vercel_request(method: str, endpoint: str, data: dict = None, params: dict = None) -> dict:
    """Make authenticated request to Vercel API"""
    headers = {
        "Authorization": f"Bearer {VERCEL_TOKEN}",
        "Content-Type": "application/json"
    }
    url = f"{BASE_URL}{endpoint}"
    
    # Add team ID to params if set
    if VERCEL_TEAM_ID:
        params = params or {}
        params["teamId"] = VERCEL_TEAM_ID
    
    try:
        with httpx.Client(timeout=30.0) as client:
            if method == "GET":
                response = client.get(url, headers=headers, params=params)
            elif method == "POST":
                response = client.post(url, headers=headers, json=data, params=params)
            elif method == "PATCH":
                response = client.patch(url, headers=headers, json=data, params=params)
            elif method == "DELETE":
                response = client.delete(url, headers=headers, params=params)
            elif method == "PUT":
                response = client.put(url, headers=headers, json=data, params=params)
            else:
                return {"error": f"Unknown method: {method}"}
            
            if response.status_code in [200, 201, 202, 204]:
                if response.status_code == 204:
                    return {"success": True}
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}", "details": response.text[:500]}
    except Exception as e:
        return {"error": str(e)}

TOOLS = [
    {
        "name": "list_projects",
        "description": "List all Vercel projects",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 20, "description": "Max projects to return"}
            }
        }
    },
    {
        "name": "get_project",
        "description": "Get details of a specific project",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID or name"}
            },
            "required": ["project_id"]
        }
    },
    {
        "name": "create_project",
        "description": "Create a new Vercel project",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Project name"},
                "framework": {"type": "string", "description": "Framework preset (nextjs, react, vue, etc.)"},
                "git_repository": {"type": "object", "description": "Git repository config {type, repo}"}
            },
            "required": ["name"]
        }
    },
    {
        "name": "delete_project",
        "description": "Delete a Vercel project",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID or name"}
            },
            "required": ["project_id"]
        }
    },
    {
        "name": "list_deployments",
        "description": "List deployments for a project",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID or name"},
                "limit": {"type": "integer", "default": 10},
                "state": {"type": "string", "enum": ["BUILDING", "ERROR", "INITIALIZING", "QUEUED", "READY", "CANCELED"]}
            }
        }
    },
    {
        "name": "get_deployment",
        "description": "Get details of a specific deployment",
        "inputSchema": {
            "type": "object",
            "properties": {
                "deployment_id": {"type": "string", "description": "Deployment ID or URL"}
            },
            "required": ["deployment_id"]
        }
    },
    {
        "name": "cancel_deployment",
        "description": "Cancel a running deployment",
        "inputSchema": {
            "type": "object",
            "properties": {
                "deployment_id": {"type": "string", "description": "Deployment ID"}
            },
            "required": ["deployment_id"]
        }
    },
    {
        "name": "list_domains",
        "description": "List all domains",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 20}
            }
        }
    },
    {
        "name": "add_domain",
        "description": "Add a domain to a project",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "domain": {"type": "string", "description": "Domain name to add"}
            },
            "required": ["project_id", "domain"]
        }
    },
    {
        "name": "remove_domain",
        "description": "Remove a domain from a project",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "domain": {"type": "string", "description": "Domain name to remove"}
            },
            "required": ["project_id", "domain"]
        }
    },
    {
        "name": "list_env_vars",
        "description": "List environment variables for a project",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"}
            },
            "required": ["project_id"]
        }
    },
    {
        "name": "create_env_var",
        "description": "Create an environment variable",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "key": {"type": "string", "description": "Variable name"},
                "value": {"type": "string", "description": "Variable value"},
                "target": {"type": "array", "items": {"type": "string"}, "description": "Targets: production, preview, development"}
            },
            "required": ["project_id", "key", "value"]
        }
    },
    {
        "name": "delete_env_var",
        "description": "Delete an environment variable",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "env_id": {"type": "string", "description": "Environment variable ID"}
            },
            "required": ["project_id", "env_id"]
        }
    },
    {
        "name": "redeploy",
        "description": "Trigger a redeployment of the latest deployment",
        "inputSchema": {
            "type": "object",
            "properties": {
                "deployment_id": {"type": "string", "description": "Deployment ID to redeploy"}
            },
            "required": ["deployment_id"]
        }
    },
    {
        "name": "get_user",
        "description": "Get current authenticated user info",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]

def handle_tool_call(name: str, args: dict) -> dict:
    """Execute tool and return result"""
    try:
        if name == "list_projects":
            result = vercel_request("GET", "/v9/projects", params={"limit": args.get("limit", 20)})
            
        elif name == "get_project":
            result = vercel_request("GET", f"/v9/projects/{args['project_id']}")
            
        elif name == "create_project":
            data = {"name": args["name"]}
            if args.get("framework"):
                data["framework"] = args["framework"]
            if args.get("git_repository"):
                data["gitRepository"] = args["git_repository"]
            result = vercel_request("POST", "/v10/projects", data=data)
            
        elif name == "delete_project":
            result = vercel_request("DELETE", f"/v9/projects/{args['project_id']}")
            
        elif name == "list_deployments":
            params = {"limit": args.get("limit", 10)}
            if args.get("project_id"):
                params["projectId"] = args["project_id"]
            if args.get("state"):
                params["state"] = args["state"]
            result = vercel_request("GET", "/v6/deployments", params=params)
            
        elif name == "get_deployment":
            result = vercel_request("GET", f"/v13/deployments/{args['deployment_id']}")
            
        elif name == "cancel_deployment":
            result = vercel_request("PATCH", f"/v12/deployments/{args['deployment_id']}/cancel")
            
        elif name == "list_domains":
            result = vercel_request("GET", "/v5/domains", params={"limit": args.get("limit", 20)})
            
        elif name == "add_domain":
            result = vercel_request("POST", f"/v10/projects/{args['project_id']}/domains", data={"name": args["domain"]})
            
        elif name == "remove_domain":
            result = vercel_request("DELETE", f"/v9/projects/{args['project_id']}/domains/{args['domain']}")
            
        elif name == "list_env_vars":
            result = vercel_request("GET", f"/v9/projects/{args['project_id']}/env")
            
        elif name == "create_env_var":
            data = {
                "key": args["key"],
                "value": args["value"],
                "target": args.get("target", ["production", "preview", "development"]),
                "type": "encrypted"
            }
            result = vercel_request("POST", f"/v10/projects/{args['project_id']}/env", data=data)
            
        elif name == "delete_env_var":
            result = vercel_request("DELETE", f"/v9/projects/{args['project_id']}/env/{args['env_id']}")
            
        elif name == "redeploy":
            result = vercel_request("POST", f"/v13/deployments", data={
                "deploymentId": args["deployment_id"],
                "target": "production"
            })
            
        elif name == "get_user":
            result = vercel_request("GET", "/v2/user")
            
        else:
            return {"content": [{"type": "text", "text": f"Unknown tool: {name}"}], "isError": True}
        
        return {"content": [{"type": "text", "text": json.dumps(result, indent=2, default=str)}]}
        
    except Exception as e:
        logger.error(f"Tool error {name}: {e}")
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}], "isError": True}

def process_mcp_message(data: dict) -> dict:
    method = data.get("method", "")
    params = data.get("params", {})
    request_id = data.get("id", 1)
    
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {"listChanged": True}},
                "serverInfo": {"name": "vercel-mcp", "version": "1.0.0"}
            }
        }
    elif method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOLS}}
    elif method == "tools/call":
        result = handle_tool_call(params.get("name", ""), params.get("arguments", {}))
        return {"jsonrpc": "2.0", "id": request_id, "result": result}
    elif method == "notifications/initialized":
        return {"jsonrpc": "2.0", "id": request_id, "result": {}}
    else:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}

@app.route("/", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "vercel-mcp",
        "version": "1.0.0",
        "tools": len(TOOLS),
        "team_id": VERCEL_TEAM_ID[:8] + "..." if VERCEL_TEAM_ID else "not set"
    })

@app.route("/mcp", methods=["POST"])
def mcp_handler():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}), 400
        response = process_mcp_message(data)
        return jsonify(response)
    except Exception as e:
        logger.error(f"MCP handler error: {e}")
        return jsonify({"jsonrpc": "2.0", "id": 1, "error": {"code": -32603, "message": str(e)}}), 500

if __name__ == "__main__":
    logger.info("Vercel MCP starting...")
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
