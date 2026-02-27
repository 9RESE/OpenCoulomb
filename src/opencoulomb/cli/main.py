"""OpenCoulomb CLI."""

from __future__ import annotations

import click

from opencoulomb.cli.compute import compute_cmd
from opencoulomb.cli.convert import convert_cmd
from opencoulomb.cli.info import info_cmd
from opencoulomb.cli.plot import plot_cmd
from opencoulomb.cli.validate import validate_cmd


@click.group()
@click.version_option(package_name="opencoulomb")
def cli() -> None:
    """OpenCoulomb: Coulomb failure stress computation."""


cli.add_command(compute_cmd)
cli.add_command(convert_cmd)
cli.add_command(plot_cmd)
cli.add_command(info_cmd)
cli.add_command(validate_cmd)
