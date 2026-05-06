"""CLI interface for geoagent."""
import os
import sys
import click
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from geoagent.config import Config
from geoagent.pipeline import Pipeline
from geoagent.geo.rules import GEORules


DEFAULT_CONFIG_PATH = os.path.expanduser("~/.geoagent/config.yaml")


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """GeoAgent - GEO-optimized article transformation CLI."""
    pass


def process_single_file(args, verbose=False):
    """Process a single file. Returns (success, filename, output_count, error)."""
    md_file, pipeline, output_dir, target_languages = args

    try:
        output_files = pipeline.transform(str(md_file), output_dir, target_languages)
        return (True, md_file.name, len(output_files), None)
    except Exception as e:
        return (False, md_file.name, 0, str(e))


@cli.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.option('--model', default=None, help='Model to use (provider/model)')
@click.option('--output-dir', default='./output', help='Output directory')
@click.option('--geo-rules', default=None, help='Custom GEO rules file')
@click.option('--lang', default='en', help='Target languages (comma-separated)')
@click.option('--verbose', is_flag=True, help='Show detailed logs')
@click.option('--recursive', '-r', is_flag=True, help='Process directories recursively')
@click.option('--concurrency', '-c', default=4, help='Number of concurrent threads (default: 4)')
def transform(input_path, model, output_dir, geo_rules, lang, verbose, recursive, concurrency):
    """Transform a markdown article or directory of articles into GEO-optimized versions."""
    config = load_config()

    provider, model_name = parse_model_option(model or config.default_model)

    api_key = os.environ.get(
        config.models.get(provider, config.models.get('minimax')).api_key_env,
        os.environ.get('ANTHROPIC_API_KEY', '')
    )

    if not api_key:
        click.echo("Error: API key not found. Set ANTHROPIC_API_KEY environment variable.", err=True)
        sys.exit(1)

    model_client = config.get_model_client(provider, api_key)

    rules_path = geo_rules or config.geo_rules_path or "shared/rubrics/content-quality-rubric.md"
    geo_rules_obj = GEORules.from_rubric_file(rules_path)

    pipeline = Pipeline(
        model_client=model_client,
        translation_client=model_client,
        geo_rules=geo_rules_obj,
        default_model=model_name,
        max_tokens_translate=config.max_tokens_translate,
        max_tokens_geo=config.max_tokens_geo,
        max_tokens_understand=config.max_tokens_understand
    )

    target_languages = [l.strip() for l in lang.split(',')]

    input_path_obj = Path(input_path)

    if input_path_obj.is_dir():
        md_files = find_markdown_files(input_path_obj, recursive)
        if not md_files:
            click.echo(f"No markdown files found in {input_path}")
            return

        click.echo(f"Found {len(md_files)} markdown file(s) to process")
        click.echo(f"Model: {provider}/{model_name}")
        click.echo(f"Target languages: {target_languages}")
        click.echo(f"Concurrency: {concurrency}")
        click.echo(f"Output directory: {output_dir}")
        click.echo("")

        total_files = 0
        success_count = 0
        failed_count = 0

        # Prepare work items
        work_items = [(f, pipeline, output_dir, target_languages) for f in md_files]

        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = {executor.submit(process_single_file, item, verbose): item[0] for item in work_items}

            for future in as_completed(futures):
                success, filename, count, error = future.result()
                if success:
                    success_count += 1
                    total_files += count
                    click.echo(f"  ✓ {filename} → {count} files")
                else:
                    failed_count += 1
                    click.echo(f"  ✗ {filename} failed: {error}", err=True)

        click.echo(f"\nTotal: {total_files} files generated ({success_count} succeeded, {failed_count} failed)")
    else:
        if verbose:
            click.echo(f"Input: {input_path}")
            click.echo(f"Model: {provider}/{model_name}")
            click.echo(f"Target languages: {target_languages}")
            click.echo(f"Output directory: {output_dir}")

        try:
            output_files = pipeline.transform(input_path, output_dir, target_languages)
            click.echo(f"\nGenerated {len(output_files)} files:")
            for f in output_files:
                click.echo(f"  - {f}")
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)


def find_markdown_files(directory: Path, recursive: bool) -> list[Path]:
    """Find all markdown files in a directory."""
    if recursive:
        return sorted(directory.rglob("*.md"))
    return sorted(directory.glob("*.md"))


def load_config() -> Config:
    """Load configuration from default or custom path."""
    if os.path.exists(DEFAULT_CONFIG_PATH):
        return Config.from_file(DEFAULT_CONFIG_PATH)

    return Config.default()


def parse_model_option(model_str: str) -> tuple[str, str]:
    """Parse model string like 'minimax/MiniMax-M2.7' into (provider, model)."""
    if '/' in model_str:
        provider, model = model_str.split('/', 1)
        return provider, model
    return "minimax", model_str


def main():
    cli()


if __name__ == "__main__":
    main()
