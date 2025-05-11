from constants import BDA_DAMAGE_CLASSES, OBSCURED

def get_class_counts_from_ids(id2labels, ignore_obscured):
    bda1_damage_labels = {l:0 for l in BDA_DAMAGE_CLASSES}

    ids_to_consider = []
    for bld_id in id2labels.keys():
        if (ignore_obscured and id2labels[bld_id] != OBSCURED) or not ignore_obscured:
            ids_to_consider.append(bld_id)

    for bld_id in ids_to_consider:
        bda1_damage_labels[id2labels[bld_id]] += 1

    return bda1_damage_labels

def get_intersecting_ids(annotations_data1, annotations_data2):
    bda_1_ids = []
    bda_2_ids = []
    # Count Damage Labels for sUAS data format
    for data in annotations_data1:
        for building in data:
            bda_1_ids.append(building["id"])

    # Count Damage Labels for Satellite data format
    for data in annotations_data2:
        for building in data:
            bda_2_ids.append(building["id"])

    valid_ids = list(set(bda_1_ids) & set(bda_2_ids))
    return valid_ids

def remove_obscured_labels(labeled_data):
    result = []
    for data in labeled_data:
        result.append([])
        for building in data:
            if building["label"] != OBSCURED and building["label"] != OBSCURED.lower():
                result[-1].append(building)
    return result