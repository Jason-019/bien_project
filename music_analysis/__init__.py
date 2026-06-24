"""
music_analysis — BWV861 音乐形式化分析工具箱

严格按照 formalization_v1.md 实现:
    event → window → motif → theme → network → fracture metrics
"""

from . import config
from . import events
from . import windows
from . import features
from . import motifs
from . import themes
from . import distance
from . import network
from . import dynamics
from . import viz
