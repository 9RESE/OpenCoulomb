"""OpenCoulomb CLI."""

from __future__ import annotations

import click

from opencoulomb.cli.compute import compute_cmd
from opencoulomb.cli.info import info_cmd
from opencoulomb.cli.plot import plot_cmd


@click.group()
@click.version_option(package_name="opencoulomb")
def cli() -> None:
    """OpenCoulomb: Coulomb failure stress computation."""


cli.add_command(compute_cmd)
cli.add_command(plot_cmd)
cli.add_command(info_cmd)
