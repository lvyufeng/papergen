"""Discovery CLI commands for research exploration."""

import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(help="Research discovery commands")
console = Console()


@app.command("survey")
def analyze_survey(
    pdf_path: Path = typer.Argument(..., help="Path to survey PDF"),
    topic: str = typer.Option(..., "--topic", "-t", help="Research topic"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output JSON path")
):
    """Analyze a survey paper to understand research landscape."""
    from ..discovery.survey import SurveyAnalyzer
    from ..sources.pdf_extractor import PDFExtractor

    console.print(f"[bold]Analyzing survey:[/bold] {pdf_path.name}")
    console.print(f"[bold]Topic:[/bold] {topic}\n")

    # Extract PDF content
    with console.status("Extracting PDF content..."):
        extractor = PDFExtractor()
        content = extractor.extract(pdf_path)

    # Analyze survey
    with console.status("Analyzing research landscape with AI..."):
        analyzer = SurveyAnalyzer()
        results = analyzer.analyze_survey(content.get("full_text", ""), topic)

    # Display results
    _display_survey_results(results)

    # Save if output specified
    if output:
        import json
        with open(output, 'w') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        console.print(f"\n[green]Results saved to {output}[/green]")


def _display_survey_results(results: dict):
    """Display survey analysis results."""
    # Research gaps
    gaps = results.get("research_gaps", [])
    if gaps:
        console.print("\n[bold cyan]Research Gaps:[/bold cyan]")
        for i, gap in enumerate(gaps, 1):
            if isinstance(gap, dict):
                console.print(f"  {i}. {gap.get('gap', gap)}")
            else:
                console.print(f"  {i}. {gap}")

    # Key papers
    papers = results.get("key_papers_to_read", [])
    if papers:
        console.print("\n[bold cyan]Key Papers to Read:[/bold cyan]")
        for p in papers[:10]:
            if isinstance(p, dict):
                console.print(f"  - {p.get('title', p)}")
            else:
                console.print(f"  - {p}")

    # Future directions
    directions = results.get("future_directions", [])
    if directions:
        console.print("\n[bold cyan]Future Directions:[/bold cyan]")
        for d in directions:
            if isinstance(d, dict):
                console.print(f"  - {d.get('direction', d)}")
            else:
                console.print(f"  - {d}")


@app.command("paper")
def analyze_paper(
    pdf_path: Path = typer.Argument(..., help="Path to paper PDF"),
    title: str = typer.Option(None, "--title", "-t", help="Paper title")
):
    """Deep analysis of a single paper."""
    from ..discovery.papers import PaperFinder
    from ..sources.pdf_extractor import PDFExtractor

    paper_title = title or pdf_path.stem
    console.print(f"[bold]Deep analyzing:[/bold] {paper_title}\n")

    with console.status("Extracting PDF..."):
        extractor = PDFExtractor()
        content = extractor.extract(pdf_path)

    with console.status("Analyzing paper with AI..."):
        finder = PaperFinder()
        results = finder.analyze_paper(content.get("full_text", ""), paper_title)

    _display_paper_analysis(results)


def _display_paper_analysis(results: dict):
    """Display paper analysis results."""
    console.print(Panel(f"[bold]{results.get('title', 'Paper')}[/bold]"))

    if results.get("core_contribution"):
        console.print(f"\n[cyan]Core Contribution:[/cyan] {results['core_contribution']}")

    if results.get("strengths"):
        console.print("\n[green]Strengths:[/green]")
        for s in results["strengths"]:
            console.print(f"  + {s}")

    if results.get("weaknesses"):
        console.print("\n[yellow]Weaknesses:[/yellow]")
        for w in results["weaknesses"]:
            console.print(f"  - {w}")

    if results.get("inspiration_for_new_research"):
        console.print("\n[magenta]Research Inspirations:[/magenta]")
        for i in results["inspiration_for_new_research"]:
            if isinstance(i, dict):
                console.print(f"  * {i.get('idea', i)}")


@app.command("brainstorm")
def brainstorm_ideas(
    topic: str = typer.Argument(..., help="Research topic"),
    num_ideas: int = typer.Option(5, "--num", "-n", help="Number of ideas per LLM"),
    context_file: Optional[Path] = typer.Option(None, "--context", "-c", help="Context JSON from survey"),
    multi_llm: bool = typer.Option(False, "--multi", "-m", help="Use multiple LLMs"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory for reports")
):
    """Generate novel research ideas through AI brainstorming."""
    from ..discovery.brainstorm import IdeaGenerator
    import json

    console.print(f"\n[bold magenta]Brainstorming Research Ideas[/bold magenta]")
    console.print(f"Topic: {topic}")
    if multi_llm:
        console.print("[cyan]Mode: Multi-LLM (parallel generation)[/cyan]\n")
    else:
        console.print("[cyan]Mode: Single LLM[/cyan]\n")

    generator = IdeaGenerator(use_multi_llm=multi_llm)

    # Load context if provided
    if context_file and context_file.exists():
        with open(context_file) as f:
            ctx = json.load(f)
        generator.set_context(
            topic=topic,
            research_gaps=ctx.get("research_gaps", []),
            paper_weaknesses=ctx.get("weaknesses", []),
            future_directions=ctx.get("future_directions", [])
        )
    else:
        generator.set_context(topic=topic, research_gaps=[], paper_weaknesses=[], future_directions=[])

    with console.status(f"Generating {num_ideas} research ideas..."):
        ideas = generator.generate_ideas(num_ideas)

    # Handle multi-LLM output
    if multi_llm:
        _display_multi_llm_results(generator, output)
    else:
        _display_ideas(ideas)


def _display_ideas(ideas: list):
    """Display generated research ideas."""
    for i, idea in enumerate(ideas, 1):
        if isinstance(idea, dict):
            title = idea.get("title", f"Idea {i}")
            console.print(f"\n[bold yellow]Idea {i}: {title}[/bold yellow]")

            if idea.get("one_sentence"):
                console.print(f"  {idea['one_sentence']}")

            if idea.get("novelty"):
                console.print(f"  [cyan]Novelty:[/cyan] {idea['novelty']}")

            if idea.get("feasibility"):
                console.print(f"  [green]Feasibility:[/green] {idea['feasibility']}")

            if idea.get("potential_venues"):
                venues = ", ".join(idea["potential_venues"])
                console.print(f"  [magenta]Target Venues:[/magenta] {venues}")

            if idea.get("first_steps"):
                console.print("  [blue]First Steps:[/blue]")
                for step in idea["first_steps"][:3]:
                    console.print(f"    - {step}")


def _display_multi_llm_results(generator, output: Optional[Path]):
    """Display results from multi-LLM brainstorming."""
    import json

    # Display summary first
    summary = generator.get_summary()
    console.print(Panel("[bold green]Summarized Results[/bold green]"))

    if summary.get("summary"):
        console.print(f"\n[cyan]Summary:[/cyan] {summary['summary']}")

    # Display top recommendations
    if summary.get("top_recommendations"):
        console.print("\n[bold yellow]Top Recommendations:[/bold yellow]")
        for idea in summary["top_recommendations"][:5]:
            if isinstance(idea, dict):
                console.print(f"  - {idea.get('title', idea)}")
            else:
                console.print(f"  - {idea}")

    # Display consensus themes
    if summary.get("consensus_themes"):
        console.print("\n[bold magenta]Consensus Themes:[/bold magenta]")
        for theme in summary["consensus_themes"]:
            console.print(f"  - {theme}")

    # Display individual LLM reports
    reports = generator.get_reports()
    console.print(f"\n[bold]Individual Reports ({len(reports)} LLMs):[/bold]")

    for report in reports:
        console.print(f"\n[cyan]{report.provider}/{report.model}:[/cyan]")
        console.print(f"  Ideas: {len(report.ideas)}")

    # Save reports if output specified
    if output:
        output.mkdir(parents=True, exist_ok=True)
        _save_reports(generator, output)


def _save_reports(generator, output_dir: Path):
    """Save individual LLM reports and summary."""
    import json

    # Save summary
    summary_path = output_dir / "summary.json"
    with open(summary_path, 'w') as f:
        json.dump(generator.get_summary(), f, indent=2, ensure_ascii=False)
    console.print(f"\n[green]Summary saved to {summary_path}[/green]")

    # Save individual reports
    for report in generator.get_reports():
        report_path = output_dir / f"{report.provider}_{report.model}.json"
        report_data = {
            "provider": report.provider,
            "model": report.model,
            "ideas": report.ideas
        }
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        console.print(f"[green]Report saved to {report_path}[/green]")
