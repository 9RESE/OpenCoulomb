"""OpenCoulomb CLI."""

from __future__ import annotations

import click

from opencoulomb.cli.catalog import catalog_cmd
from opencoulomb.cli.compute import compute_cmd
from opencoulomb.cli.convert import convert_cmd
from opencoulomb.cli.fetch import fetch_cmd
from opencoulomb.cli.info import info_cmd
from opencoulomb.cli.plot import plot_cmd
from opencoulomb.cli.scale import scale_cmd
from opencoulomb.cli.validate import validate_cmd


@click.group()
@click.version_option(package_name="opencoulomb")
def cli() -> None:
    """OpenCoulomb: Coulomb failure stress computation."""


cli.add_command(catalog_cmd)
cli.add_command(compute_cmd)
cli.add_command(convert_cmd)
cli.add_command(fetch_cmd)
cli.add_command(info_cmd)
cli.add_command(plot_cmd)
cli.add_command(scale_cmd)
cli.add_command(validate_cmd)
