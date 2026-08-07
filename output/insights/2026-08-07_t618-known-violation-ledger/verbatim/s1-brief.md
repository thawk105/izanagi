# 段 1 brief — [T-618] 既知違反台帳へ `3f2c43d7` を追加する

## scope

`tools/check_ai_provenance.py` の `KNOWN_PROVENANCE_VIOLATIONS` へ 7 件目として
`3f2c43d7580b8c26724d90278589862057508965` / `missing-ai-agent` を追加し、注記を伴わせる。
`orchestrator/tests/test_check_ai_provenance.py` の台帳を pin する既存テストを追随させる。
docs は親が書く (worklog / decisions fragment、必要なら `docs/provenance/audit.md` PR-A02)。
履歴書き換え、correction 枠の再開放、範囲式の変更、他 SHA の追加は scope 外。

## 確定済みユーザー裁定 (2026-08-07 /rulings 第 3 回、択 (b)、worklog(293))

`3f2c43d7` を既知違反台帳へ追加する。注記 =「trailer は本文に実在するが、`AI-Agent:` と
`Co-Authored-By:` の間の空行で Git が trailer block と認識しない形式崩れ」。帰属の欠落ではなく
書式の崩れの記録であり、rc を新規のみで決める案 3 (D221) の目的を回復する。履歴書き換えはしない。

## 実測済みの前提 (2026-08-07、worktree `dev-wave-t618-provenance-known-ledger`、起点 `bb824d8b`)

- 既定 full 監査は **1702 件中 新規 1 / 既知 6 / rc=1**。新規は `3f2c43d7580b` の
  「AI-Agent trailer がない」ただ 1 件。→ 台帳追加後の期待値は **既知 7 / 新規 0 / rc=0**。
- `git log -1 --format=%B 3f2c43d7 | cat -A` で、`AI-Agent:` 行と `Co-Authored-By:` 行の間に
  空行 (`$` 単独行) が実在することを確認した。裁定の注記は一次資料と一致する。
- `KnownViolationSpec` は `commit` / `expected_finding_kind` / `ruling` の 3 field。`ruling` は
  どこにも出力されていない (source 内の記録のみ)。
- `tools/check_ai_provenance.py` の bytes を pin する凍結台帳は無い
  (`FROZEN_MANIFEST` 23 entry に不在、`s1_expected_goldens` / `test_check_docs` にも hash pin なし)。
  → `DW-O09` / `DW-O10` は不成立。
- 追随が要る既存テスト 4 本を実測で特定した (行番号は起点時点):
  `test_known_violation_ledger_is_exactly_six_literal_entries` (1323、`3f2c43d7…` 不在を明示 assert)、
  `test_known_violation_ledger_matches_real_commit_findings` (1370)、
  `test_empty_registry_restores_all_six_real_findings` (1809)、
  `test_unledgered_3f2c43d7580b_remains_new_and_rc1` (1832、rc=1 と known-violation 不在を pin)。

## provisional 裁定 (親の暫定。段 3 の攻撃対象)

- **(P1) 注記の載せ方** = `KnownViolationSpec` へ既定値 `""` の `note` field を追加し、7 件目だけが
  設定する。非空なら `known-violation` 行へ `note=…` として stdout に出す。既存 6 件は空のまま。
  対立案: (i) source コメントのみで schema を変えない、(ii) 全 7 件に必須 `note` を書かせる。
- **(P2) ruling 文字列** = 7 件目だけ `"worklog(293) 2026-08-07 /rulings"` を持ち、既存 6 件が使う
  `_KNOWN_VIOLATION_RULING` (worklog 284) は変えない。裁定回が異なるため共有定数にしない。
- **(P3) 既存 4 テストは「削除」ではなく「反転して残す」**。とくに 1832 は
  `test_ledgered_3f2c43d7580b_is_known_and_rc0` へ反転し、rc=0・stdout に当該 SHA の
  `known-violation` 行・`新規違反なし` の 3 点を pin する。「消して緑」を許さない。
- **(P4) 注記の妥当性検査** = `note` は `str` であること、非空なら改行を含まないことを
  `_known_violation_registry()` で検査し、破れば rc=2 (既存の型破損検査と同じ fail-closed)。

## 不変条件 (緩めない)

- 台帳の照合は **full SHA 完全一致 × 期待 finding 種別一致**のまま。prefix 一致・種別 wildcard・
  「その commit の finding を全部既知にする」への一般化をしない (規律 2)。
- 1 entry が吸収するのは期待種別の finding **1 件だけ**。同 commit の他 finding は新規として残る。
- 台帳 entry が範囲内にありながら期待 finding を生まないときの **stale rc=2** を維持する。
- 台帳破損 (型・重複・非 full SHA・未知種別・空 ruling) は rc=2 のまま。
- 既知は rc に関わらず stdout へ公開する。`新規` 修飾も維持する (rc=0 を緑と読ませない)。
- 履歴を書き換えない。`AI-Agent-Correction` 枠 (`PR-C01`、消費済み) に触れない。

## 成果物影響 (`DW-G05`)

研究成果物 (certified 選択、レポート、試行台帳) の値は不変。変わるのは **commit gate の受理集合**
だけ — 既定 full 監査の rc が 1 → 0 になり、`3f2c43d7` 1 件ぶんの手作業帰属が不要になる。
実装しない場合、既定監査は rc=1 のまま残り、以後の全 wave が「新規違反 0 件」を機械で確認できず
毎回手で 1 件を差し引く残余リスクが続く (新規違反 1 件が既存 1 件に紛れる)。

## 成果物の形

1. `tools/check_ai_provenance.py` の台帳 +1 entry (+ `note` field と検査)。
2. `orchestrator/tests/test_check_ai_provenance.py` の既存 4 テスト追随 + `note` 検査の純増テスト。
   純増検出力 = 「注記が失われる / 改行混入で stdout 行が壊れる」経路の検出 (現状は被覆ゼロ)。
3. worklog / decisions fragment (親)、insights 逐語凍結 (親)。

## 並列分割方針

編集面が `tools/check_ai_provenance.py` と同 test file の 2 本しかなく、台帳 entry と
その pin テストは同時に変えないと必ず赤になる。**段 5 は Codex `role=author` 1 単位**とし、
worktree 分割はしない。段 3 と段 6 は 2 レンズ並列。

## 受入・実測環境

Pegasus (worklog が主戦場の正本)。login node から `python3 tools/run_tests.py` (追加 flag なし)、
provenance 監査は `python3 tools/check_ai_provenance.py`。いずれも実行場所は tool が自分で決める。
変異は `tools/mutation_harness.py`、`--runner-mode dispatch` + `--force-dispatch`
(memory: 変異 runner は dispatch recipe が既定)。
