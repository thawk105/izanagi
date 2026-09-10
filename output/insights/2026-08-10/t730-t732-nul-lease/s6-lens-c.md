指定4成果物はすべて読取済み。以下は静的検査のみで、テスト・変異は実走していない。

## 所見

### C1 — `_safe_path` の受理集合説明は、任意の `str` サブクラスまで含めると正確でない

主張: exact 化により、NUL や `__contains__` 偽装以外にも、`__len__`・`__eq__`・`__ne__` を偽装する `str` サブクラスの受理・拒否が変わりうる。

file:line: `orchestrator/campaign/s8c_preregistration_evidence.py:183`、`s4_ruling.md:57`、`s5_out.md:3`

成果物影響: production の唯一の caller は `_strict_json` 由来の exact `str` を渡すため、現行 certified 選択・proof chain・凍結台帳の値は変わらない。ただし「受理集合の縮小は2種だけ」という証明文を任意の Python object に拡張すると偽になる。

深刻度: should-fix

推奨: 保証を「NUL-free の exact `str` および JSON 契約入力では不変」と明記する。任意の `str` サブクラスも受理集合契約に含めるなら親裁定へ戻す。例えば安全な本文で `__len__` が 0 を返す subclass は旧実装で `contract-string`、新実装で受理となる。

実測なし。静的所見。

### C2 — H7/M5 は exact 化による検査を固定するが、「返り値も exact `str`」を固定していない

主張: H7 は拒否例だけなので `return` へ到達せず、検査には exact `text` を使いながら最後に元の subclass を返す変異は緑のまま残る。

file:line: `orchestrator/tests/test_s8c_preregistration_predicates.py:258`、`orchestrator/campaign/s8c_preregistration_evidence.py:190`、`:194`

成果物影響: 現行 JSON loader は exact `str` しか生成しないため現在の certified 選択・proof chain・凍結台帳は変わらない。ただし将来 subclass が到達すると、`_ConditionProbe.cache`・`refs` の key、`EvidenceRef.path` の equality/hash/sort が偽装可能になり、proof chain の参照 path が検査済み値と一致する保証が失われる。

深刻度: should-fix

推奨: NUL-free の hostile subclass を `_safe_path` に渡し、返り値について `type(result) is str` と内容一致を assert する正例を追加する。「検査は exact、返却だけ元 value」の変異も別途事前登録する。

実測なし。静的所見。

## 実装の静的確認

`read_blob_at` は `rendered` を一度だけ作り、`"".join((rendered,))` で exact `str` の `text` に固定している。同じ `text` が検査、`spec` 構築、git stdin に使われる。`__eq__`、`__hash__`、`__iter__`、`__getitem__`、`__len__`、`__str__`、`__format__` によって検査値と使用値を分離する経路は見つからなかった。NUL、CR、LF は git 呼出し前に拒否される。

`_safe_path` も str branch では exact 化後の値だけを検査・canonical 化・返却しており、実装自体は正しい。dataclass field、cache key、`EvidenceRef.path` には exact `str` が伝播する。semantic hash は元の canonical JSON bytes に基づくため、NUL-free の通常契約では hash 値も不変。

非 `str` の `else` は `_nonempty_string(value, where=where)` が必ず `contract-string` を送出するため、代入成功経路はない。冗長ではあるが、旧実装の reason と `where` は維持されており、迂回路ではない。

scope 外として残した `evidence_contract_sha256()` の凍結経路は依然 `load_contract_bytes()` を通らない。そのため NUL 契約を凍結台帳へ束縛できるが、発効時には loader が `evidence-contract-invalid` へ倒す。これは段4裁定どおり未変更。

## 新設テストの恒真性

すべて実測なし。

- `test_read_blob_at_rejects_nul_alias[trailing-nul]`: 層2の NUL 選言を外すと prefix blob が返って赤。恒真ではない。
- 同 `[embedded-nul]`: 同様に赤。独立した alias 形を固定している。
- predicate `[required-nul]`: 層1の NUL 選言を外すと契約が受理されて赤。
- predicate `[consumer-nul]`: consumer 側の別 caller を固定しており赤。
- predicate `[trailing-nul]`: strip の偶然拒否に依存せず、層1を外すと赤。
- `test_contract_loader_accepts_embedded_tab_path`: M3 の層1 C0 一般拒否だけで赤。
- `test_read_blob_at_accepts_embedded_tab_path`: M4 の層2 C0 一般拒否だけで赤。M3では赤くならないため、層1・層2を殺し分けられている。
- `test_safe_path_rejects_membership_spoofing_str_subclass`: M5 で赤。ただし C2 の exact-return 部分は固定しない。

## M1〜M5 の完全集合

登録された各変異そのものについては、登録漏れ・過剰登録を認めない。

| 変異 | 静的に赤となる完全集合 |
|---|---|
| M1 | predicates `test_contract_loader_rejects_embedded_path_control_chars[required-nul]`、同 `[consumer-nul]`、`test_contract_loader_reports_explicit_path_reason_for_trailing_controls[trailing-nul]` |
| M2 | core `test_read_blob_at_rejects_nul_alias[trailing-nul]`、同 `[embedded-nul]` |
| M3 | predicates `test_contract_loader_accepts_embedded_tab_path` のみ |
| M4 | core `test_read_blob_at_accepts_embedded_tab_path` のみ |
| M5 | predicates `test_safe_path_rejects_membership_spoofing_str_subclass` のみ |

ただし M1〜M5 全体では C2 の「exact 検査後に subclass を返す」退行を対象にしていない。

## 既存テストへの波及

実際の diff により赤くなると静的に予想される既存 node は 0 件。

既存 CR/LF node は同じ reason のまま拒否され、通常 path、PathLike の単一文字列化、`__format__` 偽装、現行契約 snapshot、candidate freeze 検査はいずれも NUL-free かつ既存の exact 化経路を使うため期待値は変わらない。

## 総括

**GO — must-fix 0 件。**

実装上の NUL 防壁は2層とも閉じている。統合前に、受理集合の説明の限定と exact-return 用テスト／変異の追加を should-fix として推奨する。