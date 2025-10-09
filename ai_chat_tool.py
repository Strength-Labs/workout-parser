import os
import json
import tempfile
import subprocess
import base64
from cryptography.fernet import Fernet
from openai import OpenAI
from rich.console import Console

# Import shared functions
from api_client import get_workout_history
from format_tool import format_workouts_to_markup
from upload_tool import parse_workouts_from_file, upload_workout
from settings import get_default_editor, get_llm_credentials

console = Console()

def run_ai_chat(token, user_id, client, exercise_map):
    """AI chat for workout assistance."""
    print("Debug: AI chat started")
    try:
        workouts = get_workout_history(token, client)
    except Exception as e:
        print(f"Error loading workout history: {e}")
        input("Press Enter to continue.")
        return
    valid_workouts = [w for w in workouts if w.get('workout_date')]
    print(f"Debug: Loaded {len(workouts)} workouts, {len(valid_workouts)} valid")
    if not valid_workouts:
        console.print("[red]No workout history found.[/red]")
        input("Press Enter to continue.")
        return
    valid_workouts.sort(key=lambda w: w['workout_date'])
    markup_content = format_workouts_to_markup(valid_workouts, user_id)

    # Load markup guide
    try:
        with open("markup.md", "r", encoding='utf-8') as f:
            markup_guide = f.read()
    except FileNotFoundError:
        markup_guide = "Markup guide not found. Use standard workout formatting."

    system_prompt = f"You are an AI assistant for strength coaching. Use the following markup guide for workouts: {markup_guide}. The client's workout history is: {markup_content}"

    # Custom context
    custom_context = ""
    if input("Upload custom context file? (y/n): ").lower() == 'y':
        CLIENT_DATA_DIR = os.path.expanduser("~/TurnkeyClients")
        context_dir = os.path.join(CLIENT_DATA_DIR, "coaching_context")
        os.makedirs(context_dir, exist_ok=True)
        files = [f for f in os.listdir(context_dir) if f.endswith(('.md', '.txt'))]
        console.print(f"[dim]Coaching context directory: {context_dir}[/dim]")
        console.print("[dim]Add .md or .txt files here for AI chat context.[/dim]")
        if not files:
            console.print("[yellow]No context files found.[/yellow]")
            path = input("File path: ").strip()
        else:
            console.print("Available context files:")
            for i, f in enumerate(files):
                console.print(f"  {i+1}. {f}")
            choice = input("Select file number(s) (e.g., 1 or 1,3) or 'm' for manual path: ").strip()
            if choice.lower() == 'm':
                try:
                    import readline
                    import glob
                    def complete(text, state):
                        return (glob.glob(text+"*")+[None])[state]
                    readline.set_completer(complete)
                    readline.parse_and_bind("tab: complete")
                except ImportError:
                    pass
                path = input("File path: ").strip()
            else:
                try:
                    indices = [int(x.strip()) - 1 for x in choice.split(',')]
                    for idx in indices:
                        if 0 <= idx < len(files):
                            filepath = os.path.join(context_dir, files[idx])
                            with open(filepath, 'r', encoding='utf-8') as f:
                                custom_context += f.read() + "\n\n"
                    console.print(f"[green]Loaded context from {len(indices)} file(s)[/green]")
                except ValueError:
                    path = input("Invalid selection. Enter file path: ").strip()
        if custom_context:
            system_prompt += f"\nAdditional context: {custom_context}"

    # Get LLM credentials
    provider, api_key = get_llm_credentials()
    if not provider:
        provider = input("Provider (openai/xai): ").strip().lower()
        api_key = input("API Key: ").strip()
        save = input("Save to settings? (y/n): ").lower()
        if save == 'y':
            from settings import load_or_init_settings, SETTINGS_FILE
            settings = load_or_init_settings()
            key_str = settings.get('encryption_key')
            if key_str:
                key = base64.urlsafe_b64decode(key_str.encode('utf-8'))
                fernet = Fernet(key)
                encrypted_key = fernet.encrypt(api_key.encode()).decode('utf-8')
                settings['llm_provider'] = provider
                settings['llm_encrypted_key'] = encrypted_key
                with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, indent=2)
                console.print("[green]Saved.[/green]")

    # Set up the client based on provider
    if provider == 'xai':
        try:
            client_ai = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
            model = "grok-4"
        except Exception as e:
            console.print(f"[red]Error setting up xAI client: {e}[/red]")
            input("Press Enter to continue.")
            return
    elif provider == 'openai':
        try:
            client_ai = OpenAI(api_key=api_key)
            model = "gpt-5"
        except Exception as e:
            console.print(f"[red]Error setting up OpenAI client: {e}[/red]")
            input("Press Enter to continue.")
            return
    else:
        console.print("[red]Unsupported provider. Use 'openai' or 'xai'.[/red]")
        input("Press Enter to continue.")
        return

    # Start the chat loop
    messages = [{"role": "system", "content": system_prompt}]
    console.print("[bold green]AI Chat started. Type 'exit' or 'quit' to quit, 'edit' to edit the last AI response, 'upload' to upload workouts.[/bold green]" )

    while True:
        console.print("[bold]You: [/bold]", end="")
        user_input = input()
        if user_input.lower() in ['exit', 'quit']:
            console.print("[dim]Exiting AI chat. Back to the shadows...[/dim]")
            break
        elif user_input.lower() == 'edit':
            if not messages or messages[-1]["role"] != "assistant":
                console.print("No previous AI response to edit.")
                continue
            last_response = messages[-1]["content"]
            client_id = client['id']
            client_dir = os.path.join(os.path.expanduser("~/TurnkeyClients"), str(client_id))
            os.makedirs(client_dir, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt', dir=client_dir, encoding='utf-8') as temp_file:
                temp_file.write(last_response)
                temp_path = temp_file.name
            editor_cmd = get_default_editor()
            subprocess.run(editor_cmd + [temp_path], check=False)
            with open(temp_path, 'r', encoding='utf-8') as f:
                edited_content = f.read().strip()
            messages[-1]["content"] = edited_content
            console.print("[green]Updated last response with edited content.[/green]")
            save_name = input("Save edited plan to client directory? Enter filename (or blank to skip): ").strip()
            if save_name:
                save_path = os.path.join(client_dir, save_name)
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(edited_content)
                console.print(f"[green]Saved to {save_path}[/green]")
            os.remove(temp_path)
            continue
        elif user_input.lower() == 'upload':
            console.print("Upload options:")
            console.print("1. Upload previous AI response")
            console.print("2. Select file from client directory")
            choice = input("Choose (1/2): ").strip()
            if choice == '1':
                if not messages or messages[-1]["role"] != "assistant":
                    console.print("No previous response.")
                    continue
                content = messages[-1]["content"]
                with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt', encoding='utf-8') as temp_file:
                    temp_file.write(content)
                    temp_path = temp_file.name
                workouts_parsed = parse_workouts_from_file(temp_path, client['id'], exercise_map)
                for workout in workouts_parsed:
                    upload_workout(token, workout)
                os.remove(temp_path)
                console.print("[green]Uploaded previous response.[/green]")
            elif choice == '2':
                client_id = client['id']
                client_dir = os.path.join(os.path.expanduser("~/TurnkeyClients"), str(client_id))
                if not os.path.exists(client_dir):
                    console.print("[yellow]Client directory not found.[/yellow]")
                    continue
                files = [f for f in os.listdir(client_dir) if f.endswith('.txt') or f.endswith('.md')]
                if not files:
                    console.print("[yellow]No files found in client directory.[/yellow]")
                    continue
                console.print("Available files:")
                for i, f in enumerate(files):
                    console.print(f"  {i+1}. {f}")
                try:
                    idx = int(input("Select file number: ")) - 1
                    if 0 <= idx < len(files):
                        file_path = os.path.join(client_dir, files[idx])
                        workouts_parsed = parse_workouts_from_file(file_path, client['id'], exercise_map)
                        for workout in workouts_parsed:
                            upload_workout(token, workout)
                        console.print(f"[green]Uploaded {files[idx]}.[/green]")
                    else:
                        console.print("[red]Invalid selection.[/red]")
                except ValueError:
                    console.print("[red]Invalid input.[/red]")
            continue
        else:
            messages.append({"role": "user", "content": user_input})

        try:
            extra_params = {}
            if not model.startswith(("gpt-5", "o1-")):
                extra_params["temperature"] = 0.7
                if provider == 'openai':
                    extra_params['max_completion_tokens'] = 1500
                else:
                    extra_params['max_tokens'] = 1500

            response = client_ai.chat.completions.create(
                model=model,
                messages=messages,
                **extra_params
            )
            ai_response = response.choices[0].message.content.strip()
            console.print(f"[bold cyan]AI:[/bold cyan] [bold]{ai_response}[/bold]")

            messages.append({"role": "assistant", "content": ai_response})

        except Exception as e:
            console.print(f"[red]Error in AI response: {e}[/red]")
