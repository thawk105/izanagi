単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair

必読事項の射影:

- `/home/SFC/tanab/.claude/jobs/0ef29ace/tmp/dev-wave-t2314-inert-reason-pair/s4-ruling.md`
  — **親の段 4 裁定。これが確定仕様である。** 読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/0ef29ace/tmp/dev-wave-t2314-inert-reason-pair/s1-brief.md`
  — 段 1 brief。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/0ef29ace/tmp/dev-wave-t2314-inert-reason-pair/verbatim-d1625.md`
  — 確定済みユーザー裁定 D1625 の逐語。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/0ef29ace/tmp/dev-wave-t2314-inert-reason-pair/codex-artifacts/t2314-inert-reason-pair/s2-plan-out.md`
  — 段 2 プラン。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/0ef29ace/tmp/dev-wave-t2314-inert-reason-pair/codex-artifacts/t2314-inert-reason-pair/s3-lensA-out.md`
  — 段 3 レンズ A。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/0ef29ace/tmp/dev-wave-t2314-inert-reason-pair/codex-artifacts/t2314-inert-reason-pair/s3-lensB-out.md`
  — 段 3 レンズ B。読めなければ即停止。

編集してよい file は次の 2 つだけである。

- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py`

## 依頼

段 4 裁定の「プラン v2 (確定)」1〜4 をそのまま実装せよ。5 (受入台帳) は親が受入後に行うので
**触るな**。裁定と食い違う点を見つけたら実装せず報告して止まれ。

## 実装の要点 (裁定より再掲。ここが正)

1. probe に `_INERT_CONDITION_GATE_PAIRS: frozenset[tuple[str, str]]` を置く。要素は
   `("stock-inert-preprocess-identical", "stock-inert-identity")` と
   `("stock-inert-preprocess-root-location-only", "stock-inert-root-location-only")` の 2 組だけ。
2. `_condition_gate_receipt_summary` の supply entry へ
   `"comparison": supply.evidence.get("comparison")` を足す。
   **添字 `evidence["comparison"]` を使ってはならない** — 赤 record には key が無く `KeyError` で
   `verdict_s6` を脱出し、fail-closed 判定が process 失敗に変わる (段 3 レンズ A の A-01)。
   `evidence` mapping 自体は receipt へ出さない。
3. `_condition_gate_family_valid` の
   `supply.reason_code == ... and supply.evidence.get("comparison") == ...` の 2 行を
   `(supply.reason_code, supply.evidence.get("comparison")) in _INERT_CONDITION_GATE_PAIRS`
   に置き換える。他の条件 (`observed == expected`、receipt summary 一致、`admitted is True`、
   `driver_id`、`macro`、`terminal_status == "green"`、meaning arm の 2 条件) はすべて残す。
4. test を足す。既存 fixture `_condition_gate_receipts` の supply entry にも `comparison` を純増する。
   - `test_s6_accepts_each_exact_inert_condition_gate_pair[identity]` — 既存 identity family で S6 `go`。
   - `test_s6_accepts_each_exact_inert_condition_gate_pair[root-location-only]` —
     `tmp_path` へ fixture を copy し、requested/stock 双方の header へ `__FILE__` 行を足して
     **production evaluator** (`evaluate_define_supply_effectuation`) に本物の record を発行させる。
     driver_id は `tools.pegasus.probes.t316_sandbox_backend_probe`、`macro="BACKOFF_FIXED"`、
     `requested_value=-1`、`default_value=None`、`stock_comparison=True` と production に揃える。
     `gate._arm_record` で reason/comparison を手書きした偽物にしてはならない。
     参考は `orchestrator/tests/test_condition_meaning_gate.py` の
     `test_inert_root_location_only_difference_is_green` (同 file の `_copied_fixture` /
     `_append_inert_header_lines` と同じ生成条件)。**その file は編集するな。**
   - `test_s6_rejects_crossed_inert_condition_gate_pair[identical_reason__root_location_comparison]`
     と `[root_location_reason__identity_comparison]` — 2 つの本物 family から reason 側と
     comparison 側を交叉させる。通常経路では gate の admission が先に弾くので、
     `condition_meaning_gate.require_condition_gate_family` をこの test 内だけ差し替えて
     gate 層を中和し、**かつ交叉 family から作り直した receipt summary を observation へ渡す**
     こと。渡さないと `receipt_summary == _condition_gate_receipt_summary(value)` の手前で
     恒真に拒否され、probe の述語を守らない (段 3 レンズ B の B-03)。
   - `test_s6_rejects_requested_default_preprocess_difference` — production evaluator が発行し
     gate 自体は admit する本物の `requested-default-preprocess-different` family を渡し、
     probe が `S6_CONDITION_GATE_UNPROVEN` を返すことを要求する。この helper は
     **`stock_comparison=False`** でなければ `request-contract-invalid` で evaluator 前段から
     落ち、負例が恒真になる (段 3 レンズ B の B-02)。

## 検査と報告 (すべて守れ)

- 緑を主張するときは**実走した nodeid と範囲**を併記せよ。子の実走は親の全走を代替しない。
  実走できなければ `closed` と申告せず「実装済み・未実走」と書け。
- この repo では `tools/run_tests.py` は sandbox から rc=16 になり、`python -m pytest` は guard に
  拒否される。走らせるなら worktree root を cwd にして
  `PYTHONPATH=. python3 orchestrator/tests/test_t316_sandbox_probe.py` の自走 harness を使え。
  C++ compiler / cmake が無ければその旨を書いて止まれ (推測で緑と書くな)。
- テスト新設の単位では、親の名指しを網羅と見なさず、制約 meta-test を自ら洗い出して走らせよ。
- fixture へ現行 hash を差し込むなど、**テストを甘くして緑にする**ことをしてはならない。
  機構の正例・負例は実体を名指しし、依存先を stub しない。
- 期待値へ揮発 payload (working tree hash 等) を焼き込むな。
- 完了報告に、所有外 caller・共有 fixture・consumer test への波及可能性を静的に列挙せよ。
- **指示外の受理集合変更をするな。** 変更前の現行の受理・拒否挙動を報告に明記せよ。

## 禁止

- 上の 2 file 以外を編集しない。gate 本体・policy・hooks・受入所要台帳・docs を触らない。
- commit・git 操作 (add/commit/checkout/branch/stash など) をしない。
- 既存テストの期待値を変更・緩和・反転・skip・削除しない。赤なら実装側が誤りとする。
  期待値の方が誤りだと判断したら、実装を変えず報告して止まれ。
- 受理集合を D1625 の 2 組より広げない。exact 一致検査を外さない。
- 新しい gate・検査・台帳・互換層・一般化・防御的堅牢化を足さない。

## 出力形式

```
## 実装した内容
（file:line と変更前後）

## 変更前の受理・拒否挙動
（現行が何を受理し何を拒否していたか）

## 実走した検査
（nodeid・範囲・rc。実走不能ならその理由）

## 波及の静的列挙
（所有外 caller・共有 fixture・consumer test）

## 残した赤・未了
（あれば。無ければ「なし」）

## 総括
（3〜6 行）
```
