単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2

必読事項の射影 (いずれも絶対パス。読めなければ即停止し、その旨を出力に書いて終わること):

- **作業 root (書込み可。ここだけを編集する)**: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c3-a2`
- **親の段 4 裁定 (これが scope の正本)**: `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/s4-adjudication.md`
- 親の段 1 brief: `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/s1-brief.md`
- 段 2 plan: `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/out-s2-plan.md`
- 段 3 レンズ A (ordinal の 5 軸の実測がここにある): `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/out-s3-lensA.md`
- 段 3 レンズ B: `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/out-s3-lensB.md`
- 契約の正本: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c3-a2/output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.1.md`
- 契約の追記訂正 1 (書式の先例): `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c3-a2/output/insights/2026-09-08_t1851-unit-c2-derivation/contract-v3.1-erratum-1.md`
- 共通規律: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c3-a2/CLAUDE.md`

# 段 5 子 A2 — campaign retry ordinal の束縛を実軸へ直す

## 所有 path (これ以外を 1 行も変えない)

- `orchestrator/campaign/s8b_terminal_evidence.py`
- `orchestrator/campaign/s8b_attempt_registry.py`
- `orchestrator/tests/test_s8b_terminal_evidence.py`
- `orchestrator/tests/test_s8b_attempt_registry.py`

**docs は編集しない。commit しない。`git add` もしない。** 親が行う。
契約の追記訂正 (erratum) は**親が書く**ので、あなたは書かない。

## 直す内容 (親の裁定。択一 2 (a))

v2 `slot_id` の 5 軸は `(freeze_holdout_key, configuration_id, repetition, measurement_ordinal,
attempt_ordinal)` である。**campaign の retry 軸は `measurement_ordinal` = `slot_id[3]`、
`attempt_ordinal` = `slot_id[4]` は series 内の recovery 軸**であり、production registry は
`attempt_ordinal != 0` を拒否する。

現行はここを取り違えている。

- `s8b_terminal_evidence.py:760-768` が `retry_ordinal` を非負整数に限り、planned の `None` を拒否する。
- 同 `:1140-1157` が `campaign_record.retry_ordinal == slot_id[4]` を要求する。
- `s8b_attempt_registry.py:1394-1429` の adapter / replay も同じ誤束縛を独立に要求する。

**直す先の束縛はこれである。**

- `retry_ordinal is None` ⟺ `measurement_ordinal == 0` (planned)
- それ以外は `retry_ordinal == measurement_ordinal` (retry、campaign 契約の `1..N`)

**これは緩和ではない。** 現行は production で常に 0 の軸へ束縛していたため retry の `1..N` を
構造的に表現できなかった。訂正後は束縛が実軸へ再照準され、planned も表現できる。

## 既存 test 期待値を変えてよい 3 箇所 (親が名指しした。これ以外は不可)

1. `orchestrator/tests/test_s8b_terminal_evidence.py:124-142,159-169` の fixture
2. `orchestrator/tests/test_s8b_attempt_registry.py:367-388` の fixture (`kind="planned"` なのに
   `retry_ordinal=slot.attempt_ordinal`)
3. 同 `:4300-4372` の transplant 負例のうち、誤軸を pin している部分

**強度を落とさないこと。** 訂正後も次の 2 つの負例が**実際に発火**しなければならない。

- (i) planned なのに `retry_ordinal` が非 null なら拒否される
- (ii) retry の `retry_ordinal` を `attempt_ordinal` (recovery 軸) へ差し替えたら拒否される

上記 3 箇所以外の既存期待値を変える必要が生じたら、**実装せず報告して止まる**。

## 新設する test (自分で走らせて nodeid と件数を報告する)

- `test_planned_terminal_binds_none_retry_ordinal` — planned の `None` が通る正例
- planned の非 null が拒否される負例
- retry の `retry_ordinal == measurement_ordinal` が通る正例
- `test_durable_replay_binds_measurement_ordinal` — adapter / replay 側の同じ束縛
- retry を recovery 軸へ差し替えると拒否される負例
- `measurement_ordinal` と `attempt_ordinal` が**異なる値**を取る fixture で、
  どちらに束縛されているかが判別できること (両方 0 の fixture では判別できない)

## 禁止

- `attempt_registry_core.py` を変更しない。`aborted=False` keyword と `OriginSealed(False, ...)` を
  書かない (`test_reflux_formal_consumer.py` の AST 走査が拒否する)。
- `FORMULA_ID`、凍結成果物に触れない。
- 名指しされた 3 箇所以外の既存 test 期待値を変えない。反転・緩和・skip・削除をしない。
- 受理集合を指示外に変えない。とくに「型検査を外して何でも通す」方向にしない。
- 期待値へ揮発 payload を焼き込まない。
- 出力へ結合文字 U+0300〜U+036F を使わない。

## 検査 (自分で実走する)

**`tools/run_tests.py` は sandbox では rc=16 になるので使わない。** 自走 harness を使う。

```
cd /work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c3-a2
PYTHONPATH=. python3 orchestrator/tests/test_s8b_terminal_evidence.py
PYTHONPATH=. python3 orchestrator/tests/test_s8b_attempt_registry.py
```

- 緑は**実走した nodeid 数と範囲を併記**する。走らせていないものを緑と書かない。
- 新設・改名した test の単位は、親の名指しを網羅と見なさず、**自分で制約 meta-test を洗い出して**
  走らせる (公開署名 pin、import 集合 pin、AST 走査 test など)。
- 実走不能なら `closed` と申告せず「実装済み・未実走」と書く。

## 出力形式

```
## 総括
(3-5 行)

## 現行の誤束縛と訂正後の束縛 (file:line で対)

## 実装した内容

## 変更した既存 fixture (3 箇所のどこを、なぜ、強度をどう保ったか)

## 新設した test (nodeid / 正例・負例)

## 実走結果 (command と passed/failed の実数)

## 所有外への波及可能性 (静的列挙)

## 残った懸念
```
