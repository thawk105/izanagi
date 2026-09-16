# 段 1 brief — [T-2634] 非 silo の within-run floor の保留解除 (実証範囲限定)

wave = `dev-wave-t2634-nonsilo-floor-lift`、branch = `worktree-dev-wave-t2634-nonsilo-floor-lift`、
worktree = `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2634-nonsilo-floor-lift`、
起点 local main = `8f17db5981a689789916fcc56ccf373b10347e1a` (2026-09-16)。CCBench pin = `511c953`。

## 研究前進 (1 行)

論文の環境節 (D1639: 走行間ばらつきの記述) と C-1 cross-protocol の土台として、現行 Pegasus における
非 silo (mocc / tictoc) の**測定品質 = within-run floor** を、実測済みの 4 対 (tictoc rr50 / rr95、mocc rr50 / rr95)
に限って公式成果物へ登録する。完了判定 = 4 対の accepted 較正 record が現行 phase doc の 8b 節に silo と同形で
登録され、限定 (性能比較でも床値本走の完了でもない) が同じ行に書かれ、解除の裁定実装と「between-run 実測が
現行 pin で起動できない」事実が decisions fragment に残ること。

## scope

- **入れる**: (1) 4 対の accepted 較正 record を `docs/phase3.md` 8b 節へ登録 (先例 = 5f37936fa の silo rr95、
  [T-2515] の silo rr5 の行と同形)。(2) worklog / decisions fragment (spool)。(3) insight README。
- **入れない**: 新 gate・検査・台帳・一般化、tests の追加、between_run_floor.py の D1373 関門の変更、pin の変更、
  rr5 / cicada の較正取得、性能比較、床値本走。

## 確定済みユーザー裁定

- D2044 項 12 (逐語 `verbatim/D2044-item12.md`): 保留を解除する。範囲は実測で示された protocol と workload に限る。
  較正が取れたことを性能比較や床値本走の完了とは扱わない。
- D1360: stock 専用計測経路の値は公式 report・selector・比較表・順位・headline に入れない (規律 2)。
- D1373: between-run floor の生成を許す protocol は source の trace hook 証拠で判定し、無ければ拒否 (規律 2 の関門)。
- D1639: 「床値」= between-run noise floor。within-run は 1 測定の品質。

## 段 1 で実測した事実 (依頼の前提を覆すものを含む)

- F1 **「embargo」は code に無い。** 実体は worklog / insight の散文 (archive 1405・1503) と、`docs/phase3.md` 8b 節に
  非 silo の 4 record が未登録である状態。code 側の照合 (`orchestrator/campaign/layer3_report.py:477-495, 511-657`) は
  genome 付き record を protocol 問わず (protocol, records, threads, workload) で一致させ、非 silo を弾く分岐は無い。
  `orchestrator/campaign/env_contract.py:248-312` の registry は silo rr50 の g1/g2 だけ pin し、silo rr95 / rr5 も
  pin していないので「登録先」ではない。
- F2 **依頼の測定 `between_run_floor.py --protocol {tictoc,mocc}` は現行 pin で起動できない (親の実測、
  `verbatim/parent-probe-gate.txt`)。** `--protocol tictoc` は `BASELINES={silo,mocc}`
  (`orchestrator/campaign/between_run_floor.py:60-75, 285-288`) に無く rc=2。`--protocol mocc` は argv を通るが
  `main()` (同 `:292, :304-307`) の `_protocol_source_has_trace_hook_evidence_only('mocc')` が False で build 前に ValueError。
  pin 511c953 で `izanagi_trace` を持つのは `cc/si` / `cc/silo` / `include/trace.hh` だけ。mocc の hook は submodule branch
  `izanagi-t1943-mocc-g2-readfrom-witness` にあり pin の祖先ではない。tictoc は全 branch で 0 件。
  `orchestrator/tests/test_between_run_floor.py:252-253, 440` が「実 submodule で mocc は拒否」を期待値として pin する。
- F3 **4 対の within-run floor は既に accepted 較正 record として存在する** (`output/env/pegasus/calibration/registered/`):
  tictoc rr50 `calibration-9b49335d02ad4d2e.json` (CV 2.2160%)、tictoc rr95 `calibration-cb98513996e5ae35.json` (0.8336%)、
  mocc rr50 `calibration-449d0ad22f13e366.json` (1.4348%、[T-2535] 989271.nqsv)、mocc rr95 `calibration-b3329d93417c76ad.json`
  (1.7204%)。出所 = `output/insights/2026-09-15/t2224-nonsilo-calibration/README.md` §2・§8 と
  `output/insights/2026-09-10/t2535-certify-offline-fetch/README.md`。records は 4 件とも 1,000,000、threads 48。
- F4 並行 wave t2386 (`s8b_floor_evacuation.py`、`test_s8b_floor_evacuation.py`、`test_s8b_holdout_freeze.py`、
  `test_ccbench_spawn_sites.py`、`phase3-8b-restart-runbook.md`) と本 wave の編集面の重複は committed / 未 commit とも 0。
  codex worktree `t548-a-procure` が `docs/phase3.md:1547` に 1 行の未 commit 差分 (別節、hunk 非重複)。

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- **(P1) between-run の実測は本 wave では走らせない。** D1373 の関門は規律 2 の関門であり迂回しない。pin の変更は
  scope 外。tictoc は hook 自体が無い。→ 実測せず、起動不能の事実と解除条件 (mocc: pin が hook を含む commit へ進む /
  tictoc: hook 移植 = phase3.md 段 7 Group B) を decisions fragment に書く。
- **(P2) 裁定の「within-run floor」= accepted 較正 record の `noise_floor` (reps=10 の CV)。** T-2224 insight §2 が
  「within-run CV」と呼ぶ量そのもの。between_run_floor.py が併記する within-run とは別の producer だが同じ定義
  (WITHIN_REPS=10、`between_run_floor.py:77`)。
- **(P3) 公式成果物の登録先 = `docs/phase3.md` 8b 節 (現行 phase doc)。** 先例 5f37936fa (silo rr95) と [T-2515] の
  silo rr5 の行 (`phase3.md:542-549`) が path・request・records・LLC miss・within-run CV を書く。同形で 4 対を書く。
  env_contract registry / runbook / paper-story には書かない (前者は世代 pin、後者は次版で親が書く)。
- **(P4) `between_run_floor.py` の BASELINES へ tictoc を足さない。** 起動できない機構を足すのは規律 5 (盛らない)。
  依頼の「仮想リスク向けの追加は scope 外」にも掛かる。→ 実装面差分ゼロ (docs-only)。
- **(P5) 較正 record は正しさ検証を経ていない stock 計測だが、D2044 項 12 はそれを「較正 (物差し)」として公式成果物へ
  入れると裁定した。** D1360 が禁じるのは性能比較値の流入であり、CV の登録は抵触しない、と読む。

## 不変条件

- 規律 2: D1373 の関門・`test_between_run_floor.py` の期待値を 1 bit も変えない。規律 1: trace-disabled のまま。
- 較正 record・registered/ 配下・凍結成果物の bytes を変えない (本 wave は output/ を書かない)。
- 4 対以外 (rr5、cicada、silo) の状態語を変えない。「性能比較」「床値本走の完了」と読める文を書かない。

## 成果物の形

- `docs/phase3.md` 8b 節: `[x] [T-2634]` 1 項目 (4 record の path・request・records・LLC miss・within-run CV・限定)。
- `docs/spool/` fragment: worklog 1 件、decisions 1 件 (P1 の事実と解除条件)。
- `output/insights/2026-09-16/t2634-nonsilo-floor-lift/README.md` + verbatim (brief、plan、consult、裁定)。

## 分割方針

軽量版ではなく段 2 plan 1 本 + 段 3 consult 2 本 (規律 2 の関門に接し、P1〜P5 が割れうる)。実装面差分ゼロなら段 5・6 の
実装子は不要 (docs-only、DW-C00)。変異 matrix = 実装面差分ゼロで免除。受入・実測環境 = login node (docs-only の検査
`check_docs.py` と focus test)、計算ノード投入なし。
