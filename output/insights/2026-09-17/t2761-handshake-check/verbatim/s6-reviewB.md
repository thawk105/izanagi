## 所見一覧 (番号・real/refuted・must-fix/nit・scope 内/外・成果物影響・根拠 file:line)

**must-fix は見つかりませんでした。** 以下は静的レビュー結果です。pytest・変異 matrix・login probe の再実行はしていません。

参照略号：

- `T` = `orchestrator/tests/test_pegasus_dispatch_compute.py`
- `P` = `tools/pegasus/dispatch_compute.py`
- `G` = `/home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/make_mutation_spec.py`
- `L` = 同 directory の `login_probe_b4_b5.py`

| 番号 | 判定 | 重要度 | scope | 所見・成果物影響・根拠 |
|---|---|---|---|---|
| B-1 | refuted | nit | 内 | **anchor 不一致・誤帰属の疑いを否定。** test block、production の両 anchor は byte 一致で各1件。開始キー自体も1件。`OLD_CHECK` は旧 HEAD `38353207f` の2行と末尾改行まで一致。根拠: `G:25–64`、`T:2598–2636`、`P:871–892`。 |
| B-2 | refuted | nit | 内 | **P5・既存 assert が handshake 検査を先取りする疑いを否定。** B/B2/B3 は marker 名と `mv` の順序を保持し、needle の個数・終端条件を満たす。最初の拒否は `T:2635`。B3 の終端文字は `;` で、正規化後にも `; until …release…` が残る。根拠: `G:38–52`、`T:2596–2636`。 |
| B-3 | refuted | nit | 内 | **runner が待機・構文エラーで自壊する疑いを否定。** MARKER は使用前に定義済みで非空。B2 の gate も MARKER から代入済み。各 `until` は初回条件が真となり待機本体に入らない。Python AST と、f-string を展開した script の `bash -n` で構文を確認。根拠: `P:864–890`、`G:38–52`。 |
| B-4 | refuted | nit | 内 | **B4/B5 が対象検査を迂回する疑いを否定。** 対象関数は引数から文字列を生成・検査するだけで、fixture の副作用やディレクトリ実在に依存しない。B5 は `REPO=/__t2761__/release` を作り、needle 直後の `a` を P5 が拒否するため A-1 と同値。根拠: `T:2585–2636`、`L:19–57`。pytest の収集経路全体の証明ではない。 |
| B-5 | real | nit | 内 | **probe の終了コードだけでは成否判定できない。** B4/B5 の想定外結果も文字列に記録するだけで、非ゼロ終了しない。今回の保存ログは期待する拒否理由を明記しており証拠は有効。記録では終了コードでなく本文を根拠にする。追加 gate は求めない。根拠: `L:34–62`。 |
| B-6 | real | nit | 外 | **裁定パッケージ候補: `while` の同型偽赤は残る。** repo/submission path に `while` があれば元 script に対する最終 assert が拒否する。「path 非依存になった」という一般化は不可。根拠: `T:2636`。 |

## 変異 spec の検算表 (変異 × anchor 一意性 × 単一理由 × 期待 node)

C/R は新しい `repo-current` / `repo-release-path`、O は旧 HEAD の未パラメータ化 node。期待 node は**静的予測であり実測結果ではありません**。

| 変異 | anchor 一意性 | 単一理由・最初の拒否位置 | 期待 node |
|---|---|---|---|
| m0-comment | `PROD_ANCHOR` byte一致、1件 | comment の追加のみ。release・while・既存部分文字列検査に影響なし | SURVIVED `[]` |
| a-old-check | 新検査 block byte一致、1件。復元2行も旧 HEAD と一致 | R は旧 release assert で拒否。C の非失敗は実効 repo/tmp path に release がないことが条件 | KILLED `[R]`、probe で条件確認 |
| b-handshake | `PROD_ANCHOR` 1件 | P5 と既存先頭2 assert を通過し、release 候補行 assert で拒否 | KILLED `[C,R]` |
| ab-old-check-handshake | test / production 各1件、別 file | C は旧 release assert による handshake 検出。R は path と handshake の過剰決定で、単独証拠に数えない | KILLED `[C,R]` |
| b2-alias | `PROD_ANCHOR` 1件 | `RELEASE_FILE=…` と後続参照が候補行として残り、同じ release assert で拒否 | KILLED `[C,R]` |
| b3-same-line | `PROD_ANCHOR_B3` 1件 | MARKER needle 消費後の `; until …` が残る。P5 の許容終端 `;` を通過後、release assert で拒否 | KILLED `[C,R]` |
| 旧 arm b-handshake | 旧 HEAD でも `PROD_ANCHOR` byte一致、1件 | 旧 release assert で拒否。旧 baseline の path 条件は別途確認が必要 | KILLED `[O]` |

`{{` / `}}` の escape は new 側でも正しいです。展開結果は `${MARKER}.release` となり、B3 も `MARKER=…; until [[ … ]]; do sleep 1; done` という有効な Bash 構文です。M0/B/B2/B3 の各 production 変異について AST parse と `bash -n` が成功しました。script 自体は実行していません。

B/B2/B3 が証明するのは**静的な release 候補行の検出**です。即抜け条件を付けた変異なので、待機動作の検出証拠にはなりません。

## 波及と記録事項の検算

- **差分と scope:** snapshot patch と現物の `git diff` は byte 単位で一致しました。変更は T の1 file、46追加・3削除。`shlex` import、対象 test の入力追加、検査置換だけです。production・共有 helper・docs の変更はありません。`git diff --check` も成功しました。

- **他 caller:** 報告された直接 caller `T:1064,1117,2300,5383,5970,6162,6659` を確認しました。共有 helper の生成箇所 `T:4123,4185,5098` も一致し、consumer test 定義数はそれぞれ19・14・4件でした。

- **production 変異による余分な赤:** 対象 file の grep と caller の検査内容から、生成 script の全文比較・行数比較・`until` 不在検査は見つかりませんでした。他の script 検査は unset、環境変数、REPO、request hash、exec 等の部分文字列を対象にし、今回の注入箇所では変化しません。保存 script を検査する `T:6530–6538` も同様です。実測の完全集合は予定する file 全体の probe で確認してください。

- **node 数1→2:** 対象旧 node の稼働 allowlist/pin は検索で見つかりませんでした。duration ledger には旧 node の `0.001` が残ります（`orchestrator/tests/acceptance_duration_ledger.json:13320`）。新 C/R は未登録扱いで、それぞれ `1.0` の配分重みになるため、**shard 配分への影響はあります**。これは受入可否の gate ではありません（`tools/acceptance_shards.py:392–406`）。ledger 据置は裁定と一致します。

- **login probe:** script と spec 生成器は job directory にあり、repo 内に同名 file は見つかりませんでした。保存ログの B4 は `MARKER=<SUBMISSION>/compute-visible.release`、B5 は `not word-terminated` を示し、狙った拒否理由と一致します。直接呼出しは対象関数本体の検査に対する補助証拠として妥当です。

- **暫定防壁の撤去:** 他 test に生成 script/path の `release` 語不在を要求する検査は検索で見つかりませんでした。6値から環境由来部分を除く実装と合わせ、「着地後は wave 名に release を含めない暫定防壁が不要」と記録する根拠になります。ただし、**release 検査に限ることと、while の偽赤は残ることを併記すべきです**。

- **実測の区別:** 親の焦点走ログは `2 passed in 4.59s`、login probe ログは対照成功・B4/B5期待拒否を記録しています。本レビュー自身はそれらを再実行していません。変異 matrix と旧 arm の成功はまだ主張できません。

## 総括

静的レビューでは、実装・snapshot・裁定・変異 anchor は整合し、scope 内の must-fix はありません。予定された変異 probe → 本走へ進める状態です。

本走では A の実効 path と C の非失敗、B/B2/B3 の traceback、失敗 node の完全集合を確認してください。AB の R は冗長赤として扱い、記録では「release 偽赤の是正」と「while 偽赤の残存」を区別するのが適切です。