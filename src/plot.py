import os

import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix

from constants import BDA_DAMAGE_CLASSES, OBSCURED

def plot_transistion_matrix(suas_id2labels, sat_id2labels, plot_folder, prefix="", ignore_obscured=True):

    suas_labels = [suas_id2labels[bld_id] for bld_id in sat_id2labels]
    sat_labels = [sat_id2labels[bld_id] for bld_id in sat_id2labels]

    labels = BDA_DAMAGE_CLASSES[:]
    try:
        labels.remove(OBSCURED)
    except ValueError:
        pass

    transition_matrix = confusion_matrix(y_true=suas_labels, y_pred=sat_labels, labels=labels)

    conf_matrix = np.array(transition_matrix)
    fig, ax = plt.subplots(figsize=(9, 9))
    ax.matshow(conf_matrix, cmap=plt.cm.Blues, alpha=0.3)
    plt.xticks(range(conf_matrix.shape[1]), labels, fontsize=13)
    plt.yticks(range(conf_matrix.shape[0]), labels, fontsize=13)
    for i in range(conf_matrix.shape[0]):
        for j in range(conf_matrix.shape[1]):
            ax.text(x=j, y=i, s=conf_matrix[i, j], va="center", ha="center", size="xx-large")
            plt.xlabel("Satellite", fontsize=15)
            plt.ylabel("Drone", fontsize=15)
    plt.title(prefix + " vs. Drone Confusion Matrix | N=" + str(len(sat_labels)), fontsize=18)

    print("Saving Confusion Matrix at ", str(os.path.join(plot_folder, prefix + "suas_vs_satellite_transition_matrix.png")))
    plt.savefig(os.path.join(plot_folder, prefix + "suas_vs_satellite_transition_matrix.png"), dpi=300, bbox_inches="tight")

def plot_mulistrategy_class_balances(suas_damage_counts, sat_multistrategy_damage_counts, plot_folder, valid_ids):
    all_bars = {"Drone": suas_damage_counts}
    for strategy_name in sat_multistrategy_damage_counts.keys():
        all_bars[strategy_name] = sat_multistrategy_damage_counts[strategy_name]
        all_bars[strategy_name].pop("Obscured", None)

    all_bars["Drone"].pop("Obscured", None)
    categories = all_bars["Drone"].keys()

    num_buildings = sum(all_bars["Drone"][label] for label in all_bars["Drone"].keys())

    x = np.arange(len(categories))
    multicol_area = 1.0
    bar_width = multicol_area / (len(categories) + 1)
    bar_width_downscale = 0.9

    fig, ax = plt.subplots(figsize=(24, 8))
    all_plotted_bars = []
    hatches = [".", "/", "x", "|", "*", "-", "+"]
    for i, (strat_label, damage_label_counts) in enumerate(all_bars.items()):
        if i == 0:
            all_plotted_bars.append(
                ax.bar(x + bar_width * i, list(damage_label_counts.values()), bar_width, label=strat_label, color="black", edgecolor="white", hatch=hatches[i])
            )
        else:
            all_plotted_bars.append(
                ax.bar(x + bar_width * i, list(damage_label_counts.values()), bar_width, label=strat_label, color="lightgrey", edgecolor="black", hatch=hatches[i])
            )

    ax.set_xlabel("Building Damage Classes", fontsize=22)
    ax.set_ylabel("Counts", fontsize=20)
    ax.set_title("Building Damage Class Counts: Drone vs Satellite ($N_{Buildings}$=" + str(num_buildings) + ")", fontsize=30)
    ax.set_xticks(x + (bar_width * (len(categories) - 2)) / 2)
    ax.set_xticklabels(categories, fontsize=18, rotation=0)
    ax.tick_params(axis="y", which="major", labelsize=16)
    ax.legend(fontsize=20)

    max_bar = 0
    for bars in all_plotted_bars:
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f"{height}", xy=(bar.get_x() + bar.get_width() / 2, height), xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=13)

            if height > max_bar:
                max_bar = height

    ax.set_ylim(0, max_bar * 1.2)

    print("Saving Class Balance Figure at ", str(os.path.join(plot_folder, "suas_vs_satellite_strat_bda_class_balances.png")))
    plt.savefig(os.path.join(plot_folder, "suas_vs_satellite_multistrat_bda_class_balances.png"), dpi=300, bbox_inches="tight")

def plot_sat_views_per_building_histogram(satellite_data, valid_ids, plot_folder, file_prefix=""):
    views_per_building = defaultdict(lambda: 0)
    for data in satellite_data:
        for building in data:
            if building["id"] in valid_ids:
                views_per_building[building["id"]] += 1
    
    x = list(views_per_building.values())

    tick_positions = [1.5, 2.5, 3.5, 4.5]

    fig, ax = plt.subplots(figsize=(12, 8))
    n, bins, _ = plt.hist(x, bins=[1, 2, 3, 4, 5], color="grey")
    ax.set_xlabel("Number of Views", fontsize=20)
    ax.set_ylabel("Number of Buildings", fontsize=20)
    ax.set_title("Histogram of Satellite Views per Building\n($N_{Buildings}$=" + str(len(x)) + " | $N_{Views}$=" + str(int(sum(x))) + ")", fontsize=25)
    ax.set_xticks(tick_positions)
    ax.set_xticklabels([1, 2, 3, 4])
    ax.tick_params(axis="both", which="major", labelsize=16)

    for x, val in zip(tick_positions, n):
        ax.annotate(f"{int(val)}", xy=(x, val), xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=14,)

    print("Saving view histogram figure at ", str(os.path.join(plot_folder, file_prefix + "view_histogram.png")))
    plt.savefig(os.path.join(plot_folder, file_prefix + "satellite_view_counts_per_building.png"), dpi=300, bbox_inches="tight")
