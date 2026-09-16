# [T-2635] 段 1 brief — 高域の対照: 候補設定の到達と共通辺の成立を記録済み走行から判定する

2026-09-16。branch `worktree-dev-wave-t2635-high-band-control-feasibility`、base main `8f17db598`。

## 研究前進

B-10 の機序説明 (D1932「滞在分布」、却下枝「計数ノイズが符号を支配」) を帯域外 (`Backoff_` > 50 µs) へ
伸ばせるかを決める材料。D2020 は「既存 J1 経路は高域の条件比較を実行できない。新しい走行か辺の
同一性の改訂が要る」で止まっている。本 wave は **新走行の候補設定が (i) 高域へ届き、(ii) 既存 J1 が
要求する共通辺 (順序なし完全一致、両側に非ゼロ符号、K >= 10) を作るか** を、記録済み走行の読取だけで
判定し、既存の事前登録 (T-2188 `s4-ruling.md` §6 J1) を変えずに対照が作れるかを答える。
完了判定 = 判定語と根拠の数値が insight に載り、「新走行を取る / 改めて諮る」のどちらかが確定する。

## 確定済みユーザー裁定と引数

- D2044 項 13 (2026-09-16): 候補設定について高域到達と共通辺の成立を先に確かめる。既存の事前登録を
  変えずに対照が作れると分かれば新走行、分からなければ改めて諮る。辺の同一性を帯へ束ねる案は採らない。
- 引数: まず記録済み走行の読取で判定。新走行が要る場合も job script は編集せず main の現物で投入する
  (稼働中 `dev-wave-t548` が `tools/pegasus/**` を編集中 — `t2187_adaptive_const_probe.pbs` も 13 行差分)。
  規律 2 を緩めない。本題の成立確認だけ。gate・検査・台帳・一般化の追加は scope 外。

## brief 前の前提実測 (覆す新事実を含む)

1. **初期値の knob は無い。** stock `external/ccbench/include/backoff.hh:124` は `Backoff_(0)` 固定。
   cell 文字列 11 field (label:back_off:step:ceiling:update:count_window:count_cap:step_adapt:step_min:step_max:dyn_ceiling[:policy])
   に初期値は無い。
2. **main の現物 driver は trace mode で登録済み 4 cell 集合しか受理しない。** `.pbs` 219〜247 行
   (`backoff trace mode requires one exact diagnostic cell set` rc=2) と `.py` `_validate_backoff_trace_contract`
   (`BACKOFF_TRACE_CONTRACTS.get(args.cells)` 不在で ValueError、かつ `rep_index == 0` 必須)。
   解析器 `_load_new_trace` も `_NEW_TRACE_CELL_AXES` の 6 cell 固定。
   **⇒ 既存事前登録の J1 対照 (`nm-step1` × `nm-step1-u2560`) は全軸が固定済みで自由な knob が 1 つも無く、
   main の現物で投入できる「新走行」は同じ登録集合の再走だけである。**
3. 記録済み時間トリガ trace は `trace-t2188/stage1-rep0-0_989505.nqsv.json` の 6 cell のみ
   (他 dir の trace は count トリガ cell `cw*`、J1 の「トリガ型同一」を満たさない)。
   広窓側 `nm-step1-u2560` は 1,170 event、最大 12.0 µs (D2020 と一致、本 wave で再実測)。
4. T-2583 の 5 状態語 (`no_high_band_observation` / `no_nonzero_high_band_sign` / `no_common_high_band_edge` /
   `insufficient_common_support` / `executable`、閾値 10 不変) をそのまま使う。

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- **(P1) 「既存の事前登録を変えずに」の読み。** 親の読み: J1 は cell を名指しし他の全軸を固定するので、
  広窓側を高域へ置く設定は必ず別 cell (別の刻み・extime・上限) になり、既存 J1 の対照そのものは変えられない。
  新 cell 対は「既存 J1 を変えない新しい事前登録 (J1')」であって、その採否は D2044 項 13 の「改めて諮る」側。
  ⇒ 本 wave の判定は「候補ごとの到達予測 + 共通辺予測」を裁定パッケージにまとめて返すのが正、
  同じ登録集合の再走 (唯一の無編集投入) は候補設定ではなく、D2020 の不到達を繰り返す見込みなので取らない。
- **(P2) 記録済み走行からの予測法。** (a) 記録済み広窓 walk (`nm-step1-u2560`) の刻み単位の到達
  (1,170 update で 0〜12 刻み) を刻み S へ外挿する、(b) 各 u10 cell の先頭 1,170 update の到達と
  高域非ゼロ符号辺の集合 (同 update 数の双子近似)、(c) 格子の構造上限 (刻み S の高域遷移辺の本数、
  例 S=100 は 9 本 < 10 で K_high >= 10 が構造的に不可能)。3 つを別々に出し、1 つで他を代用しない。
  (a)(b) は模擬であり、実測でないことを明記する (F29)。
- **(P3) 到達の判定語。** 候補ごとに `reach_predicted` / `reach_not_predicted` / `reach_undetermined` の 3 値、
  共通辺は K の予測レンジと構造上限を出し、`K >= 10` の可否を 3 値で書く。結果を見る前に固定する。

## 不変条件

- 新しい計測は取らない (本 wave の主経路は読取)。凍結済み事前登録 (`s4-ruling.md` §6、T-2583 `s4-adjudication.md`)
  と解析器は 1 byte も変えない。probe は Codex author が worktree 内に書き、親が実行前に job dir へ退避、repo へ commit しない。
- 実装面の repo 差分ゼロ → 変異 matrix は `DW-S04` により免除、受入全走は免除しない。
- 規律 2・3 に触れない (verifier・正しさ gate・受理集合は不変)。

## 成果物の形

- `output/insights/2026-09-16/t2635-high-band-control-feasibility/README.md` (判定・候補表・主張しないこと)
  + `verbatim/` (brief・plan・consult・adjudication・probe.py.txt・出力 JSON 逐語)。
- `docs/spool/` fragment (worklog 1 件・decisions 1 件)。
- 裁定パッケージ (判定が「作れない」なら README に択一・推奨・やらない理由の最強形を置く)。

## 並列分割

段 2 plan 1 本 (read-only)、段 3 consult 2 本 (レンズ A = P1/P3 の裁定妥当性、レンズ B = P2 の予測法の破れ)、
段 5 author 1 本 (probe)、段 6 焦点 review 1 本。実測はすべて login node (入力 140 MB、先例 T-2583 は RSS 385 MiB / 2.9 s)。

## 変更面 (実アンカー)

| 面 | path | 扱い |
|---|---|---|
| 入力 | `/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/trace-t2188/stage1-rep0-0_989505.nqsv.json` | 読取のみ |
| 再利用部品 | `orchestrator/campaign/backoff_nonmonotonicity_analysis.py` `_load_new_trace` / `_edge_observations` / `_edge_counts` | import のみ、無改変 |
| probe | worktree 内 `probe_t2635.py` (作成後 job dir へ退避、commit しない) | Codex author |
| docs | `output/insights/2026-09-16/t2635-high-band-control-feasibility/**`、`docs/spool/**` | 親 |
| 触らない | `tools/pegasus/**`、`patches/**`、`external/**`、解析器、テスト | — |
