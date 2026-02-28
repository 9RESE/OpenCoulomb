"""Scale CLI command — earthquake scaling relations."""
from __future__ import annotations

import click


@click.command("scale")
@click.argument("magnitude", type=float)
@click.option(
    "--type", "-t", "fault_type",
    type=click.Choice(["strike_slip", "reverse", "normal", "all"]),
    default="all",
    help="Fault mechanism type",
)
@click.option(
    "--relation", "-r",
    type=click.Choice(["wells_coppersmith_1994", "blaser_2010"]),
    default="wells_coppersmith_1994",
    help="Scaling relation",
)
def scale_cmd(magnitude: float, fault_type: str, relation: str) -> None:
    """Estimate fault dimensions from magnitude using scaling relations.

    Example: opencoulomb scale 7.0 --type strike_slip
    """
    from opencoulomb.core.scaling import FaultType, blaser_2010, wells_coppersmith_1994

    ft = FaultType(fault_type)

    if relation == "wells_coppersmith_1994":
        result = wells_coppersmith_1994(magnitude, ft)
    else:
        result = blaser_2010(magnitude, ft)

    click.echo(f"Scaling relation: {result.relation}")
    click.echo(f"Magnitude:        Mw {result.magnitude:.1f}")
    click.echo(f"Fault type:       {result.fault_type.value}")
    click.echo(f"Length:            {result.length_km:.2f} km")
    click.echo(f"Width:             {result.width_km:.2f} km")
    click.echo(f"Area:              {result.area_km2:.2f} km²")
    click.echo(f"Displacement:      {result.displacement_m:.3f} m")
