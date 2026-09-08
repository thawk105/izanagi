## 所見

1. submodule pointer の変更を隠して spec-only 判定を通せる

   - 主張: `_git_changed_paths` は `--ignore-submodules=none` を指定していない。`.gitmodules` または Git 設定が対象 submodule を `ignore=all` とした repository では gitlink の更新が差分から消える。具体例は、唯一の親 `C` から子 `H` で `spec.json` を追加すると同時に `vendor/db` の gitlink を `S1` から `S2` へ変更する入力である。コマンド出力が `b"spec.json\0"` だけになり、exact 比較を通る。Git 公式仕様でも `none` が ignore 設定を上書きし、`all` が submodule の全変更を隠すとされる。[Git `git-diff-tree` documentation](https://git-scm.com/docs/git-diff-tree)
   - file:line: [floor_pair_driver.py:612](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/campaign/floor_pair_driver.py:612)、[floor_pair_driver.py:1326](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/campaign/floor_pair_driver.py:1326)、通常ファイルしか攻撃していない [test_floor_pair_driver.py:515](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/tests/test_floor_pair_driver.py:515)
   - これが real なら成果物がどう変わるか: 非 spec tree が親と異なる `H` を loader が受理し、window・summary はその `H` を `loaded_head` として記録する。一方、`proof_limitations` は spec path 以外の tree 同値を保証すると記録するため、成果物の主張が偽になる。
   - 提案する対処: `diff-tree` に `--ignore-submodules=none` を明示し、模擬 Git の argv 期待値を更新する。`ignore=all` の下で spec と gitlink を同時変更する実 Git 負例により拒否を固定する。
   - real / refuted の自己判定: **real**

2. 全 bound blob 比較の存在を M06 test が固定していない

   - 主張: `test_blob_queries_use_the_once_resolved_loaded_head` は「観測された blob query が1件以上あり、その全件が `HEAD` OIDを使う」ことしか検査しない。具体的に [floor_pair_driver.py:668](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/campaign/floor_pair_driver.py:668) の calibration/build-receipt blob 比較を丸ごと削除しても、spec query が残るためこの test は緑になる。
   - file:line: [test_floor_pair_driver.py:842](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/tests/test_floor_pair_driver.py:842)、特に `assert blob_queries` と `all(...)` の [test_floor_pair_driver.py:862](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/tests/test_floor_pair_driver.py:862)
   - これが real なら成果物がどう変わるか: `H` の spec が receipt SHA `X` を宣言する一方、`H` の receipt blob は `Y`、dirty checkout の receipt は有効な `X`、という入力を当該変異が受理する。成果物は `loaded_head=H` を記録しながら、`H` に存在しない receipt bytes に基づいて生成され得る。
   - 提案する対処: 同 test で `HEAD:spec`、calibration、全一意 build receipt の exact query multiset を要求する。少なくとも一つの receipt について working-tree bytes と loaded-commit bytes を分ける負例も既存 test に組み込む。
   - real / refuted の自己判定: **real（test 防壁の欠落。現行実装自体の比較は正しい）**

## 破れなかった箇所

- 新しい二述語は恒真ではない。唯一親判定には「親が `(P,F)`、spec の `source_commit=P`、`P→M` の通常差分は spec のみ」という merge 反例があり、[test_floor_pair_driver.py:531](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/tests/test_floor_pair_driver.py:531) が拒否を通している。changed-path 判定には spec と `unexpected.txt` を同時追加する反例があり、[test_floor_pair_driver.py:515](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/tests/test_floor_pair_driver.py:515) が exact 性を通している。
- `loaded_head` は [floor_pair_driver.py:1249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/campaign/floor_pair_driver.py:1249) で一度だけ解決され、spec と calibration/receipt の現行 blob query はいずれもその OIDを使用している。`expected_sha256` と spec bytes 比較も緩んでいない。
- 親 parser は空行を root の `()`、複数親を複数要素として返し、loader の exact tuple 判定が双方を拒否する。path parser は空出力を `()` とし、非空出力には NUL 終端を要求している。
- rename は `--no-renames` により旧・新の2 pathとして現れ、非 spec の mode change も pathとして現れるため拒否される。spec path 自体の変更種別を区別しない点は、裁定の機械条件が change type ではなく path 集合の exact 一致として定義しているため、範囲超過とは判定しなかった。
- runtime status、finalizer header、proof-limit 文言、schema/exact key 集合は裁定どおりであり、既存負例の裁定外の削除・緩和は差分中に見つからなかった。

## 総括

real は2件で、うち1件は submodule pointer による実際の受理集合拡大であり修正必須。  
もう1件は、全 bound blob 比較を削除する変異でも緑になる test 防壁の欠落。  
それ以外の唯一親、通常 path 差分、OID束縛、runtime/finalizer の変更は裁定と一致した。  
レビューは read-only で行い、pytest は未実走。指定外参照は submodule 差分の判定に使った Git 公式仕様のみ。