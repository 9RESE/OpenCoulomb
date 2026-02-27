"""OpenCoulomb CLI."""
import click


@click.group()
@click.version_option(package_name="opencoulomb")
def cli() -> None:
    """OpenCoulomb: Coulomb failure stress computation."""
