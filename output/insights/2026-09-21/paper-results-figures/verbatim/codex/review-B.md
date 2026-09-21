## 所見

| # | 種別 (過剰 / 不足 / 縮小可) | 重大度 | 対象 (file:line / README 節) | 内容 | 根拠 | 推奨 (削る / 足す / 置き換える) と成果物影響 1 行 |
|---|---|---|---|---|---|---|
| 1 | 過剰 | should | `tools/plotting/README.md:514` | Fisher p・commit 数平均まで `summary.json` と照合したように記述している。 | brief P6 は両量が summary に無いと明記。`plot_mocc_witlight_four_arm.py:208` の照合対象にも無い。figures README:1998 は正しく区別している。 | **置き換える**：「summary が持つ量だけ照合し、Fisher p・commit 平均・曝露比は稿と test で照合」。過大な照合主張を削っても図・caption・provenance の値、受理集合、参照先は不変。 |
| 2 | 不足 | should | `orchestrator/tests/test_plot_mocc_witlight_four_arm.py:20` | plain runner が既存 A-1 と異なり、repo package を import できる外部環境設定に依存する。 | `python3 orchestrator/tests/test_plot_mocc_witlight_four_arm.py` では script のディレクトリが探索起点になる。repo のインストールや `PYTHONPATH` が無い環境では `orchestrator.tests.skiputil` を解決できない。A-1:17–20 は同階層の `skiputil` を読む。段4は A-1 と同型の直接起動を指定。 | **置き換える**：A-1 と同じ同階層 import に揃える。図・caption・provenance・README と生成器の受理集合は不変で、検査起動の環境依存だけを除く。静的所見であり、環境を外した実走は未実施。 |
| 3 | 縮小可 | nit | `tools/plotting/plot_mocc_witlight_four_arm.py:342` | 隣接 panel への侵入検査は、この専用生成器では到達不能。 | :329 で `fig.axes` が指定した唯一の axes と一致することを要求する。その後の :344 の「別 axes」は存在しない。段4も 1 axes 固定。 | **削る**：:342–345 の隣接 panel 検査だけを削除する。1 axes 制約、figure 外逸脱、text 重なり検査を残せば、成果物の値・受理集合・参照は変わらない。 |

## 探したが所見なしの項目

- **fig14 の形と breach 開示**：fig9 の3 panel・点・平均・区間・床線を維持し、breach・sd・planned sigma と attempt 限定を実 artist に追加している。attempt-0001 の値を併記する経路は見当たらない。
- **fig15 の情報と限定**：4 arm の率・CP 区間・曝露量を1図に配置。非 certifying、TRACE=1、曝露と性能の区別、片側 Fisher、計算上の power、根因を同定しない旨が可視注記にある。条件・smoke 除外・独立性仮定は caption にある。
- **汎用化・互換層**：attempt は exact 2 entry、mocc は固定4 block・4 arm。任意構成への一般化、verbatim fallback、240走の provenance 保存は追加されていない。
- **再現コマンド**：figures README の fig14 は attempt-0002 を明示し、fig15 は正しい外部 root を指定する。CLI と整合する。
- **テスト所要・実描画**：親実測の合計約6.6秒は段4の60秒基準内。単一プロセスでは fig14 追加4 Figure、mocc は共有 fixture・CLI・実証拠の計3 Figure。削減必須とする所要の根拠はない。
- **負例と閉包**：bundle 欠落は裁定どおり全欠落＋単独欠落3例。repo 内自己整合と外部原本再導出の違いも figures README に明記されている。

## 総括

本レビューの **must-fix は0件、should は2件、nit は1件**。
本レンズの判定は **GO**。図素材を使えなくする新たな欠陥は、静的審査では見つからなかった。
README の照合範囲と plain runner の import は局所修正を推奨する。
削除候補は1 axes 制約下の隣接 panel 検査で、追加の仕組みは不要。
親ログは **800 passed / 4 failed / 3 skipped、36.70秒**であり、全緑とは扱っていない。
既知4失敗は指示どおり所見に重複計上せず、予定済みの修正・再検査に委ねる。
書込み・テスト再実行・画像の目視検査は行っておらず、本判定は指定差分と資料・親実測の射程に限る。