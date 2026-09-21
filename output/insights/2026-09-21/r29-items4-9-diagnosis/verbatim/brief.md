# 段 1 brief — 第 29 回 /rulings 項 4 (R2) と項 9 (exact 目録 test) の診断

起点: ユーザーの `/dev-wave` 起動 (2026-09-21、背景 job f5c26dfa)。起点 local main `d99c556df` (fresh worktree
`worktree-dev-wave-r29-items4-9-diagnosis`、開始 gate rc 0 = 2026-09-21T14:06:02+09:00、`startup-gate.log`)。軽量版 + 診断 wave の最小
(段 2 plan 1 本、段 3 相談 1 本、段 6 独立 read-only レビュー 1 本、実装面 0 行、変異免除 = DW-S04、受入全走は免除しない)。

## 研究前進 (土台)

止めている研究: 研究 wave (直近 12 wave の impl 7 本) の焦点走は 1 wave 平均 22.1 分 (焦点走あり 8 wave、wall の 74 % はノード開始前の待ち)。
T-2832 (i) (裁定済み: D325 の字面 = 変更 test file ごとの別 process 単独走に戻す) を別 job で払うと 1 本あたり待ち 9〜632 秒が wave 数に比例して乗る。
完了判定 = 項 4 の (a) 残件数・(b) 最小改修範囲・(c) 同条件の効果と、項 9 の局所策・追加実行時間を insight に書き、T-2832 (i) の実現手段の択一を
裁定パッケージとして再提示し、記録を land する。最小差分 = insight 1 本 + spool fragment (実装 0 行)。

## 確定裁定 (一次資料)

- 控え `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-09-21-rulings-full29-verdicts.md`: 項 3 = T-2832 (i)、実現手段は項 4 の結果で決める /
  項 4 = R2 は今回決めない、残件数・改修範囲・同条件の効果を測って再提示 / 項 9 = (b) 2 例を既存探索で拾う局所策と追加実行時間だけ。
- 相談 A 原文 (`rulings-all-20260921c/artifacts/consult-a-out.md` 項 2): 「既存走の置換で満たせない残件数と、最小改修の範囲・同条件での効果」「K1 / K3 は過去の比較値で将来待ち・完了時間短縮を保証しない」。
- D325 (決定 = 既に回す走行の形を変えて 1 本を単独走に、追加 dispatch 原則 0 本。却下 = 段 6 受入へ 1 本足す / 受入と同一 job へ畳む、「往復の除去は本件とは別に評価する」)。
- D289 (独立 job は既定で並行、同じ作業木の同時実行は直列の理由)、D130 (変異の 1 job 束ね: 削減は順番待ちだけ、手書き投入器は環境正規化を写し漏らす)。
- **新事実 (純増):** D2194 項 8 = T-2820 (裁定済み・未実装、DW-O26 inventory 4 群 → 6 群に `test_ccbench_spawn_sites.py` を追加)。項 9 の 2 例
  (T-2737 = `test_patch_define_inventory_matches_condition_gate_registry` ほか、T-2797 = `test_reviewed_*` 2 件) はどちらもこの file の test で、両 wave とも production を変えた
  (T-2737 = `tools/pegasus/run_ss2pl_lock_study.py` + patch、T-2797 = 4 file)。第 29 回の材料 (final-index 項 9) はこの既裁定を引いていない。

## 不変条件

- repo の実装面 (runner・dispatcher・test・docs 契約) を変えない。受理集合・inventory 群・D325 / DW-O26 の字面を変えない。規律 2 を緩めない。
- 実測は既存の道具だけ (`tools/run_tests.py --force-dispatch`、`tools/pegasus/dispatch_compute.py --task generic`)。新しい harness・目録基盤・gate・台帳を作らない。
- held test (成長比例) は走らせない (ユーザー明示の env 指示が今回無い)。K3 は既存値と (b) の範囲だけで扱う。

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- (P1) 項 4 (a) の標本は前回診断と同じ 12 wave (2026-09-21 07:38 JST 固定、`focus-run-count-diagnosis/verbatim/`)。07:38〜14:06 に着地した 12 wave は標本外 (数に混ぜない)。
- (P2) 「置換で満たせる」= その wave で契約上の他の条件 (初回診断・赤の次 fix の入力・契約追随・held) に使われていない既存走 1 本を単独走 1 file に置き換えられる場合。
  1 job = 1 invocation なので 1 本で 1 file。候補は表 A の (g) merge 後再確認と、緑で後続 fix が続いた (b) (事後情報)。
- (P3) (c) は同時刻の対照: 腕 C = generic 1 job (t2797 の焦点集合 21 file + 変更 test 7 file の単独 7 invocation) と、腕 S = `--force-dispatch` の集合 1 job + 単独 7 job の直列を、
  同 SHA の別 worktree から同時に始める。腕 S の各 job の RUN は腕 C の同 invocation 所要と対応する (同じ job の中で「別 job の固定費」と「中身」を両方測れる)。
- (P4) 腕 C の複数 invocation は generic の argv (`bash -c '...'`) で渡し、launcher file を作らない (新 harness を作らない)。guard が拒否したら腕 C を落として腕 S の固定費だけで報告する。
- (P5) 項 9 の局所策 = T-2820 の実装 (既裁定)。追加実行時間 = 腕 S の単独走 (`test_ccbench_spawn_sites.py`) と、generic 1 job 内で t2797 集合から同 file を抜いた走と入れた走の差。
- (P6) login bounded local での単独走は既存手段として択に並べるが、実測しない (既知の偽赤 = memory login-tmp-git-dir、前回の login 走の記録だけ引く)。

## 成果物

`output/insights/2026-09-21/r29-items4-9-diagnosis/README.md` (+ `verbatim/`: brief・plan・相談・裁定・レビューの逐語、実測 log の生 stdout)、worklog fragment 1。
decisions fragment は裁定を採用した場合だけ (再提示だけなら書かない)。

## 分割方針・環境

段 2 read-only codex 1 本 = (b) の file:line 範囲と generic 経路の実在確認。段 3 相談 1 本 = 本 brief と plan を攻撃 (レンズ = 契約解釈・算術・同条件性)。
実測は親 (Pegasus login から計算ノードへ dispatch)。受入全走は記録 commit を含む最終 tip に 1 回 (`tools/dev_wave_wait.py acceptance`)。
