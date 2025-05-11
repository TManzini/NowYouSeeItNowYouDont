import os
import json
import argparse

from collections import defaultdict
from itertools import combinations

import pandas as pd
import numpy as np

from constants import DAYS_AFTER_SUAS_ORTHO, FILENAME, UNCLASSIFIED, OBSCURED

def get_probability_of_disagreement(suas_id2labels, sat_id2labels, ignore_sat_obscured=False):
    count_agree = 0
    count_disagree = 0
    for bld_id in suas_id2labels.keys():
        if (ignore_sat_obscured and sat_id2labels[bld_id] != OBSCURED) or not ignore_sat_obscured:
            if suas_id2labels[bld_id] == sat_id2labels[bld_id]:
                count_agree += 1
            else:
                count_disagree += 1
    return count_disagree / (count_agree + count_disagree)

def get_swapped_unclassified_label(base_label, new_label, ignore_lone_unclassified):
    if base_label is None:
        return new_label
    if (
        new_label == UNCLASSIFIED
        and base_label != UNCLASSIFIED
        and ignore_lone_unclassified
    ):
        return base_label
    return new_label

def get_best_cheat_label_for_building(suas_data, satellite_data, valid_ids, comparison, ignore_lone_unclassified=True):
    sUAS_labels = {}

    for data in suas_data:
        for building in data:
            if building["id"] in valid_ids:
                sUAS_labels[building["id"]] = building["label"]

    satellite_labels = defaultdict(lambda: None)
    for data in satellite_data:
        for building in data:
            if building["id"] in valid_ids:
                new_label = get_swapped_unclassified_label(
                    satellite_labels[building["id"]],
                    building["label"],
                    ignore_lone_unclassified,
                )
                if satellite_labels[building["id"]] is None:
                    satellite_labels[building["id"]] = new_label
                elif comparison(new_label, sUAS_labels[building["id"]]):
                    satellite_labels[building["id"]] = new_label

    return sUAS_labels, satellite_labels

def get_best_antioracle_label_for_building(suas_data, satellite_data, valid_ids, ignore_lone_unclassified=True):
    neq = lambda a,b:a!=b
    return get_best_cheat_label_for_building(suas_data, satellite_data, valid_ids, comparison=neq, ignore_lone_unclassified=True)

def get_best_oracle_label_for_building(suas_data, satellite_data, valid_ids, ignore_lone_unclassified=True):
    eq = lambda a,b:a==b
    return get_best_cheat_label_for_building(suas_data, satellite_data, valid_ids, comparison=eq, ignore_lone_unclassified=True)

def get_best_temporal_label_for_building(suas_data, satellite_data, valid_ids, multiview_info, sort_strategy="abs", ignore_lone_unclassified=True):
    sUAS_labels = {}

    for data in suas_data:
        for building in data:
            if building["id"] in valid_ids:
                sUAS_labels[building["id"]] = building["label"]

    satellite_labels = defaultdict(lambda: None)
    for data in satellite_data:
        for building in data:
            if building["id"] in valid_ids:
                new_label = building["label"]
                if satellite_labels[building["id"]]:
                    new_label = get_swapped_unclassified_label(satellite_labels[building["id"]][0], building["label"], ignore_lone_unclassified,)
                source_filename_label = building[FILENAME].split("\\")[-1].replace(".json", "")
                days_after_suas_ortho = multiview_info[multiview_info[FILENAME] == source_filename_label][DAYS_AFTER_SUAS_ORTHO].iloc[0]
                if sort_strategy == "abs":
                    days_after_suas_ortho = np.abs(days_after_suas_ortho)
                elif sort_strategy == "real":
                    pass
                if satellite_labels[building["id"]] is None:
                    satellite_labels[building["id"]] = [new_label, days_after_suas_ortho]
                elif satellite_labels[building["id"]][1] > days_after_suas_ortho:
                    satellite_labels[building["id"]] = [new_label, days_after_suas_ortho]

    resulting_sat_labels = {}
    for bld_id, value in satellite_labels.items():
        if not value is None:
            label, _ = value
            resulting_sat_labels[bld_id] = label

    return sUAS_labels, resulting_sat_labels

def compute_paired_difference_views(temporal_views, field, ignore_unclassified=True, ignore_obscured=True):
    sat_view_1 = []
    sat_view_2 = []

    for (day1, view1), (day2, view2) in combinations(temporal_views.items(), 2):
        buildings_day2 = {building["id"]: building for building in view2}
        delta_days = np.abs(day1 - day2)
        for building1 in view1:
            building_id = building1["id"]
            if building_id in buildings_day2:
                value = None
                valid = False

                if field == "days":
                    value = delta_days
                    valid = True
                else:
                    try:
                        field1 = building1["view_properties"][field]
                        field2 = buildings_day2[building_id]["view_properties"][field]
                        value = np.abs(field1 - field2)
                        valid = True
                    except KeyError:
                        pass
                if valid:
                    label1 = building1["label"]
                    label2 = buildings_day2[building_id]["label"]
                    if not (
                        (
                            (label1 == UNCLASSIFIED or label2 == UNCLASSIFIED)
                            and ignore_unclassified
                        )
                        or (
                            (label1 == OBSCURED or label2 == OBSCURED)
                            and ignore_obscured
                        )
                    ):
                        sat_view_1.append([label1, value])
                        sat_view_2.append([label2, value])

    agree_dist = []
    disagree_dist = []
    for i, (label1, field) in enumerate(sat_view_1):
        if label1 == sat_view_2[i][0]:
            agree_dist.append(field)
        else:
            disagree_dist.append(field)
    return agree_dist, disagree_dist

def group_buildings_temporally(satellite_data, multiview_info):
    group_temporal = {}

    for data in satellite_data:
        for building in data:
            source_filename_label = building[FILENAME].split("\\")[-1].replace(".json", "")
            if len(multiview_info[multiview_info[FILENAME] == source_filename_label]) == 0:
                print(source_filename_label)
            days_after_suas_ortho = multiview_info[multiview_info[FILENAME] == source_filename_label][DAYS_AFTER_SUAS_ORTHO].iloc[0]
            if days_after_suas_ortho not in group_temporal.keys():
                group_temporal[days_after_suas_ortho] = []
            group_temporal[days_after_suas_ortho].append(building)

    return group_temporal

