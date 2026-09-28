import asyncio
import json
import logging
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path

import asyncssh

from honeypot_sensor import EventClient, EventEnvelope
from shell import VirtualShell


logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(message)s")
logger = logging.getLogger("ssh-honeypot")
PORT = int(os.getenv("SSH_PORT", "2222"))
HOST_KEY_PATH = Path(os.getenv("SSH_HOST_KEY_PATH", "/data/ssh_host_key"))
SESSION_IDLE_TIMEOUT = int(os.getenv("SSH_SESSION_IDLE_TIMEOUT", "300"))
client: EventClient | None = None
sessions: dict[tuple[str, int], str] = {}


def log_event(event: str, **fields) -> None:
    logger.info(json.dumps({"timestamp": datetime.now(UTC).isoformat(), "service": "ssh-honeypot", "event": event, **fields}))


def peer(process_or_connection) -> tuple[str, int]:
    value = process_or_connection.get_extra_info("peername") or ("0.0.0.0", 0)
    return str(value[0]), int(value[1])


async def emit(**kwargs) -> None:
    if client is not None:
        await client.send(EventEnvelope(destination_port=PORT, protocol="SSH", honeypot="SSH", **kwargs))


class SSHServer(asyncssh.SSHServer):
    def connection_made(self, conn) -> None:
        self.connection = conn
        self.source_ip, self.source_port = peer(conn)
        self.session_id = str(uuid.uuid4())
        sessions[(self.source_ip, self.source_port)] = self.session_id
        asyncio.create_task(
            emit(
                source_ip=self.source_ip,
                source_port=self.source_port,
                session_id=self.session_id,
                event_type="CONNECTED",
                payload={"node_name": os.getenv("HONEYPOT_NODE_NAME", "ssh-primary")},
            )
        )
        log_event("connected", session_id=self.session_id, source_ip=self.source_ip)

    def connection_lost(self, exc) -> None:
        sessions.pop((self.source_ip, self.source_port), None)
        log_event("disconnected", session_id=self.session_id, source_ip=self.source_ip, error=type(exc).__name__ if exc else None)

    def begin_auth(self, username: str) -> bool:
        self.username = username
        return True

    def password_auth_supported(self) -> bool:
        return True

    def validate_password(self, username: str, password: str) -> bool:
        asyncio.create_task(
            emit(
                source_ip=self.source_ip,
                source_port=self.source_port,
                session_id=self.session_id,
                event_type="LOGIN_ATTEMPT",
                username=username,
                password=password,
                payload={"node_name": os.getenv("HONEYPOT_NODE_NAME", "ssh-primary"), "accepted_by_decoy": True},
            )
        )
        log_event("login_attempt", session_id=self.session_id, source_ip=self.source_ip, username=username)
        return True


async def handle_shell(process: asyncssh.SSHServerProcess) -> None:
    source_ip, source_port = peer(process)
    session_id = sessions.get((source_ip, source_port), str(uuid.uuid4()))
    username = str(process.get_extra_info("username") or "admin")
    shell = VirtualShell(username=username)
    process.stdout.write(
        "Ubuntu 22.04.4 LTS web-prod-01\r\n"
        "System information as of " + datetime.now(UTC).strftime("%a %b %d %H:%M:%S UTC %Y") + "\r\n\r\n"
    )
    await emit(
        source_ip=source_ip,
        source_port=source_port,
        session_id=session_id,
        event_type="SESSION_STARTED",
        username=username,
        payload={"node_name": os.getenv("HONEYPOT_NODE_NAME", "ssh-primary")},
    )
    try:
        while True:
            process.stdout.write(shell.prompt)
            try:
                line = await asyncio.wait_for(process.stdin.readline(), timeout=SESSION_IDLE_TIMEOUT)
            except TimeoutError:
                process.stdout.write("\r\nConnection timed out.\r\n")
                break
            if not line:
                break
            command = line.strip()
            response, should_exit = shell.execute(command)
            await emit(
                source_ip=source_ip,
                source_port=source_port,
                session_id=session_id,
                event_type="COMMAND",
                username=username,
                command=command,
                simulated_response=response,
                payload={"node_name": os.getenv("HONEYPOT_NODE_NAME", "ssh-primary")},
            )
            if response:
                process.stdout.write(response.replace("\n", "\r\n") + "\r\n")
            if should_exit:
                break
    finally:
        await emit(
            source_ip=source_ip,
            source_port=source_port,
            session_id=session_id,
            event_type="SESSION_ENDED",
            username=username,
            payload={"node_name": os.getenv("HONEYPOT_NODE_NAME", "ssh-primary")},
        )
        process.exit(0)


async def main() -> None:
    global client
    client = EventClient()
    heartbeat = asyncio.create_task(
        client.heartbeat_loop(os.getenv("HONEYPOT_NODE_NAME", "ssh-primary"), "SSH", PORT)
    )
    HOST_KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not HOST_KEY_PATH.exists():
        asyncssh.generate_private_key("ssh-ed25519").write_private_key(HOST_KEY_PATH)
    server = await asyncssh.create_server(
        SSHServer,
        "0.0.0.0",
        PORT,
        server_host_keys=[str(HOST_KEY_PATH)],
        process_factory=handle_shell,
        login_timeout=30,
        keepalive_interval=30,
        keepalive_count_max=3,
    )
    log_event("listening", port=PORT)
    try:
        await server.wait_closed()
    finally:
        heartbeat.cancel()
        await asyncio.gather(heartbeat, return_exceptions=True)
        await client.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (OSError, asyncssh.Error) as exc:
        log_event("startup_failed", error=type(exc).__name__)
        raise SystemExit(1) from exc
