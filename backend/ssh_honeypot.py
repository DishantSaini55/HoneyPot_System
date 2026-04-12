import os
import asyncio
import asyncssh
import logging
import uuid
import aiohttp
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Basic console logging so you can watch hackers in real-time
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - [HONEYPOT] - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ssh_honeypot")

load_dotenv()

DEFAULT_MODEL = os.getenv("FEATHERLESS_MODEL", "Qwen/Qwen2.5-7B-Instruct")
DEFAULT_BASE_URL = os.getenv("FEATHERLESS_BASE_URL", "https://api.featherless.ai/v1")
API_KEY = os.getenv("FEATHERLESS_API_KEY", "").strip()

# Initialize async OpenAI client
client = AsyncOpenAI(base_url=DEFAULT_BASE_URL, api_key=API_KEY) if API_KEY else None

async def query_llm_deception_engine(command: str, process=None) -> str:
    """Uses Featherless.ai (Qwen) to generate fake, highly realistic terminal outputs."""
    if not client:
        return "bash: API_KEY missing. Cannot contact Generative Deception Engine."
    
    system_prompt = (
        "You are a Debian Linux embedded terminal. The user attempts commands as root on a compromised server. "
        "Your task is to return ONLY the exact raw terminal output of their command. "
        "DO NOT use markdown formatting blocks like ```bash or ```txt. "
        "DO NOT add conversational text or explanations. Act strictly as a command-line interface. "
        "If reading a file (e.g. /etc/shadow, /etc/passwd or AWS keys), generate highly realistic fake data formats. "
        "If the command is destructive (like 'rm -rf /'), simulate a realistic permission denied error. "
        "CRITICAL: The filesystem is highly populated. If the user runs 'ls', 'ls -la', or similar commands, NEVER return 'total 0' or an empty list. "
        "ALWAYS hallucinate a highly realistic, complex directory structure with configuration files (docker-compose.yml, .env), "
        "hidden folders (.ssh/, .aws/, .bash_history), logs, web app source code (src/, node_modules/), and credentials. "
        "Make it look like a production machine."
    )
    
    try:
        if process:
            response = await client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"The attacker typed: {command}"}
                ],
                temperature=0.7,
                max_tokens=600,
                stream=True
            )
            
            content_chunks = []
            async for chunk in response:
                if chunk.choices and len(chunk.choices) > 0:
                    token = chunk.choices[0].delta.content or ""
                    if token:
                        content_chunks.append(token)
                        process.stdout.write(token.replace('\n', '\r\n'))
            
            content = "".join(content_chunks).strip()
        else:
            response = await client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"The attacker typed: {command}"}
                ],
                temperature=0.7,
                max_tokens=600
            )
            content = (response.choices[0].message.content or "").strip()
        
        # Strip out any markdown fences if the AI mistakenly added them
        if content.startswith("```"):
            lines = content.split('\n')
            
            # Remove top row (```bash) and bottom row (```)
            if lines[0].startswith("```"): lines = lines[1:]
            if len(lines) > 0 and lines[-1].startswith("```"): lines = lines[:-1]
            
            content = "\n".join(lines).strip()
            
        return content
    except Exception as e:
        logger.error(f"LLM Engine Error: {e}")
        return "bash: I/O disk error. Retry read/write sequence."


class HoneypotSSHServer(asyncssh.SSHServer):
    """Handles the SSH protocol layer authentication and setup."""
    def connection_made(self, conn):
        self._conn = conn
        logger.info(f"Incoming SSH attack detected from {conn.get_extra_info('peername')[0]}")

    def connection_lost(self, exc):
        logger.info("The attacker abruptly disconnected.")

    def begin_auth(self, username):
        return True

    def password_auth_supported(self):
        return True

    def validate_password(self, username, password):
        # We accept EVERY login attempt, regardless of credentials.
        logger.info(f"Hacker attempting login -> Username: '{username}' | Password: '{password}'")
        return True


async def push_telemetry(data):
    """Pushes live SSH events to the React Dashboard via Flask."""
    try:
        async with aiohttp.ClientSession() as session:
            await session.post("http://127.0.0.1:5000/api/telemetry/logs", json=data)
    except Exception as e:
        logger.error(f"Failed to push telemetry to dashboard API: {e}")


async def handle_interactive_shell(process):
    """Manages the fake bash prompt loop after successful login."""
    
    # Notify React dashboard a connection began
    try:
        hack_ip = process.get_extra_info('peername')[0]
    except Exception:
        hack_ip = "Unknown IP"
    
    await push_telemetry({
        "id": str(uuid.uuid4()), 
        "type": "connection", 
        "message": f"Connection established from {hack_ip}. Interactive shell spawned."
    })
    
    # Print the MOTD (Message of the Day) that hackers expect on logging in
    motd = (
        "Welcome to Ubuntu 22.04.3 LTS (GNU/Linux 5.15.0-1053-aws x86_64)\r\n\r\n"
        " * Documentation:  https://help.ubuntu.com\r\n"
        " * Management:     https://landscape.canonical.com\r\n"
        " * Support:        https://ubuntu.com/advantage\r\n\r\n"
        "Last login: Wed Oct 11 14:23:45 2023 from 192.168.1.101\r\n"
    )
    process.stdout.write(motd)
    
    prompt = "root@target:~# "
    process.stdout.write(prompt)
    
    while True:
        try:
            command = ""
            while True:
                char = await process.stdin.read(1)
                if not char: # EOF
                    break
                if char in ('\r', '\n'):
                    process.stdout.write('\r\n') # echo newline
                    break
                elif char == '\x08' or char == '\x7f': # backspace
                    if len(command) > 0:
                        command = command[:-1]
                        process.stdout.write('\b \b') # erase char on screen
                elif char in ('\x03', '\x04'): # Ctrl+C or Ctrl+D
                    break
                else:
                    command += char
                    process.stdout.write(char) # echo back to user
            
            if not char and not command:
                break
                
            command = command.strip()
            if not command:
                process.stdout.write(prompt)
                continue
                
            if command in ['exit', 'quit', 'logout']:
                process.stdout.write("logout\r\n")
                break
                
            logger.info(f"Hacker Executed Command: {command}")
            
            cmd_id = str(uuid.uuid4())
            await push_telemetry({
                "id": cmd_id, 
                "type": "command",
                "command": command, 
                "response": None, 
                "status": "generating"
            })
            
            # Feed the command to the Featherless AI model
            response = await query_llm_deception_engine(command, process=process)
            
            await push_telemetry({
                "id": cmd_id,
                "type": "command", 
                "command": command, 
                "response": response, 
                "status": "done"
            })
            
            # The AI already streamed the text directly to the process stdout line by line
            # We just need to add a final trailing newline before returning the prompt
            if response:
                if not response.endswith('\n'):
                    process.stdout.write('\r\n')
            else:
                process.stdout.write('\r\n')
                
            process.stdout.write(prompt)
                
        except asyncssh.BreakReceived:
            break
        except Exception as e:
            logger.error(f"Shell panic: {e}")
            break

    # Once the loop breaks (hacker exits or disconnects), log the termination
    await push_telemetry({
        "id": str(uuid.uuid4()), 
        "type": "connection", 
        "message": f"Connection terminated from {hack_ip}. Session archived to Threat Intel Database."
    })

async def start_honeypot():
    key_path = 'ssh_host_rsa_key'
    if not os.path.exists(key_path):
        logger.info("Generating new RSA host key (First run only)...")
        key = asyncssh.generate_private_key('ssh-rsa')
        key.write_private_key(key_path)

    logger.info("Deploying AI SSH Honeypot Listener on 0.0.0.0:2222...")
    
    # Expose port 2222 handling SSH TCP connections
    await asyncssh.create_server(
        HoneypotSSHServer, 
        '0.0.0.0', 
        2222,
        server_host_keys=[key_path],
        process_factory=handle_interactive_shell
    )

if __name__ == '__main__':
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(start_honeypot())
        loop.run_forever()
    except (OSError, asyncssh.Error) as exc:
        print(f"Failed to bind SSH engine: {exc}")
    except KeyboardInterrupt:
        logger.info("Honeypot deactivated.")