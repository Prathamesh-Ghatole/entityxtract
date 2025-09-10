from pathlib import Path
import polars as pl
import time

from llm_extractor.extractor_types import Document
from llm_extractor.logging_config import setup_logging, get_logger
from llm_extractor.extractor import extract_objects
from llm_extractor import extractor_types as et
from utils_io import save_results_to_csv

# Initialize logging for the script
setup_logging()
logger = get_logger(__name__)

SAMPLE_PDF_PATH = Path(__file__).parent / "data" / "sample_3.pdf"
MODEL = "google/gemini-2.5-pro"

TABLE1 = et.TableToExtract(
    name="monthly_production_and_export_figures_details",
    example_table=pl.DataFrame(
        [
            {
                "production_day": "1-Sep-25",
                "opening_stock_g_bbls": 790123,
                "opening_stock_n_bbls": 789987,
                "production_g_bbls": 85201,
                "production_n_bbls": 85150,
                "closing_stock_g_bbls": 875324,
                "closing_stock_n_bbls": 875137,
                "export_g_bbls": None,
                "export_n_bbls": None,
            },
            {
                "production_day": "2-Sep-25",
                "opening_stock_g_bbls": 875324,
                "opening_stock_n_bbls": 875137,
                "production_g_bbls": 86120,
                "production_n_bbls": 86090,
                "closing_stock_g_bbls": 961444,
                "closing_stock_n_bbls": 961227,
                "export_g_bbls": None,
                "export_n_bbls": None,
            },
            {
                "production_day": "3-Sep-25",
                "opening_stock_g_bbls": 961444,
                "opening_stock_n_bbls": 961227,
                "production_g_bbls": 82955,
                "production_n_bbls": 82910,
                "closing_stock_g_bbls": 1044399,
                "closing_stock_n_bbls": 1044137,
                "export_g_bbls": None,
                "export_n_bbls": None,
            },
        ]
    ),
    instructions="Daily production, stock, and export figures. Generally found on page 1 of the report.",
    required=True,
)

TABLE2 = et.TableToExtract(
    name="monthly_production_and_export_figures_summary",
    example_table=pl.DataFrame(
        [
            {
                "type": "Total Production",
                "g_bbls": 254276,
                "n_bbls": 254150,
            },
            {
                "type": "Total Exports",
                "g_bbls": 0,
                "n_bbls": 0,
            },
        ]
    ),
    instructions=(
        "Summary of the MONTHLY PRODUCTION AND EXPORT FIGURES table."
        " The relevant details can be found at the end of the MONTHLY PRODUCTION AND EXPORT FIGURES table in a single row."
    ),
    required=True,
)


TABLE3 = et.TableToExtract(
    name="agbami_fpso_data",
    example_table=pl.DataFrame(
        [
            {
                "facility": "agbami_fpso",
                "draft_fwd_m": 15.20,
                "draft_aft_m": 17.50,
                "after_before_load_discharge_interim": "interim at 09:00",
                "rvp_reading": 10.3,
                "cot_hdr_bar": 0.068,
                "cot_hdr_psi": 0.9862335,
                "berth_place_and_transhipment_vessel_name": "some vessel name",
                "api_60f": 49.25,
                "api_76f": 50.85,
                "sample_bsw_percent": 0.055,
                "density_15c_kg_m3": 762.50,
                "sea_state_and_vessel_motion": "low swell, vessel rolling",
                "ullage_by": "hand",
                "dpr_witness": "yes",
                "trim_m": 2.6,
                "date": "04-sep-25",
            }
        ]
    ),
    instructions=(
        "Details of the facility, including draft readings, API gravity, and other operational data."
        " The table contains only one row, and all table and column names are in lowercase, snake case, and simplified."
        " You'll find the actual data on page 2 of the document in a weird multi level table."
    ),
    required=True,
)

TABLE4 = et.TableToExtract(
    name="agbami_condensate_and_water_stock",
    example_table=pl.DataFrame(
        [
            {
                "tank": "1c",
                "grade": "agbami condensate",
                "ullage_m_obs": 22.50,
                "ullage_m_corrected": 22.45,
                "corr_total_volume_in_m3_at_obs_temp_tov": 5500.0,
                "freewater_obs_dip": 6.8,
                "freewater_m3": 0.0,
                "gov_m3": 5493.2,
                "temp": 30.0,
                "vcf_table_api_mpms_chip": 0.98670,
                "density_at_15c": 791.50,
                "gsv_m3_at_15c_in_air": 5424.1,
                "bsw": 0.050,
                "nsv_m3_at_15c_in_air": 5396.2,
                "methanol_ppm": 0,
                "methanol_quantity_m3": 0.000,
            },
            {
                "tank": "slp_s",
                "grade": "water",
                "ullage_m_obs": 14.80,
                "ullage_m_corrected": 14.80,
                "corr_total_volume_in_m3_at_obs_temp_tov": 2850.0,
                "freewater_obs_dip": 14.70,
                "freewater_m3": 2690.0,
                "gov_m3": 40.5,
                "temp": 30.0,
                "vcf_table_api_mpms_chip": 0.97000,
                "density_at_15c": 765.0,
                "gsv_m3_at_15c_in_air": 38.8,
                "bsw": 0.050,
                "nsv_m3_at_15c_in_air": 38.8,
                "methanol_ppm": 0,
                "methanol_quantity_m3": 0.000,
            },
            {
                "tank": "totals_or_vol_averages",
                "grade": None,
                "ullage_m_obs": None,
                "ullage_m_corrected": None,
                "corr_total_volume_in_m3_at_obs_temp_tov": 170000.0,
                "freewater_obs_dip": 3800.0,
                "freewater_m3": 165000.0,
                "gov_m3": 165000.0,
                "temp": 30.0,
                "vcf_table_api_mpms_chip": None,
                "density_at_15c": 792.50,
                "gsv_m3_at_15c_in_air": 164000.0,
                "bsw": None,
                "nsv_m3_at_15c_in_air": 163000.0,
                "methanol_ppm": None,
                "methanol_quantity_m3": None,
            },
        ]
    ),
    instructions=(
        "Details on tank stock data, including ullage, volume, density, and freewater measurements for various tanks."
        " Column names are in lowercase snake case and normalized."
        " The original table will be in multiple column levels but all on a single page on page 2."
        " Empty cells should be set to 'None'"
    ),
    required=True,
)

TABLE5 = et.TableToExtract(
    name="condensate_volume_and_weight",
    example_table=pl.DataFrame(
        [
            {
                "grade_of_cargo": "AGBAMI CONDENSATE",
                "unit": "m3",
                "volume_gross": 165800.0,
                "weight_long_tonnes": 161900.0,
                "UNK COLUMN": 160570.1,
            },
            {
                "grade_of_cargo": "AGBAMI CONDENSATE",
                "unit": "US Barrels",
                "volume_gross": 1042000,
                "weight_long_tonnes": 1018000,
                "UNK COLUMN": 1009000.0,
            },
            {
                "grade_of_cargo": "AGBAMI CONDENSATE",
                "unit": "Long Tons",
                "volume_gross": 131500.0,
                "weight_long_tonnes": 127900.0,
                "UNK COLUMN": 126800.0,
            },
            {
                "grade_of_cargo": "AGBAMI CONDENSATE",
                "unit": "Metric Tonnes",
                "volume_gross": 133900.0,
                "weight_long_tonnes": 129900.0,
                "UNK COLUMN": 128800.0,
            },
            {
                "grade_of_cargo": "AGBAMI CONDENSATE",
                "unit": "Free Water",
                "volume_gross": 133900.0,
                "weight_long_tonnes": 129900.0,
                "UNK COLUMN": "N/A",
            },
        ]
    ),
    instructions=(
        "Gross volume and weight in various units for Condensate."
        " You'll find this data on page 2 of the document in a weird multi level table."
        " All column and table names are in lowercase, snake case, and simplified."
    ),
    required=True,
)

TABLE6 = et.TableToExtract(
    name="conversion_factors",
    example_table=pl.DataFrame(
        [
            {
                "factor_type": "weight_long_tonnes_table_57_factor",
                "factor_value": 0.7863,
            },
            {
                "factor_type": "weight_metric_tonnes_table_1_factor",
                "factor_value": 1.01605,
            },
        ]
    ),
    instructions=(
        "Conversion factors used for calculating weight and volume."
        " You'll find this data on page 2 of the document in a weird multi level table."
        " All column and table names are in lowercase, snake case, and simplified."
    ),
    required=True,
)

TABLE7 = et.TableToExtract(
    name="tank_stock_and_production_volume",
    example_table=pl.DataFrame(
        [
            {
                "data_type": "present_tank_stock",
                "category": "gsv",
                "m3": 163000.0,
                "bbls": 1025000,
            },
            {
                "data_type": "present_tank_stock",
                "category": "nsv",
                "m3": 162500.0,
                "bbls": 1022500,
            },
            {
                "data_type": "daily_production",
                "category": "gsv",
                "m3": 13000.0,
                "bbls": 80600,
            },
            {
                "data_type": "daily_production",
                "category": "nsv",
                "m3": 12900.0,
                "bbls": 80500,
            },
            {
                "data_type": "daily_production",
                "category": "water",
                "m3": -300.0,
                "bbls": -1860,
            },
        ]
    ),
    instructions=(
        "Consolidated data on tank stock volumes for different time periods and daily production figures, measured in M3 and barrels (bbls)."
        " You'll find this data on page 2."
        " This table combines multiple sections from the original data source."
        " All column and table names are in lowercase, snake_case, and simplified."
    ),
    required=True,
)

TABLE8 = et.TableToExtract(
    name="24hrs_total_prod_and_recovered_oil_from_process_tanks",
    example_table=pl.DataFrame(
        [
            {
                "category": "volume_recovered",
                "m3": 0.0,
                "bbls": "N/A",
            },
            {
                "category": "24hrs_total_prod",
                "m3": 12850.0,
                "bbls": 80700,
            },
        ]
    ),
    instructions=(
        "A summary of the 24-hour total production and recovered oil from process tanks, in M3 and barrels."
        " This data can be found on page 2 of the document."
        " All column and table names are in lowercase, snake case, and simplified."
    ),
    required=True,
)

TABLE9 = et.TableToExtract(
    name="methanol_and_water_content",
    example_table=pl.DataFrame(
        [
            {
                "category": "methanol_content",
                "description": "nett_volume_oil_m3",
                "value": 162500.0,
            },
            {
                "category": "methanol_content",
                "description": "total_volume_of_methanol",
                "value": 0.00,
            },
            {
                "category": "methanol_content",
                "description": "average_methanol_content_ppm",
                "value": 0.0,
            },
            {
                "category": "water_content",
                "description": "average_water_cut_percent",
                "value": 2.5,
            },
        ]
    ),
    instructions=(
        "Methanol and water content data, including oil volume and average water cut."
        " All column and table names are in lowercase, snake case, and simplified."
    ),
    required=True,
)

TABLE10 = et.TableToExtract(
    name="production_summary",
    example_table=pl.DataFrame(
        [
            {
                "product": "oil_stb",
                "daily_volume": 81000,
                "cumulative_mtd": 245000,
                "cumulative_ytd": 19700000,
                "average_mtd": 82000,
                "average_ytd": 80000,
            },
            {
                "product": "gas_mscf",
                "daily_volume": 452000,
                "cumulative_mtd": 1370000,
                "cumulative_ytd": 101000000,
                "average_mtd": 457000,
                "average_ytd": 408000,
            },
            {
                "product": "water_bbls",
                "daily_volume": 54000,
                "cumulative_mtd": 162000,
                "cumulative_ytd": 11400000,
                "average_mtd": 54000,
                "average_ytd": 47000,
            },
        ]
    ),
    instructions=(
        "Summary of daily, cumulative, and average production volumes for oil, gas, and water. 'stb' is stock tank barrels, 'mscf' is thousand standard cubic feet."
        " This data will be found on page 3 of the document."
        " All column and table names are in lowercase, snake case, and simplified."
    ),
    required=True,
)

TABLE11 = et.TableToExtract(
    name="water_injection_summary",
    example_table=pl.DataFrame(
        [
            {
                "category": "total_water_injected_bbls",
                "daily_volume": 113000,
                "cumulative_mtd": 340000,
                "cumulative_ytd": 16600000,
                "average_mtd": 114000,
                "average_ytd": 76000,
            }
        ]
    ),
    instructions=(
        "Summary of total water injected, with daily, cumulative, and average volumes. 'bbls' is barrels."
        " This data will be found on page 3 of the document."
        " All column and table names are in lowercase, snake case, and simplified."
    ),
    required=True,
)

TABLE12 = et.TableToExtract(
    name="gas_volume_summary",
    example_table=pl.DataFrame(
        [
            {
                "category": "gas_injection_mscf",
                "daily_volume": 426000,
                "cumulative_mtd": 1290000,
                "cumulative_ytd": 94000000,
                "average_mtd": 430000,
                "average_ytd": 381000,
            },
            {
                "category": "fuel_gas_mscf",
                "daily_volume": 24000,
                "cumulative_mtd": 72000,
                "cumulative_ytd": 5000000,
                "average_mtd": 23800,
                "average_ytd": 20700,
            },
            {
                "category": "flare_mscf",
                "daily_volume": 2400,
                "cumulative_mtd": 7300,
                "cumulative_ytd": 1600000,
                "average_mtd": 2420,
                "average_ytd": 6500,
            },
        ]
    ),
    instructions=(
        "Summary of gas volume for injection, fuel, and flaring. 'mscf' is thousand standard cubic feet."
        " This data will be found on page 3 of the document."
        " All column and table names are in lowercase, snake case, and simplified."
    ),
    required=True,
)

TABLE13 = et.TableToExtract(
    name="export_last_liftings",
    example_table=pl.DataFrame(
        [
            {
                "vessel_name": "dalian",
                "account": "star deep",
                "offload_number": "agb-1205",
                "bol_date": "07-aug-2025",
                "grs_vol_shipped_stb": 1000000,
                "api": 50.2,
                "bsw_percent": 0.09,
                "methanol_ppm": 0.08,
            },
            {
                "vessel_name": "mt",
                "account": "famfa",
                "offload_number": "agb-1205",
                "bol_date": "21-aug-2025",
                "grs_vol_shipped_stb": 1001000,
                "api": 48.7,
                "bsw_percent": 0.00,
                "methanol_ppm": 0.00,
            },
            {
                "vessel_name": "houston",
                "account": "front tyne",
                "offload_number": "nnepct2",
                "bol_date": "01-sep-2025",
                "grs_vol_shipped_stb": 1002000,
                "api": 49.5,
                "bsw_percent": 0.06,
                "methanol_ppm": 0.00,
            },
        ]
    ),
    instructions=(
        "Details of recent condensate liftings. 'bol' is bill of lading, 'grs vol' is gross volume, 'stb' is stock tank barrels, 'bsw' is basic sediment and water, 'ppm' is parts per million."
        " This data will be found on page 3 of the document."
        " All column and table names are in lowercase, snake case, and simplified."
    ),
    required=True,
)

TABLE14 = et.TableToExtract(
    name="next_scheduled_liftings",
    example_table=pl.DataFrame(
        [
            {
                "vessel_name": "gustavia",
                "account": "star deep",
                "eta": "09-sep-2025",
                "loading_range_start": "09-sep-2025",
                "loading_range_end": "11-sep-2025",
                "est_vol_to_ship_stb": 7400000,
            }
        ]
    ),
    instructions=(
        "Details of the next scheduled lifting, including vessel name, estimated time of arrival, and volume. 'eta' is estimated time of arrival, 'stb' is stock tank barrels."
        " This data will be found on page 3 of the document."
        " The example data is randomized and limited to one row. All column and table names are in lowercase, snake case, and simplified."
    ),
    required=True,
)

TABLE15 = et.TableToExtract(
    name="export_summary",
    example_table=pl.DataFrame(
        [
            {
                "daily_stb": 0,
                "mtd_stb": 0,
                "ytd_stb": 19400000,
            }
        ]
    ),
    instructions=(
        "Summary of export volumes on a daily, MTD (Month-to-Date), and YTD (Year-to-Date) basis. 'stb' is stock tank barrels."
        " This data will be found on page 3 of the document."
        " The example data is randomized and limited to one row. All column and table names are in lowercase, snake case, and simplified."
    ),
    required=True,
)

TABLE16 = et.TableToExtract(
    name="well_data_last_approved_well_test_for_oil_producers",
    example_table=pl.DataFrame(
        [
            {
                "well_name": "agb-03b-st2",
                "last_test_date": "03/03/25",
                "hours_on_test": 6,
                "oil_rate_stb_d": 2500,
                "well_head_press_psia": 190,
                "well_head_temp_degf": 195,
                "choke_open_percent": 2.2,
                "test_sep_psia": 320,
                "water_rate_bbls_d": 2420,
                "bsw_percent": 50.0,
                "gas_rate_mscf_d": 8500,
                "gor": 8700,
                "glr": 1500,
            },
            {
                "well_name": "agb-07",
                "last_test_date": "04/19/25",
                "hours_on_test": 8,
                "oil_rate_stb_d": 3100,
                "well_head_press_psia": 185,
                "well_head_temp_degf": 200,
                "choke_open_percent": 3.1,
                "test_sep_psia": 300,
                "water_rate_bbls_d": 2100,
                "bsw_percent": 40.0,
                "gas_rate_mscf_d": 9200,
                "gor": 9500,
                "glr": 1600,
            },
            {
                "well_name": "agb-20a",
                "last_test_date": "04/13/25",
                "hours_on_test": 12,
                "oil_rate_stb_d": 1700,
                "well_head_press_psia": 190,
                "well_head_temp_degf": 195,
                "choke_open_percent": 2.2,
                "test_sep_psia": 320,
                "water_rate_bbls_d": 2420,
                "bsw_percent": 50.0,
                "gas_rate_mscf_d": 8500,
                "gor": 8700,
                "glr": 1500,
            },
        ]
    ),
    instructions=(
        "Last approved well test data for oil producers. 'stb/d' is stock tank barrels per day, 'mscf/d' is thousand standard cubic feet per day, 'psig' is pounds per square inch gauge, 'degF' is degrees Fahrenheit, 'bbls' is barrels, 'scf/bbl' is standard cubic feet per barrel, and 'ppm' is parts per million."
        " The data for this table can be found on page '2 of 3' of the document."
        " The example data is randomized, limited to three rows, and all column names are in lowercase and snake case."
    ),
    required=True,
)

TABLE17 = et.TableToExtract(
    name="well_data_last_24_hours_allocated_readings",
    example_table=pl.DataFrame(
        [
            {
                "well_name": "agb-03b-st2",
                "production_day": "04/09/25",
                "hrs_on": 24,
                "oil_stb_d": 2185,
                "water_bbls": 6020,
                "gas_mscf_d": 10550,
                "choke_open_percent": 7.6,
                "well_head_press_psia": 182,
                "well_head_temp_degf": 258,
                "annulus_press_psia": 178,
            },
            {
                "well_name": "agb-04",
                "production_day": "04/09/25",
                "hrs_on": 24,
                "oil_stb_d": 4080,
                "water_bbls": 6100,
                "gas_mscf_d": 1420,
                "choke_open_percent": 7.7,
                "well_head_press_psia": 162,
                "well_head_temp_degf": 257,
                "annulus_press_psia": 182,
            },
            {
                "well_name": "agb-06",
                "production_day": "04/09/25",
                "hrs_on": 24,
                "oil_stb_d": 920,
                "water_bbls": 1010,
                "gas_mscf_d": 460,
                "choke_open_percent": 10.1,
                "well_head_press_psia": 196,
                "well_head_temp_degf": 261,
                "annulus_press_psia": 186,
            },
            {
                "production_day": "04/09/25",
                "well_name": "agb-10a",
                "hrs_on": 24,
                "oil_stb_d": 4980,
                "gas_mscf_d": 15000,
                "water_bbls": 9800,
                "choke_open_percent": 15.0,
                "well_head_press_psia": 200,
                "well_head_temp_degf": 198,
                "annulus_press_psia": 195,
            },
            {
                "production_day": "04/09/25",
                "well_name": "agb-11",
                "hrs_on": 24,
                "oil_stb_d": 2500,
                "gas_mscf_d": 5200,
                "water_bbls": 6200,
                "choke_open_percent": 6.8,
                "well_head_press_psia": 195,
                "well_head_temp_degf": 190,
                "annulus_press_psia": 122,
            },
        ]
    ),
    instructions=(
        "Last 24 hours of allocated well readings for oil producers. 'stb/d' is stock tank barrels per day, 'mscf/d' is thousand standard cubic feet per day, 'psia' is pounds per square inch absolute, and 'degF' is degrees Fahrenheit."
        "The data for this table can be found on page '2 of 3' of the document."
        " all column names are in lowercase and snake case."
    ),
    required=True,
)

TABLE18 = et.TableToExtract(
    name="gas_injection_wells",
    example_table=pl.DataFrame(
        [
            {
                "well_name": "agb-13",
                "production_day": "09/03/25",
                "hours_on": 24,
                "choke_open_percent": 100.0,
                "well_head_pressure_psia": 4550,
                "f_l_psia": 4585,
                "well_head_temp_degf": 107,
                "metered_volume_mscf": 95150,
                "allocated_volume_mscf": 95150,
                "month_cumulative_mscf": 279700,
                "year_cumulative_mscf": 18600000,
                "comments": "",
            },
            {
                "well_name": "agb-15",
                "production_day": "09/03/25",
                "hours_on": 0,
                "choke_open_percent": 0.0,
                "well_head_pressure_psia": 4510,
                "f_l_psia": 4525,
                "well_head_temp_degf": 40,
                "metered_volume_mscf": 0,
                "allocated_volume_mscf": 0,
                "month_cumulative_mscf": 0,
                "year_cumulative_mscf": 271500,
                "comments": "",
            },
            {
                "well_name": "agb-18",
                "production_day": "09/03/25",
                "hours_on": 24,
                "choke_open_percent": 100.0,
                "well_head_pressure_psia": 4900,
                "f_l_psia": 4935,
                "well_head_temp_degf": 112,
                "metered_volume_mscf": 131600,
                "allocated_volume_mscf": 131600,
                "month_cumulative_mscf": 421300,
                "year_cumulative_mscf": 32100000,
                "comments": "",
            },
            {
                "well_name": "agb-23b",
                "production_day": "09/03/25",
                "hours_on": 24,
                "choke_open_percent": 100.0,
                "well_head_pressure_psia": 4860,
                "f_l_psia": 4910,
                "well_head_temp_degf": 112,
                "metered_volume_mscf": 122700,
                "allocated_volume_mscf": 122700,
                "month_cumulative_mscf": 364500,
                "year_cumulative_mscf": 26800000,
                "comments": "",
            },
            {
                "well_name": "agb-36",
                "production_day": "09/03/25",
                "hours_on": 24,
                "choke_open_percent": 100.0,
                "well_head_pressure_psia": 4470,
                "f_l_psia": 4495,
                "well_head_temp_degf": 101,
                "metered_volume_mscf": 76550,
                "allocated_volume_mscf": 76550,
                "month_cumulative_mscf": 224500,
                "year_cumulative_mscf": 16000000,
                "comments": "",
            },
        ]
    ),
    instructions=(
        "Gas injection well data, including metered and allocated volumes, and cumulative totals for the month and year. 'mscf' is thousand standard cubic feet, 'psia' is pounds per square inch absolute, 'degF' is degrees Fahrenheit."
        "The data for this table can be found on page '3 of 3' of the document."
        " All column names are in lowercase and snake case."
    ),
    required=True,
)

TABLE19 = et.TableToExtract(
    name="water_injection_wells",
    example_table=pl.DataFrame(
        [
            {
                "well_name": "agb-13",
                "production_day": "09/03/25",
                "hours_on": 24,
                "choke_open_percent": 100.0,
                "well_head_pressure_psia": 4550,
                "f_l_psia": 4585,
                "well_head_temp_degf": 107,
                "metered_volume_bbls": 95150,
                "allocated_volume_bbls": 95150,
                "month_cumulative_bbls": 279700,
                "year_cumulative_bbls": 18600000,
                "comments": "",
            },
            {
                "well_name": "agb-15",
                "production_day": "09/03/25",
                "hours_on": 0,
                "choke_open_percent": 0.0,
                "well_head_pressure_psia": 4510,
                "f_l_psia": 4525,
                "well_head_temp_degf": 40,
                "metered_volume_bbls": 0,
                "allocated_volume_bbls": 0,
                "month_cumulative_bbls": 0,
                "year_cumulative_bbls": 271500,
                "comments": "",
            },
            {
                "well_name": "agb-18",
                "production_day": "09/03/25",
                "hours_on": 24,
                "choke_open_percent": 100.0,
                "well_head_pressure_psia": 4900,
                "f_l_psia": 4935,
                "well_head_temp_degf": 112,
                "metered_volume_bbls": 131600,
                "allocated_volume_bbls": 131600,
                "month_cumulative_bbls": 421300,
                "year_cumulative_bbls": 32100000,
                "comments": "",
            },
            {
                "well_name": "agb-23b",
                "production_day": "09/03/25",
                "hours_on": 24,
                "choke_open_percent": 100.0,
                "well_head_pressure_psia": 4860,
                "f_l_psia": 4910,
                "well_head_temp_degf": 112,
                "metered_volume_bbls": 122700,
                "allocated_volume_bbls": 122700,
                "month_cumulative_bbls": 364500,
                "year_cumulative_bbls": 26800000,
                "comments": "",
            },
            {
                "well_name": "agb-36",
                "production_day": "09/03/25",
                "hours_on": 24,
                "choke_open_percent": 100.0,
                "well_head_pressure_psia": 4470,
                "f_l_psia": 4495,
                "well_head_temp_degf": 101,
                "metered_volume_bbls": 76550,
                "allocated_volume_bbls": 76550,
                "month_cumulative_bbls": 224500,
                "year_cumulative_bbls": 16000000,
                "comments": "",
            },
        ]
    ),
    instructions=(
        "Water injection well data, including metered and allocated volumes, and cumulative totals for the month and year. 'bbls' is barrels, 'psia' is pounds per square inch absolute, 'degF' is degrees Fahrenheit."
        "The data for this table can be found on page '3 of 3' of the document."
        " All column names are in lowercase and snake case."
    ),
    required=True,
)

TABLE20 = et.TableToExtract(
    name="production_comments",
    example_table=pl.DataFrame(
        [
            {
                "category": "oil_production",
                "comment": "Production curtailment for flare management.",
            },
            {
                "category": "flared_gas",
                "comment": "Flare volume estimated due to suspected fault on HP Flare Meter FIT-501010.",
            },
            {
                "category": "water_injection",
                "comment": "AGB-21 offline due to suspected restriction on WMC riser XV-410067. Repair awaiting delivery of seal ring.",
            },
        ]
    ),
    instructions=(
        "Operational comments regarding oil production, flared gas, and water injection."
        " This data will be found on page '3 of 3' of the document."
        " All column and table names are in lowercase, snake case, and simplified."
    ),
    required=True,
)


def main():
    logger.info(f"Loading document from {SAMPLE_PDF_PATH}")

    start_time = time.time()
    doc = Document(SAMPLE_PDF_PATH)

    logger.info(f"Loaded document text: {len(doc.text)} characters")
    logger.info(f"Loaded document text preview: \n{doc.text[:500]}...\n")
    logger.info(f"Loaded document image data: {doc.image}")

    config_file_input = et.ExtractionConfig(
        model_name=MODEL,
        temperature=0.0,
        file_input_modes=[
            et.FileInputMode.FILE,
        ],
        parallel_requests=4,
        calculate_costs=True,
    )

    objects_to_extract = et.ObjectsToExtract(
        objects=[
            TABLE1,
            TABLE2,
            TABLE3,
            TABLE4,
            TABLE5,
            TABLE6,
            TABLE7,
            TABLE8,
            TABLE9,
            TABLE10,
            TABLE11,
            TABLE12,
            TABLE13,
            TABLE14,
            TABLE15,
            TABLE16,
            TABLE17,
            TABLE18,
            TABLE18,
            TABLE19,
            TABLE20,
        ],
        config=config_file_input,
    )

    logger.info(f"\nUsing extraction config: {config_file_input}")

    result = extract_objects(doc, objects_to_extract)

    if result.success:
        logger.info(
            f"\n\nExtraction successful. Results keys:\n{list(result.results.keys())}"
        )
        output_dir = Path(__file__).parent / "logs" / "extracted_csv"
        save_results_to_csv(result.results, output_dir, logger, SAMPLE_PDF_PATH.stem)
        for name, res in result.results.items():
            logger.info(
                f"[{name}] success={res.success} message={res.message} input_tokens={res.input_tokens} output_tokens={res.output_tokens} costs={res.cost}"
            )
            logger.info(
                f"[{name}] extracted data:\n{pl.DataFrame(res.extracted_data)}\n\n"
            )

    time_taken = round(time.time() - start_time, 2)

    logger.info(
        f"Extracted {len(result.results)} tables in ${result.total_cost} using {result.total_input_tokens} input tokens and {result.total_output_tokens} output tokens in {time_taken} seconds"
    )


if __name__ == "__main__":
    main()
