# -*- coding: utf-8 -*-
"""材料レポート射影器 (D12 / roadmap §3.6(4)・§7 forensic binding)。

WAL / calibration の生データを、人間可読な材料レポート (gnuplot グラフ + 数値表 + 手打ち
再現コマンド) に射影する。**再現性が一級市民**: 各図は .dat (データ + 生成コマンドを #
コメント) + .plt (gnuplot script) + .png の3点セットで残し、後で手打ちでも近似再現できる。
"""
from .plot import DatFile, PlotSpec, Series, make_plot          # noqa: F401
from .calibration_report import calibration_report              # noqa: F401

__all__ = ["DatFile", "PlotSpec", "Series", "make_plot", "calibration_report"]
