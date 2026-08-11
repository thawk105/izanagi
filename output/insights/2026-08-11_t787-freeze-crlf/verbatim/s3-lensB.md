結論は **NO-GO** です。brief と段 2 プランは全文読了済み、pytest は実行していません。段 2 の骨格は強いですが、検出力と変異帰属に未解消の穴があります。

## 1. 生き残る弱実装

### B1 — root 直下の exact `path` が未検査

段 2 の malformed cases は `/conditions/path`、`/metadata/path` など深さ 2 以上だけで、root の `{"path": "x\\ralias"}` がありません（[stage2-plan.md:136](</work/1/SFC/tanab/dev-wave-jobs/t787-freeze-crlf/stage2-plan.md:136>)、[stage2-plan.md:150](</work/1/SFC/tanab/dev-wave-jobs/t787-freeze-crlf/stage2-plan.md:150>)）。

例えば次の弱実装は、計画中の全テストを通り得ます。

```python
if pointer.count("/") >= 2:
    # exact path の CR/LF 検査
```

root の `/path` を見落とします。`{"path":"x\\ralias"}` と LF の 2 node、可能なら `{"items":[{"path":"x\\ralias"}]}` も追加すべきです。

影響: schema 検証をしない契約 hash の受理集合に root-level CR/LF path が残り、凍結台帳・proof chain に hash／protected hash が入ります。

### B2 — CR/LF の「最初の pointer」と走査順が固定されていない

計画は `first_crlf_pointer is None` で最初の pointer を保存しますが、テストは基本的に 1 fixture 1 path です（[stage2-plan.md:101](</work/1/SFC/tanab/dev-wave-jobs/t787-freeze-crlf/stage2-plan.md:101>)）。`earlier-path-cr/lf` は後続 NUL の優先順位だけを検査しており、CR/LF 同士の先後を検査していません（[stage2-plan.md:117](</work/1/SFC/tanab/dev-wave-jobs/t787-freeze-crlf/stage2-plan.md:117>)）。

次の変異は生き残ります。

```python
first_crlf_pointer = pointer  # None 判定を削除し、最後の CR/LF を採用
```

また `reversed(...)` を外して stack の走査順を逆転させても、単一注入テストと「後側 NUL」のテストだけなら通ります。最初と最後の path に同時に CR、同時に LF を入れ、最初の pointer を要求する 2 node を追加してください。

影響: 受理集合・hash は変わりませんが、D281 が固定する拒否 detail の pointer 参照と failure proof の帰属が変わります。これは診断契約上の nit 相当ですが、D281 違反です。

### B3 — non-string `path` の dict 境界が未検査

正例は list と number だけです（[stage2-plan.md:154](</work/1/SFC/tanab/dev-wave-jobs/t787-freeze-crlf/stage2-plan.md:154>)）。次の正例がありません。

```json
{"path": {"nested": "x\r︎alias"}}
```

`path` の値が dict のときだけ `is_path=True` を子へ伝播する弱実装は、list 正例を通しながらこの入力を誤拒否できます。dict 正例を exact hash で追加してください。独立計算値は `0ad0978c428b8983ea777c5248f9e8656f457f4c41753e4807d23cf98d0038a9` です。

影響: CR/LF を含む schema 非検証入力の受理集合が狭まり、従来 hash・protected hash・凍結可能集合が変わります。

### B4 — canonicalization 変異の fixture 形が未指定

現行順序は strict JSON → canonicalization → path scan です（[s8c_preregistration.py:329](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/campaign/s8c_preregistration.py:329>)、[s8c_preregistration.py:365](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/campaign/s8c_preregistration.py:365>)）。

CR/LF + lone surrogate の 2 node（[stage2-plan.md:140](</work/1/SFC/tanab/dev-wave-jobs/t787-freeze-crlf/stage2-plan.md:140>)）は、必ず次のような escaped raw bytes で作る必要があります。

```python
b'{"path":"x\\r\\ud800"}'
b'{"path":"x\\n\\ud800"}'
```

実際の CR/LF byte を JSON string に入れると `bad-json` で strict JSON gate に先取りされます。`json.dumps(..., ensure_ascii=False)` で lone surrogate を encode しても fixture 側で落ちます。

影響: helper-before-canonicalization 変異の kill が baseline の `bad-json`／fixture setup failure と混同され、`evidence-contract-json` から `evidence-contract-path-crlf` への `freeze_reason_code` 変更を証明できません。

## 2. 変異の帰属

`tools/mutation_harness.py` は expected node 集合と実際の失敗集合が完全一致しないと KILLED にしません（[tools/mutation_harness.py:1187](</work/1/SFC/tanab/izanagi/tools/mutation_harness.py:1187>)）。

| 変異 | 判定 |
|---|---|
| wave 前の NUL-only へ revert | 登録済み（[stage2-plan.md:173](</work/1/SFC/tanab/dev-wave-jobs/t787-freeze-crlf/stage2-plan.md:173>)、[stage2-plan.md:186](</work/1/SFC/tanab/dev-wave-jobs/t787-freeze-crlf/stage2-plan.md:186>)）。現状の 90 node は追加 node 分だけ再計算が必要 |
| CR 条件削除 / LF 条件削除 | 各 45 node で妥当 |
| `endswith` 化 | suffix 4 node は通るため、38×2 + interior 4 + malformed 6 = 86 node で妥当 |
| CR/LF 即時 raise | 「NUL check 後に raise」なら earlier-path 2 nodeだけ。「CR/LF を NUL より先に見る」なら same-node 4 nodeも落ちる。計画の「最低4 node」（[stage2-plan.md:119](</work/1/SFC/tanab/dev-wave-jobs/t787-freeze-crlf/stage2-plan.md:119>)）と mutation 表の2 node（[stage2-plan.md:176](</work/1/SFC/tanab/dev-wave-jobs/t787-freeze-crlf/stage2-plan.md:176>)）が不整合 |
| reason を NUL 語／統一語へ変更 | 新 branch の reason だけなら CR/LF 90 node。NUL reason まで統一する変異なら既存 NUL test・E2Eも expected nodes に必要。1 mutationに混ぜない |
| `is_path` 条件削除 | non-path 3 node + `not_path` + non-string-list の5 nodeで妥当 |
| 全 C0 拒否 | `other-path-control` 1 nodeで妥当 |
| 既知 schema 位置だけ検査 | malformed 6 nodeで妥当だが、root path追加後に更新 |
| canonicalization 前へ移動 | NUL 1 + CR/LF 2 node。ただし B4 の escaped raw が条件 |
| exact `path` string を無条件拒否 | current hash + VT positive の2 nodeで妥当 |
| detail を `repr(node)` に変更 | CR/LF 拒否 nodeの exact message assertionで妥当 |
| 最初の CR/LF を最後で上書き / stack 順逆転 | **未登録**。B2の複数 path testとmutationを追加すべき |
| root scalar pathをスキップ / `path` dict下へ誤伝播 | **未登録**。B1/B3の正負例とmutationを追加すべき |

影響: expected node の不足や変異の曖昧さを残すと、実際には防壁を破る変異が `MISMATCH`・`SURVIVED`・帰属不能になり、certified な mutation matrix と proof chain を成立させられません。

## 3. 既存資産との衝突

現行の受理側固定は、次の 1 件だけです。

- [test_s8c_preregistration_core.py:623](</work/1/SFC/tanab/izanagi/orchestrator/tests/test_s8c_preregistration_core.py:623>)  
  `test_evidence_contract_hash_accepts_non_nul_path_controls` の required/consumer × CR/LF 4 param。これは段 2 のとおり必ず拒否側へ反転が必要です。

衝突しない既存資産:

- `test_s8c_preregistration_predicates.py:193` は loader 層で CR/LF を拒否。
- `test_s8c_preregistration_predicates.py:279` は registry 層で invalid 扱い。
- `test_s8c_preregistration_core.py:1342` 以降は `read_blob_at` 層の CR/LF 拒否。
- 現行 evidence contract と g1 freeze record に CR/LF path はありません。

ただし T-739 の凍結成果物には旧受理 test node が残っています。

- `output/insights/2026-08-11_t739-freeze-nul/mutation-spec.json:158`
- `output/insights/2026-08-11_t739-freeze-nul/mutation-ledger.json:623`
- `output/insights/2026-08-11_t739-freeze-nul/verbatim/s2-plan.md:199`
- `output/insights/2026-08-11_t739-freeze-nul/verbatim/s3-lensB.md:13`
- `output/insights/2026-08-11_t739-freeze-nul/verbatim/s4-adjudication.md:90`
- `output/insights/2026-08-11_t739-freeze-nul/verbatim/s5-impl-out.md:59`

これらは歴史資料なので編集してはいけません。T-787 の mutation spec が T-739 の凍結成果物を実行対象にしないことを明示してください。

影響: 旧 test を現行 suite に残すと受入全走が赤になり、逆に T-739 の凍結資料を書き換えると過去 wave の ledger／proof chain の bytes と参照が変わります。

## 4. helper 再利用

- `_contract_path_cases` / `EVIDENCE_CONTRACT_PATH_CASES`（[test_s8c_preregistration_core.py:121](</work/1/SFC/tanab/izanagi/orchestrator/tests/test_s8c_preregistration_core.py:121>)–142）は NUL 前提なし。
- `_contract_with_selector_suffix`（[同:145](</work/1/SFC/tanab/izanagi/orchestrator/tests/test_s8c_preregistration_core.py:145>)–153）も NUL 前提なし。
- `_contract_with_path_suffix`（[同:156](</work/1/SFC/tanab/izanagi/orchestrator/tests/test_s8c_preregistration_core.py:156>)–173）も CR/LF に流用可能。
- `_contract_with_interior_path_nul`（[同:176](</work/1/SFC/tanab/izanagi/orchestrator/tests/test_s8c_preregistration_core.py:176>）–199）は `\x00` を hard-code しており、そのまま流用不可。
- `b"\\u0000" in raw` は NUL 専用 assertion（[同:564](</work/1/SFC/tanab/izanagi/orchestrator/tests/test_s8c_preregistration_core.py:564>)、[同:583](</work/1/SFC/tanab/izanagi/orchestrator/tests/test_s8c_preregistration_core.py:583>)）。CR/LF test にコピーしてはいけません。

影響: helper を誤流用するとテスト自体が赤になるか、CR/LF の escaped injection を検証できず mutation の帰属が弱まります。これは直接の受理集合変更ではないため nit 相当ですが、実装子への明記が必要です。

## 5. P1〜P3

- P1 の reason 分離は維持すべきです。NUL を `evidence-contract-path-nul` のままにし、CR/LF だけ新語にする方が既存診断契約と T-739 の参照を守れます。
- P2 は親 brief の `_assert_no_control_chars_in_contract_paths` より、段 2 が提案する `_assert_no_forbidden_control_chars_in_contract_paths` が正しいです。「全制御文字を拒否する」誤解を避けます。
- P3 の 38×2、`control + "alias"`、exact hash は妥当です。そこへ root path、non-string dict、複数 CR/LF、複数 NUL の少数高効率ケースを追加してください。
- 既存の 4 param 反転は重複していても、wave 前の受理固定を直接反転するため残す価値があります。

## 総括

- **NO-GO**。root-level path と pointer 順序の検出が不足。
- 複数 CR/LF、複数 NUL、non-string dict の正負例を追加する。
- canonicalization 変異は escaped raw JSON で fixture を作る。
- immediate-raise と reason-unification の mutation を分離する。
- T-739 凍結成果物は変更せず、T-787 の実行対象から除外する。
- pytest は未実施。