"""Exercise both decoys locally; never sends traffic to an external host."""

import argparse
import asyncio
import socket
from pathlib import Path

import asyncssh
import httpx


SSH_COMMANDS = [
    "whoami",
    "pwd",
    "ls",
    "cat /etc/passwd",
    "uname -a",
    "id",
    "wget http://127.0.0.1:9/payload",
    "curl http://127.0.0.1:9/payload",
    "chmod 777 /tmp/payload",
    "cmd.exe /c echo ESCAPED > .runtime/ssh-host-escape-marker",
    "exit",
]


async def verify_ssh(host: str, port: int, escape_marker: Path) -> None:
    escape_marker.unlink(missing_ok=True)
    async with asyncssh.connect(
        host,
        port=port,
        username="admin",
        password="native-validation-only",
        known_hosts=None,
    ) as connection:
        process = await connection.create_process(term_type="xterm")
        process.stdin.write("\n".join(SSH_COMMANDS) + "\n")
        process.stdin.write_eof()
        output = await process.stdout.read()
        await process.wait()
    assert "admin" in output
    assert "/root" in output
    assert "root:x:0:0" in output
    assert "Linux web-prod-01" in output
    assert "cmd.exe: command not found" in output
    assert not escape_marker.exists(), "virtual shell command escaped to the host"
    print("SSH virtual-shell transcript validated; host escape marker was not created.")


def verify_http(host: str, port: int) -> None:
    with httpx.Client(base_url=f"http://{host}:{port}", timeout=5) as client:
        probes = [
            ("GET", "/admin", {"User-Agent": "native-validation"}, None, 200),
            ("POST", "/login", {}, "username=admin&password=invalid", 401),
            ("GET", "/..%2f..%2fetc/passwd?id=1%20OR%201=1--", {"User-Agent": "sqlmap/native"}, None, 404),
            ("GET", "/api/test?x=%3Bid", {"User-Agent": "nikto/native"}, None, 401),
            ("GET", "/.env", {"User-Agent": "masscan/native"}, None, 404),
        ]
        for method, target, headers, body, expected in probes:
            response = client.request(method, target, headers=headers, content=body)
            assert response.status_code == expected, (target, response.status_code)
    with socket.create_connection((host, port), timeout=5) as connection:
        connection.sendall(b"BROKEN REQUEST\r\n\r\n")
        response = connection.recv(256)
        assert b"400 Bad Request" in response
    print("HTTP decoy accepted login, traversal, SQLi, command-injection, scanner, and malformed probes.")


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--ssh-port", type=int, default=2222)
    parser.add_argument("--http-port", type=int, default=8080)
    args = parser.parse_args()
    await verify_ssh(args.host, args.ssh_port, Path(".runtime/ssh-host-escape-marker"))
    verify_http(args.host, args.http_port)


if __name__ == "__main__":
    asyncio.run(main())
