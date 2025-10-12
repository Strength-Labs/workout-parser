import os
import json
import tempfile
import subprocess
import base64
from cryptography.fernet import Fernet
from openai import OpenAI
from rich.console import Console

# Import shared functions
from api_client import get_workout_history, fetch_metric_catalog
from format_tool import format_workouts_to_markup
from upload_tool import parse_workouts_from_file, upload_workout, build_metric_catalog_index, prepare_assigned_metrics_for_workout
from settings import get_default_editor, get_llm_credentials
from directory_migration import get_client_dir, get_coaching_context_dir
from encoding_utils import safe_open, safe_temp_file, read_text_file, write_text_file

console = Console()

def estimate_token_count(text: str) -> int:
    """Rough estimate of token count (approximately 4 characters per token for English text)."""
    return len(text) // 4

def input_with_completion(prompt: str) -> str:
    """Input with path hints (tab completion attempted but may not work on all systems)."""
    console.print(f"[dim]{prompt}[/dim]")
    console.print(f"[dim]Examples: ~/Documents/file.txt, ./local/file.md, /absolute/path.txt[/dim]")
    try:
        return input("> ").strip()
    except (EOFError, KeyboardInterrupt):
        return ""

def run_ai_chat(token, user_id, client, exercise_map):
    """AI chat for workout assistance."""
    try:
        workouts = get_workout_history(token, client)
    except Exception as e:
        console.print(f"[red]Error loading workout history: {e}[/red]")
        input("Press Enter to continue.")
        return
    valid_workouts = [w for w in workouts if w.get('workout_date')]
    console.print(f"[green]Loaded {len(workouts)} workouts ({len(valid_workouts)} with dates)[/green]")
    if not valid_workouts:
        console.print("[red]No workout history found.[/red]")
        input("Press Enter to continue.")
        return
    valid_workouts.sort(key=lambda w: w['workout_date'])
    markup_content = format_workouts_to_markup(valid_workouts, user_id)

    # Load markup guide
    try:
        markup_guide = read_text_file("markup.md")
    except FileNotFoundError:
        markup_guide = "Markup guide not found. Use standard workout formatting."

    system_prompt = f"You are an AI assistant for strength coaching. Use the following markup guide for workouts: {markup_guide}. The client's workout history is: {markup_content}"
    
    # Display token count estimate for context
    estimated_tokens = estimate_token_count(system_prompt)
    console.print(f"[dim]Context loaded: ~{estimated_tokens:,} tokens[/dim]")

    # Custom context
    custom_context = ""
    if input("Upload custom context file? (y/n): ").lower() == 'y':
        context_dir = get_coaching_context_dir()
        os.makedirs(context_dir, exist_ok=True)
        files = [f for f in os.listdir(context_dir) if f.endswith(('.md', '.txt'))]
        console.print(f"[dim]Coaching context directory: {context_dir}[/dim]")
        console.print("[dim]Add .md or .txt files here for AI chat context.[/dim]")
        if not files:
            console.print("[yellow]No context files found in coaching_context directory.[/yellow]")
            path = input_with_completion("File path")
        else:
            console.print("Available context files:")
            for i, f in enumerate(files):
                console.print(f"  {i+1}. {f}")
            choice = input("Select file number(s) (e.g., 1 or 1,3) or 'm' for manual path: ").strip()
            if choice.lower() == 'm':
                path = input_with_completion("File path")
            else:
                try:
                    indices = [int(x.strip()) - 1 for x in choice.split(',')]
                    for idx in indices:
                        if 0 <= idx < len(files):
                            filepath = os.path.join(context_dir, files[idx])
                            custom_context += read_text_file(filepath) + "\n\n"
                    console.print(f"[green]Loaded context from {len(indices)} file(s)[/green]")
                    path = None  # Don't process path if we used numbered selection
                except ValueError:
                    console.print("[yellow]Invalid selection, switching to manual path entry.[/yellow]")
                    path = input_with_completion("File path")
        # Handle manual file path if provided
        if 'path' in locals() and path and path.strip():
            try:
                # Expand user path (~) and resolve relative paths
                expanded_path = os.path.expanduser(path)
                if not os.path.isabs(expanded_path):
                    expanded_path = os.path.abspath(expanded_path)
                
                if os.path.exists(expanded_path) and os.path.isfile(expanded_path):
                    custom_context += read_text_file(expanded_path) + "\n\n"
                    console.print(f"[green]Loaded context from {os.path.basename(expanded_path)}[/green]")
                else:
                    console.print(f"[red]File not found: {expanded_path}[/red]")
            except Exception as e:
                console.print(f"[red]Error loading file: {e}[/red]")
        
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
                with safe_open(SETTINGS_FILE, 'w') as f:
                    json.dump(settings, f, indent=2, ensure_ascii=False)
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
            client_dir = get_client_dir(client_id)
            os.makedirs(client_dir, exist_ok=True)
            # Create temp file manually for editor workflow
            import tempfile
            try:
                with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt', dir=client_dir, encoding='utf-8') as temp_file:
                    temp_file.write(last_response)
                    temp_path = temp_file.name
            except (OSError, IOError) as e:
                console.print(f"[red]Error creating temp file: {e}[/red]")
                continue
            
            editor_cmd = get_default_editor()
            editor_name = editor_cmd[0] if editor_cmd else 'editor'
            
            # Give editor-specific instructions
            editor_full_cmd = ' '.join(editor_cmd)
            
            # Editors that auto-save when closing (no manual save needed)
            if ('notepad' in editor_name.lower() or 
                ('open' in editor_name.lower() and '-e' in editor_full_cmd)):
                console.print(f"[dim]Opening editor. Make your edits and close the window - it will save automatically.[/dim]")
            
            # Vim-like editors need special instructions
            elif any(vim_editor in editor_name.lower() for vim_editor in ['vim', 'nvim', 'vi']):
                console.print(f"[yellow]Opening in {editor_name}. Use :wq to save and exit, or :q! to exit without saving.[/yellow]")
            
            # All other editors (VS Code, Sublime, nano, etc.) need manual save reminder
            else:
                console.print(f"[yellow]Opening in {editor_full_cmd}. Remember to SAVE your changes before closing![/yellow]")
            
            try:
                subprocess.run(editor_cmd + [temp_path], check=False)
                edited_content = read_text_file(temp_path).strip()
            except (subprocess.SubprocessError, FileNotFoundError, UnicodeDecodeError) as e:
                console.print(f"[red]Error with editor or reading file: {e}[/red]")
                # Clean up temp file and continue
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
                continue
            messages[-1]["content"] = edited_content
            console.print("[green]Updated last response with edited content.[/green]")
            save_name = input("Save edited plan to client directory? Enter filename (or blank to skip): ").strip()
            if save_name:
                save_path = os.path.join(client_dir, save_name)
                write_text_file(save_path, edited_content)
                console.print(f"[green]Saved to {save_path}[/green]")
            
            # Clean up temp file
            try:
                os.remove(temp_path)
            except OSError:
                pass
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
                # Create temp file for upload workflow
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt', encoding='utf-8') as temp_file:
                    temp_file.write(content)
                    temp_path = temp_file.name
                
                try:
                    assignments, _ = parse_workouts_from_file(temp_path, client['id'], exercise_map)
                    pending_total = sum(len(a.get("pending_metrics", [])) for a in assignments)
                    metric_index = {}
                    if pending_total:
                        console.print(f"[dim]Resolving {pending_total} metric placeholder(s) before upload...[/dim]")
                        metric_catalog = fetch_metric_catalog(token)
                        metric_index = build_metric_catalog_index(metric_catalog)
                        if not metric_index:
                            console.print("[yellow]Warning: Could not load metric catalog. Metrics will be skipped.[/yellow]")
                    for assignment in assignments:
                        if metric_index and assignment.get("pending_metrics"):
                            _, skipped = prepare_assigned_metrics_for_workout(assignment, metric_index)
                            for metric in skipped:
                                console.print(
                                    f"[yellow]Warning: Unknown metric '{metric.get('metric_type')}' "
                                    f"on {assignment.get('workout_date')} – skipping.[/yellow]"
                                )
                        else:
                            assignment.pop("pending_metrics", None)
                            assignment.setdefault("assigned_metrics", [])
                        upload_workout(token, assignment)
                finally:
                    # Clean up temp file
                    try:
                        os.remove(temp_path)
                    except OSError:
                        pass
                console.print("[green]Uploaded previous response.[/green]")
            elif choice == '2':
                client_id = client['id']
                client_dir = get_client_dir(client_id)
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
                        assignments, _ = parse_workouts_from_file(file_path, client['id'], exercise_map)
                        pending_total = sum(len(a.get("pending_metrics", [])) for a in assignments)
                        metric_index = {}
                        if pending_total:
                            console.print(f"[dim]Resolving {pending_total} metric placeholder(s) before upload...[/dim]")
                            metric_catalog = fetch_metric_catalog(token)
                            metric_index = build_metric_catalog_index(metric_catalog)
                            if not metric_index:
                                console.print("[yellow]Warning: Could not load metric catalog. Metrics will be skipped.[/yellow]")
                        for assignment in assignments:
                            if metric_index and assignment.get("pending_metrics"):
                                _, skipped = prepare_assigned_metrics_for_workout(assignment, metric_index)
                                for metric in skipped:
                                    console.print(
                                        f"[yellow]Warning: Unknown metric '{metric.get('metric_type')}' "
                                        f"on {assignment.get('workout_date')} – skipping.[/yellow]"
                                    )
                            else:
                                assignment.pop("pending_metrics", None)
                                assignment.setdefault("assigned_metrics", [])
                            upload_workout(token, assignment)
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
