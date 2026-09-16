# [T-2634] 非 silo の within-run floor の保留を既取得の較正 4 対に限って解除した — 依頼が名指した between-run の実測は D1373 の関門で起動できず未実施

`authority: none`
`default_effect: no-state-change`

- 日付: 2026-09-16
- wave: dev-wave-t2634-nonsilo-floor-lift (branch `worktree-dev-wave-t2634-nonsilo-floor-lift`)
- 起票: `docs/archive/worklog-phase3-0915-1503-1504.md` の [T-2634] (T-2224 wave が 2026-09-15 に起票)。
  裁定: `docs/archive/worklog-phase3-0916-1528.md` の [T-2634] と D2044 項 12 (2026-09-16 ユーザー裁定)
- 正本: D2044 項 12 (解除の範囲は実測で示された protocol と workload に限る)、D1639 (床値 = between-run)、
  D1373 (between-run floor の protocol 判定は source の trace hook 証拠)、D1360 (stock 専用計測経路は公式へ入れない)、
  D1508 (層 3 の較正走査は `calibration/` 直下 + 契約 pin)
- 基準: local main `8f17db5981a689789916fcc56ccf373b10347e1a` (着手時)、CCBench submodule はその pin `511c9538`
- **実装面 (D95 決定 2) の差分は 0。** 成果物は `docs/phase3.md` 8b 節の 1 項目、台帳 fragment 2 件、本書。
  可変状態の正本は worklog 末尾と現行 phase doc であり、本書ではない。

## 1. 何をしたか

D2044 項 12 の「非 silo の within-run floor の保留を解除する。解除の範囲は実測で示された protocol と workload に限る」を
実装した。**解除 = 文書登録**である。accepted な認定較正 record が存在する 4 対を、現行 phase doc の 8b 節へ silo の
rr95 / rr5 と同じ形で登録した。

| 対 | record (`output/env/pegasus/calibration/registered/`) | request / node | records | 採用点 LLC miss | within-run CV | n |
|---|---|---|---:|---:|---:|---:|
| tictoc / rr50 | `calibration-9b49335d02ad4d2e.json` | `998860.nqsv` / bnode093 | 1,000,000 | 7.969% | 2.2160% | 10 |
| tictoc / rr95 | `calibration-cb98513996e5ae35.json` | `998863.nqsv` / bnode103 | 1,000,000 | 9.557% | 0.8336% | 10 |
| mocc / rr50 | `calibration-449d0ad22f13e366.json` | `989271.nqsv` / bnode020 | 1,000,000 | 14.821% | 1.4348% | 10 |
| mocc / rr95 | `calibration-b3329d93417c76ad.json` | `998864.nqsv` / bnode016 | 1,000,000 | 17.008% | 1.7204% | 10 |

値は各 record の `saturation.miss_rate_at`・`noise_floor.cv`・`noise_floor.throughputs` の長さ・`host.node`・
`acquisition_receipt.qsub.request_id` から jq で読んだ (`verbatim/parent-record-facts.txt`)。4 件とも
`quality=accepted`、`cache_floor_warning=false`、`lower_bound_selected=true`、threads 48、
CCBench `511c9538e4e8efa54b45cda62e72389ed3b706ec` / `pinned_clean=true`。
mocc rr50 の LLC miss と CV の桁は先行 insight (`output/insights/2026-09-10/t2535-certify-offline-fetch/README.md`) の
散文には無く、record 自身から取った。他 3 件は `output/insights/2026-09-15/t2224-nonsilo-calibration/README.md` §2 と一致する。

**較正が取れたことは性能比較でも床値本走の完了でもない。** 非 silo の rr5・cicada へは広げない。

## 2. 「保留 (embargo)」の実体 — code に無い

- `orchestrator/` `tools/` `hooks/` に `embargo` は 0 件。語が現れるのは worklog (archive 1405・1503) と T-2224 の insight の
  散文だけである。
- code 側の照合 (`orchestrator/campaign/layer3_report.py` の `_floor_protocol_and_basis` / `_calibration_floors`) は
  genome 付き record を protocol 問わず (protocol, records, threads, workload) で一致させ、非 silo を弾く分岐は無い。
- 環境契約の registry (`orchestrator/campaign/env_contract.py` の `_build_registry`) は silo rr50 の g1 / g2 だけを
  pin し、silo の rr95 / rr5 も pin していない。世代ごとに 1 件の較正を契約値へ束縛する pin であって、較正の一覧ではない。
- したがって保留の実体は、**認定較正 record が非 silo に無かった事実 (T-2224 が 2026-09-15 に解消) と、
  phase doc に非 silo の record が未登録だった状態**である。本 wave は後者を埋めた。

**ただし文書登録は report 消費の開通ではない** (段 3 レンズ B の real 所見)。層 3 report の within-run 候補は
`calibration/` 直下の glob と契約 pin の和集合だけで `registered/` を再帰しない (D1508)。silo の rr95 / rr5 も同じ状態に
あり、登録の水準はそれと揃う。report へ接続するには契約世代の登録・活性化とその契約を持つ campaign が別に要り、
本 wave は行っていない (T-2136 の insight が挙げた未接続条件のまま)。

## 3. 依頼の前提が実測で覆った — between-run の実測は現行 pin で起動できない

依頼は「測定は既存の `orchestrator/campaign/between_run_floor.py --protocol {tictoc,mocc}` を計算ノードで走らせる」と
した。親が login node で述語を実測した (`verbatim/parent-probe-gate.txt`):

```
trace-hook evidence (D1373 gate) at pin 511c953: silo=True mocc=False tictoc=False
BASELINES keys: ['mocc', 'silo']
argv --protocol tictoc -> unknown protocol: 'tictoc' (選択肢: ['mocc', 'silo'])
argv --protocol mocc -> (None, 'mocc')
```

- **tictoc** は `BASELINES` に無く、`_parse_cli_args` が `ValueError` を投げ `main()` は rc=2 で終わる (静的帰結)。
- **mocc** は引数解析を通るが、`main()` が build の前に `_protocol_source_has_trace_hook_evidence_only('mocc')` を
  評価して偽なら `ValueError` を投げる (静的帰結)。現行 pin `511c9538` の checkout で `izanagi_trace` を持つ file は
  `cc/si/transaction.cc`・`cc/silo/transaction.cc`・`include/trace.hh` だけで、`cc/mocc` と `cc/tictoc` には無い。
  mocc の hook は submodule branch `izanagi-t1943-mocc-g2-readfrom-witness` にあり、pin の祖先ではない。
  tictoc の hook は全 branch で 0 件。
- この関門は D1373 が「規律 2 の関門」と定めたもので、`orchestrator/tests/test_between_run_floor.py` が
  「実 submodule で silo は受理・mocc は拒否」を期待値として pin する。**迂回も緩和も pin の変更もしていない。**
- 関門は checkout の source text だけを読むので計算ノードでも同じ判定になるが、**計算ノードで実走して確かめてはいない**
  (段 3 レンズ A の指摘に従い、実測 = 述語値・`BASELINES`・引数解析の 3 点、rc=2 と `ValueError` = 静的帰結、と分けて書く)。

## 4. between-run 実測の再開に必要な条件 (必要条件であって十分条件ではない)

- **mocc:** 実際に checkout される `cc/mocc/CMakeLists.txt` の SOURCES に列挙された同一 file に、`trace.hh` の include・
  `#if TRACE`・`izanagi_trace::` 呼出しの 3 証拠が (コメントと literal `#if 0` を除いて) 揃う pin へ進むこと。
  「pin を進める」だけでは足りない — D1373 の述語は commit 履歴でなく実 file を読む。
- **tictoc:** 上に加えて hook 自体の移植 (現行 phase doc 段 7 Group B (e)(f)) と、driver の `BASELINES` への
  baseline 登録。stock genome は認定較正の genome
  `tictoc|BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,PREEMPTIVE_ABORTS=1,TIMESTAMP_HISTORY=1`
  と一致させる (TICTOC_SPACE の 5 軸を満たし、no-wait 両 1 の制約にも当たらない)。
- いずれも関門を通る条件であり、測定の成功・verifier の通過・accepted 較正の意味論的正しさを保証しない。
- `BASELINES` へ tictoc を先に足す案は採らなかった — 足しても関門で止まり測定は開通せず、今回の登録に要らない。
  「起動できない baseline を置くこと自体が規律違反」という一般論は採らない (現行 mocc がその反例)。

## 5. 段 3 が親の brief を訂正した点

1. 「D1360 が禁じるのは性能比較値だけ」は逐語より狭い。登録根拠は D2044 項 12 の明示的な用途限定解除に置き、
   「較正の変動係数は元から禁止対象外」とは書かない (レンズ A、real)。
2. 「pin を進めれば関門を通る」は条件不足 (レンズ A、real → §4)。
3. 「between-run floor は現行 pin で起動不能」は protocol を省くと過大 — silo は True (レンズ A、real)。
4. login node の probe を計算ノード実走の証拠にしない (レンズ A、real → §3)。
5. mocc rr50 の LLC miss / CV は README に無いが record にある。段 2 plan の「欠落扱い」は README 単独の限界
   (レンズ A・B、real → §1)。
6. 「本 wave は output/ を書かない」は新規 insight と矛盾 — 既存較正 record・凍結成果物の bytes は不変、新規 insight は作る
   (レンズ A・B、real)。
7. 文書登録 ≠ report 接続 (レンズ B、real → §2)。

refuted: 裁定矛盾 (within-run 登録と between-run 拒否の非対称は D2044 項 12 と D1373 の射程が違うだけ)、5 件目の候補、
非 silo 一律拒否分岐、文書登録による受理集合の変化、tictoc 追加で既存 test が赤、8b 節に触れる他 branch。

## 6. 主張しないこと・触らなかったこと

- 性能を比較していない。床値本走 (A-4 official) を進めていない。4 対の較正に correctness certification を付けていない
  (accepted 較正は trace 分離検査を通っているが、正しさ検証の通過ではない)。
- 層 3 report への接続 (契約世代の登録・活性化・v2 campaign) は行っていない。
- `docs/pegasus-runbook.md` の「登録済み calibration は 2 件」(環境契約が pin する 2 件の意味で、registered の現物は
  8 件) の限定訂正は scope 外として触っていない — 観察として残す。
- 非 silo の rr5・cicada の較正取得、`BASELINES` への tictoc 追加、D1373 の関門・pin の変更は行っていない。

## 7. 並行 wave との照合

- 稼働中の `dev-wave-t2386-floor-evac-order` (`s8b_floor_evacuation.py`、`test_s8b_floor_evacuation.py`、
  `test_s8b_holdout_freeze.py`、`test_ccbench_spawn_sites.py`、`phase3-8b-restart-runbook.md`) と本 wave の編集面
  (`docs/phase3.md` 8b 節、spool fragment、本書) の重複は committed / 未 commit とも 0。
- codex worktree `t548-a-procure` に `docs/phase3.md` の別節 (裁定・完了記録節付近) へ 1 行の未 commit 差分があるが、
  hunk は重ならない。

## 8. 工数と検査

- codex 子 3 本 (段 2 plan、段 3 consult 2 本、いずれも gpt-6-astra / medium / read-only、receipt accepted)。
  段 5・6 の子は実装面差分ゼロのため起動していない。変異 matrix は実装面差分ゼロで免除。
- 記録前の検査 (作業木、base 8f17db598 + 未 commit の docs 差分): `tools/check_docs.py` rc=0 (初回は phase doc の
  pin 値 literal 再掲で rc=1、`pin.CURRENT_PIN` の記号参照へ直して rc=0)、`tools/spool_fold.py --dry-run --show-diff`
  rc=0。実 repo の docs を読む焦点 test 2 file (`orchestrator/tests/test_check_docs.py`、`test_spool_fold.py`) は
  login の headroom 判定で計算ノードへ dispatch され (Pegasus request 1949.nqsv、bnode012、Elapse 22 秒)
  741 passed / 3 skipped、失敗 0。
- 受入全走は記録 commit を含む最終 tip に対して land 前に 1 回投入する。結果は worklog に残す。

## 9. 一次資料

- 逐語: `verbatim/s1-brief.md`、`verbatim/s2-plan.md`、`verbatim/s3-consult-A-correctness-boundary.md`、
  `verbatim/s3-consult-B-effectiveness.md`、`verbatim/s4-ruling.md`、`verbatim/parent-probe-gate.txt`、
  `verbatim/parent-record-facts.txt`
- record 4 件: §1 の表の path。生証拠と attempt は T-2224 / T-2535 の insight §8 に従う。
