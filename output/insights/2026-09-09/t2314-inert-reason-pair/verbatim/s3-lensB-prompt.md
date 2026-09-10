単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair

必読事項の射影:

- `/home/SFC/tanab/.claude/jobs/0ef29ace/tmp/dev-wave-t2314-inert-reason-pair/s1-brief.md`
  — 親の段 1 brief。**これ自身も検査対象**。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/0ef29ace/tmp/dev-wave-t2314-inert-reason-pair/verbatim-d1625.md`
  — 確定済みユーザー裁定 D1625 の逐語。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/0ef29ace/tmp/dev-wave-t2314-inert-reason-pair/codex-artifacts/t2314-inert-reason-pair/s2-plan-out.md`
  — 段 2 のプラン。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.py`
  — 変更対象。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py`
  — 変更対象の test。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_condition_meaning_gate.py`
  — gate 側の既存正例。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/campaign/condition_meaning_gate.py`
  — gate 本体。読めなければ即停止。

## 依頼 — レンズ B: 整合・実効性・波及

プランを**守らずに攻撃**せよ。実装はするな。書込み可能な tmp が無いので pytest 緑は要求しない。
静的検査で足りる。予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。

このレンズは「書いたものが本当に効くか」と「他所を壊さないか」を見る。具体的に探すもの:

1. **2 組目の正例が本物か。** プランが提案する fixture は、2 組目
   (`stock-inert-preprocess-root-location-only` / `stock-inert-root-location-only`) の record を
   どう作るか。gate の `require_condition_gate_family` が要求する evidence
   (`root_diff_has_residual`、root-dependent builtin path、configure argv の `-S`、
   `root_diff_source_roots` の束縛など) を満たさずに `gate._arm_record` で作った record は、
   admission で弾かれるはずだ。プランがそこを踏んでいないか実コードで検算せよ。
   **正例が実体を名指しせず、依存先を stub して「通った」ことにしていないか。**
2. **負例が恒真でないか。** 交叉の負例が、probe の述語ではなく gate の admission で先に落ちるなら、
   その test は probe の変更を守っていない。どの層で落ちるかを入力ごとに特定せよ。
3. **consumer test の取り残し (参照関係で引く)。** 変更する production の識別子
   (`_condition_gate_family_valid`、`_condition_gate_receipt_summary`、`condition_gates`) を
   `orchestrator/tests/` で grep し、波及する test を**名前の推測でなく参照関係で**全列挙せよ。
   `test_t316_sandbox_probe.py` の受領証形状 assert (`evidence` 不在、`_condition_gate_receipts()`
   との一致など) が新しい field でどう動くかを行番号つきで示せ。
4. **受領証形状の変更が壊すもの。** 既に発行済みの receipt
   (`output/env/pegasus/t316-sandbox-backend/*/receipt.json`) や schema 版
   (`SCHEMA_VERSION`、`tools/pegasus/policies/t316_sandbox_backend_v1.json`)、
   `orchestrator/tests/test_official_perf_closure.py`、`orchestrator/tests/test_hooks.py` への波及。
   版を上げるべきか、上げなくてよい理由が実コードで示せるかを判定せよ。
5. **親 brief 自身の誤り。** 「pin 閉包は空 (FROZEN_MANIFEST に t316 なし、blob/sha256 の grep が
   0 件)」「到達可能性は worklog の 1 行で実測済み」「編集面は 2 file の一枚岩」という
   **親自身の実測値とその一般化**を疑え。親が見落とした pin の張り方 (path 以外を key にする pin、
   role 名、xdist group 名など) を探せ。
6. **受入台帳。** 新しい test nodeid を足すと
   `orchestrator/tests/acceptance_duration_ledger.json` に何が要るか。プランがそれを落としていないか。

## 禁止

- gate 本体の変更を提案しない。新しい gate・検査・台帳・互換層・一般化を提案しない。
- 既存テストの期待値の変更・緩和・反転・skip・削除を提案しない。
- commit・git 操作・docs 編集・ファイル書き換えをしない。
- scope 外の real 所見は「裁定パッケージ候補」と明記して返す。実装したふりをしない。

## 出力形式

```
## 所見
（1 件ずつ。所見 ID / 対象 file:line / なぜ壊れるか / 具体的な入力例 / 重大度）

## 波及一覧
（参照関係で引いた consumer test の file:line と、新しい形で通るか落ちるか）

## 親 brief への反証
（brief の前提・実測値・一般化のうち、誤り・過大なもの）

## 裁定パッケージ候補
（scope 外だが real なもの）

## 総括
（3〜6 行）
```
