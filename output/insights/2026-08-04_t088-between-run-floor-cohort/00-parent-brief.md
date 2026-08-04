# 段 1 brief — [T-088]/[T-296]/[T-011] between-run noise floor 実測 (Pegasus)

## scope

Pegasus の**層 C = between-run noise floor** を 1 ジョブ束で実測し、env タグ付きで
`output/env/pegasus/calibration/registered/` 系へ登録する。実装面は 3 つ:
(1) `orchestrator/campaign/between_run_floor.py` の env パラメタ化、
(2) Pegasus 計算ノードで走らせる実行資材、(3) 登録経路。

## 確定済みユーザー裁定 (worklog (145)、一次控え = rulings-inbox 3 番)

着手可。**1 wave (ジョブ束 1 回) 規模に収め、足りなければ拡大せず裁定へ返す。**
レコード数は calibrator が cache miss 率の飽和最小で決める (規律 4)。計測前にノード上で
単独性を確認する (pgrep)。取得値は env タグ付きで `registered/` 系へ登録する。
wave は「使った規模」と「この floor が品質ゲートとして使えるか」の判定を返す。

## 前提実測で判明した新事実 (DW-S01。段 4 で再裁定する)

- **N1 — `pegasus` env-tag は既に存在する。** `orchestrator/campaign/env_contract.py:181-193`
  (clocks_per_us=2100 / numactl=() / attestation_mode=required / single_process=True)。
  導入 commit = `26a9ad6`。裁定が置いた順序「env-tag 新設 → floor 実測 → 登録」の第 1 段は
  **既済 (stale)** であり、[T-296] の未達 (1) は閉じている (F35 = 済なら繰り上げる)。
- **N2 — レコード数は calibrator が決定済み。** 登録済み `calibration-753f535a8d024727.json` が
  `records=1,000,000` / `threads=48` / skew0.9-rr50-rmw0、`lower_bound_selected=true`
  (working set 517MB = L3 105MB の 4.93 倍)、within-run CV **1.17%**、quality=accepted。
  規律 4 の「飽和最小」は充足済みで、本 wave が新たに決め直す必要はない。
- **N3 — between-run floor driver は実在するが linux-baremetal 固定。**
  `between_run_floor.py:45-47` が `p2_2.py:40-47` から `ENV_TAG/CLK=1800/NUMA=interleave/
  RECORDS/THREADS/EXTIME` を定数継承し、出力先 `env_scope_dir(ENV_TAG)/calibration` も固定。
  Pegasus は TSC 2100・単一 NUMA。
- **N4 (裁定の前提を覆す) — (145) が挙げた前提 gate 2 件は本 track を塞いでいない。**
  gate は official guard (`s8b_floor_campaign.py:194-212` core / `:3473-3476` CLI) だが、
  `between_run_floor.py` の import 閉包は `calibrator.*` + `campaign.{buildcache,pin,
  source_digest,build_admission,layout,model,p2_2}` のみで、**`s8b_floor_campaign` も
  official mode も含まない**。official guard が塞ぐのは 8b selector の**床値** campaign であり、
  本裁定が求める**層 C の noise floor** とは別成果物である (同名異義。DW-O13)。
  worklog (131) は同一エントリ内で「(b) between-run floor の残 gate は [T-088] 段階 3・4」と
  「8b 非依存の一般用途 floor は実在するが Pegasus 未対応」を併記しており、内部で食い違う。
- **N5 — 既存 registered calibration は bytes pin されている (DW-O09 閉包、全 6 箇所)。**
  `env_contract.py:189,191` / `test_env_contract.py:239,242,649,650` /
  `test_s8b_floor_campaign.py:3239`。**不可侵。新ファイルへ書く。**
- **N6 — 計測資材の注入 seam は実在する。** `certify_calibration.sh:719-744` が
  `calibrate-argv.json` を組んで `exec_calibrate.py` に exec させる形で、測定段は
  **差し替え可能な単一 argv** である。前段 700 行 (worktree staging / gflags・glog build /
  ccbench build / attestation / perf 選定 / topology) は再利用しうる。

## 不変条件

- `calibration-753f535a8d024727.json` の bytes 不変 (N5 の 6 pin すべて緑のまま)
- 規律 1: 計測は trace-disabled build。規律 4: レコード数は 1M/48 を使い拡大しない
- 規律 2/3 を緩めない。official guard を迂回しない (触らない)
- push・remote 操作をしない。`registered/` の既存ファイルを上書きしない (create-only)

## (P) — 親の provisional 裁定。**攻撃対象**

- **(P1)** N4 により、[T-088] 段階 3・4 と実行 revision 束縛は本 track の gate ではない。
  したがって着手は 1 wave 束縛と両立し、裁定へ差し戻す必要はない。
- **(P2)** 「ジョブ束 1 回」= 複数 PBS request を 1 度に投入してよい。D19 は fresh な
  back-to-back セッションが真の run 間ドリフトを捉えない**楽観的下限**だと実測しており、
  D138 (f) は独立単位を node / 時間窓 cluster で数えると定める。単一 allocation 内の
  8 セッションだけでは D19 が floor へ採らなかった量を再生産する。
- **(P3)** 登録は `registered/` へ**新ファイル追加**とし、`env_contract` の
  `calibration_ref` は変更しない (受理集合を動かさない)。
- **(P4)** 裁定文の「1 測定の品質ゲートとして使えるか」は D19 では **within-run** の役割で、
  between-run は**採否の床**である。両方を測って併記し、どちらの用途に耐えるかを判定で返す。
- **(P5)** 実行資材は N6 の argv seam を再利用し、700 行の前段を複製しない。
- **(P6)** 裁定の「1 wave 規模」は**計測規模 (ジョブ束 1 回)** への束縛であり、
  それを可能にする実装 (env パラメタ化・実行資材・登録経路) を禁じるものではない。

## 成果物の形

env パラメタ化された floor driver + Pegasus 実行資材 + 実測 artifact +
`registered/` への新規登録ファイル + 判定 2 件 (使った規模 / 用途適合) + 台帳 fragment。

## 成果物影響 (DW-G05)

実装しない場合、Pegasus で測る性能差は linux-baremetal 由来の `BETWEEN_RUN_CV=0.030`
(`p2_2.py:62`、consumer = `search_baselines`/`guided`/`replay`/`backoff_repro`/`p2_2_report`)
で採否判定され続ける。Pegasus の within-run CV は 1.17% で linux-baremetal の 2.28% より
小さく、3.0% の流用は差を過剰に tie へ丸める側に効きうる = certified 選択の受理集合が変わる。
**ただし現時点で発火する計測 ID は 0 件** ((131) の実測。`output/campaigns/` /
`output/exploration/` 検索で hit なし)。したがって本 wave は既存の値を書き換えず、
roadmap §5 が層 C に課す「env-tag ごとの取り直し」義務の履行と、将来の Pegasus 計測が
参照できる床の**新規供給**として位置づける。

## 分割方針

段 2 = codex plan 1 本 (read-only)。段 3 = 敵対レンズ 2 本 (統計的妥当性 / 実装と gate 整合)。
段 5 = 実装子 1〜2 本 (driver env 化 / 実行資材・登録)。段 6 = 敵対レビュー 2 本。
DW-C00 の軽量版条件には**該当しない** — 設計択一が割れ ((P2)/(P3))、受理集合が動きうる。
