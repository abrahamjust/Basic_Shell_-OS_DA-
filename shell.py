import os
import sys
import subprocess
import threading
import requests
from rich.console import Console
from rich.syntax import Syntax

console = Console()

if sys.platform == "win32":
    from prompt_toolkit import prompt
    from prompt_toolkit.completion import WordCompleter


    def input_with_completion(prompt_text, commands):
        completer = WordCompleter(commands, ignore_case=True)
        return prompt(prompt_text, completer=completer)
else:
    import readline


    def input_with_completion(prompt_text, commands):
        def complete(text, state):
            results = [cmd for cmd in commands if cmd.startswith(text)]
            return results[state] if state < len(results) else None

        readline.set_completer(complete)
        readline.parse_and_bind("tab: complete")
        return input(prompt_text)

# Command History
history_file = os.path.expanduser("~/.my_shell_history")
if os.path.exists(history_file):
    try:
        readline.read_history_file(history_file)
    except Exception:
        pass


def save_history():
    try:
        readline.write_history_file(history_file)
    except Exception:
        pass


# Alias System
aliases = {}


def execute_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        console.print(Syntax(result.stdout, "bash", theme="monokai", line_numbers=False))
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error:[/red] {e}")


def fetch_web_page(url):
    try:
        response = requests.get(url)
        console.print(Syntax(response.text, "html", theme="monokai", line_numbers=True))
    except requests.RequestException as e:
        console.print(f"[red]Failed to fetch page:[/red] {e}")


def custom_commands(cmd_parts):
    global aliases

    if cmd_parts[0] == "alias":
        if len(cmd_parts) < 3:
            console.print("[yellow]Usage:[/yellow] alias name command")
        else:
            alias_name = cmd_parts[1]
            alias_command = " ".join(cmd_parts[2:])
            aliases[alias_name] = alias_command
            console.print(f"[green]Alias set:[/green] {alias_name} -> {alias_command}")
        return True

    if cmd_parts[0] == "run":
        if len(cmd_parts) < 2:
            console.print("[yellow]Usage:[/yellow] run script.sh")
        else:
            script = cmd_parts[1]
            if os.path.exists(script) and os.access(script, os.X_OK):
                threading.Thread(target=execute_command, args=(f"./{script}",)).start()
            else:
                console.print("[red]Script not found or not executable.[/red]")
        return True

    if cmd_parts[0] == "mkdir":
        if len(cmd_parts) < 2:
            console.print("[yellow]Usage:[/yellow] mkdir directory_name")
        else:
            os.makedirs(cmd_parts[1], exist_ok=True)
            console.print(f"[green]Directory {cmd_parts[1]} created.[/green]")
        return True

    if cmd_parts[0] == "rm":
        if len(cmd_parts) < 2:
            console.print("[yellow]Usage:[/yellow] rm file_or_directory")
        else:
            target = cmd_parts[1]
            if os.path.isdir(target):
                os.rmdir(target)
                console.print(f"[red]Directory {target} removed.[/red]")
            elif os.path.isfile(target):
                os.remove(target)
                console.print(f"[red]File {target} removed.[/red]")
            else:
                console.print("[red]Target does not exist.[/red]")
        return True

    if cmd_parts[0] == "fetch":
        if len(cmd_parts) < 2:
            console.print("[yellow]Usage:[/yellow] fetch URL")
        else:
            threading.Thread(target=fetch_web_page, args=(cmd_parts[1],)).start()
        return True

    if cmd_parts[0] in aliases:
        execute_command(aliases[cmd_parts[0]])
        return True

    return False


def shell_loop():
    commands = ["exit", "alias", "mkdir", "rm", "run", "fetch"]
    while True:
        try:
            cmd = input_with_completion("mysh> ", commands)
            if cmd.strip() == "exit":
                save_history()
                sys.exit(0)

            cmd_parts = cmd.split()
            if not cmd_parts:
                continue

            if custom_commands(cmd_parts):
                continue

            threading.Thread(target=execute_command, args=(cmd,)).start()
        except KeyboardInterrupt:
            console.print("\n[cyan]Use 'exit' to quit the shell.[/cyan]")
        except EOFError:
            console.print("\n[cyan]Exiting shell.[/cyan]")
            save_history()
            break


if __name__ == "__main__":
    console.print("[bold green]Welcome to MyShell! Type 'exit' to quit.[/bold green]")
    shell_loop()
