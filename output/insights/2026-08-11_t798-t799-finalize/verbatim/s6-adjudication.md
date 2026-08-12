# 段 6 裁定 — 敵対レビュー 2 本の所見

親が両レンズを独立に評価した結果。**「must-fix と書いてあるから採る」ことはしない。**

## must-fix (この wave で閉じる)

| ID | 判定 | 対応 |
|---|---|---|
| **A6-SOL-01** forged noop plan を `apply_fold` が無検査で受理 | **real / 本 wave が作った受理集合の拡大** | `apply_fold` は `status=="noop"` を名乗る plan について、`transaction_id` / `input_closure_sha256` が空文字、`targets` / `fragments` / `gc_paths` が空であることを検証し、違えば `TransactionError`。負例テストを足す |
| **LUNA-S6-ID-03(a)** author が `startswith` 比較 | **real** | author header を `FOLD_AUTHOR_IDENTITY + " " + <unix ts> <±hhmm>` の**厳密形**で照合する (timestamp があるため完全一致は不可だが、残余の形を正規表現で拘束する)。`... <任意の追記>` が通ってはならない |
| **A6-SOL-02** recovery の `wave_ref` gate が未テスト | **real** | `kind="land"` かつ `origin.wave_ref != 現 wave_ref` の state を拒否することを pin するテストを足す |
| **A6-SOL-03** commit identity 条件 4 が mode-only fixture で過剰決定 | **real** | path 集合の完全一致 / target の `A`・`M` status / new blob OID / GC の `D` status を**それぞれ単一理由で**落とす fixture を分けて足す |
| **A6-SOL-04** transaction ID payload の各項が未 pin | **real** | `gc_paths`・fragment 各 field・`projected_worklog_bytes`・`rotation_path`・target の path/before/after SHA を**state JSON 側で 1 項ずつ改変**して拒否されることを pin する (両辺を再計算する形にしない) |

## 不採用・格下げ (根拠を明記)

| ID | 親判定 | 根拠 |
|---|---|---|
| **LUNA-S6-NOOP-04** noop で canonical/FOLDED 検査を飛ばせる | **一部誤り** | `_discover` は noop 経路でも `FOLDED.md` の receipt を parse する (`tools/spool_fold.py:1189-1191`)。canonical を読まない点は **wave 前と同一**で回帰でない。main の canonical 妥当性は受入全走の `check_docs` が担う |
| **LUNA-S6-FIN-02** finalize の unlink 後から自動復旧できない | **real だが回帰でない → 裁定パッケージ** | 段 1 実測で**wave 前も同一の残骸** (state 無し・main=fold commit・再投入 rc=10) だった。閉じるには「state 無しの verified fold child を already-landed と認識する経路」が要り、それ自体が受理集合の拡大なので独立の裁定と敵対検証が要る |
| **LUNA-S6-RACE-01** state の ID 検査が CAS でない | **real だが改善済み → 裁定パッケージ** | wave 前の `_rollback_fold` は **ID を見ずに無条件 unlink** していた。ID 照合を足したので厳密に改善している。根本は standalone が land lock を取らないことで、既に裁定パッケージ項目 2 |
| **LUNA-S6-ID-03(b)** 同一 tree/author/message の手動 commit が通る | **real だが仕様 → 裁定パッケージ** | gate は content-addressed に「意図した tree か」を検査する設計であり、「誰が作ったか」は commit message へ transaction ID を入れない限り証明できない。`_FOLD_MESSAGE` の変更は段 4 で scope 外と裁定済み |
| **LUNA-S6-CLOSURE-06** resume preflight が外部巻き戻しを識別しない | **real だが原理的限界 → 裁定パッケージ** | resume では target が unstaged 変更されているのが正常なので、porcelain の厳密拒否は使えない。かつ**byte 単位で before と一致する外部復元は content では原理的に判別不能**。段 4 で既に限界として明記した |
| **LUNA-S6-RB-05** rollback 3 中断点が自動復旧不能 | **backlog** | 段 4 で `[T-800]/[T-801]` scope と裁定済み |
| **A6-SOL-05** land の `kind != "land"` 再検査が実 plan では恒真 | **nit・維持** | fake module / 壊れた interface に対する防御として残す。削除しても実 state の受理集合は変わらない |

## 段 3 所見の最終状態 (レンズ B の対応表への親の上書き)

LUNA-P5-01 = closed / LUNA-P5-02 = **must-fix 1 件を閉じれば closed** (author 厳密化) /
LUNA-RB-03 = partial (fsync は closed、残余は backlog) / LUNA-FIN-04 = partial (rollback 分離は
closed、終端冪等性は裁定パッケージ) / LUNA-RACE-05 = partial (ID 照合まで、直列化は裁定パッケージ) /
LUNA-CLOSURE-07 = partial (resume preflight は closed、原理的限界は明記) / LUNA-VERIFY-08 = closed。
