from shell import VirtualShell


def test_virtual_shell_supports_expected_commands_without_host_execution():
    shell = VirtualShell("admin")
    assert shell.execute("whoami") == ("admin", False)
    assert "Linux web-prod-01" in shell.execute("uname -a")[0]
    assert "root:x:0:0" in shell.execute("cat /etc/passwd")[0]
    assert "404 Not Found" in shell.execute("wget http://example.com/payload")[0]
    assert shell.execute("exit") == ("logout", True)


def test_virtual_filesystem_does_not_read_host_paths():
    shell = VirtualShell("admin")
    output, _ = shell.execute("cat C:/Windows/System32/drivers/etc/hosts")
    assert output.endswith("No such file or directory")

