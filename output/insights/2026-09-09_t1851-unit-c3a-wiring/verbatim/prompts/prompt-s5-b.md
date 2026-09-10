単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2

必読事項の射影 (いずれも絶対パス。読めなければ即停止し、その旨を出力に書いて終わること):

- **作業 root (書込み可。ここだけを編集する)**: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c3-b`
- **親の段 4 裁定 (これが scope の正本)**: `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/s4-adjudication.md`
- 親の段 1 brief: `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/s1-brief.md`
- 段 2 plan (配線のアンカーがここにある): `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/out-s2-plan.md`
- 段 3 レンズ A: `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/out-s3-lensA.md`
- 段 3 レンズ B: `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/out-s3-lensB.md`
- 先行子 A1 の報告 (launcher 二段入口の実装): `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/out-s5-a1.md`
- 先行子 A2 の報告 (ordinal 束縛の訂正): `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/out-s5-a2.md`
- 契約の正本: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c3-b/output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.1.md`
- 共通規律: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c3-b/CLAUDE.md`

# 段 5 子 B — 床値 campaign の production 経路を certified launcher へ配線する

**作業 root には子 A1 と A2 の実装が既に統合されている。** 二段入口と訂正済み ordinal 束縛は
**現物を読んで確かめること** (親の要約ではなく作業 root の code が正)。

## 所有 path (これ以外を 1 行も変えない)

- `orchestrator/campaign/s8b_floor_campaign.py`
- `orchestrator/tests/test_s8b_floor_campaign.py`

**docs は編集しない。commit しない。`git add` もしない。** 親が行う。

## 実装する配線

1. **phase 1 の probe を先に実行する。** `probe_floor_attempt_preconditions()` を呼び、封印
   pre-probe を得る。
2. **competing なら marker を消費せず launcher を呼ばない。** 既存の competing 枝
   (`s8b_floor_campaign.py:6243-6256` 付近で `strict_probe()` の結果を読んでいる箇所) の記録は
   従来どおり残す。**holdout inspector を 1 bit も緩めない。** これがこの単位の blocker 解消の本体である。
3. **clean のときだけ** `consume_attempt_ticket()` で marker を取り、`launch_probed_floor_attempt()` を
   呼ぶ。injected `measure_fn` の既存 test 経路 (`:6262` の直接計測) は**残す** — 既存期待値を守るため、
   default production 経路だけを launcher へ送る。
4. **journal emit は launcher が返した terminal の内容と byte 一致**にする。campaign 側で作り直さない。
5. **registry prefix を最後の terminal の後に capture** し、同じ proof を result assembly と
   既設 live inspector の双方へ渡す (`:7795-7838` の finalize-pending と `:7962-7986` の通常 finalize の
   両方)。
6. **production result だけ schema を既設 `RESULT_SCHEMA_V5` にする。**
   `s8b_floor_contract.py` は**変更しない** (親の択一 3(a))。injected test 経路は v4 のまま。
7. planned は `retry_ordinal=None`、retry は `measurement_ordinal` を供給する (A2 の訂正束縛に合わせる)。

## 行番号 pin の保存 (触ると受入が赤になる)

`orchestrator/tests/test_ccbench_spawn_sites.py:895-910,2642-2720` が
`s8b_floor_campaign.py` の**行番号 4707 と 8636** を pin している。
**新しい helper は 8636 より後ろへ置き、それより前方の物理行数を保存する。**
`test_ccbench_spawn_sites.py` は所有外なので編集しない。触る必要が出たら**止めて報告する**。

同じく所有外で触ってはいけない pin:
`test_official_perf_closure.py` の `_REVIEWED_PERF_FILES` と AST 集合等値、
`test_s8b_floor_stats.py:1603-1629` の live verifier caller exact 3 file、
`test_s8b_floor_contract.py:164-180` の alias re-export identity。

## 新設する test (自分で走らせて nodeid と件数を報告する)

正例と負例を分け、**実体を名指しする**。依存先を stub して通す形にしない。

- `test_default_production_attempt_uses_certified_launcher_once` — launcher 呼び出し回数を直接数える
- `test_registry_plan_declares_exact_planned_and_retry_slot_closure` — helper の exact slot 集合を直接比較
- `test_registry_plan_maps_round_to_zero_based_repetition` — helper 直接 (integration だと過剰決定)
- `test_certified_campaign_rejects_unissued_consumption_marker` — exact な issuer 拒否理由を pin
- `test_journal_emits_launcher_terminal_record_byte_identically`
- `test_default_production_result_is_v5`
- `test_production_v5_self_check_rejects_prefix_head_mismatch` — exact reason
  `attempt-registry-prefix-head-mismatch` を pin
- `test_v5_prefix_covers_every_consumed_non_competing_session`
  — 被覆は「消費された非 competing session」。**「emit した全 session」に広げない**
  (pre-probe competing は marker も attempt row も 0 が正例である)
- `test_competing_pre_probe_consumes_no_marker_and_writes_no_registry_row`
  — **実** `inspect_floor_holdout_admission_evidence()` を通す。stub や synthetic case で代替しない
- `test_injected_measurement_core_retains_noncertifying_legacy_path` — 既存 injected 経路が v4 のまま残る
- `test_finalize_pending_replays_live_v5_prefix`

**過剰拒否していないことの対照 (正例)**
- pre-probe competing の session が従来どおり有効なまま受理されること
- planned (`measurement_ordinal == 0`) が拒否されないこと

## 禁止

- 既存 test の期待値を変えない。反転・緩和・skip・削除をしない。赤なら実装側が誤りとする。
  期待値が誤りだと判断したら**実装を変えず報告して止まる**。
- `s8b_floor_contract.py`、`attempt_registry_core.py`、`FORMULA_ID`、凍結成果物に触れない。
- launcher の perf 述語の**新しい直接 call** を作らない。
- 受理集合を指示外に変えない。**holdout inspector と marker 規則を緩めない。**
- 期待値へ揮発 payload (working tree hash、時刻、pid、artifact_sha256 の実値など) を焼き込まない。
- fake registry や injected `measure_fn` を「実環境の値域」と数える記述をしない。
- 出力へ結合文字 U+0300〜U+036F を使わない。

## 検査 (自分で実走する)

**`tools/run_tests.py` は sandbox では rc=16 になるので使わない。** 自走 harness を使う。

```
cd /work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c3-b
PYTHONPATH=. python3 orchestrator/tests/test_s8b_floor_campaign.py
```

- 緑は**実走した nodeid 数と範囲を併記**する。走らせていないものを緑と書かない。
- 新設・改名した test の単位は、親の名指しを網羅と見なさず、**自分で制約 meta-test を洗い出して**
  走らせる (行番号 pin、AST 走査、alias identity、perf inventory)。
- 実走不能なら `closed` と申告せず「実装済み・未実走」と書く。

## 出力形式

```
## 総括
(3-5 行)

## 配線前と配線後の順序 (file:line で対)

## 実装した内容

## 新設した test (nodeid / 正例・負例)

## 実走結果 (command と passed/failed の実数)

## 行番号 pin の保存の検算 (4707 / 8636)

## 所有外への波及可能性 (静的列挙)

## 残った懸念
```
