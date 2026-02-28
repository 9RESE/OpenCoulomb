"""File I/O (parsers, writers)."""

from opencoulomb.io.catalog_io import read_catalog_csv, write_catalog_csv
from opencoulomb.io.cou_writer import write_dcff_cou, write_section_cou
from opencoulomb.io.csv_writer import write_csv, write_summary
from opencoulomb.io.dat_writer import write_coulomb_dat, write_fault_surface_dat
from opencoulomb.io.fsp_parser import parse_fsp, parse_geojson_faults
from opencoulomb.io.gps_reader import read_gps_csv, read_gps_json
from opencoulomb.io.inp_parser import parse_inp_string, read_inp
from opencoulomb.io.volume_writer import write_volume_csv, write_volume_slices

__all__ = [
    "parse_fsp",
    "parse_geojson_faults",
    "parse_inp_string",
    "read_catalog_csv",
    "read_gps_csv",
    "read_gps_json",
    "read_inp",
    "write_catalog_csv",
    "write_coulomb_dat",
    "write_csv",
    "write_dcff_cou",
    "write_fault_surface_dat",
    "write_section_cou",
    "write_summary",
    "write_volume_csv",
    "write_volume_slices",
]
