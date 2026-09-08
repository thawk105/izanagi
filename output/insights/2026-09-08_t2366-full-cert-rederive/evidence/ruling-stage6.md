# [T-2366] 段 6 裁定 — レビュー所見と fix 1 の内容

裁定日時: 2026-09-08 08:35 JST。統合 snapshot patch = `diff.patch` (fix 前、= `snapshot-before-fix1.patch`)。

## 所見の裁定

| # | 出所 | 所見 | 判定 | 採否 |
|---|---|---|---|---|
| 1 | A1 | `report == expected` は Python の `dict ==` なので `True == 1` を同一視し、JSON 型だけ違う偽造 (`legacy_repetitions_observed: 1 → True`) が通る | real | **scope 外・裁定パッケージへ**。partial 側 (4431) も同じ `==` で、ユーザー指示は「partial をそのまま射影」。full だけ canonical JSON bytes 比較にすると非対称が逆向きに残る。両側を同時に `_canonical_json(report) == _canonical_json(expected)` へ変える案として次の一手へ送る (production CLI では到達しない、直接呼出し境界のみ) |
| 2 | A2 | validator の `return canonical_full_evidence` を `return evidence` に弱めても新規・既存テストが緑のまま (P4 の意味を観測する正例が無い) | real (テスト防壁の欠落) | 採用。fix 1 で正例 1 本を足し、変異 M05 を登録 |
| 3 | B1 | 読み直した canonical evidence に対する receipt chain 検査 (partial の 4390〜4395 相当) が無く、partial の受領証を偽装 field で包んだ evidence dict + そこから作った indeterminate report が通る | real (射影の欠落) | 採用。fix 1 で production 側に 3 行足し、負例 1 本を足し、変異 M06 を登録。raw manifest schema chain の全拒否までは写さない (full の manifest 無効 = indeterminate の裁定と衝突) |
| 4 | B2 | M04 の old は代入文全体で一意化 | real | 採用済み (probe spec は代入文全体) |

## fix 1 (Codex author、1 単位。対象 2 file は段 5 と同じ)

production `orchestrator/campaign/paper_story_a2_certification.py`:

- `_validate_certification_result` の v4 full 枝で、`canonical_full_evidence = validate_acquisition_bundle(...)` の**直後**、`expected = _canonical_full_report(...)` の**前**に次を足す (partial の 4390〜4395 と同型):

```
        if (canonical_full_evidence.get("acquisition_schema") != ACQUISITION_SCHEMA
                or canonical_full_evidence.get("completion_schema")
                != COMPLETION_SCHEMA):
            raise SchemaChainError(
                "certification result is crossed with a re-read partial receipt chain")
```

  エラー文言はこの逐語 (既存の `legacy result is crossed with a partial receipt or manifest` と区別し、変異の帰属を一意にするため)。他は変えない。

test `orchestrator/tests/test_paper_story_a2_certification.py` (新規 2 node、名前はこのとおり):

- `test_full_materializer_writes_reread_receipt_bytes_not_supplied_bytes` (正例、A2 対応):
  `_full_materializer_forgery_case` の正規 report と evidence を使い、evidence の deepcopy の
  `acquisition_bytes` / `submission_bytes` / `completion_bytes` を別 bytes (例 `b"{\"forged\": true}\n"`) に差し替えて `materialize` へ渡す。
  materialize は**成功**し、生成された `acquisition-receipt.json` / `submission-receipt.json` / `completion-receipt.json` の bytes が
  disk の acquisition / submission / completion receipt を読み直した bytes (元の `evidence[...]_bytes`) と一致し、差し替えた bytes と**一致しない**ことを assert する。
  `artifact-manifest.json` の sha も元 bytes の sha と一致することを assert する。
- `test_full_materializer_rejects_reread_partial_receipt_chain_behind_forged_full_fields` (負例、B1 対応):
  `_partial_materializer_forgery_case` で partial の root / evidence を作り、evidence の deepcopy に
  `acquisition_schema=A2.ACQUISITION_SCHEMA`、`completion_schema=A2.COMPLETION_SCHEMA`、`raw_manifest_valid=False`、`raw_manifest_schema=None` を上書きし、
  `A2._canonical_full_report(policy, forged_evidence, attempt_id=root.name, current_pin=CURRENT_PIN)` で indeterminate report を作って `materialize` へ渡す。
  `pytest.raises(A2.SchemaChainError, match="crossed with a re-read partial receipt chain")` と tracked destination 不在を assert する。
  この負例が**fix 前の実装では通る** (materialize 成功) ことを確認し、確認方法を報告に書く。

## 変異事前登録の追記 (M01〜M04 は段 4 のまま)

| id | category | 置換 (意味) | 期待 | 期待 node |
|---|---|---|---|---|
| M05-return-supplied-evidence | negative | `        return canonical_full_evidence\n` → `        return evidence\n` | KILLED | `test_full_materializer_writes_reread_receipt_bytes_not_supplied_bytes` |
| M06-reread-chain-check-removed | negative | 上記 `if (canonical_full_evidence.get("acquisition_schema") ...` 条件を `if False:` に | KILLED | `test_full_materializer_rejects_reread_partial_receipt_chain_behind_forged_full_fields` |

M03 の期待 node (8 正例) は review B の現物列挙のとおり。M05 の正例 test は M03 でも赤になる (materialize が拒否される) ので M03 の期待 node に加える (probe で確定)。

## 受入台帳

新規 node (段 5 の 3 + fix 1 の 2 = 5 node) は親が dispatch で junit を取り、別の Codex author 単位 (fix 2) が `tools/update_acceptance_duration_ledger.py --add-only` で登録する。
