## 親差分の保持

両親の変更は失われていません。

- 親1（wave）→ `HEAD` の差分には、main 側の DW-O15 廃止がすべて反映されています。
  - `_OPERATION_NUMBERS` から O15 を除外
  - 条件15を `DW-M07` 専用に変更
  - fixture の範囲表記、operation 条件削除 mutation、19節の固定テストを追従
  - 該当箇所: [tools/check_docs.py:352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/tools/check_docs.py:352)、[test_check_docs.py:161](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/orchestrator/tests/test_check_docs.py:161)、[test_check_docs.py:4707](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/orchestrator/tests/test_check_docs.py:4707)

- 親2（main）→ `HEAD` の差分には、wave 側の admission 実装がすべて反映されています。
  - checker 本体807行、`main()` 呼び出し
  - `json` / `py_compile` import
  - admission 合成 fixture、補助関数、mutation テスト群、実 repo assertion
  - 該当箇所: [tools/check_docs.py:2270](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/tools/check_docs.py:2270)、[test_check_docs.py:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/orchestrator/tests/test_check_docs.py:47)

merge-base からの行数も両親の差分の和と一致しています。

| ファイル | wave 側 | main 側 | 合成結果 |
|---|---:|---:|---:|
| `tools/check_docs.py` | +807/-0 | +3/-2 | +810/-2 |
| `test_check_docs.py` | +815/-1 | +13/-7 | +828/-8 |

## 合成構造

静的な AST 検査では、両ファイルとも構文として解析できました。

- トップレベルの関数、class、定数・変数に重複定義なし
- import の重複なし
- admission が使用する `sys`、`Mapping`、`dataclass` は既存 import に存在
- テスト追加が使用する `json`、`py_compile` はそれぞれ一度だけ追加
- admission ブロックは `_check_dispatch_inventory()` の終了後から `_provenance_markdown_ambiguities()` の直前まで、独立したトップレベル定義として配置されています。別関数の内側への侵入はありません。

## `main()` の配線

呼び出しは次の順序で保持されています。

- command docs guard: [tools/check_docs.py:3979](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/tools/check_docs.py:3979)
- spool guard
- dispatch inventory
- admission docs guard: [tools/check_docs.py:3990](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/tools/check_docs.py:3990)
- backlog guard: [tools/check_docs.py:4079](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/tools/check_docs.py:4079)

main 側の O15 変更は既存 command docs guard の契約データ更新であり、独立した新規呼び出しを必要としません。その契約と wave 側 admission 呼び出しの双方が有効です。

## Admission 検査の保持

main 側の変更による無効化・迂回は見つかりませんでした。

- `_ADMISSION_PREFIX` 以下の定数、registry loader、表解析、README解析、fail-closed wrapper が連続して保持されています。
- runbook §7.0 の投影表は registry との集合完全一致を検査します。
- `unknown` 表は unknown entry と grandfather 警告を検査します。
- 実測表は `runbook §7.0 実測` evidence の path 集合を検査します。
- README 宣言表は path、site、class の整合を検査します。
- fenced command は宣言表および `admission-site` タグと結合され、`qsub-job-body` の実体も確認されます。
- O15 の operation 契約変更とは定数、入力ファイル、呼び出し経路のいずれも共有していません。

## 合成 fixture

fixture は両親の期待を同時に満たす構造です。

- admission registry、投影表、`unknown` 表、実測表の class/evidence/path が相互に一致しています。
- README 宣言表の4実体と fenced command の site タグが一致しています。
- grandfather 対象 `submit_silo_ladder_rung1.sh` は runbook の必須警告として保持されています。
- `_build_min_repo()` は command fixture の後に admission fixture を構築し、相互のファイルを上書きしません: [test_check_docs.py:694](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/orchestrator/tests/test_check_docs.py:694)
- main 側の fixture は operation 条件を19件として生成し、条件15を mutation の `DW-M07` として別途固定しています。
- admission mutation 群は runbook、README、registry を対象とし、main 側の `.claude/commands/dev-wave.md` mutation と衝突しません。

## 意味的に壊れている箇所

無し。

## 総括

**GO** — 対象2ファイルの統合結果を採用してよいと判断します。  
両親の差分は保持され、重複定義・hunk侵入・import不整合はありません。  
main 側の O15 契約変更と wave 側 admission 検査・fixture は相互に整合しています。  
これは静的検査のみの判断であり、テスト実走や実行結果の保証はしていません。