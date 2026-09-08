# 段 1 brief — [T-1998] balanced stock-inline 対照の最小 3 部品

- 基準 commit: `c5754d1f4b3d915f2e55615e69674190f48c69a8` (着手直前の local main と同一)
- worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts`

## scope

D1244 が採用した最小 3 部品だけを実装する。(1) producer evidence の read-only 到達性監査、
(2) 既存 backoff sweep を呼ぶ薄い sanctioned launcher、(3) 事前登録で固定した 2 点だけを読む consumer。
新しい汎用 driver を作らない。**本 wave では測定を 1 回も走らせない。** prospective 事前登録と
正式測定認可は 3 部品の land 後に人間手番へ返す (D1244, D1267)。

## 確定済みユーザー裁定 (逐語は `verbatim/` に置いた)

- D1244: 上の 3 部品に限定して実装する。汎用 driver は作らない。
- D20: 診断 build (`BACKOFF_NOINLINE=1`) 下の throughput は headline へ流用しない。
- D1137: 既存 balanced 機序 profile は headline 利得を説明しない (帯・散布・bar を実走前に凍結した別命題)。
- D1525: Pegasus で取れた A-5 の値を D1100 の充足と読み替えない。

## 不変条件

- 規律 2 を緩めない。anomaly を出した variant は即 reject。判定を甘くする変更を採らない。
- trace-disabled の variant / baseline を別走で揃える。診断 build 値と headline 値を混ぜない。
- consumer は post-result argmax を使わない。事前登録で固定した 2 点だけを受理し、片側欠損・
  不安定・identity 不一致は inconclusive / reject にする。
- 既存テストの期待値を変えない。凍結成果物の bytes を変えない。

## 段 1 で実測した新事実 (D1244 の裁定日 2026-08-28 より後に着地したもの)

1. **薄い launcher は既に実在しうる。** `tools/pegasus/a5_second_boot_backoff_sweep.sh` (初出
   2026-09-02 `86579ee01`) が `backoff_sweep.py <workload>` を非 screening で 1 回呼ぶ PBS job body で、
   `submit_a5_second_boot_backoff_sweep.sh` が login 側 fan-out、
   `orchestrator/tests/test_a5_second_boot_job_contract.py` が契約テストを持つ。
2. **pair consumer も job body 内に実在しうる。** 同 job body の finalizer が
   `BASELINE_FLAGS = {"BACK_OFF":0,"BACKOFF_FIXED":-1}` と `TARGET_FIXED_US = {"balanced":5}` の
   exact pair だけを `selected_by_flags()` で取り出し `a5-second-boot-result/v1` を書く。
   argmax を使わない点は T-1998 の要求と同形である。
3. **balanced の stock-inline 対の値は 2026-09-07 に実測済みである。** none = 3,803,883 tps (CV 3.30%)、
   fixed 5 µs = 4,294,095 tps (CV 1.19%)。ただし balanced job は commit 後の終了処理で rc=1 になり、
   finalizer は走っていない (`result.json` は無い)。
4. 中断 handoff の段 4 裁定「launcher 不在 / consumer 不適格」は 2026-08-28 時点の観測であり、
   1〜3 はその後に着地した。

## (P1) 親の provisional 裁定 — 段 2・3 の攻撃対象

**(P1-a)** 第 2 部品は純増ゼロで、必要なのは A-5 job body の再実装ではなく **T-1998 の主張へ束縛する
薄い層だけ**である。A-5 は D1100 (別 boot の再現) に束縛されており、D1525 が読み替えを禁じているので、
同じ job body を T-1998 の主張の producer として名指す経路が別に要る。
**(P1-b)** 第 3 部品は repo 内の独立 module + テストとして作る。A-5 の finalizer は job body の
heredoc 内にあり、単体で読めず T-1998 の受理・拒否条件 (診断 tps 拒否、不安定 → inconclusive) を持たない。
**(P1-c)** 第 1 部品は producer schema の拡張を要さない。中断 wave が名指した
`CertifiedCampaignView` と public `admit_replay_evidence()` は現行 repo に実在する。
ただし**この結論は独立監査を受けていない**ので、反証する形で確かめる (worklog 1101)。
**(P1-d)** consumer の入力 field は実環境で到達可能である (DW-O13)。**親が現物を読んで実測した:**
`a5-second-boot-result/v1` の実物は 1 件だけ存在する — write-heavy の
`/work/1/SFC/tanab/a5-second-boot-runs/a5-second-boot-backoff-sweep-20260906T171922Z-31812-write-heavy/result.json`
(`status=complete`、no_backoff 中央値 2,368,703 / target 中央値 3,925,215、improvement 65.71%)。
**balanced の実物は無い** (2026-09-07 の balanced job は 8 genome を commit した後、finalizer の前に rc=1)。
同 file は repository_commit / ccbench_commit / toolchain / perf_preflight / campaign 記録の
2 つの sha256 / boot 証拠を持つが、**環境契約 digest・build mode (trace 有無)・診断 knob
`BACKOFF_NOINLINE` の状態・verifier receipt への参照・安定性 (CV) は持たない。**
これは読解による推定ではなく、現物 1 件の実測である。

## 成果物の形

- 第 1 部品: 到達性監査の結論を insight へ書き、consumer が要求する evidence 種別ごとに
  「どの成果物のどの field から再検証できるか」を対応表で残す。不足時だけ既存 result schema を限定拡張する。
- 第 2 部品: 既存 A-5 経路との純増だけを実装する。純増ゼロなら実装せず裁定パッケージへ返す。
- 第 3 部品: `orchestrator/campaign/` 配下の consumer module + `orchestrator/tests/` のテスト。
- 事前登録本体と正式測定認可は作らない (人間手番)。

## 分割方針

実装面があるので段 5 の Codex `role=author` 実装子は省略不可。設計択一 (P1-a / P1-b) が割れるので
軽量版にせず段 2・3 と段 6 の敵対レビュー 2 本を回す。所有 path は
(A) consumer module + そのテスト、(B) launcher 側 (`tools/pegasus/` + 契約テスト + 登録簿) で素集合に分ける。

## 変更面の実アンカー表

| 役割 | anchor |
|---|---|
| exact pair の定義 | `orchestrator/campaign/backoff_sweep.py:193-202` (`genomes()`) |
| sweep 定数 | `orchestrator/campaign/backoff_sweep.py:56-70` (`_BASE`, `SWEEP_US`, `WORKLOADS`) |
| 既存 A-5 job body | `tools/pegasus/a5_second_boot_backoff_sweep.sh:589-592` (driver 呼出し) |
| 既存 A-5 finalizer | `tools/pegasus/a5_second_boot_backoff_sweep.sh:615-618,735-747,769-790` |
| 既存 A-5 投入器 | `tools/pegasus/submit_a5_second_boot_backoff_sweep.sh` |
| 既存 A-5 契約テスト | `orchestrator/tests/test_a5_second_boot_job_contract.py` |
| 不適格な既存 consumer | `orchestrator/campaign/backoff_sweep_report.py:53-80` |
| certified view の入口 | `orchestrator/campaign/artifact_admission.py:377,1538` |
| verifier receipt の再検証 | `orchestrator/verifier/commit_receipt.py:388` (`admit_replay_evidence`) |
| Pegasus 実行体の登録簿 | `tools/pegasus/admission_registry.json`、`orchestrator/tests/test_hooks.py:3032,3083,3111,3405,3942` |
| run_campaign 呼び手の棚卸し | `orchestrator/tests/test_campaign.py:5346-5360,5432-5440` |
| s1 凍結 golden | `orchestrator/tests/s1_expected_goldens.py:253-258` (`backoff_sweep.py` の `_BASE and SWEEP_US`) |

## 凍結 pin 閉包 (DW-O09)

- `backoff_sweep.py` の `_BASE` / `SWEEP_US` は `s1_known_axes_freeze.py:398-423` と
  `s1_expected_goldens.py` に pin されている。**この 2 定数と `genomes()` の中身を変えない。**
- `tools/pegasus/` へ file を足すと `admission_registry.json` と `test_hooks.py` の分類表が
  集合完全一致を要求して赤になる。追加するなら同じ commit で登録する。
- `orchestrator/campaign/` へ `run_campaign` を呼ぶ module を足すと `test_campaign.py` の
  inventory が `new_callers` で赤になる。consumer は `run_campaign` を呼ばない。

## DW-G05 — 成果物影響

第 3 部品が無いと、stock-inline 対の値が headline 主張へ束縛されず、balanced の +11.27% が
診断 profile の産物かどうかを certified な形で言えないままになる (受理集合が定まらない)。
第 1 部品が無いと、consumer が要求する identity 証拠を再検証できず、
値と source / env / build-mode の対応づけが consumer 側で確認できない。

## 受入・実測環境

- 受入全走は login node で `tools/dev_wave_wait.py acceptance -- python3 tools/run_tests.py`。
- 計算ノードへの測定投入は**行わない**。build も benchmark も走らせない。
