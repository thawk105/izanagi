## 所見

1. `real` / `must-fix` — guard の repository 同一性判定を subdirectory で回避できる。

   根拠: [patchharness.py:272](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/campaign/patchharness.py:272) は working-tree root の `realpath` 完全一致だけで実共有 submodule を認識する。一方、`checkout()` は渡された任意のディレクトリをそのまま `git -C` の基点にする（[patchharness.py:315](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/campaign/patchharness.py:315)）。read-only probe では `external/ccbench` と `external/ccbench/include` の `--absolute-git-dir` / `--git-common-dir` が同一だった。したがって `base_dir=<実 ccbench>/include` は guard を通過した後、同じ common-dir に `worktree add/remove` する。相対表記と symlink は `realpath` で捕れるが、subdirectory、既存 linked-worktree、bind mount は捕れない。`--git-dir` 文字列は現 API の directory 引数としては直接使えない。

   影響: 未登録 node が直列鎖外で同じ common-dir を更新でき、`ccbench_pin`、source evidence、proof chain、受理集合が race 依存になる。

2. `refuted` / `nit` — 現行 caller に別 thread・別 process から `checkout()` する経路は確認できない。

   根拠: `checkout()` caller を `orchestrator/`・`tools/` に限定して追ったが、caller 群には `ThreadPoolExecutor`、`multiprocessing`、`asyncio.to_thread` 等との接続がない。実 canary は同一 pytest 実行 context から `prepare_cell()` を同期呼出しする（[s1_direct_comparison.py:529](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/campaign/s1_direct_comparison.py:529)）。通常の `asyncio.Task` は作成元の `ContextVar` context を複製するため、それ自体は直ちに抜け道ではない。thread と新規 interpreter process には伝播しないが、現在の実 caller は見つからなかった。

   影響: 現行の certified 選択結果・proof chain・受理集合は変わらない。将来 thread/process caller を追加する際の既知 gap である。

3. `refuted` / `nit` — `checkout()` 以外に、現行未登録 pytest node が common-dir を更新する経路は確認できない。

   根拠: `_worktree_paths()` は列挙のみ（[patchharness.py:287](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/campaign/patchharness.py:287)）。`_git()` の patchharness 外 caller はない。`revert_worktree()` は working tree を戻す writer、`applied()` は apply/revert writerだが、`_tree_lock` 下にあり（[patchharness.py:247](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/campaign/patchharness.py:247)）、確認した pytest caller は tmp worktree または monkeypatch 経路だった。従って現行の「linked-worktree 管理領域 writer」という系統 2 に限れば、所見 1 の path identity 欠陥を除いて `checkout()` が実経路である。ただし guard は「実共有 source の全 writer」を包括するものではない。

   影響: 現行値は変わらない。将来 `applied()` 等を実 submodule に直接使う pytest node を追加した場合は別途 guard 対象化が必要になる。

4. `refuted` / `nit` — `pytest_runtest_protocol` の import に growth-hold と同じ fallback は不要。

   根拠: import は conftest の module import 時でなく、実際の runtest protocol 内で遅延実行される（[conftest.py:434](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/conftest.py:434)）。ここで `orchestrator.campaign.patchharness` が import 不能なら test 全体が error となり、正しさ guard としては fail-closed である。既存 fallback は conftest だけを package path 無しで読む failure-digest probe 用である（[conftest.py:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/conftest.py:41）。その probe は runtest hook を呼ばない。

   影響: fallback を追加しなくても certified 選択結果・proof chain・受理集合は変わらない。むしろ import error の握り潰しは guard 不在を許す。

5. `real` / `nit` — fixture 閉包は現行系統 1・3を捕るが、autouse/function/root fixture の detector control がない。

   根拠: `names_closure` 自体は明示・transitive・autouse fixture を含むが、実装は `scope == "function"` または `baseid == ""` を無条件に除外する（[test_real_repo_serialization.py:402](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/test_real_repo_serialization.py:402)、[同:439](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/test_real_repo_serialization.py:439)）。現行系統 1 は function-scope の `freeze_env` が消えても、transitive closure に module-scope の `real_known_axes_doc` が残る（[test_s1_measurement_freeze.py:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/test_s1_measurement_freeze.py:43)、[同:63](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/test_s1_measurement_freeze.py:63)）。系統 3 の `benchmark_snapshots` も module scope である（[test_codex_reasoning_ab.py:275](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/test_codex_reasoning_ab.py:275)）。したがって現在の 2 系統は取れる。しかし将来、function-scope autouse fixture、または root conftest 由来で空 `baseid` の資源 fixture を追加すると検出されない。現 control は集約の `[:1]` 変異だけで（[test_real_repo_serialization.py:729](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/test_real_repo_serialization.py:729)）、scope/baseid/autouse edge を撃たない。これは段 4 R7 の未実装 matrix と一致する。

   影響: 現行 certified 値は不変だが、将来その形の fixture consumer が直列正本外でも検査が緑になり、受理集合が誤って広がる。

6. `refuted` / `nit` — positive control に `golden` を使うことは恒真化を生まない。

   根拠: control の直前に `configured == golden` を強制しており（[test_real_repo_serialization.py:706](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/test_real_repo_serialization.py:706)）、その後の `golden - {removed}` と `configured - {removed}` は同一集合になる。独立 oracle を control 入力に使う意味も保たれる。

   影響: certified 選択結果・proof chain・受理集合は変わらない。

7. `refuted` / `nit` — parametrize stamp と growth-hold property は干渉しない。

   根拠: canonical node は `originalname` を優先するため（[test_real_repo_serialization.py:449](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/test_real_repo_serialization.py:449)）、`test_m3_focus_artifact_directions` の 3 instance は同じ canonical node になり、それぞれに stamp がちょうど 1 個付く。監査も各 instance の stamp を exact 1 個要求する（[test_real_repo_serialization.py:763](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/test_real_repo_serialization.py:763)）。growth-hold は `growth_hold_*` という別 key だけを追加する（[conftest.py:411](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/conftest.py:411)。

   影響: certified 選択結果・proof chain・受理集合は変わらない。

8. `real` / `must-fix` — `source_digest` の paired snapshot が異なる Git repository を見る。

   根拠: `_tracked_status_paths()` だけが repository 指定環境を除去する（[source_digest.py:761](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/campaign/source_digest.py:761)）一方、その直後に組になる `_tracked_diff_sha256()` は親 env をそのまま継承する（[source_digest.py:808](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/campaign/source_digest.py:808)）。`resolve_evidence()` は両結果について clean/dirty の真偽しか突き合わせない（[source_digest.py:858](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/campaign/source_digest.py:858)）。例えば `GIT_DIR` / `GIT_WORK_TREE` が dirty な decoy repo を指すと、status は実 ccbench、diff hash は decoy から取得される。両方が non-clean なら boolean 整合検査を通り、`tracked_paths` と `tracked_diff_sha256` が別 repository の proof を構成する。新設テストは `_tracked_status_paths()` 単体しか呼ばない（[test_campaign.py:10238](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/test_campaign.py:10238)）。

   影響: `SourceEvidence.tracked_diff_sha256` と proof chain が実 source と異なる値で受理され、再照合の結果および受理集合が親 Git env に依存する。

9. `real` / `nit` — 除去リストは `t810_validator` より 1 個不足する。

   根拠: 新規 2 箇所は 6 変数だけを除去する（[source_digest.py:766](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/campaign/source_digest.py:766)、[repo_tree_util.py:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/repo_tree_util.py:23)）。参照実装はこれらに加えて `GIT_CEILING_DIRECTORIES` も除去する（[t810_validator.py:334](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/campaign/t810_validator.py:334)）。現在の consumer は repository root 自体を渡すため通常は `.git` をその場で発見し、現行結果への影響は確認できない。subdirectory を root とする将来 caller では親の ceiling により rc=128 の偽拒否になり得る。

   影響: 現行 certified 値は不変だが、将来の subdirectory caller では受理集合を不必要に縮める。

10. `refuted` / `nit` — 正本削除・既存 assert 緩和・裁定外実装はない。

   根拠: `REAL_REPO_SERIAL_NODES` は 43→65、追加22、削除0を AST literal 比較で確認した。対象差分 `5519f783..47ce274b` は指定7ファイルのみで、`test_codex_reasoning_ab.py` と `tools/codex_reasoning_ab.py` は未変更。新規 AST 固定点解析もない。R1 は22 node追加、R4は fixture 閉包と runtime guard、R5は2 status 箇所として実装されている。R2の sort 8 node、R3のAST解析、R7の runner/silo/autouse matrix 等は実装されていない。既存 assert の削除・skip・xfail化もない。

   影響: 所見1・8以外の裁定整合面では certified 選択結果・proof chain・受理集合は意図どおりである。

## fail-open の具体シナリオ

1. subdirectory 経由で runtime guard を迂回する。

   1. 正本外 pytest node で `_PYTEST_NODE=("test_new.py::test_new", False)` の状態にする。
   2. `base_dir=_default_ccbench_dir() + "/include"` を渡して `checkout(pin, base_dir=...)` を呼ぶ。
   3. `realpath(base) != realpath(default)` なので guard が return する。
   4. `git -C .../include worktree add` は親 repository を発見し、default と同じ common-dir を更新する。
   5. node は `real-repo` loadgroup 外のまま実共有管理領域へ書き込む。

2. status と diff を別 repository から合成する。

   1. 実 ccbench に allowlist 内の tracked 変更を置く。
   2. 別の dirty Git repo を用意し、親 env の `GIT_DIR` / `GIT_WORK_TREE` で指す。
   3. `resolve_evidence(..., ccbench_dir=<実 ccbench>)` を呼ぶ。
   4. `_tracked_status_paths()` は env を除去して実 ccbench の path を返す。
   5. `_tracked_diff_sha256()` は env を継承して decoy の diff hash を返す。
   6. 両方 non-clean なので clean/dirty 整合 assert は通り、異なる repository の path/hash 組が proof chain に入る。

3. 将来 autouse fixture を検出しない。

   1. function-scope の autouse fixture に実 submodule readerを追加する。
   2. 正本外の複数 node に自動適用させる。
   3. `names_closure` には載るが `scope == "function"` で除外される。
   4. `fixture_consumers`、`seeded`、`missing` のいずれにも現れず、親所見1とは別の理由で閉包検査が緑になる。

## must-fix の一覧

1. [patchharness.py:272](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/campaign/patchharness.py:272)

   path root の文字列比較ではなく Git repository identity を比較すること。候補と default の `git rev-parse --path-format=absolute --git-common-dir` を read-only・scrubbed env で解決し、canonical pathに加えて可能なら `(st_dev, st_ino)` を比較する。subdirectory、linked-worktree、bind mount 相当を同一と判定する positive control を追加し、解決不能は pytest context 内では fail-closed にする。

2. [source_digest.py:761](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/campaign/source_digest.py:761)、[同:808](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/campaign/source_digest.py:808)

   status と diff に同じ sanitised env helper を必ず渡すこと。`t810_validator` と揃えて `GIT_CEILING_DIRECTORIES` を含む7変数を除去し、`GIT_OPTIONAL_LOCKS=0` を固定する。回帰テストは `_tracked_status_paths()` 単体でなく paired `resolve_evidence()` 経路を踏み、status/diff の双方が同じ env を受けることと、decoy `GIT_DIR` で proof が混成されないことを固定する。

## 未確認のまま残した点

- 指示どおり pytest、受入全走、変異 matrix は実行していない。緑とは報告しない。
- `FixtureDef` の実 pytest version 上の shape は collection 実走していない。現行 fixture scope・依存関係はソースから確認した。
- bind mount と linked-worktree alias は実作成していない。実 submoduleへの書込みを避け、default root と既存 subdirectory が同一 common-dirを解決することだけ read-only で確認した。
- decoy repo を用いた `resolve_evidence()` の動的再現は read-only 制約のため行っていない。所見8は subprocess の env 配線と呼出順からの静的判定である。
- レビュー中に親工程が対象差分を `47ce274b` へ commitし、その後 local main を mergeした。対象 bytes は開始時の `git diff` と `5519f783..47ce274b` が同一であることを確認し、後続 merge の別差分はレビュー対象に含めていない。
- 調査回数は50回に達していない。Web検索は行っていない。

## 総括

親所見1とは別に、must-fix は2件ある。runtime guard は subdirectory という単純な同一-repository表現で回避でき、`source_digest` は statusだけを衛生化したため paired diff と別 repository の証拠を合成できる。現行 fixture 閉包と stamp は系統1・3およびparametrizeを正しく扱うが、function/root autouse fixture の将来 drift はR7どおり未防護である。