import json
import requests

SERVER_URL = "http://127.0.0.1:8000/mcp"


class MCPClient:
    def __init__(self, server_url):
        self.server_url = server_url
        self.session_id = None
        self.request_id = 0
        self.session = requests.Session()

        self.session.headers.update({
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        })

    def send_request(self, method, params=None):
        self.request_id += 1

        payload = {
            "jsonrpc": "2.0",
            "id": self.request_id,
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
            timeout=30,
        )

        response.raise_for_status()

        session_id = response.headers.get("Mcp-Session-Id")
        if session_id:
            self.session_id = session_id

        if "text/event-stream" in response.headers.get(
            "Content-Type", ""
        ):
            for line in response.text.splitlines():
                if line.startswith("data:"):
                    try:
                        message = json.loads(line[5:].strip())
                        if message.get("id") == payload["id"]:
                            return message
                    except json.JSONDecodeError:
                        continue

            raise RuntimeError("No JSON-RPC response received.")

        return response.json() if response.text.strip() else None

    def initialize(self):
        result = self.send_request(
            "initialize",
            {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {
                    "name": "LifePilot-Task-Tester",
                    "version": "1.0.0",
                },
            },
        )

        if result and "error" in result:
            raise RuntimeError(result["error"])

        self.send_notification("notifications/initialized")
        print("MCP session initialized successfully.")

    def send_notification(self, method):
        response = self.session.post(
            self.server_url,
            json={
                "jsonrpc": "2.0",
                "method": method,
            },
            headers={
                "Mcp-Session-Id": self.session_id,
            },
            timeout=30,
        )

        response.raise_for_status()

    def list_tools(self):
        return self.send_request("tools/list")

    def call_tool(self, name, arguments):
        return self.send_request(
            "tools/call",
            {
                "name": name,
                "arguments": arguments,
            },
        )


def main():
    client = MCPClient(SERVER_URL)

    try:
        client.initialize()

        result = client.list_tools()

        if not result or "result" not in result:
            print("Could not retrieve tools:", result)
            return

        tools = result["result"].get("tools", [])

        print("\nAvailable MCP tools:")
        for tool in tools:
            print("-", tool["name"])

        while True:
            print("\n===== LifePilot-AI Task Tester =====")
            print("1. Add a task")
            print("2. List tasks")
            print("3. Complete a task")
            print("4. Delete a task")
            print("5. Exit")

            choice = input("Choose an option: ").strip()

            if choice == "1":
                title = input("Task title: ").strip()
                description = input("Description: ").strip()
                due_date = input("Due date (optional): ").strip()

                if not title:
                    print("Task title cannot be empty.")
                    continue

                arguments = {
                    "title": title,
                    "description": description,
                    "due_date": due_date,
                }

                name = "add_task"

            elif choice == "2":
                status = input(
                    "Status (all/pending/completed): "
                ).strip().lower() or "all"

                arguments = {"status": status}
                name = "list_tasks"

            elif choice == "3":
                try:
                    task_id = int(input("Task ID to complete: "))
                except ValueError:
                    print("Enter a valid numeric task ID.")
                    continue

                arguments = {"task_id": task_id}
                name = "complete_task"

            elif choice == "4":
                try:
                    task_id = int(input("Task ID to delete: "))
                except ValueError:
                    print("Enter a valid numeric task ID.")
                    continue

                confirm = input(
                    f"Delete task {task_id}? Type YES to confirm: "
                )

                if confirm != "YES":
                    print("Deletion cancelled.")
                    continue

                arguments = {"task_id": task_id}
                name = "delete_task"

            elif choice == "5":
                print("Exiting task tester.")
                break

            else:
                print("Invalid choice.")
                continue

            available_names = {tool["name"] for tool in tools}

            if name not in available_names:
                print(f"Tool '{name}' is not available on this server.")
                print("Check the available tool names above.")
                continue

            result = client.call_tool(name, arguments)

            print("\nResult:")
            print(json.dumps(result, indent=2))

    except requests.RequestException as error:
        print("Connection error:", error)
        print("Check that the MCP server is running.")

    except Exception as error:
        print("Error:", error)


if __name__ == "__main__":
    main()