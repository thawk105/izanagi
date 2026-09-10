# 段 1 brief — [T-1815] 8c 事前登録 CLI の二重実体化と相対 import を直す

## scope (これだけ)

1. `orchestrator/campaign/s8c_preregistration.py` を実プロセス CLI として起動したとき、core module が
   二重に実体化して 12 条件すべてが `ERROR / evaluator-exception` になる欠陥を直す。
2. `orchestrator/campaign/s8c_gate_report.py` をファイルパス直接起動したときの `ImportError` を直す。
3. 再発防止として、CLI を**実プロセスとして起動する**回帰検査を新設する。

これ以外は scope 外。仮想リスク向けの gate・検査・台帳・一般化・互換層を足さない (`DW-G05`)。

## 確定済みユーザー裁定

- Codex `role=author` = D95。実装面は実装子だけが書き、親は docs のみ。
- sandbox 子は `run_tests` が rc=16 になるため、自走 harness を `PYTHONPATH=.` で使う。
- 規律 2 を緩めない。

## 親が実測した事実 (2026-09-07, main cf4273f56)

- `python3 orchestrator/campaign/s8c_preregistration.py check --json` → 12 件すべて
  `ERROR / evaluator-exception`、rc=1。
- `python3 -m orchestrator.campaign.s8c_preregistration check --json` → **同じく 12 件 ERROR、rc=1**。
- `python3 orchestrator/campaign/s8c_gate_report.py` → `ImportError: attempted relative import with
  no known parent package`。
- 正しい内訳 (`python3 -m orchestrator.campaign.s8c_gate_report`, rc=1) →
  C01/C02/C04/C06/C07/C09/C11/C12 = `EVIDENCE_UNDEFINED completion-proof-not-machine-checkable`、
  C03 = `UNSATISFIED manifest-registry-proof-undefined`、C05 = `EVIDENCE_UNDEFINED
  schedule-schema-absent`、C08 = `EVIDENCE_UNDEFINED prereg-binding-proof-undefined`、
  C10 = `SATISFIED cross-binding-readiness-satisfied`。`effective=false`。
- 条件凍結 g15 は module blob を pin しない (`protected_sha256` / `evidence_contract_sha256` /
  `section6_*` / `decider_version` のみ)。現行 core blob sha256 の tracked file 内 hit は 0 件。

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- **(P1)** 根本原因は `s8c_preregistration.py:36-39` の bootstrap が `sys.modules` へ canonical 名を
  登録しないことだけであり、`_normalize_predicate_results` の `isinstance` 検査は正しい。修正は
  bootstrap 側だけで足りる。
- **(P2)** `-m` 起動も同じ欠陥を持つので、修正は「ファイルパス直接」と「`-m`」の両起動形を同時に
  直さなければならない。F631 の恒久対応が独立入口とした `-m` は、`s8c_gate_report` でだけ健全である。
- **(P3)** この 2 file の bytes 変更は凍結成果物を無効化せず、`DECIDER_VERSION` の bump も不要
  (受理意味は不変)。ただし両 file は `campaign_lock.py` の enforcement source なので HEAD blob 束縛であり、
  commit 前の焦点走は `contract-loader-drift` で赤になる。
- **(P4)** `_default_registry_results` の `except Exception` が例外理由を握り潰す点 (F631 が
  「なぜ通らなかったかが消える」と書いた部分) は本 wave の scope 外とする。

## 不変条件 (破ったら停止)

- **受理集合不変**: 修正後も `effective` は false、両 CLI とも rc=1。`SATISFIED` の集合は C10 のみ。
- `_normalize_predicate_results` の型検査・件数検査・id 集合検査を緩めない。診断を良くするために
  型検査を弱める方向の変異は採用しない (規律 2)。
- `DECIDER_VERSION`、条件凍結 g15、`docs/phase3-8c-preregistration.md` の bytes を変えない。
- 既存テストの期待値を変えない。赤なら実装側が誤り。
- 新設検査は現行 HEAD で**実際に落ちる**こと (恒真な検査を作らない)。

## 変更面 実アンカー表

| path:line | 役割 | 本 wave の扱い |
|---|---|---|
| `orchestrator/campaign/s8c_preregistration.py:36-39` | `if __package__ in {None, ""}` bootstrap | 修正対象 |
| `orchestrator/campaign/s8c_preregistration.py:2213-2214` | `if __name__ == "__main__"` | 参照 |
| `orchestrator/campaign/s8c_preregistration.py:1739-1756` | `_normalize_predicate_results` | **不変** |
| `orchestrator/campaign/s8c_preregistration.py:1841-1856` | `_default_registry_results` の握り潰し | **不変** (P4) |
| `orchestrator/campaign/s8c_preregistration_evidence.py:18` | `from . import s8c_preregistration as core` | 不変・原因の相手側 |
| `orchestrator/campaign/s8c_gate_report.py:16` | `from . import s8c_preregistration as _prereg` | 修正対象 (bootstrap 追加) |
| `orchestrator/campaign/s8c_gate_report.py:172-173` | `if __name__ == "__main__"` | 参照 |
| `orchestrator/tests/test_s8c_gate_report.py:434-461` | 既存の `-m` subprocess 検査 (先例) | 不変 |

## 成果物の形

- production 差分: 上記 2 file の bootstrap のみ。
- 新規 test file 1 本 (実プロセス CLI 検査)。末尾に `if __name__ == "__main__": raise
  SystemExit(pytest.main([__file__]))` の自走 harness を付ける。
- 変異 matrix、worklog / decisions fragment (`docs/spool/`)、insight。

## 分割方針

編集 path が 3 file と少なく相互依存するため、段 5 は**単一の Codex 実装子**へ寄せる (一枚岩)。
段 3 と段 6 のレンズだけ 2 本並列にする。
