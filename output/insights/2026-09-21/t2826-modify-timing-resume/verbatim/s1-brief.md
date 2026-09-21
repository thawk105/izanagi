# 段 1 brief — [T-2826] 再開 wave (前 wave = entry 1800、段 4 から再開する型)

wave `dev-wave-t2826-resume`、起点 local main `36fb14a3d131d516dc57b02ec69f56c711927c2e` (fresh worktree、HEAD == main、clean、submodule 初期化 rc 0、開始 gate `check_wave_startup.py --mode fresh --external-handoff` rc 0)。
**標本の時点 (本 wave で固定):** 計測 tip = `36fb14a3d`、as-of = 2026-09-21 20:26:33 JST (`startup-gate.log` の mtime。gate command の起動は 20:26:20、`startup-gate.started.txt`)。job 完了まで wave 木へ main を取り込まない。
依頼の逐語は `T-2826-resume-origin.md`。前 wave の資料は `output/insights/2026-09-21/t2826-shard-plugin-modify-timing/` (README §6 が再開手順、`verbatim/s4-ruling.md` §3 / §4 が仕様の正本)。

## 研究前進 (1 行)
前 wave と同じ (土台: 受入全走の最遅 shard を 5 分以内へ、D2148 項 6)。完了判定 = S2 / S3 形で modify 複合区間の関数別内訳を事前登録 R1 で判定し、反実仮想 S3cf で worker 側の短縮量と `pre` の変化を別々に測った値が出ること。無ければ D2200 項 4・7 の再提示条件が「T-2617 の単一 process 値」と「T-2817 の 48 並列 +45 秒」の未分解のまま評価される (DW-G05)。

## scope
前 wave brief の scope のまま (計算ノード 1 job・11 セル、repo の実装 0 行、probe は job dir で Codex author、仮想リスク向けの gate・検査・台帳・一般化は scope 外)。段 2 は省き、段 3 相談は前 wave の 1 本 (所見 9 件、全件 real・採用) を流用する (入口「裁定後に別 context が段 4 から再開する型」、変更面の骨格 = probe 3 file・job dir・repo 差分ゼロは同一)。再検査は段 6 review 1 本へ寄せる。

## 確定済みユーザー裁定
前 wave brief の列挙 (D1936 項 35、D2148 項 6、D2185、D532、D1729 / D2047 / D2200 項 7、D2200 項 4・5、T-2617 §4 を覆さない) に加え、今回の起動引数: 段 4 で前 wave 裁定 §3 / §4 を**変えずに**採り直す、段 5 prompt は前 wave の雛形の wave 固有値だけ差し替え新しい `--job-id`、書きかけ probe は参考資料だけ、F818 は他 wave が記録済みなら足さない、本題の計測だけ。

## brief 前の前提実測 (新事実)
- N1 (更新). 対象 3 file (`tools/acceptance_shards.py`・`orchestrator/tests/conftest.py`・`tools/run_tests.py`) は T-2817 の計測 tip `2afb39768` からも前 wave の基点 `d99c556df` からも `36fb14a3d` まで差分 0 行 (git diff --shortstat が空) → 関数の行番号は雛形のまま (L761 / 790 / 381 / 895 / 1013 / 1097、conftest L2180 / 2252 / 2388 / 2469 / 2550)。**所要台帳** `orchestrator/tests/acceptance_duration_ledger.json` は T-2825 の refresh 再生成 (`26387b617`、`36fb14a3d` の祖先・`d99c556df` の祖先でない) で `d99c556df` → `36fb14a3d` が +15,645 / −13,852 行 (`2afb39768` → は +15,645 / −13,419 行)。`allocate` は台帳の値を重みに使うので shard-0 の選択集合と shard 内順序は前 wave の基点とも T-2817 とも変わり得る。T-2825 (entry 1803) は固定 2 tree の A / B で「shard-0 の構成は同一、変わったのは shard-1 ↔ 2 の割付と shard 内の順序」と観測したが、本 tip での同一性は見ていない (見るなら集合照合)。R4 の集合照合は同 job 内の比較なので tip 差の影響を受けない。T-2817 の S2 / S3 値は参照に留める (裁定 §4「比較の限定」の「台帳 +434 行」は本 tip では上記の差に読み替える)。
- N1b. `d99c556df` → `36fb14a3d` で `orchestrator/` と `tools/` の変更は 11 file すべて M (追加・削除 0)。test file は 4 本 (317 行追加 / 30 行削除、`def test_` の追加・削除行 10) → collection 件数は前 wave の login 観測 27,033 と同じとは限らない。
- N5 (更新). T-2825 は land 済み (entry 1803、archive `worklog-phase3-0921-1803.md`)。比較測定の区間の重なりはもう生じない。稼働中の peer は next-tasks・cleanup-branches・tier0 generator・t2632 b4・rulings の 5 本 (20:24 の ListAgents)。計算ノードでの外乱は R8 (受入 collection 区間の照合) と各セルの単独性記録で扱う。
- N6. Codex の可用性: 17:46 JST の他 wave の子は `You’ve hit your usage limit ... Sep 26th, 2026 7:35 PM` で停止したが、`~/.codex/auth.json` が 20:19 に更新され、20:20 投入の他 wave の子は上限表示 0 件で command 実行 30 件まで進んでいる → 使える状態と判断 (確定は本 wave の子の receipt で見る)。
- N7. F818 には 2026-09-21 の再発追記が既に 2 件ある (論文草稿 wave の段 6 review、T-2833 の段 6 review)。前 wave の漏れ (同日同型) は依頼どおり**足さない**。
- N8. 書きかけ probe: branch `author-t2826-probe` は cleanup-branches が 20:26:54 に削除した (peer 通知)。commit `31894443efd6c662f9e257d1055a0da0d15ca375` は object DB に在り (`git cat-file -t` = commit)、その `tools/` の 3 blob と前 job dir `partial-author/` の 3 file の `git hash-object` が一致することを本 wave で実測した → prompt では `partial-author/` の絶対 path を参考資料 (未検査) として渡す。
- N9. T-2817 の probe 原本 (`dev-wave-t2817-acceptance-bottleneck-3/probe/` の runner / plugin / aggregate) は現存。

## 不変条件
規律 2 (受理集合・hold・verifier に触れない)、規律 7 (T-2617 / T-2817 の値を無効化しない)、D1936 項 35 (実装しない)、tracked file の一時変異 0 件、probe は job dir (repo は逐語 `.txt`)、計測 tip = `36fb14a3d`。

## 成果物
前 wave の insight dir を上書きせず、新しい insight `output/insights/2026-09-21/t2826-modify-timing-resume/` (README = 結論・計測・関数別表・R1〜R8 の判定・限界・再現、機械集計、`raw/`、`verbatim/`)。worklog fragment。T-2826 の次の一手の更新。

## 分割方針
段 1 → 段 4 (前 wave 裁定 §3 / §4 を採り直し、wave 固有値の差し替え表だけ新規) → 段 5 Codex author 1 本 → 親の login 生死確認 (`T2826_WORKERS=2`) → 計算ノード job 1 本 → 集計・README → 段 6 read-only review 1 本 + 焦点再レビュー (上限 3 巡) → 受入 1 走 → 7 → 8 → 9。
