"""Catalog CLI command — query earthquake catalogs."""
from __future__ import annotations

import logging
from pathlib import Path

import click

logger = logging.getLogger("opencoulomb")


@click.command("catalog")
@click.option("--start", required=True, type=str, help="Start date (YYYY-MM-DD)")
@click.option("--end", required=True, type=str, help="End date (YYYY-MM-DD)")
@click.option("--min-mag", type=float, default=4.0, help="Minimum magnitude")
@click.option("--max-mag", type=float, default=None, help="Maximum magnitude")
@click.option("--source", type=click.Choice(["isc", "usgs"]), default="isc", help="Catalog source")
@click.option("--output", "-o", type=click.Path(path_type=Path), default="catalog.csv", help="Output CSV path")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def catalog_cmd(
    start: str,
    end: str,
    min_mag: float,
    max_mag: float | None,
    source: str,
    output: Path,
    verbose: bool,
) -> None:
    """Query ISC or USGS earthquake catalog and save to CSV.

    \b
    Examples:
      opencoulomb catalog --start 2024-01-01 --end 2024-12-31 --min-mag 5.0
      opencoulomb catalog --start 2025-01-01 --end 2025-06-01 --source usgs
    """
    from opencoulomb.cli._logging import setup_logging
    setup_logging(verbose)

    logger.info("Querying %s catalog...", source.upper())

    try:
        if source == "isc":
            from opencoulomb.io.isc_client import query_isc
            catalog = query_isc(start_time=start, end_time=end, min_magnitude=min_mag)
        else:
            from opencoulomb.io.isc_client import query_usgs_catalog
            catalog = query_usgs_catalog(start_time=start, end_time=end, min_magnitude=min_mag)
    except ImportError as exc:
        raise click.ClickException(str(exc)) from exc
    except Exception as exc:
        raise click.ClickException(f"Catalog query error: {exc}") from exc

    if max_mag is not None:
        catalog = catalog.filter_by_magnitude(min_mag=min_mag, max_mag=max_mag)

    click.echo(f"Found {len(catalog)} event(s)")

    from opencoulomb.io.catalog_io import write_catalog_csv
    write_catalog_csv(catalog, output)
    click.echo(f"Saved: {output}")
