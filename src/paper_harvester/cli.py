"""Command-Line Interface supporting Bilingual Interactive Wizard (Path A) and CLI flags (Path B)."""

import argparse
from pathlib import Path
import sys
from typing import Optional

from rich.console import Console
from rich.panel import Panel

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

console = Console(force_terminal=True, legacy_windows=False)

from . import __version__
from .core import PaperHarvester
from .ui import create_pacman_progress, show_interactive_wizard, print_token_analytics

BANNER = r"""[bold cyan]
  ____                         _   _                               _             
 |  _ \ __ _ _ __   ___ _ __  | | | | __ _ _ ____   _____  ___ ___| |_ ___ _ __  
 | |_) / _` | '_ \ / _ \ '__| | |_| |/ _` | '__\ \ / / _ \/ __/ __| __/ _ \ '__| 
 |  __/ (_| | |_) |  __/ |    |  _  | (_| | |   \ V /  __/\__ \__ \ ||  __/ |    
 |_|   \__,_| .__/ \___|_|    |_| |_|\__,_|_|    \_/ \___||___/___/\__\___|_|    
            |_|                                                          v0.1-beta
[/bold cyan]"""


def parse_arguments(args: Optional[list] = None) -> argparse.Namespace:
    """Configure and parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="paper-harvester",
        description="PaperHarvester: Layout-aware academic paper harvester and dossier compiler.",
    )

    parser.add_argument(
        "-s", "--sources",
        type=Path,
        default=None,
        help="Path to the source markdown/text file containing paper links (default: sources.md).",
    )

    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Path for compiled output file or directory (default: output.md, output.txt, or output.json).",
    )

    parser.add_argument(
        "-d", "--papers-dir",
        type=Path,
        default=Path("papers"),
        help="Directory to store downloaded academic papers (default: papers).",
    )

    parser.add_argument(
        "-f", "--format",
        choices=["md", "txt", "json"],
        default=None,
        help="Output compilation format: md (Markdown), txt (Plain Text), json (Structured JSON).",
    )

    parser.add_argument(
        "--download-only",
        action="store_true",
        help="Download and archive papers to disk without running extraction or compilation.",
    )

    parser.add_argument(
        "--compile-only",
        action="store_true",
        help="Compile existing papers from the papers directory without downloading.",
    )

    parser.add_argument(
        "--split",
        action="store_true",
        help="Save output as separate individual files per paper inside a folder instead of a single file.",
    )

    parser.add_argument(
        "-w", "--workers",
        type=int,
        default=4,
        help="Number of concurrent download worker threads (default: 4).",
    )

    parser.add_argument(
        "--force", "--no-cache",
        action="store_true",
        dest="force_download",
        help="Force re-download of papers even if already present locally on disk.",
    )

    parser.add_argument(
        "--lang",
        choices=["en", "tr"],
        default=None,
        help="Language for interactive wizard (en: English, tr: Turkish).",
    )

    parser.add_argument(
        "-t", "--timeout",
        type=int,
        default=30,
        help="Network request timeout in seconds (default: 30).",
    )

    parser.add_argument(
        "--no-interactive",
        action="store_true",
        help="Skip the interactive wizard even if no command-line flags are provided.",
    )

    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    return parser.parse_args(args)


def resolve_sources_file(requested_path: Optional[Path]) -> Path:
    """Find the sources file checking sources.md first, then fallback to TEXT.md."""
    if requested_path:
        return requested_path

    for candidate in [Path("sources.md"), Path("TEXT.md")]:
        if candidate.exists():
            return candidate

    return Path("sources.md")


def main() -> None:
    """Main CLI execution flow supporting both Path A (Wizard) and Path B (Flags)."""
    raw_args = sys.argv[1:]
    args = parse_arguments(raw_args)

    console.print(BANNER)

    is_interactive = len(raw_args) == 0 and not args.no_interactive

    if is_interactive:
        lang, selected_mode, selected_structure, selected_format = show_interactive_wizard(forced_lang=args.lang)
    else:
        if args.download_only:
            selected_mode = "download_only"
        elif args.compile_only:
            selected_mode = "compile_only"
        else:
            selected_mode = "full"

        selected_structure = "split" if args.split else "single"
        selected_format = args.format or "md"

    sources_file = resolve_sources_file(args.sources)
    if not sources_file.exists() and selected_mode != "compile_only":
        console.print(
            f"[bold red]Error:[/bold red] Sources file '{sources_file}' not found.\n"
            f"[dim]Please create a 'sources.md' file or specify one with -s / --sources.[/dim]"
        )
        sys.exit(1)

    if args.output:
        output_file = args.output
    else:
        if selected_structure == "split":
            output_file = Path("output_dossier")
        else:
            output_file = Path(f"output.{selected_format}")

    harvester = PaperHarvester(
        download_dir=args.papers_dir,
        output_file=output_file,
        mode=selected_mode,
        structure_type=selected_structure,
        format_type=selected_format,
        max_workers=args.workers,
        force_download=args.force_download,
        timeout=args.timeout,
    )

    with create_pacman_progress() as progress:
        task_id = progress.add_task("Harvesting papers...", total=100)

        def update_pacman(desc: str, current: int, total: int):
            pct = int((current / total) * 100)
            progress.update(task_id, description=f"[bold green]{desc}[/bold green]", completed=pct)

        try:
            processed_count, accumulated_text = harvester.process_file(
                sources_file,
                progress_callback=update_pacman,
            )
            progress.update(task_id, description="[bold green]Complete![/bold green]", completed=100)
        except Exception as exc:
            console.print(f"\n[bold red]Pipeline Error:[/bold red] {exc}")
            sys.exit(1)

    if selected_mode == "download_only":
        msg = f"Successfully downloaded and archived [bold]{processed_count}[/bold] papers to [bold underline]papers/[/bold underline]."
    else:
        msg = (
            f"Successfully processed [bold]{processed_count}[/bold] papers.\n"
            f"Output generated at: [bold underline cyan]{output_file}[/bold underline cyan]"
        )

    console.print(Panel(msg, title="[bold green]Operation Succeeded[/bold green]", border_style="green"))

    if selected_mode != "download_only" and accumulated_text:
        print_token_analytics(accumulated_text)


if __name__ == "__main__":
    main()
