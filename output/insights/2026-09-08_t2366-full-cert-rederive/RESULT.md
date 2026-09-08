# [T-2366] full certification の materializer に exact 再導出を入れた — 変異台帳と実測

- wave: dev-wave-t2366-full-cert-rederive
- 対象 HEAD (変異本走): `82a57e92e4eea61f24274d34586b7ac056ba61b6`
- 実装 commit: `97dffc7df` (Codex author)、main c12e25078 取り込み: `0a4f4db98`、受入台帳: `82a57e92e` (Codex author)
- 裁定: 段 4 = `evidence/ruling.md`、段 6 = `evidence/ruling-stage6.md`。設計判断は decisions (fragment `docs/spool/decisions/2026-09-08-dev-wave-t2366-full-cert-rederive-2.md`)

## 何を閉じたか

partial (v2) 側の materializer は D1259 以降、acquisition receipt を読み直して report 全体を再導出し
完全一致を要求していた。full (v4) 側は外形と identity しか見ておらず、正の evidence に対する偽 status /
偽 effects / 偽 driver_rcs と整合する indeterminate report を tracked 成果物として公開できた (D1692 が別項へ
送った既存の非対称)。partial の既存実装をそのまま full へ射影した。新しい検査層・schema 版・台帳は作っていない。

変更前の実装で通ってしまう偽造 (実装子が一時変異で materialize 成功を確認、親が現物で読んだ):

| 負例 | 偽造 | 変更後の拒否 |
|---|---|---|
| `test_full_materializer_rejects_forged_status_from_positive_evidence` | 正の evidence の report の `status` を `observed-positive` → `reject` | `differs from evidence re-derivation` |
| `test_full_materializer_rejects_forged_effects_from_positive_evidence` | `effects[rr5]` を +1.0 | 同上 |
| `test_full_materializer_rejects_indeterminate_report_from_full_success_acquisition` | 渡す evidence dict の `driver_rcs[rr5]=7` と整合する indeterminate report (disk は全 driver 成功) | 同上 (読み直しが positive expected を返す) |
| `test_full_materializer_rejects_reread_partial_receipt_chain_behind_forged_full_fields` | partial の受領証を `acquisition_schema` / `completion_schema` / `raw_manifest_*` の表層 field だけ full に偽装 | `crossed with a re-read partial receipt chain` (SchemaChainError) |

正例 `test_full_materializer_writes_reread_receipt_bytes_not_supplied_bytes`: 渡された evidence の
`acquisition_bytes` / `submission_bytes` / `completion_bytes` を差し替えても materialize は成功し、成果物の
receipt bytes と manifest sha は disk から読み直した bytes になる (渡された bytes は authority ではない)。

## 変異 matrix

事前登録 6 件 (段 4 で M01〜M04、段 6 fix 裁定で M05〜M06 を追記)。probe (全件 SURVIVED 登録で観測 node を
収集) → final の 2 段、計算ノード dispatch、runner argv `python3 tools/run_tests.py
orchestrator/tests/test_paper_story_a2_certification.py -q -rf --force-dispatch`。

| id | 変異 | category | 期待 | 実測 | 期待 node |
|---|---|---|---|---|---|
| M01-rederive-removed | `expected = _canonical_full_report(...)` → `expected = report` | negative | KILLED | KILLED | 偽 status / 偽 effects / 偽 driver_rcs の負例 3 |
| M02-reread-removed | `canonical_full_evidence = validate_acquisition_bundle(...)` → `= evidence` | negative | KILLED | KILLED | 偽 driver_rcs の負例、canonical bytes の正例、偽装包装の負例 (3) |
| M03-always-reject | `if not full_report_matches_rederived_evidence:` → `if True:` | positive (過剰拒否の正例) | KILLED | KILLED | 既存 full 正例 8 + canonical bytes の正例 (9) |
| M04-equivalent-swap | `report == expected` → `expected == report` (代入文全体) | positive (等価) | SURVIVED | SURVIVED | (空) |
| M05-return-supplied-evidence | `return canonical_full_evidence` → `return evidence` | negative | KILLED | KILLED | canonical bytes の正例 (1) |
| M06-reread-chain-check-removed | 読み直し後の chain 条件 → `if False:` | negative | KILLED | KILLED | 偽装包装の負例 (1) |


台帳は `evidence/mutation-ledger-final.json` (probe は `evidence/mutation-ledger-probe.json`)、spec は
`evidence/mutation-spec-final.json` (sha256 `a7e9c51b9272d7e6b4ba70024f772adaa3f12026b744644133cdd95c92ceb8e6`)。
baseline `PASSED`、`repo_head` は上記 HEAD。

M04 の SURVIVED は等価変異 (`report == expected` ↔ `expected == report`、両辺とも dict) で、harness の
SURVIVED 検出が生きていることの正例。M05 候補「helper 冒頭の `_require_materializable_authority` を外す」は
`_collect_command` と `materialize` の同名呼出しが冗長 gate になり単一理由性が無いため登録しなかった (DW-M03)。

## 敵対レビューの所見と裁定

段 3 (consult A/B、plan と brief を検査): 9 件すべて real・採用。要点は「既存 identity 検査を読み直した
evidence へ一括切替すると受理集合が広がる」(両レンズ独立)、helper 冒頭の authority gate 欠落、変異 old の
partial 側との重複、brief の記述 3 点の訂正。

段 6 (review A/B、実装差分を検査): real 4 件。採用 3 件 (canonical bytes の正例欠落、読み直し後の receipt
chain 検査欠落、M04 old の一意化)。scope 外 1 件: `dict ==` は `True == 1` を同一視するので JSON 型だけ
違う偽造が通る — partial 側の既存比較も同じ形で、ユーザー指示 (partial の射影・新しい検査層を作らない) の
範囲外として実装せず、両側同時に canonical JSON bytes 比較へ変える案を次の一手へ送った。
焦点再レビュー (fix 1 統合後): 所見ゼロ。逐語は `evidence/consult-a.md` `consult-b.md` `review-a.md`
`review-b.md` `focus.md`。

## 親の実測

- 段 5 後: 計算ノード dispatch で同 file 173 passed / rc=0。fix 1 後: 175 passed / rc=0 (JUnit
  `evidence/junit-a2-1.xml`)。
- 受入台帳: 同 file 175 node 中 106 node のみ登録済みだったので、本 wave の 5 node を含む 69 node を
  `update_acceptance_duration_ledger.py --add-only` で登録 (Codex author、親が `--check` rc=0 で検算)。
- provenance: `c12e25078..HEAD` (本 wave の 3 commit) は違反なし。`34af5a571..HEAD` は main 側の
  c12e25078 (`.codex/worktrees/*` gitlink 110 本) が 1 違反 — 本 wave の差分ではない。

## 限界

- production CLI (`collect`) は同じ evidence から report を作るので、この一致検査は構成上ほぼ恒真である。
  縮むのは `materialize` を直接呼ぶ API 境界 (tests・将来の呼び手) と二回読みの間の disk 整合性。
- legacy v3 full / v1 partial は identity-only のまま (D1259 と同じ理由)。
- `dict ==` の JSON 型問題は上記のとおり未対応。
