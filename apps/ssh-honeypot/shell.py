import posixpath
import shlex
from dataclasses import dataclass, field


FILES = {
    "/etc/passwd": "root:x:0:0:root:/root:/bin/bash\nwww-data:x:33:33:www-data:/var/www:/usr/sbin/nologin\napp:x:1001:1001:Application:/srv/app:/bin/bash",
    "/etc/shadow": "root:$y$j9T$decoyHashOnly:19620:0:99999:7:::\napp:$y$j9T$anotherDecoyHash:19620:0:99999:7:::",
    "/home/app/.bash_history": "docker ps\ncd /srv/app\ngit status\n",
    "/srv/app/.env": "DATABASE_HOST=db.internal\nDATABASE_USER=app\nDATABASE_PASSWORD=DECOY-NOT-A-REAL-SECRET\n",
}


@dataclass
class VirtualShell:
    username: str
    cwd: str = "/root"
    history: list[str] = field(default_factory=list)

    @property
    def prompt(self) -> str:
        shown = "~" if self.cwd == "/root" else self.cwd
        return f"{self.username}@web-prod-01:{shown}$ "

    def execute(self, raw: str) -> tuple[str, bool]:
        command = raw.strip()
        if not command:
            return "", False
        self.history.append(command)
        try:
            parts = shlex.split(command)
        except ValueError:
            return "bash: syntax error: unmatched quote", False
        if not parts:
            return "", False
        name, args = parts[0], parts[1:]
        if name in {"exit", "logout", "quit"}:
            return "logout", True
        handlers = {
            "whoami": self._whoami,
            "pwd": self._pwd,
            "ls": self._ls,
            "cd": self._cd,
            "uname": self._uname,
            "id": self._id,
            "ps": self._ps,
            "netstat": self._netstat,
            "ifconfig": self._ifconfig,
            "ip": self._ip,
            "cat": self._cat,
            "history": self._history,
            "wget": self._download,
            "curl": self._download,
            "chmod": self._chmod,
        }
        handler = handlers.get(name)
        if handler is None:
            return f"bash: {name}: command not found", False
        return handler(args), False

    def _whoami(self, _: list[str]) -> str:
        return self.username

    def _pwd(self, _: list[str]) -> str:
        return self.cwd

    def _ls(self, _: list[str]) -> str:
        listings = {
            "/root": "backup  deploy.sh  notes.txt  .ssh",
            "/": "bin  boot  dev  etc  home  lib  opt  root  run  srv  tmp  usr  var",
            "/etc": "hosts  hostname  passwd  shadow  ssh  systemd",
            "/srv/app": "Dockerfile  README.md  app  docker-compose.yml  requirements.txt",
            "/home/app": ".bash_history  .ssh",
        }
        return listings.get(self.cwd, "")

    def _cd(self, args: list[str]) -> str:
        target = args[0] if args else "/root"
        new_path = posixpath.normpath(target if target.startswith("/") else posixpath.join(self.cwd, target))
        allowed = {"/", "/root", "/etc", "/srv", "/srv/app", "/home", "/home/app", "/tmp", "/var", "/var/log"}
        if new_path not in allowed:
            return f"bash: cd: {target}: No such file or directory"
        self.cwd = new_path
        return ""

    def _uname(self, args: list[str]) -> str:
        return "Linux web-prod-01 6.5.0-1025-aws #26-Ubuntu SMP x86_64 GNU/Linux" if "-a" in args else "Linux"

    def _id(self, _: list[str]) -> str:
        return f"uid=1001({self.username}) gid=1001({self.username}) groups=1001({self.username}),27(sudo)"

    def _ps(self, _: list[str]) -> str:
        return "  PID TTY          TIME CMD\n 2147 pts/0    00:00:00 bash\n 2191 pts/0    00:00:00 ps"

    def _netstat(self, _: list[str]) -> str:
        return "Active Internet connections\ntcp  0  0 0.0.0.0:22  0.0.0.0:*  LISTEN\ntcp  0  0 127.0.0.1:5432  0.0.0.0:*  LISTEN"

    def _ifconfig(self, _: list[str]) -> str:
        return "eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500\n        inet 10.42.0.18  netmask 255.255.0.0"

    def _ip(self, _: list[str]) -> str:
        return "2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500\n    inet 10.42.0.18/16 brd 10.42.255.255 scope global eth0"

    def _cat(self, args: list[str]) -> str:
        if not args:
            return ""
        path = posixpath.normpath(args[0] if args[0].startswith("/") else posixpath.join(self.cwd, args[0]))
        return FILES.get(path, f"cat: {args[0]}: No such file or directory")

    def _history(self, _: list[str]) -> str:
        return "\n".join(f"{index + 1:5}  {command}" for index, command in enumerate(self.history))

    def _download(self, args: list[str]) -> str:
        target = next((arg for arg in args if arg.startswith(("http://", "https://"))), None)
        if not target:
            return "curl: no URL specified"
        return f"Connecting to {target}...\nHTTP request sent, awaiting response... 404 Not Found"

    def _chmod(self, _: list[str]) -> str:
        return ""

