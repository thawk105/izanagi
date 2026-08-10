## 所見

### 1. exact-13 が production 契約に固定されていない

- **深刻度** = `must-fix`
- **根拠の file:line** = `orchestrator/preregistration/addendum_envelope.py:87-109`、`orchestrator/tests/test_t139_preregistration_binding.py:45-46,177-190`、`s4-adjudication.md:61-62`
- **失敗シナリオ** = future resolver が `require_exact_fields(blob, frozenset({"a01", …, "a12"}))` と呼ぶ、または `parse_addendum_fields()` だけを呼ぶ → `{a01..a12}` が通る。production には `{a01..a13}` の固定値がなく、固定はテスト定数だけである。
- **成果物影響 1 行** = `a13` の有意水準を欠く追補が受理され、certified 選択の判定基準と台帳の追補参照が変わる。

### 2. manifest を通さず合成でき、load-bearing 検査も任意呼出しである

- **深刻度** = `must-fix`
- **根拠の file:line** = `orchestrator/preregistration/__init__.py:8-20`、`orchestrator/preregistration/erratum.py:82-91,280-306`、`orchestrator/preregistration/blobref.py:72-115`、`erratum-core-s15.md:129-155`
- **失敗シナリオ** = 次 wave が caller または受領証由来の `core_ref` / `erratum_refs` をそのまま `compose_core()` に渡し、`require_sha256()` を呼ばない → approval manifest、`approval_fold_commit`、承認 blob identity、`composed_sha256` のいずれも読まずに `ComposedCore` が得られる。空の `erratum_refs=()` も拒否されない。
- **成果物影響 1 行** = 未承認の追補 A′・erratum を使った cluster が受理集合へ入り、certified 選択、レポートの preregistration 参照、受領証台帳が分岐する。

### 3. plural API が将来の exact-set を実際には合成できない

- **深刻度** = `must-fix`
- **根拠の file:line** = `orchestrator/preregistration/erratum.py:207-229,244-257,280-296`、`erratum-core-s15.md:136-149`
- **失敗シナリオ** = manifest の exact set が現行 §15 erratum と将来の core §7 erratum の2件になる → `compose_core(..., erratum_refs=(e15, e7))` は全 erratum に「operation 数2」「`a01`〜`a12` の対象行と一致」を課すため、正当な e7 を `OperationCountError` または `OccurrenceCountError` で拒否する。
- **成果物影響 1 行** = 承認済み exact set が解決不能となり、pilot と certified 選択の受理集合が不当に空のまま残る。

### 4. 追補 grammar が fenced code 内の文字列を見出しとして扱う

- **深刻度** = `must-fix`
- **根拠の file:line** = `orchestrator/preregistration/addendum_envelope.py:67-84`、`addendum-a-reissue.md:52-63`
- **失敗シナリオ** = `fields` 内の fenced code に `## fake-end` を置き、その後へ実見出し `### a14` を置く → line 73 が code 内の文字列で範囲を終了し、a14 を無視して exact-13 と誤受理する。逆に code 内の `### a13` だけで欠落 field を補うこともできる。
- **成果物影響 1 行** = 閉集合外 field または実体のない field が通り、受理追補の key 集合とレポート上の固定条件が変わる。

### 5. 既存の Git blob 解決を弱い形で再発明している

- **深刻度** = `must-fix`
- **根拠の file:line** = `orchestrator/preregistration/blobref.py:38-48,72-115`、`orchestrator/campaign/trial_registry.py:677-705,755-785`、`orchestrator/campaign/s8c_preregistration.py:86-104,938-978`
- **失敗シナリオ** = 40桁の tree object ID や symlink mode の path を `BlobRef.commit` として与える → `git cat-file blob <tree>:<path>` は bytes を返し得るため、「commit」として受理される。新実装には commit peel、tree entry mode、blob size、Git root、安全な履歴状態の検査もない。
- **成果物影響 1 行** = 受領証・台帳へ commit でない identity や不正 mode の blob 参照が記録され、再現参照と ancestry 証明が壊れる。

既存の `trial_registry` は commit object と tree entry mode を検査し、`s8c_preregistration` は commit peel・replace/graft/shallow・サイズ上限を扱う。private 関数の直接流用でなくても、共通の hardened primitive を抽出すべきである。

### 6. fail-closed テストが二つの失敗理由を一つの node に混ぜ、resolution を通っていない

- **深刻度** = `must-fix`
- **根拠の file:line** = `orchestrator/tests/test_t139_preregistration_binding.py:193-199`、`s4-adjudication.md:95-110`
- **失敗シナリオ** = future resolver が `BlobResolutionError` だけを捕捉して `{a01..a12}` へ fallback する → 現テストは低水準関数が直接例外を出すことしか見ないため緑のまま。さらに「fields 節なし」と「commit 不在」が同一 node で、変異の単一理由帰属もできない。
- **成果物影響 1 行** = 解決失敗時の fallback により受理集合が拡大しても mutation 台帳が kill を誤認し、certification 根拠が偽陽性になる。

M7/M8 の余剰・欠落、M6 の範囲限定は別 node になっている。M1 の1件/3件は同じ「件数≠2」理由なので混同ではない。

### 7. 「投入 gate ではない」の固定テストになっていない

- **深刻度** = `nit`
- **根拠の file:line** = `s4-adjudication.md:64-66`、`orchestrator/preregistration/__init__.py:1-6`、`orchestrator/tests/test_t139_preregistration_binding.py:217-225`
- **失敗シナリオ** = docstring の非-gate 宣言を削除しても、禁止された4名称を追加しない限りテストは通る。またファイル名は `binding` だが、テスト自身が `PreregBinding` の不在を確認している。
- **成果物影響 1 行** = 収集レポートや worklog が「binding/gate 検証済み」と誤参照するが、現時点の受理値自体は変わらない。

## 確認できた点

正例2本は合成 fixture ではなく、固定 commit の実 repo blob を読んでいる（`test_t139_preregistration_binding.py:29-44,201-213`）。この点は有効である。

半実装の記録リスク: `s5b-impl.md:1` の「実装は完了」とテストファイル名の `binding` を worklog に転記すると、同文書 `:24-28` で未実装と認める resolver・manifest・binding を含む「producer 実装済み」と読まれる。

テストは本レビューでは実行していない。親実測の **12 passed / rc=0** は前提として扱った。

## 総括

**NO-GO**。  
exact-13 と manifest 照合が必須経路になっておらず、将来の複数 erratum exact-set も正しく処理できない。  
12件の緑では、grammar の偽見出し・resolver fallback・API 誤用経路を閉じられていない。