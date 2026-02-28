"""Fetch CLI command — download USGS finite fault data."""
from __future__ import annotations

import logging
from pathlib import Path

import click

logger = logging.getLogger("opencoulomb")


@click.command("fetch")
@click.argument("event_id", required=False, default=None)
@click.option("--search", is_flag=True, help="Search for events instead of fetching")
@click.option("--min-mag", type=float, default=5.0, help="Minimum magnitude for search")
@click.option("--start", type=str, default=None, help="Start date (YYYY-MM-DD)")
@click.option("--end", type=str, default=None, help="End date (YYYY-MM-DD)")
@click.option("--limit", type=int, default=20, help="Max events to return")
@click.option("--output", "-o", type=click.Path(path_type=Path), default=None, help="Output .inp path")
@click.option("--compute", is_flag=True, help="Also compute CFS after fetching")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def fetch_cmd(
    event_id: str | None,
    search: bool,
    min_mag: float,
    start: str | None,
    end: str | None,
    limit: int,
    output: Path | None,
    compute: bool,
    verbose: bool,
) -> None:
    """Fetch USGS finite fault data.

    \b
    Examples:
      opencoulomb fetch us7000abcd              # Download .inp
      opencoulomb fetch us7000abcd --compute    # Download + compute CFS
      opencoulomb fetch --search --min-mag 7.0  # Search events
    """
    from opencoulomb.cli._logging import setup_logging
    setup_logging(verbose)

    if search:
        from opencoulomb.io.usgs_client import search_events
        events = search_events(
            min_magnitude=min_mag,
            start_time=start,
            end_time=end,
            limit=limit,
        )
        if not events:
            click.echo("No events found.")
            return
        click.echo(f"Found {len(events)} event(s):\n")
        for ev in events:
            click.echo(f"  {ev.event_id}  M{ev.magnitude:.1f}  {ev.title}")
        return

    if event_id is None:
        raise click.ClickException("Provide an event ID or use --search")

    from opencoulomb.io.usgs_client import fetch_coulomb_inp

    if output is None:
        output = Path(f"{event_id}.inp")

    logger.info("Fetching finite fault for %s...", event_id)
    try:
        path = fetch_coulomb_inp(event_id, output)
    except Exception as exc:
        raise click.ClickException(f"Fetch error: {exc}") from exc
    click.echo(f"Saved: {path}")

    if compute:
        from opencoulomb.core import compute_grid
        from opencoulomb.io import read_inp, write_csv, write_dcff_cou
        model = read_inp(path)
        result = compute_grid(model)
        out_dir = path.parent
        stem = path.stem
        write_dcff_cou(result, model, out_dir / f"{stem}_dcff.cou")
        write_csv(result, out_dir / f"{stem}.csv")
        click.echo(f"Computed CFS. Output in {out_dir}")
