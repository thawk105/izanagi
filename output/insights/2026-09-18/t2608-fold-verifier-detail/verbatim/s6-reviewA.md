## must-fix

0 件。現行の実 verifier が生成する例外について、受理・拒否集合を変える実装上の不具合は見つかりませんでした。

## should

実装への指摘なし。親資料の集計誤りを「親 brief / 裁定への所見」に記載します。

## nit

実装への指摘なし。裁定のテスト説明に軽微な不一致があります。

## 検証済み (問題なし)

1. **例外経路と import の扱い**

   (a) [spool_fold.py:3418](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2608-fold-verifier-detail/tools/spool_fold.py:3418)、同ファイル:3474、`git_state.py:15`、`schema.py:101`。
   (b) 現行経路では拒否判定は不変。構造的拒否の文面も差分で変更されていません。
   (c) `git_state` の相対 import `.schema` と追加された絶対 import は同じ `tools.dev_waves.schema` を指します。別名ロードや subclass を生成する経路は見つかりません。通常の subclass も `isinstance` に含まれます。verifier 内の OSError、subprocess 例外、`_validate_base` の ValueError、KeyboardInterrupt / SystemExit は従来の非 DevWavesError 分岐で TransactionError に包まれます。追加 import の ImportError / AttributeError も既存の「import できない」経路です。それ以外の import 時例外を包まない点も同じです。両分岐の `from exc` により cause は元の例外そのものです。
   (d) fix 不要（scope 内の確認）。任意に改変された例外属性まで JSON 化成功を保証するものではありませんが、現行 producer にその経路はありません。

2. **detail の表示と JSON**

   (a) `spool_fold.py:3477,3713`、`redaction.py:46,73,79,155`、`git_state.py:209,219,227`。
   (b) 現行 verifier の detail から path・URL・token・child bytes を新たに表示する経路や、stderr JSON を壊す経路は確認できません。
   (c) 到達する例外生成箇所を追うと、表示値は固定の診断語、allowlist operation、固定の label です。非 UTF-8 出力は本文を保持せず `non-utf8-output` 等になります。`return_code` は ERROR_DETAIL_ALLOWLIST にないため除外されます。`None` は `null`、自由文字列由来の detail は `byte_length` / `kind=detail-omitted` / `sha256` の dict として出ます。外側の `json.dumps({"error": str(exc), ...})` が内側 JSON の引用符をエスケープします。

   ただし、**sanitize 済みというだけで任意の値の秘匿や UTF-8 安全性まで保証されるわけではありません**。`_safe_string` は一般の path や孤立 surrogate を除去せず、認識する URL/token パターンにも範囲があります。本件で問題なしと判断できる根拠は、現行 producer がそれらを detail に入れないことです。
   (d) 本変更の fix 不要。sanitizer 自体の一般化は scope 外です。

3. **新テストは実 verifier の HEAD 失敗を検査している**

   (a) [test_spool_fold.py:2452](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2608-fold-verifier-detail/orchestrator/tests/test_spool_fold.py:2452)、同ファイル:48,181,385、`spool_fold.py:3396,3439,3459`、`git_state.py:1068`。
   (b) 先行検査で別理由の拒否を拾う構成ではなく、狙った例外表示を検査しています。
   (c) `_run_git` は任意の引数を subprocess に渡す helper で、`symbolic-ref` を妨げる allowlist はありません。HEAD 変更前に plan・commit・健全性確認を完了します。その後の先行検査は明示 SHA の rev-parse / cat-file / diff-tree / rev-list と hash-object で、HEAD を参照しません。verifier の最初の Git 操作が `head` です。失敗時の detail は sanitize 後に `{"kind":"head","label":"git"}` となります。cause の型と detail の assert も一致します。ただし、このテスト単体が cause のオブジェクト同一性まで pin するわけではなく、同一性は実装の `from exc` で確認しました。
   (d) fix 不要（scope 内）。

4. **M0 / M1 / M2 の静的な影響範囲**

   (a) `spool_fold.py:3474`、`test_spool_fold.py:181,385,2340,2366,2401,2429,2459`。
   (b) 登録された各変異の期待は静的には妥当です。M2 が既存の `_assert_declared_fold` 利用テストを赤にする根拠はありません。
   (c) M0 は定数 keyword 引数の順序交換なので等価です。M1 は従来の `"…invalid-run"` に戻るため、最初に helper:389 の末尾空白付き needle 照合で失敗します。detail assertion には到達しませんが、原因は診断追加の消失の一つです。M2 は新テストで helper:391 の「TransactionError を返さなかった」に到達します。既存の `_assert_declared_fold` は内側 verifier を直接呼び、変更対象の wrapper を通りません。既存の identity 拒否テストは wrapper の先行検査で拒否されます。
   (d) fix 不要（scope 内）。「新テストだけ赤」は静的予測であり、変異実走済みとは扱いません。

5. **consumer と登録簿**

   (a) `test_fold_gate_nodes_contract.py:59`、`dev_wave_land.py:235,5277,5343,5368,6383`、`spool_fold.py:3501,3526`。
   (b) 既存 consumer の文字列契約・rc 分岐・登録簿を壊す変更は確認できません。
   (c) tracked file 全体への `git grep -n -F 'declared fold verifier が失敗'` は、実装の2行と新テストの1行だけでした。新テストからのローカル helper 到達集合に `_copy_real_canonical_family` はなく、real reader 登録は不要です。land は message を `LandResult.reason` に格納しますが、rc は例外処理と rollback 状態で選び、message を parse しません。新規 fold 失敗では rc=26、保存済み fold の回復失敗では rc=27、finalize 失敗では rc=30 の既存経路です。reason は JSON serializer を通り、確認した経路に文字数制限はありません。
   (d) fix 不要（scope 内）。

## 親 brief / 裁定への所見

1. **should：22 箇所と16類の対応が誤っています**

   (a) [HANDOFF.md:17](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2608-fold-verifier-detail/HANDOFF.md:17)、[s4-ruling.md:17](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2608-fold-verifier-detail/s4-ruling.md:17)、`git_state.py:209,227`。
   (b) 放置すると、成果報告が診断の区別可能性を誤った数値で記録します。受理集合への影響はありません。
   (c) AST で `DevWavesError(ReasonCode.INVALID_RUN, ...)` を抽出し、detail の label / kind 式で集約した結果は以下です。

   | 集計対象 | 独立集計 |
   |---|---:|
   | INVALID_RUN 生成箇所 | 22 |
   | label / kind が両方リテラルの箇所 | 20 |
   | その定数ペアの種類 | 16 |
   | 動的ペアの生成箇所 | 2 |
   | 動的式を別テンプレートとして含めた種類 | 18 |
   | `git/timeout` | 3 |
   | `fold-diff/record` | 2 |
   | `fold-parents/record` | 2 |

   動的な2箇所は `("git", operation)` と `(label, "sha")` です。したがって16類は定数ペアだけの数であり、22箇所全体の実行時同値類ではありません。また、22箇所はファイル全体の数で、すべてがこの fold wrapper から到達するわけでもありません。
   (d) 最小 fix は「22箇所、定数ペア16種＋動的テンプレート2種」に訂正し、実行時の分類数と区別することです。実装2ファイルの scope 外、親資料の訂正です。

2. **nit：単一理由性の説明が実装と一致していません**

   (a) `s4-ruling.md:57`、`test_spool_fold.py:2466`。
   (b) 「message 文字列だけを assert」と残すと、テストが保証する範囲の説明が不正確になります。
   (c) 実装には message に加えて cause の型・detail の assert があります。M1 の実際の最初の失敗点は `_transaction_raises`:389 です。これらはM1の単一原因性を否定しません。
   (d) 「message と cause の型・detail を検査し、M1 は message の照合で失敗」に修正してください。実装 scope 外、裁定本文だけの訂正です。

## 総括

**GO。must-fix は0件。** 親資料に should 1件、nit 1件があります。

独立集計は **22箇所、定数ペア16種＋動的テンプレート2種＝式として18種**。重複数は **git/timeout ×3、fold-diff/record ×2、fold-parents/record ×2** で一致しました。

本レビューは静的検査のみです。提供された焦点走 log は PASS 168行、失敗行なし、末尾 `168 passed, 0 failed, 0 errors / rc=0` と整合しています。変異実走の結果は未検証です。
