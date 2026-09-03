"""Terminal User Interface with persistent language preference, clean wizard, and Pacman progress bar."""

import json
from pathlib import Path
import time
from typing import Optional, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.progress import ProgressColumn, Text, Progress, SpinnerColumn
from rich.table import Table

console = Console(force_terminal=True, legacy_windows=False)

CONFIG_PATH = Path(".paper_harvester_config.json")


def load_saved_language() -> Optional[str]:
    """Load cached language preference if available."""
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            return data.get("language")
        except Exception:
            pass
    return None


def save_language(lang: str) -> None:
    """Save language preference to local config file."""
    try:
        CONFIG_PATH.write_text(json.dumps({"language": lang}), encoding="utf-8")
    except Exception:
        pass


class PacmanColumn(ProgressColumn):
    """Arch Linux 'ILoveCandy' style Pacman progress bar column."""

    def __init__(self, bar_width: int = 24, table_column=None):
        super().__init__(table_column=table_column)
        self.bar_width = bar_width

    def render(self, task) -> Text:
        completed = task.completed
        total = task.total or 100.0
        fraction = min(max(completed / total, 0.0), 1.0)

        eaten = int(fraction * self.bar_width)
        remaining = self.bar_width - eaten
        mouth = "C" if int(time.time() * 4) % 2 == 0 else "c"

        text = Text()
        text.append("[", style="bold green")
        text.append("-" * eaten, style="green")

        if fraction < 1.0:
            text.append(mouth, style="bold yellow")
            pellet_space = remaining - 1
            if pellet_space > 0:
                pellets = "".join("o" if i % 3 == 1 else " " for i in range(pellet_space))
                text.append(pellets, style="bright_white")
        else:
            text.append("-", style="green")

        text.append("] ", style="bold green")
        text.append(f"{int(fraction * 100):3d}%", style="bold green")
        return text


def create_pacman_progress() -> Progress:
    """Instantiate a Rich Progress bar configured with the Pacman bar."""
    return Progress(
        SpinnerColumn(style="bold yellow"),
        PacmanColumn(bar_width=24),
        console=console,
        transient=False,
    )


I18N_STRINGS = {
    "en": {
        "title": "PaperHarvester Setup",
        "q_mode": "? What would you like to do?",
        "opt_mode_1": "Download & Compile",
        "opt_mode_2": "Download Pages Only",
        "prompt_mode": "Select mode [1-2, default=1]: ",
        "q_structure": "? Output structure:",
        "opt_struct_1": "Single File (output.md)",
        "opt_struct_2": "Split Directory (output_dossier/)",
        "prompt_struct": "Select structure [1-2, default=1]: ",
        "q_format": "? Output format:",
        "opt_fmt_1": "Markdown (.md)",
        "opt_fmt_2": "Plain Text (.txt)",
        "opt_fmt_3": "JSON (.json)",
        "prompt_fmt": "Select format [1-3, default=1]: ",
        "tag_rec": "[bold green][Recommended][/bold green]",
    },
    "tr": {
        "title": "PaperHarvester Kurulum",
        "q_mode": "? Ne yapmak istersiniz?",
        "opt_mode_1": "Indir ve Derle",
        "opt_mode_2": "Sadece Sayfalari Indir",
        "prompt_mode": "Mod seciniz [1-2, varsayilan=1]: ",
        "q_structure": "? Cikti yapisi:",
        "opt_struct_1": "Tek Dosya (output.md)",
        "opt_struct_2": "Ayrik Klasor (output_dossier/)",
        "prompt_struct": "Yapi seciniz [1-2, varsayilan=1]: ",
        "q_format": "? Cikti formati:",
        "opt_fmt_1": "Markdown (.md)",
        "opt_fmt_2": "Duz Metin (.txt)",
        "opt_fmt_3": "JSON (.json)",
        "prompt_fmt": "Format seciniz [1-3, varsayilan=1]: ",
        "tag_rec": "[bold green][Onerilen][/bold green]",
    },
}


def show_interactive_wizard(forced_lang: Optional[str] = None) -> Tuple[str, str, str, str]:
    """Interactive wizard with language memory, clean numbering, and zero emojis.

    Returns:
        Tuple of (lang, mode, structure_type, format_type)
    """
    lang = forced_lang or load_saved_language()

    if not lang:
        console.print()
        console.print("[bold cyan]? Select Language / Dil Seciniz:[/bold cyan]")
        console.print("  1) English")
        console.print("  2) Turkce")

        lang_input = console.input("[bold cyan]Select language [1-2, default=1]: [/bold cyan]").strip() or "1"
        lang = "tr" if lang_input == "2" else "en"
        save_language(lang)

    t = I18N_STRINGS[lang]
    rec = t["tag_rec"]

    console.print()
    console.print(Panel(f"[bold cyan]{t['title']}[/bold cyan]", border_style="cyan"))

    # Step 1: Mode
    console.print(f"\n[bold green]{t['q_mode']}[/bold green]")
    console.print(f"  1) {t['opt_mode_1']} {rec}")
    console.print(f"  2) {t['opt_mode_2']}")
    mode_input = console.input(f"\n[bold cyan]{t['prompt_mode']}[/bold cyan]").strip() or "1"

    if mode_input == "2":
        return lang, "download_only", "single", "md"

    # Step 2: Structure (Only for Download & Compile)
    console.print(f"\n[bold green]{t['q_structure']}[/bold green]")
    console.print(f"  1) {t['opt_struct_1']} {rec}")
    console.print(f"  2) {t['opt_struct_2']}")
    struct_input = console.input(f"\n[bold cyan]{t['prompt_struct']}[/bold cyan]").strip() or "1"
    selected_structure = "split" if struct_input == "2" else "single"

    # Step 3: Format (Clean without descriptions)
    console.print(f"\n[bold green]{t['q_format']}[/bold green]")
    console.print(f"  1) {t['opt_fmt_1']} {rec}")
    console.print(f"  2) {t['opt_fmt_2']}")
    console.print(f"  3) {t['opt_fmt_3']}")
    fmt_input = console.input(f"\n[bold cyan]{t['prompt_fmt']}[/bold cyan]").strip() or "1"
    fmt_map = {"1": "md", "2": "txt", "3": "json"}
    selected_format = fmt_map.get(fmt_input, "md")

    console.print()
    return lang, "full", selected_structure, selected_format


def estimate_tokens(text: str) -> int:
    """Rough heuristic token estimation (~1.33 tokens per word)."""
    if not text:
        return 0
    return int(len(text.split()) * 1.33)


def print_token_analytics(total_text: str) -> None:
    """Display token analysis card without mentioning specific model names."""
    tokens = estimate_tokens(total_text)
    word_count = len(total_text.split())

    table = Table(box=None, show_header=False, padding=(0, 2))
    table.add_row("[bold cyan]Estimated Word Count:[/bold cyan]", f"{word_count:,}")
    table.add_row("[bold cyan]Estimated Token Count:[/bold cyan]", f"~{tokens:,} Tokens")

    if tokens > 200_000:
        status_msg = (
            "[bold yellow]! Large Dossier (>200,000 Tokens)[/bold yellow]\n"
            "[dim]Note: Please be mindful of context window limits when passing this synthesis to AI models in a single prompt.[/dim]"
        )
        border_style = "yellow"
    else:
        status_msg = (
            "[bold green]Safe Context Size (<=200,000 Tokens)[/bold green]\n"
            "[dim]This document comfortably fits within modern AI context windows in a single turn.[/dim]"
        )
        border_style = "green"

    table.add_row("[bold cyan]Context Assessment:[/bold cyan]", status_msg)
    console.print()
    console.print(Panel(table, title="[bold cyan]Content & Token Analytics[/bold cyan]", border_style=border_style))
