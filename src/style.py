"""One chart style for every figure in the deck."""
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

from prep import FIGURES

INK = "#1F2A44"        # text / neutral dark
GREY = "#B8BEC9"       # context bars
ACCENT = "#D1495B"     # the point being made (bad)
GOOD = "#2A9D8F"       # the recommended option
BLUE = "#3A6EA5"
AMBER = "#E9A23B"
PCT = PercentFormatter(1.0, decimals=0)


def use():
    mpl.rcParams.update({
        "figure.figsize": (10, 5.2), "figure.dpi": 110, "savefig.dpi": 200,
        "savefig.bbox": "tight", "font.family": "DejaVu Sans", "font.size": 11,
        "axes.titlesize": 15, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "axes.labelcolor": INK, "axes.edgecolor": "#8A93A6", "axes.spines.top": False,
        "axes.spines.right": False, "axes.grid": True, "grid.color": "#E6E9EF",
        "grid.linewidth": 0.8, "axes.axisbelow": True, "text.color": INK,
        "xtick.color": INK, "ytick.color": INK, "legend.frameon": False,
    })


def titled(ax, title, subtitle=None):
    """Finding as the title, method/detail as a grey subtitle."""
    ax.set_title(title, pad=24 if subtitle else 10)
    if subtitle:
        ax.text(0, 1.03, subtitle, transform=ax.transAxes, fontsize=10.5, color="#5B6477")


def save(fig, name, source="Source: BTS Reporting Carrier On-Time Performance, 2025"):
    fig.text(0.01, -0.02, source, fontsize=8.5, color="#7A8394", ha="left")
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / f"{name}.png")
    return fig
