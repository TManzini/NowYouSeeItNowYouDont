import json
import os
import argparse

from datetime import datetime

import pandas as pd

from constants import PRE_OR_POST_EVENT, EXCLUDED_FILENAMES, DAYS_AFTER_SUAS_ORTHO, DATE, FILENAME


def days_between(d1, d2):
    d1 = datetime.strptime(d1, "%m/%d/%Y")
    d2 = datetime.strptime(d2, "%m/%d/%Y")
    return (d2 - d1).days

def is_excluded_file(filename):
    for file in EXCLUDED_FILENAMES:
        if file in filename:
            return True
    return False

if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog="make_metadata_files", description="This program produces the metatdata files necessary to run the replciation of the 2025 FAccT Paper \"Now you see it, Now you don’t: Damage Label Agreement in Drone & Satellite Post-Disaster Imagery\"")
    parser.add_argument("--crasar_u_droids_dir", type=str, help="The path to the satellite annotations file path map.")
    parser.add_argument("--output_stats_file", type=str, help="The path to the suas annotations file path map.")
    parser.add_argument("--output_suas_path_map", type=str, help="The path to the output folder file.")
    parser.add_argument("--output_satellite_path_map", type=str, help="The path to the multiview information.")
    args = parser.parse_args()

    os.makedirs(os.path.split(args.output_stats_file)[0], exist_ok=True)
    os.makedirs(os.path.split(args.output_suas_path_map)[0], exist_ok=True)
    os.makedirs(os.path.split(args.output_satellite_path_map)[0], exist_ok=True)

    stats_df = pd.read_csv(os.path.join(args.crasar_u_droids_dir, "statistics.csv"))

    suas_path_map = {}
    satellite_path_map = {}

    ortho_date = {}

    for root, dirs, files in os.walk(args.crasar_u_droids_dir):
        for filename in files:
            if ".tif.json" in filename and not ".cache" in root:
                tif_name = filename.replace(".json", "")
                is_post_disaster = stats_df[stats_df["Orthomosaic"] == tif_name][PRE_OR_POST_EVENT].iloc[0] == "POST"
                ortho_date[tif_name] = stats_df[stats_df["Orthomosaic"] == tif_name][DATE].iloc[0]
                if is_post_disaster and not is_excluded_file(tif_name):
                    if "suas" in root.lower():
                        suas_path_map[tif_name] = os.path.join(root, filename)
                    elif "satellite" in root.lower():
                        satellite_path_map[tif_name] = os.path.join(root, filename)

    days_after_suas_ortho = {}

    for sat_file in satellite_path_map.keys():
        for suas_file in suas_path_map.keys(): 
            if suas_file in sat_file:
                days_after_suas_ortho[sat_file] = {FILENAME: sat_file, DAYS_AFTER_SUAS_ORTHO: days_between(ortho_date[suas_file], ortho_date[sat_file])}
    
    for suas_file in suas_path_map.keys():
        days_after_suas_ortho[suas_file] = {FILENAME: suas_file, DAYS_AFTER_SUAS_ORTHO: 0}

    pd.DataFrame(days_after_suas_ortho).transpose().to_csv(args.output_stats_file, index=False)

    f = open(args.output_suas_path_map, "w")
    f.write(json.dumps(suas_path_map))
    f.close()

    f = open(args.output_satellite_path_map, "w")
    f.write(json.dumps(satellite_path_map))
    f.close()


