## 直した内容

[classifier](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/campaign/condition_meaning_gate.py:2300) に左 token 境界検査を追加しました。

`index > 0` かつ直前 byte が `path_bytes` に含まれる場合は置換せず、従来の不一致時と同様に1 byteだけ写して進みます。非 inert 経路、理由コード、evidence schemaには手を加えていません。

## 追加したテスト

[test_inert_root_prefixed_by_path_byte_is_red](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2226-inert-root-diff/orchestrator/tests/test_condition_meaning_gate.py:735) を追加しました。

- requested/control双方に `__FILE__` 利用行を追加。
- それぞれ `"xyz<root>/include/backoff.hh"` を追加。
- `("red", "stock-inert-mismatch")` を要求。
- builtin pathの非空、`root_diff_replacement_count >= 1`、`root_diff_has_residual is True`を確認。
- 左境界検査を外すと通常リテラルも置換され、残差が消えてgreenになる構成です。

## 所見の対応表

| レビュー | 所見 | 状態 | 根拠 |
|---|---|---|---|
| A must-fix 1 | builtin provenanceへの束縛 | not-taken (裁定による) | 段6裁定1節により限界として維持。 |
| A must-fix 2 | root左境界 | partial | 実装と専用負例を追加済みだが、dispatcher障害で未実走。 |
| A must-fix 2 | 右境界・集合外byte後の接頭辞受理 | not-taken (裁定による) | 段6裁定は左境界だけを採用。 |
| A must-fix 2 | 末尾空成分・通常fileを跨ぐ`..` | not-taken (裁定による) | 実在する展開形を拒否し得るため不採用。 |
| A must-fix 2 | control側閉包member要求 | not-taken (裁定による) | 発火可能な独立入力を作れないため不採用。 |
| A must-fix 3 | semantic member、`@policy`、`probe.hh/../other.hh`負例 | not-taken (裁定による) | 対応述語を採らないため追加しない。 |
| A must-fix 4 | M1の単一理由性の記録訂正 | closed | 段6裁定4節で上流membership拒否から残差へ至る単一因果鎖として訂正済み。 |
| A 所見 | M7左境界変異の事前登録 | partial | 専用nodeを追加済みだが未実走。 |
| A 所見 | 同一位置再消費、ASCII decode、入れ子root | closed | 今回の変更は1 pass走査と既存decode処理を維持。 |
| A 所見 | 置換ゼロ・行数差・残差のfail-closed | closed | 既存条件と期待値を変更していない。 |
| A 所見 | red record digest/IDの変化 | not-taken (裁定による) | 実測evidence拡張に伴う既知のnitとして維持。 |
| A 所見 | build root由来の将来のfalse red | not-taken (裁定による) | 既存到達例がなく、段4裁定どおり対象外。 |
| B must-fix 1 | builtin provenanceの証明 | not-taken (裁定による) | compiler追加preprocess案を段6裁定が却下。 |
| B 所見 | 段4裁定4.1から4.3との一致 | closed | 今回は分類器の左境界とテストだけを変更し、順序・契約を維持。 |
| B 所見 | 空root検査がproductionで到達不能 | not-taken (裁定による) | 冗長なfail-closed検査として維持。 |
| B 所見 | A-2の6 inert arm到達性 | partial | 実際のbuiltin path直前は引用符であり静的には維持されるが、未実走。 |
| B 所見 | schemaとrecord整合 | closed | evidence key、validator、既存2 green reason契約は未変更。 |
| B 所見 | 共通driverへの波及 | closed | 共通evaluator上の受理集合を左境界分だけ狭める変更として局所化。 |
| B 所見 | T316固有validator | not-taken (裁定による) | 本waveのscope外として変更していない。 |
| B 所見 | 線形時間・メモリ費用 | closed | 定数時間の左隣byte検査だけを追加し、計算量は不変。 |
| B 所見 | red record digest/IDの変化 | not-taken (裁定による) | 既知のnitとして維持。 |
| A/B | 今回の変更による後退 | regressed | 該当所見なし。静的差分上の後退は確認されていない。 |

## 実走結果

- `git diff --check`: 成功。
- 実走を試みたnodeid:
  `orchestrator/tests/test_condition_meaning_gate.py::test_inert_root_prefixed_by_path_byte_is_red`
- 実行経路: `python3 tools/run_tests.py ... -q`
- 結果: `qstat -Q` preflightが`rc=1`、`child_started=false`、dispatcherが`rc=16`で終了。
- テスト本体は未実走です。指示どおり再投入していません。
- 段5の6ケースおよびファイル全体も未実走です。greenの申告はありません。

## 波及の静的列挙

- 所有外caller: `backoff_sweep`利用群、`s1_direct_comparison`、`screening_driver`、`silo_ladder_rung1`、`paper_story_a1_paired`、T1683、SS2PL study。
- 共有fixture: `orchestrator/tests/fixtures/`は未編集。
- 共有test support: `condition_gate_test_support.py`は未編集。
- consumer: certified selection、campaign raw material、trial ledgerは、新しい左境界拒否を共通evaluator経由で受けます。
- T316は新green reasonを許可しない既知状態のままです。
- 既存2 green reasonのevidence key集合、非 inert経路、静的fixture、docs、`external/ccbench`には変更なしです。

## 残した未了

- dispatcher障害のため、新設nodeidと既存inert関連6ケースの実走確認。
- 実装上の未了はありません。
- `git add`、commit、merge、stash、branch操作は行っていません。

## 総括

段6裁定で採用された左token境界とM7専用負例を、段5の未コミット変更へ追加しました。差分検査は通っていますが、テストは基盤障害で未実走のため、このfixは実装済み・未実走です。