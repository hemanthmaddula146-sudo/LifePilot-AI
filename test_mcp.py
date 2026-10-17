import json
import sys
import requests

SERVER_URL = "http://127.0.0.1:8000/mcp"


class MCPTestClient:
    def __init__(self, server_url):
        self.server_url = server_url
        self.session_id = None
        self.request_id = 0

        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        })

    def next_id(self):
        self.request_id += 1
        return self.request_id

    def send_request(self, method, params=None):
        payload = {
            "jsonrpc": "2.0",
            "id": self.next_id(),
            "method": method,
        }

        if params is not None:
            payload["params"] = params

        headers = {}

        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id

        response = self.session.post(
            self.server_url,
            json=payload,
            headers=headers,
            timeout=90,
        )

        response.raise_for_status()

        new_session_id = response.headers.get("Mcp-Session-Id")

        if new_session_id:
            self.session_id = new_session_id

        content_type = response.headers.get("Content-Type", "")

        if "text/event-stream" in content_type:
            for line in response.text.splitlines():
                if line.startswith("data:"):
                    data = line[5:].strip()

                    if data:
                        try:
                            message = json.loads(data)

                            if "id" in message:
                                return message

                        except json.JSONDecodeError:
                            continue

            raise RuntimeError(
                f"No JSON-RPC response found: {response.text}"
            )

        if not response.text.strip():
            return None

        return response.json()

    def notify(self, method):
        payload = {
            "jsonrpc": "2.0",
            "method": method,
        }

        headers = {}

        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id

        response = self.session.post(
            self.server_url,
            json=payload,
            headers=headers,
            timeout=30,
        )

        response.raise_for_status()

    def initialize(self):
        print("\n1. Initializing MCP session...")

        response = self.send_request(
            "initialize",
            {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {
                    "name": "LifePilot-Test-Client",
                    "version": "1.0.0",
                },
            },
        )

        if not response or "error" in response:
            raise RuntimeError(
                f"Initialization failed: {response}"
            )

        self.notify("notifications/initialized")

        result = response.get("result", {})

        print("MCP session initialized successfully.")
        print(
            "Server:",
            result.get("serverInfo", {}).get("name", "Unknown"),
        )
        print(
            "Protocol:",
            result.get("protocolVersion", "Unknown"),
        )

    def list_tools(self):
        print("\n2. Discovering MCP tools...")

        response = self.send_request("tools/list")

        if not response or "error" in response:
            raise RuntimeError(
                f"Tool discovery failed: {response}"
            )

        tools = response.get("result", {}).get("tools", [])

        for tool in tools:
            print(f" - {tool['name']}")

        print(f"Total tools discovered: {len(tools)}")

        return {tool["name"] for tool in tools}

    def call_tool(self, name, arguments):
        response = self.send_request(
            "tools/call",
            {
                "name": name,
                "arguments": arguments,
            },
        )

        if not response:
            raise RuntimeError(f"No response from {name}")

        if "error" in response:
            raise RuntimeError(
                f"MCP error calling {name}: {response['error']}"
            )

        result = response.get("result", {})

        print(f"\nResult from {name}:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        if result.get("isError", False):
            raise RuntimeError(f"Tool execution failed: {name}")

        return result


def main():
    client = MCPTestClient(SERVER_URL)

    try:
        client.initialize()

        available_tools = client.list_tools()

        expected_tools = {
            "add_task",
            "list_tasks",
            "complete_task",
            "delete_task",
            "calculate_study_time",
            "ask_lifepilot_ai",
        }

        missing_tools = expected_tools - available_tools

        if missing_tools:
            print("\nERROR: Missing tools:", sorted(missing_tools))
            print(
                "Check that server.py contains the Gemini tool "
                "and that the updated server is running."
            )
            return 1

        print("\nSUCCESS: All six MCP tools are available.")

        print("\n3. Testing study-time calculation...")

        client.call_tool(
            "calculate_study_time",
            {
                "total_minutes": 180,
                "subjects": [
                    "Java",
                    "Python",
                    "Machine Learning",
                ],
            },
        )

        print("\n4. Testing Gemini AI through MCP...")

        client.call_tool(
            "ask_lifepilot_ai",
            {
                "question": (
                    "Give me a simple three-step plan to learn "
                    "Java as a beginner. Keep it concise."
                )
            },
        )

        print("\nSUCCESS: Gemini and MCP integration test completed.")
        return 0

    except requests.RequestException as error:
        print(f"\nHTTP CONNECTION ERROR: {error}")
        print(f"Check the MCP server at {SERVER_URL}")
        return 1

    except Exception as error:
        print(f"\nTEST FAILED: {error}")
        return 1

    finally:
        client.session.close()


if __name__ == "__main__":
    sys.exit(main())