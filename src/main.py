import os

import json
import pandas as pd
import argparse

from utils import remove_obscured_labels, get_class_counts_from_ids, get_intersecting_ids
from plot import plot_transistion_matrix, plot_mulistrategy_class_balances, plot_sat_views_per_building_histogram
from analysis import chi_squared_test, z_test_per_label, get_coincident_buildings_per_ortho, get_satellite_building_counts
from replicate import get_probability_of_disagreement, get_best_antioracle_label_for_building, get_best_oracle_label_for_building, \
                      get_best_temporal_label_for_building, compute_paired_difference_views, group_buildings_temporally

if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog="compute_satellite_BDA_dataset_stats", description="This program replicates the results of the 2025 FAccT Paper \"Now you see it, Now you don’t: Damage Label Agreement in Drone & Satellite Post-Disaster Imagery\"")
    parser.add_argument("--satellite_annotations_path_map", type=str, help="The path to the satellite annotations file path map.")
    parser.add_argument("--drone_annotations_path_map", type=str, help="The path to the suas annotations file path map.")
    parser.add_argument("--output_folder_path", type=str, help="The path to the output folder file.")
    parser.add_argument("--multiview_stats_file_path", type=str, help="The path to the multiview information.")
    args = parser.parse_args()

    try:
        os.makedirs(args.output_folder_path)
    except FileExistsError as e:
        pass

    sat_annotations_path_map = json.load(open(args.satellite_annotations_path_map))
    
    if args.drone_annotations_path_map is not None:
        drone_annotations_path_map = json.load(open(args.drone_annotations_path_map))

        # Read multiview csv for metadata information
        multiview_df = pd.read_csv(args.multiview_stats_file_path)

        suas_data = {}
        satellite_data = []

        for geotif_path, drone_annotation_path in drone_annotations_path_map.items():
            # Load the annotations
            print("Loading the sUAS BDA annotations from:", drone_annotation_path)
            f = open(drone_annotation_path, "r")
            drone_annotations_data = json.loads(f.read())
            f.close()

            suas_data[geotif_path] = drone_annotations_data

        for geotif_path, sat_annotation_path in sat_annotations_path_map.items():
            print("Loading the Satellite BDA annotations from:", sat_annotation_path)
            try:
                f = open(sat_annotation_path, "r")
                closest_annotation_path_annotations_data = json.loads(f.read())
                f.close()

                satellite_data.append(closest_annotation_path_annotations_data)
            except TypeError as e:
                print("Skipping", geotif_path, "->", sat_annotation_path, "because of", type(e))

        non_obscured_sat_data = remove_obscured_labels(satellite_data)

        valid_ids = get_intersecting_ids(list(suas_data.values()), non_obscured_sat_data)

        print("\n\nComputing sUAS vs Satellite Statistics....")
        print("Count of coincident buildings:", sum(get_coincident_buildings_per_ortho(valid_ids, suas_data).values()))
        print("Count of coincident views:", get_satellite_building_counts(non_obscured_sat_data, valid_ids))

        closest_suas_labels_abs, closest_sat_labels_abs = get_best_temporal_label_for_building(list(suas_data.values()), non_obscured_sat_data, valid_ids, multiview_df, "abs")
        closest_suas_labels_real, closest_sat_labels_real = get_best_temporal_label_for_building(list(suas_data.values()), non_obscured_sat_data, valid_ids, multiview_df, "real")
        oracle_suas_labels, oracle_sat_labels = get_best_oracle_label_for_building(list(suas_data.values()), non_obscured_sat_data, valid_ids)
        antioracle_suas_labels, antioracle_sat_labels = get_best_antioracle_label_for_building(list(suas_data.values()), non_obscured_sat_data, valid_ids)

        suas_class_counts_ignore_obscured = get_class_counts_from_ids(closest_suas_labels_real, True)
        closest_to_suas_class_counts_ignore_obscured = get_class_counts_from_ids(closest_sat_labels_abs, True)
        closest_to_disaster_class_counts_ignore_obscured = get_class_counts_from_ids(closest_sat_labels_real, True)
        oracle_class_counts_ignore_obscured = get_class_counts_from_ids(oracle_sat_labels, True)
        anti_oracle_class_counts_ignore_obscured = get_class_counts_from_ids(antioracle_sat_labels, True)

        plot_mulistrategy_class_balances(
            suas_class_counts_ignore_obscured,
            {
                "Satellite Anti-Oracle": anti_oracle_class_counts_ignore_obscured,
                "Satellite Oracle": oracle_class_counts_ignore_obscured,
                "Satellite Closest to Disaster": closest_to_disaster_class_counts_ignore_obscured,
                "Satellite Closest to Drone": closest_to_suas_class_counts_ignore_obscured,
            },
            args.output_folder_path,
            valid_ids,
        )

        print("\n\nAre the sUAS and Satellite distributions different? (Is p < 0.001?)")
        print("sUAS and Closest to Disaster (Ignore Obscured):",chi_squared_test(closest_suas_labels_abs, closest_sat_labels_abs, True))
        print("\tP-Value By Label:", z_test_per_label(closest_suas_labels_abs, closest_sat_labels_abs, True))
        print("sUAS and Closest to sUAS (Ignore Obscured):",chi_squared_test(closest_suas_labels_real, closest_sat_labels_real, True))
        print("\tP-Value By Label:", z_test_per_label(closest_suas_labels_real, closest_sat_labels_real, True))
        print("sUAS and Oracle (Ignore Obscured):",chi_squared_test(oracle_suas_labels, oracle_sat_labels, True))
        print("\tP-Value By Label:", z_test_per_label(oracle_suas_labels, oracle_sat_labels, True))
        print("sUAS and Anti-Oracle (Ignore Obscured):",chi_squared_test(antioracle_suas_labels, antioracle_sat_labels, True))
        print("\tP-Value By Label:", z_test_per_label(antioracle_suas_labels, antioracle_sat_labels, True))

        print("\n\nAre the Oracle and Anti-Oracle Distributions Different? (Is p < 0.001?)")
        print("Oracle and Anti-Oracle (Ignore Obscured):",chi_squared_test(oracle_sat_labels, antioracle_sat_labels, True))
        print("\tP-Value By Label:", z_test_per_label(oracle_sat_labels, antioracle_sat_labels, True))

        print("\n\nAre any view selection strategies different signficantly from one another (Is p < 0.001?)")
        strats = {"oracle": oracle_sat_labels, "anti_oracle": antioracle_sat_labels, "closest to disaster": closest_sat_labels_real, "closest to drone": closest_sat_labels_abs}
        for key_1, source_1 in strats.items():
            for key_2, source_2 in strats.items():
                if key_1 != key_2:
                    print("\t", key_1, key_2, chi_squared_test(source_1, source_2, True))

        print("\n\nWhat is the Probability of Disagreement for the different view selection strategies?")
        oracle_disagreement_prob_ignore_obscured = get_probability_of_disagreement(oracle_suas_labels, oracle_sat_labels, True)
        antioracle_disagreement_prob_ignore_obscured = get_probability_of_disagreement(antioracle_suas_labels, antioracle_sat_labels, True)
        closest_to_suas_disagreement_prob_ignore_obscured = get_probability_of_disagreement(closest_suas_labels_abs, closest_sat_labels_abs, True)
        closest_to_disaster_disagreement_prob_ignore_obscured = get_probability_of_disagreement(closest_suas_labels_real, closest_sat_labels_real, True)

        print("\tclosest_to_disaster_disagreement_prob_ignore_obscured", closest_to_disaster_disagreement_prob_ignore_obscured)
        print("\tclosest_to_suas_disagreement_prob_ignore_obscured", closest_to_suas_disagreement_prob_ignore_obscured)
        print("\toracle_disagreement_prob_ignore_obscured", oracle_disagreement_prob_ignore_obscured)
        print("\tantioracle_disagreement_prob_ignore_obscured", antioracle_disagreement_prob_ignore_obscured)

        # Compute Transisition Matrix for the change in labels between labels (y-axis -> sUAs label, x-axis -> satellite label)
        print("\n\nGenerating Oracle Transition Matrix...")
        plot_transistion_matrix(oracle_suas_labels, oracle_sat_labels, args.output_folder_path, "Satellite Oracle", True)
        plot_transistion_matrix(antioracle_suas_labels, antioracle_sat_labels, args.output_folder_path, "Satellite Anti-Oracle", True)
        plot_transistion_matrix(closest_suas_labels_abs, closest_sat_labels_abs, args.output_folder_path, "Satellite Closest to Drone", True)
        plot_transistion_matrix(closest_suas_labels_real, closest_sat_labels_real, args.output_folder_path, "Satellite Closest to Disaster ", True)

        # With only the sat orthos, compute the change with (time, view)
        suas_days_sat_data = group_buildings_temporally(non_obscured_sat_data, multiview_df)
        agree_dist, disagree_dist = compute_paired_difference_views(suas_days_sat_data, "days")
        disagree_rate = len(disagree_dist) / (len(disagree_dist) + len(agree_dist))
        view_count = len(disagree_dist) + len(agree_dist)
        print("\n\nProbability of Disagreement between time/view satellite", disagree_rate, "N=", view_count, "N_disagree=", len(disagree_dist), "N_agree=", len(agree_dist))