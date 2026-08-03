静的レビューで must-fix 3 件、scope 外の裁定候補 1 件を確認した。

### 1. M03 は受理集合を変えず、診断文字列だけで偽 kill になる

**根拠 (file:line)**  
M03 は status 閉集合 gate を無効化する変異である ([mutation-spec.json:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/output/insights/2026-08-03_fold-rotation-copy/mutation-spec.json:41))。しかし対応テストは `docs/worklog.md` を symlink にして `T` を生成する ([test_dev_waves_git_state.py:341](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_dev_waves_git_state.py:341))。gate を消しても `T` は `else` へ落ち、rotation regex に一致せず `added-path` で拒否される ([git_state.py:763](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/git_state.py:763), [git_state.py:777](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/git_state.py:777))。

**失敗シナリオ**  
M03 適用後も `result.ok` は false のままで、detail だけ `path-status` から `added-path` へ変わる。テストは赤になるため matrix 上は KILLED になるが、受理集合は変化していない。

**成果物影響**  
変異 matrix が実在しない検出力を記録する。status gate が実際に失われた場合、正規 rotation path の `T` は受理され得て、daemon の受理集合へ symlink/gitlink archive が入り、台帳参照を壊す。

**推奨**  
親 commit に既存の正規 rotation path を regular file として置き、fold commit で symlink/gitlink に変える。M03 適用時にその commit が `result.ok` まで到達する単一理由 fixture に差し替える。

### 2. P01 の `expected_nodes` は必ず実失敗集合と不一致になる

**根拠 (file:line)**  
P01 は全 rotation path を `added-path` で拒否するが、期待 node は正例 2 本だけである ([mutation-spec.json:154](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/output/insights/2026-08-03_fold-rotation-copy/mutation-spec.json:154))。一方、2 archive 負例は `archive-count` を逐語期待する ([test_dev_waves_git_state.py:300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_dev_waves_git_state.py:300))。P01 では最初の archive で `added-path` になり、この負例も赤になる。mutation harness は失敗 node 集合の完全一致を要求する ([mutation_harness.py:1191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/mutation_harness.py:1191))。

**失敗シナリオ**  
同じ runner は M04 のため2 archive nodeも収集・実行する。P01 の実失敗は登録済み2本に2 archive nodeを加えた集合となり、KILLED ではなく MISMATCH になる。

さらに M01 実行時も land 正例は同じ runner に含まれる。land fixture は historic bytes が大半を占める高類似度構成 ([test_dev_wave_land.py:1648](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_dev_wave_land.py:1648)) で、親環境の Git 2.34.1 は85%移動を `C084` とした ([measurements.md:8](/home/SFC/tanab/.claude/jobs/3a897f63/tmp/wave-fold-rotation-copy/measurements.md:8))。M01 でこの node まで余分に赤になる可能性が高く、Git heuristic 依存の MISMATCH も残る。

**成果物影響**  
変異 matrix が P01 で受理不能となり、wave の監査済み集合を確定できず、台帳を伴う final land へ進めない。

**推奨**  
P01 の期待集合へ2 archive nodeを追加する。M01 は対象 Git で land nodeの挙動を実測し、失敗するなら期待集合へ加える。版依存を避けるなら、M01 の runner/fixture を deterministic な C100 経路へ限定する。

### 3. land 統合テストは実際の archive 到達性 gate を通っていない

**根拠 (file:line)**  
新規 land テストは candidate の `tools/check_docs.py` を `WORKLOG_ROTATE_BYTES = 900` だけのスクリプトへ置換している ([test_dev_wave_land.py:1656](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_dev_wave_land.py:1656))。land はその candidate checker を実行するため、常に rc=0 になる ([dev_wave_land.py:1363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_wave_land.py:1363))。実 checker の archive↔README 到達性検査は [check_docs.py:3307](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/check_docs.py:3307)。shape verifier 自身は `README変更 ⇒ archive 1件` しか要求せず、逆方向を検査しない ([git_state.py:783](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/git_state.py:783))。

**失敗シナリオ**  
rotation archive は生成するが README target を落とす退行を入れる。stub checker、staged path closure、shape verifierをすべて通り、このテストは landed になる。一方、実 repo の `check_docs.py` は未掲載 archive を拒否し、final land は rollback する。

**成果物影響**  
targeted acceptance が偽緑でも、実 land では worklog・archive・FOLDED receipt が main に残らず、試行台帳と「次の一手」の更新が欠落する。

**推奨**  
少なくとも post-land で `rotation_path` の basename が `docs/archive/README.md` に掲載され、worklog が閾値以下であることを検査する。可能なら実 checker を通す fixture にする。最終的な実 repo land は引き続き必須とする。

### 4. scope 外裁定候補: daemon recovery は fold bytes/mode に束縛されない

**根拠 (file:line)**  
shape verifier は `FoldPlan` との blob 照合を明示的に行わず ([git_state.py:708](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/git_state.py:708))、path/status/count だけで受理する。daemon recovery はこの結果を直接採用する ([daemon.py:1526](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/daemon.py:1526))。

**失敗シナリオ**  
fragment を rotation path へ移し、FOLDED と README を形式上変更する。`--no-renames` では `D fragment + A rotation` となり shape を満たすが、fragment が canonical worklogへ反映された証明にはならない。

**成果物影響**  
daemon の継続集合に、欠落・改変された試行台帳や archive 参照を持つ run が入る。certified 選択値は直ちには変わらないが、後続レポートの proof-chain と「次の一手」が誤る。

**推奨**  
本 wave では実装しない。既知の T-347 として、fold tree の mode/after-bytesを durable planへ束縛する案、または recovery に追加 attestation を要求する案を別裁定にする。

## 総括

Must-fix:

- M03 fixtureを実際に fail-open する rotation-path typechangeへ変更する。
- P01の期待失敗 node集合を修正し、M01の高類似度 land nodeも実測して固定する。
- land正例で archive のREADME到達性を検査する。

Scope 外裁定候補:

- T-347: fold commit treeのbytes/mode束縛、またはdaemon recoveryの追加attestation。

Nit:

- なし。

共有 helper、環境変数残留、固定tmp path、xdist下の同一path競合については新規差分由来の所見なし。現行 dry-runはREADMEとrotation archiveの両targetを持ち、path regex・staged closure上の静的 blockerも見つからなかった。pytestおよび自走runnerは実行しておらず、緑は主張しない。