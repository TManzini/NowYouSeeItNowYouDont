from collections import defaultdict

from scipy.stats import chi2_contingency, ttest_ind
from statsmodels.stats.proportion import proportions_ztest

from constants import NO_DAMAGE, MINOR_DAMAGE, MAJOR_DAMAGE, DESTROYED, UNCLASSIFIED, OBSCURED

def chi_squared_test(suas_labels, sat_labels, ignore_sat_obscured):
    suas_label_counts = defaultdict(lambda: 0)
    sat_label_counts = defaultdict(lambda: 0)
    for suas_label, sat_label in zip(suas_labels.values(), sat_labels.values()):
        if (ignore_sat_obscured and sat_label != OBSCURED) or not ignore_sat_obscured:
            suas_label_counts[suas_label] += 1
            sat_label_counts[sat_label] += 1

    data = []
    for label in set(list(suas_label_counts.keys()) + list(sat_label_counts.keys())):
        data.append([suas_label_counts[label], sat_label_counts[label]])

    _, p, _, _ = chi2_contingency(data)

    return p

def z_test_per_label(suas_labels, sat_labels, ignore_sat_obscured):
    p_values = {}

    suas_label_counts = defaultdict(lambda: 0)
    sat_label_counts = defaultdict(lambda: 0)
    for suas_label, sat_label in zip(suas_labels.values(), sat_labels.values()):
        if (ignore_sat_obscured and sat_label != OBSCURED) or not ignore_sat_obscured:
            suas_label_counts[suas_label] += 1
            sat_label_counts[sat_label] += 1

    n_observations = [len(suas_labels), len(sat_labels)]

    for label in [NO_DAMAGE, MINOR_DAMAGE, MAJOR_DAMAGE, DESTROYED, UNCLASSIFIED]:
        data = [suas_label_counts[label], sat_label_counts[label]]
        p_values[label] = proportions_ztest(data, n_observations)[1]
    return p_values

def get_coincident_buildings_per_ortho(valid_ids, suas_data):
    file_to_coincident_count = {}
    for filename, data in suas_data.items():
        file_to_coincident_count[filename] = 0
        for building in data:
            if building["id"] in valid_ids:
                file_to_coincident_count[filename] += 1
    return file_to_coincident_count

def get_satellite_building_counts(satellite_data, valid_ids):
    view_count = 0
    for data in satellite_data:
        for building in data:
            if building["id"] in valid_ids:
                view_count += 1
    return view_count