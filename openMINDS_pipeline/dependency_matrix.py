from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Polygon, FancyArrowPatch
from matplotlib.path import Path

# ----------------------------------------------------------------------
# 1. DATA  —  edit this section to describe your own components
# ----------------------------------------------------------------------

def build_relationships(dependency_relations: dict):
    MODULES = [
        ("core",            "core",            "research products & specimen",                             "essentials", True),
        ("controlledTerms", "controlledTerms", "common terminologies",                                     "essentials", True),
        ("SANDS",           "SANDS",           "brain atlases & anatomical data locations",               "extensions", True),
        ("chemicals",       "chemicals",       "composition & mixture of chemicals",                       "extensions", False),
        ("computation",     "computation",     "computational activities & workflows",                     "extensions", False),
        ("ephys",           "ephys",           "electrophysiological experiments & equipment",            "extensions", False),
        ("publications",    "publications",    "publication types & their bibliographic records",         "extensions", False),
        ("specimenPrep",    "specimenPrep",    "pre- & post-experimental preparation steps of specimens", "extensions", False),
        ("stimulation",     "stimulation",     "stimulation specification",                                "extensions", False),
        ("neuroimaging",    "neuroimaging",    "MRI experimentations specification",                       "extensions", False),
    ]
    MODULES[:] = [
        module
        for module in MODULES
        if module[0] in dependency_relations.keys() or module[0] == 'controlledTerms'
    ]

    relationships = []
    for module in dependency_relations:
        for sub_module in dependency_relations[module]:
            target_module = 'SANDS' if 'sands' == sub_module else sub_module
            if 'true dependency' in dependency_relations[module][sub_module]:
                relationships.append((module, target_module,  "depends_on", target_module))
                continue
            else:
                relationships.append((module, target_module,  "can_link", target_module))
                continue
    return relationships, MODULES


FOOTNOTE = (
    "Available instance libraries for:\n"
    "core - License & ContentType\n"
    "controlledTerms - all terminologies\n"
    "SANDS - all atlas elements"
)

# ----------------------------------------------------------------------
# 2. STYLE
# ----------------------------------------------------------------------
DARK = "#4d4d4d"
LIGHT = "#bcbcbc"
ESSENTIAL_BG = "#a3a3a3"
EXTENSION_BG = "#dadada"
EDGE = "#161616"
ROW_H = 1.0
S = ROW_H / 2  # diamond half-diagonal

# ----------------------------------------------------------------------
# 3. LAYOUT + DRAWING  (generic — shouldn't need edits)
# ----------------------------------------------------------------------

def row_y(i):
    return -i * ROW_H


def row_box(x_left, x_right, y_c, color, notch_amt):
    pts = [(x_left, y_c + 0.5), (x_right, y_c + 0.5)]
    if notch_amt:
        pts.append((x_right + notch_amt, y_c))
    pts += [(x_right, y_c - 0.5), (x_left, y_c - 0.5)]
    return Polygon(pts, closed=True, facecolor=color, edgecolor=EDGE, linewidth=1.2, zorder=2)


def diamond(cx, cy, s):
    return Polygon(
        [(cx, cy + s), (cx + s, cy), (cx, cy - s), (cx - s, cy)],
        closed=True, facecolor="white", edgecolor=EDGE, linewidth=1.0, zorder=2,
    )


def elbow_path(cx, cy, s, mirror, nudge, scale=1.0, leg=(0.26, 0.48), round_amt=0.42):
    """A long leg + a short, tightly-rounded hook -- the shape actually used
    in the source figure, as opposed to a single smooth arc."""

    fx, fy = leg[0] * s * scale, leg[1] * s * scale
    start, end = (cx + fx, cy - fy), (cx - fx, cy + fy)   # points up-left by default
    corner = (start[0], end[1])
    if mirror:  # reflect the whole glyph about cy -> points down-left instead
        start, end, corner = ((p[0], 2 * cy - p[1]) for p in (start, end, corner))
    if nudge:
        start, end, corner = ((p[0] + nudge, p[1] + nudge) for p in (start, end, corner))
    r = round_amt
    p1 = (corner[0], corner[1] + (start[1] - corner[1]) * r)  # short of the corner, on the long leg
    p2 = (corner[0] + (end[0] - corner[0]) * r, corner[1])    # short of the corner, on the hook
    return Path([start, p1, corner, p2, end],
                [Path.MOVETO, Path.LINETO, Path.CURVE3, Path.CURVE3, Path.LINETO])


def add_cell_arrow(ax, cx, cy, s, kind, points_to_i, paired=False, nudge=0.0):
    color = DARK if kind == "depends_on" else LIGHT
    #lw = 2.2 if kind == "depends_on" else 1.35
    #mut = 8.5 if kind == "depends_on" else 6.5
    #lw, mut, scale = (1.9, 7.5, 0.55) if paired else \
    #    ((2.2, 8.5, 1.0) if kind == "depends_on" else (1.35, 6.5, 1.0))
    lw, mut, scale = (1.9, 13, 0.55) if paired else \
        ((2.2, 15, 1.0) if kind == "depends_on" else (1.35, 15, 1.0))
    path = elbow_path(cx, cy, s, mirror=not points_to_i, nudge=nudge, scale=0.55 if paired else 1.0)
    ax.add_patch(FancyArrowPatch(
        path=path, arrowstyle="-|>", mutation_scale=mut, linewidth=lw,
        color=color, shrinkA=0, shrinkB=0, joinstyle="round", capstyle="round", zorder=3,
    ))
    """
    p_ul = (cx - s * 0.55, cy + s * 0.55)
    p_dr = (cx + s * 0.55, cy - s * 0.55)
    #start, end = (p_dr, p_ul) if points_to_i else (p_ul, p_dr)
    start, end, rad = (cx + s * 0.55, cy - s * 0.55), (cx - s * 0.55, cy + s * 0.55), 0.25
    if not points_to_i:
        # mirror vertically about cy (not just swap the endpoints) so this
        # points down toward the row *lower* in the list instead of sideways
        start = (start[0], 2 * cy - start[1])
        end = (end[0], 2 * cy - end[1])
        rad = -rad

    if nudge:
        start = (start[0] + nudge, start[1] + nudge)
        end = (end[0] + nudge, end[1] + nudge)
    ax.add_patch(FancyArrowPatch(
        start, end, arrowstyle="-|>", mutation_scale=mut, linewidth=lw,
        color=color, shrinkA=0, shrinkB=0, connectionstyle="arc3,rad=0.25", zorder=3,
    ))
    """

def plot_dependency_matrix(relationships, MODULES, version):
    idx = {m[0]: i for i, m in enumerate(MODULES)}
    n = len(MODULES)
    TITLE = f"openMINDS {version}"

    fig, ax = plt.subplots(figsize=(15, 9.2), dpi=170)
    ax.set_aspect("equal")
    ax.axis("off")

    # left-hand table
    name_left, name_right = -6.4, 0.0
    group_left, group_right = -8.4, name_left
    #notch = 0.28
    notch = S

    for i, (key, label, subtitle, group, starred) in enumerate(MODULES):
        y = row_y(i)
        bg = ESSENTIAL_BG if group == "essentials" else EXTENSION_BG
        ax.add_patch(row_box(name_left, name_right, y, bg, notch))
        title = label + ("*" if starred else "")
        n_lines = subtitle.count("\n") + 1
        title_y = y + (0.20 if n_lines == 1 else 0.27)
        sub_y = y - (0.16 if n_lines == 1 else 0.10)
        ax.text(name_left + 0.18, title_y, title, fontsize=15.5, fontweight="bold", va="center", ha="left")
        ax.text(name_left + 0.18, sub_y, subtitle, fontsize=9, va="center", ha="left", linespacing=1.35, color="#222222")

    # group boxes, merging consecutive rows that share a group
    groups, cur = [], None
    for i, m in enumerate(MODULES):
        if cur and cur[0] == m[3]:
            cur[2] = i
        else:
            cur = [m[3], i, i]
            groups.append(cur)

    for group, i0, i1 in groups:
        y_top, y_bot = row_y(i0) + 0.5, row_y(i1) - 0.5
        color = ESSENTIAL_BG if group == "essentials" else EXTENSION_BG
        ax.add_patch(mpatches.Rectangle((group_left, y_bot), group_right - group_left, y_top - y_bot,
                                         facecolor=color, edgecolor=EDGE, linewidth=1.2, zorder=2))
        ax.text((group_left + group_right) / 2, (y_top + y_bot) / 2, group,
                fontsize=13, fontweight="bold", ha="center", va="center")

    # triangular diamond matrix
    rel_lookup = defaultdict(list)
    for a, b, kind, target in relationships:
        i, j = idx[a], idx[b]
        rel_lookup[(min(i, j), max(i, j))].append((kind, target))

    for i in range(n):
        for j in range(i + 1, n):
            d = j - i
            cx, cy = d * S, -(i + j) * S
            ax.add_patch(diamond(cx, cy, S))

    for (i, j), rels in rel_lookup.items():
        d = j - i
        cx, cy = d * S, -(i + j) * S
        a_key, b_key = MODULES[i][0], MODULES[j][0]
        if len(rels) == 1:
            kind, target = rels[0]
            add_cell_arrow(ax, cx, cy, S, kind, points_to_i=(target == a_key))
        else:
            for kind, target in rels[:2]:#enumerate(rels[:2]):
                #nudge = 0.12 if k == 0 else -0.12
                #dd_cell_arrow(ax, cx, cy, S, kind, points_to_i=(target == a_key), nudge=nudge)
                #nudge = 0.10 if kind == "depends_on" else -0.10  # depends_on left, can_link right
                nudge = 0
                points_to_i = target == a_key
                cy_offset = 0.1 + cy if points_to_i else -0.1 + cy
                add_cell_arrow(ax, cx, cy_offset, S, kind, points_to_i=(target == a_key), paired=True, nudge=nudge)

    # title, legend, footnote (in the empty wedge above/right)
    ax.text(1.6, 1.0, TITLE, fontsize=22, fontweight="bold", ha="left", va="bottom")

    # NOTE: this sits in the empty triangle above the "core" diagonal (y > -x),
    # which is guaranteed free of diamonds -- keep it up here, not inside the wedge.
    leg_x, leg_y = 2.55, -0.15
    ax.annotate("", xy=(leg_x - 0.5, leg_y), xytext=(leg_x + 0.1, leg_y),
                arrowprops=dict(arrowstyle="-|>", color=DARK, lw=2.6, mutation_scale=14))
    ax.text(leg_x + 0.3, leg_y, "depends on", fontsize=13, va="center", ha="left")
    ax.annotate("", xy=(leg_x - 0.5, leg_y - 0.62), xytext=(leg_x + 0.1, leg_y - 0.62),
                arrowprops=dict(arrowstyle="-|>", color=LIGHT, lw=1.6, mutation_scale=11))
    ax.text(leg_x + 0.3, leg_y - 0.62, "can link to", fontsize=13, va="center", ha="left")

    ax.set_xlim(group_left - 0.3, 8.1)
    ax.set_ylim(row_y(n - 1) - 0.7, 1.5)
    fig.patch.set_facecolor("#f2f2f2")
    ax.set_facecolor("#f2f2f2")

    OUT_PATH = f"dependency_matrix_{version}.png"
    fig.savefig(OUT_PATH, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"saved {OUT_PATH}")
