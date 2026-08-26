## 結論

実装は成立します。ただし高速化の根拠は「射影の量」ではなく、対象 path・識別子・呼出し候補を絞ったアンカー生成と、親の手作業・空転除去に置くべきです。

比較対象には次の交絡があります。

- stage6 は約 1.04 MB の diff 2 本と merged source 4 本を与え、広い4観点を監査させています。467.5 秒、28 call、raw token 約253万でした。
- t1726 は 4,137 bytes の prompt で、重複1 pathと疑い所3点を明示しています。319.9 秒、7 call、raw token 約34.7万でした。
- 両者は同じ `gpt-5.6-sol` / `xhigh` ですが、前者は `stage=consult`、後者は `stage=author` です。また監査面積が4 file対1 fileで異なります。

したがって「事前射影が厚いほど速い」という因果は支持されません。むしろ巨大な全文射影は入力費を増やしています。一方、「有用なアンカーが探索量を減らす」という仮説は整合的です。

## 前提の検証結果

### `--message-file` の発火条件

親の推測は、merge が索引へ載った後に限れば正しく、それ以前には誤りです。

[tools/check_ai_provenance.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-merge-audit-necessity/tools/check_ai_provenance.py:1667) の `_merge_preflight_parents()` は `MERGE_HEAD` 不在時に空 listを返します。続く `_message_file_paths()` は空 listなら通常の staged pathだけを返します。同処理は main の message-file 経路から呼ばれます。

現在の実測状態は `MERGE_HEAD` 不在、cached diff 空でした。この状態で `--message-file` を使っても、2 tip の重複や将来の合成結果は調べません。message形式は検査しますが、merge用の実装面 author gateは発火しません。

### 手作業射影の再現可能範囲

- `main-side-change.diff` と `wave-side-change.diff` は、baseと2 tipが分かれば決定的に再現できます。
- merged source 4本は、実際のmerge済みindexまたはmerge commitがあれば blobから再現できます。
- 2 tipだけでは、人間の競合解決を含む最終結果は一意に決まりません。さらに現環境の Git 2.34.1 は `git merge-tree --write-tree` を持たず、read-onlyで結果treeを作る経路もありません。
- よって最終監査の正本は `--index` モードとし、2 tipモードは事前プレビューに限定します。元のworktree・indexを変更する必要はありません。

### 既存関数のimport

直接import可能です。`main()` は [tools/check_ai_provenance.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-merge-audit-necessity/tools/check_ai_provenance.py:3189) のguard内にあり、import時にCLIは発火しません。

阻害要因は次の2点です。

- `REPO` が同 file 33行目でscript所在へ固定されるため、新toolは起動cwdからrepo rootを解決し、moduleの `REPO` をそのworktreeへ束縛する必要があります。
- `_combined_diff_paths()` は実在するmerge commitを要求するため、2 tipや未commit indexには使えません。

なお、親briefが述べる `sys.dont_write_bytecode` の処理は、現行 `check_ai_provenance.py` 冒頭にはありません。新tool側で、[tools/codex_worker_ledger.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-merge-audit-necessity/tools/codex_worker_ledger.py:31) と同様に、import中だけ `sys.dont_write_bytecode=True` とし、`finally` で元へ戻します。

## CLI契約

新規tool名は `tools/merge_audit_projection.py` とします。引数なしは、実運用で使う `--index` と同義にします。

| モード | 入力 | 用途 |
|---|---|---|
| `--index`、または引数なし | 現在の `HEAD`、`MERGE_HEAD`、index | commit前の最終射影。推奨経路 |
| `--tips WAVE MAIN` | 2 commitish | merge前のside差分・重複・各tipのASTプレビュー |
| `--merge-commit REV` | 2-parent merge commit | 着地済みまたはsnapshot commitのcombined diff検算 |

出力は標準出力だけに限定し、ファイルを作りません。

- `--format prompt`: 既定。監査子promptへ貼れるMarkdown
- `--format json`: `merge-audit-projection/v1` のcanonical JSON
- 両形式は同じ内部 `Projection` objectから描画し、別計算しません。

exit codeは次の意味にします。

- `0`: 宣言した母集合について完全な射影。AST parse失敗や手動面なし
- `1`: 有効な射影は出したが、tips-only、非Python、parse不能など必須手動監査が残る
- `2`: 引数、Git状態、参照、親数、内部不変条件の異常。信頼できる射影なし

`--path`、`--exclude`、件数だけを黙って切るoptionは設けません。

## path集合の算出

### 2 tip共通集合

1. `git merge-base --all WAVE MAIN` がexact 1件であることを確認します。複数なら再帰merge-baseを再実装せずrc=1とします。
2. [tools/check_ai_provenance.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-merge-audit-necessity/tools/check_ai_provenance.py:1586) の `_paths_changed_from(base, tip)` を両tipへ呼びます。
3. 同 file 1636行目の `_intersection_path_set()` で積集合を取り、1529行目の `_is_implementation_path()` で絞ります。

これを `side_overlap_implementation_paths` と呼びます。merged結果が両親双方と違う集合とは別物です。

### merge中index

1. 同 file 1667行目の `_merge_preflight_parents()` を直接呼び、exact 2親を要求します。
2. 1695行目の `_message_file_paths(parents)` を直接呼びます。
3. `_is_implementation_path()` で絞ったものを `canonical_preflight_paths` とします。

これが現在の `--message-file` gateと同じ権威です。未解決stage、unstaged差分、untracked fileがあれば、indexが最終commit予定を表していないためrc=2にします。

### merge commit

同 file 1642行目の `_commit_paths()` を呼びます。これは内部で1594行目の `_combined_diff_paths()` を使います。tool内にcombined diff判定を複製しません。

全Git subprocessへ `GIT_OPTIONAL_LOCKS=0` を渡し、`git show`、`diff`、`ls-tree`、`ls-files`、`cat-file`だけを使用します。worktree、index、ref、object databaseは変更しません。

## AST数え上げの射程

変更識別子の母集合は、両sideが変更した実装面Python pathの和集合です。module直下の次を識別子として扱います。

- function、async function、class
- assignment、annotated assignment
- importが束縛する名前

baseと各sideの `ast.dump(include_attributes=False)` を比較し、追加・削除・変更を区別します。

呼出し母集合は、選択した結果snapshotに存在する全実装面 `.py` blobです。indexモードならindexのstage 0 blob、tip/commitモードならtree blobを読みます。

報告名は「全呼出し」ではなく、次に限定します。

- 全Python母集合で静的に解決できた `ast.Call`
- `Name`、module import alias、`from ... import ... as ...` を解決したもの
- 同名methodなどを拾う保守的な末尾名候補
- 同名の非call参照を別欄に出し、first-class aliasやdynamic callの手動確認材料にする

非Pythonは次の扱いです。

- C/C++、shell、JSON、CMake、patch/diff: 実装面pathとside diffには含め、`manual_review_required`へ必ず載せる。call件数は出さない
- Markdown/RST: `_is_implementation_path()` が除外するため、`classifier_excluded_changed_paths` に母集合外として列挙する
- parse不能Python、非UTF-8、巨大blob、削除済みblob: 黙って落とさず個別に理由を出し、rc=1

JSONとpromptの両方に、実装面総数、Python候補数、parse成功数、非Python数、除外数、各pathを出します。`semantic_calls_complete` は常に `false` とし、Pythonの静的call候補だけを全件走査したことを別fieldで表します。

## 恒真化の防止

第一案、かつ最優先は「権威集合からrendererまで絞り込み口を作らない」ことです。

- canonical関数の戻り値、side集合、積集合、件数、NUL結合digestを一つの `Projection` に保持
- renderer直前に集合式と件数を再検証
- path filter optionを持たない
- human文とJSONを同一objectから生成
- `complete` が偽なら「他にない」という文を生成できない

第二案はAST被覆台帳のfail-closed化です。

- Python以外、parse失敗、blob上限超過をゼロ件へ畳まず手動監査行へ昇格
- 「呼出し0件」は全母集合のparseが完了した場合だけ出す
- dynamic/alias限界をschema fieldにし、注意書きだけにしない
- 手動行が1件でもあればrc=1

第一案はpathの過小報告を構造的に防ぐため、最も強い案です。第二案は言語被覆の偽装を防ぎますが、Pythonの意味的dispatchを完全に解決するものではありません。単なる注意文追加は採りません。

## テスト設計

新規 [orchestrator/tests/test_merge_audit_projection.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-merge-audit-necessity/orchestrator/tests/test_merge_audit_projection.py) に集約します。

追加する主なtestは次です。

- `test_tips_projection_uses_canonical_implementation_overlap`
- `test_index_projection_matches_message_file_path_authority`
- `test_merge_commit_projection_matches_combined_diff_authority`
- `test_renderer_cannot_drop_a_canonical_path_and_remain_complete`
- `test_non_python_and_unparseable_python_become_manual_review`
- `test_changed_identifier_calls_scan_the_whole_python_population`
- `test_import_alias_and_conservative_terminal_name_candidates_are_distinct`
- `test_json_and_prompt_share_one_projection`
- `test_projection_is_byte_deterministic`
- `test_projection_does_not_change_head_index_merge_head_or_status`
- `test_invalid_parent_count_and_missing_objects_return_rc2`

実repo回帰にはt1726の以下を使います。

- base `f4c2c5ded29d72d8f06bca66992a5ef5694fcb51`
- wave `1e1dfbd52c119cbaccfec72aeffd66bfc1397ee5`
- main `1f72b3043aca8fa183873ea3a59d13a8fe41db6b`

3 commitとも現在の `HEAD` 祖先であることを実測済みです。したがって到達不能objectの自動prune対象ではありません。回帰test内でもancestor性をassertし、履歴が書き換わった場合はskipせず失敗させます。期待重複は `orchestrator/tests/test_real_repo_serialization.py` のexact 1本です。

新規test fileには `_run()` と `if __name__ == "__main__"` の自走harnessを付けます。[docs/failures.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-merge-audit-necessity/docs/failures.md:1593) のF42、および `test_plain_runner_coverage.py` の契約によるものです。pytest専用allowlistには追加しません。

親が実走する集合は、新規test、`test_check_ai_provenance.py` の関連node、`test_plain_runner_coverage.py`、`test_check_docs.py` とし、すべて `tools/run_tests.py` 経由にします。

## file:line変更計画

- 新規 `tools/merge_audit_projection.py`

  - 1-45行: bytecode guard付きauthority import、定数、上限
  - 46-150行: immutableなprojection schema、Git blob/index reader
  - 151-245行: tips/index/merge-commitのcanonical path算出
  - 246-390行: top-level identifier比較、全Python母集合call走査
  - 391-480行: coverage検証、JSON/prompt renderer
  - 481-540行: argparse、exit code、`main()`

- 新規 `orchestrator/tests/test_merge_audit_projection.py`

  - 1-100行: import、synthetic Git repo helper
  - 101-330行: 3モードとauthority一致
  - 331-500行: AST射程、恒真化negative control、決定性
  - 501行以降: t1726 reachable-history回帰、自走harness

- `tools/check_ai_provenance.py`: 変更なし。私有関数を直接再利用し、受理集合を1 bitも変えません。

- [docs/decisions.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-merge-audit-necessity/docs/decisions.md:35356): 現在の末尾D1009後へ、実装時点の次番号、現在ならD1010を追加します。toolは監査判断の代替でないこと、3種のpath集合、ASTの部分被覆、rc=1の意味を固定します。

- [docs/dev-wave/operations.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-merge-audit-necessity/docs/dev-wave/operations.md:123): 現行1行を次へ置換します。

  `実装面path差はtools/merge_audit_projection.pyで射影しCodex authorへ。`

  Markdownではtool pathをcode表記にします。DW-O17節は現在974 bytesで、置換後は約995 bytesとなり、単節1,000 bytes上限内です。

## 最大の未解決点

Pegasus loginでの実行分類です。[tools/README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-merge-audit-necessity/tools/README.md:11) は新規scriptの分類を必須とし、`local-ok` の実測はユーザー端末の手番と定めています。全Python blobを走査するため、未測定のまま `local-ok` と記録できません。

実装前に入力上限とstreamingを固定したうえで、ユーザー実測により次を決める必要があります。

- `local-ok` なら `tools/pegasus/admission_registry.json` へ実測証拠付き登録
- `unknown` または `dispatch-required` なら、現状は専用dispatch経路がないため、stage 4で実行経路を裁定

架空の測定値でregistryを追加する案は採れません。

## 総括

計画の本体は、`tools/merge_audit_projection.py` をindex中心の3モードtoolとして新設し、既存provenance関数を直接再利用して、重複path、両side diff、変更識別子とPython AST call候補を決定的に出すことです。巨大なmerged file全文は既定出力にせず、母集合・除外・手動監査行を構造化して恒真化を防ぎます。

速度改善の因果は現物2件からは確定できません。確実な利得は、親の手作業射影と最初のprovenance空転をなくすことです。最大の未解決点は、Pegasus loginでこの新scriptを使うための実測済み実行分類です。