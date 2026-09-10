### 1. [must-fix] M03 は受理集合を変えず、診断 detail だけで kill される

**根拠 (file:line)**

M03 は status 閉集合 gate を無効化します（[mutation-spec.json:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/output/insights/2026-08-03_fold-rotation-copy/mutation-spec.json:41)）。テストは `docs/worklog.md` を symlink にし、対照 assert で実際の `T` を確認しています（[test_dev_waves_git_state.py:341](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_dev_waves_git_state.py:341)、[同:357](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_dev_waves_git_state.py:357)）。

しかし M03 後も `T docs/worklog.md` は `A` 相当の `else` へ入り、rotation regex に一致せず `added-path` で拒否されます（[git_state.py:763](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/git_state.py:763)、[同:778](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/git_state.py:778)）。テストが赤くなるのは `detail == "path-status"` が崩れるためだけです（[test_dev_waves_git_state.py:363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_dev_waves_git_state.py:363)）。

**失敗シナリオ**

M03 を注入すると、対照の `T` assert は通る一方、verifier は引き続き `ok=False, detail="added-path"` を返す。受理集合は拡大していないのに、expected node は診断文字列差だけで赤になる。

**成果物影響**

変異台帳の M03 が偽の `KILLED` となり、レポートと worklog が「M/D/A 閉集合をテストが固定した」と誤って参照する。certified 値は直ちに変わらないが、実効 gate の検出力証明が成立しない。

**推奨**

既存の valid rotation path を regular file として seed し、fold commit で symlink へ typechange する。そうすれば M03 後は rotation regex と minimum-shape を通って実際に受理され、単一理由の kill になる。

### 2. [must-fix] P01 は未登録の two-archive テストも診断差だけで赤くする

**根拠 (file:line)**

P01 は rotation regex の条件を無条件 `True` にします（[mutation-spec.json:154](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/output/insights/2026-08-03_fold-rotation-copy/mutation-spec.json:154)）。一方、two-archive テストは `detail == "archive-count"` を固定しています（[test_dev_waves_git_state.py:300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_dev_waves_git_state.py:300)、[同:319](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_dev_waves_git_state.py:319)）。

P01 下では最初の valid `A` が `added-path` で拒否され、`archive_adds > 1` へ到達しません（[git_state.py:778](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/git_state.py:778)、[同:781](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/git_state.py:781)）。mutation harness は failed node 集合と expected node 集合の完全一致を要求します（[mutation_harness.py:1191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/mutation_harness.py:1191)）。

**失敗シナリオ**

P01 を注入すると、登録済みの rotation 正例 2 本に加え、M04 用の two-archive 負例も `archive-count` から `added-path` への診断差で赤になる。P01 の failed node 集合は事前登録より 1 本多くなり `MISMATCH` になる。

**成果物影響**

変異 matrix の P01 値が期待した `KILLED` にならない。余分な node を後付けで kill に数えると、受理集合が元から拒否だった入力の診断差を検出力としてレポート・台帳へ誤記する。

**推奨**

P01 を、archive-count gate より後で `archive_adds == 1` の正例だけを拒否する変異へ再照準する。これなら two-archive 負例は従来どおり `archive-count` で止まり、正例 2 本だけが赤になる。

### 3. [must-fix] M01 の expected node 集合から実 land rotation テストが漏れている

**根拠 (file:line)**

M01 の expected node は command 契約テストと人工 C100 正例だけです（[mutation-spec.json:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/output/insights/2026-08-03_fold-rotation-copy/mutation-spec.json:8)）。

実 land テストの旧 entry は同一文字列を 90 回繰り返しています（[test_dev_wave_land.py:1648](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_dev_wave_land.py:1648)）。`_rotate_worklog` は最後の entry より前をそのまま archive bytes にします（[spool_fold.py:1341](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1341)）。静的に fixture と同じ regex 境界を計算すると、元 worklog 2,399 bytes 中 2,263 bytes、約 94.3% が archive になります。親実測でも 85% の同形入力は `-M -C` で `C084` です（[measurements.md:8](/home/SFC/tanab/.claude/jobs/3a897f63/tmp/wave-fold-rotation-copy/measurements.md:8)）。

M01 を戻すと land 内の shape 検査がこの `C` を `path-status` で拒否し（[dev_wave_land.py:1513](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_wave_land.py:1513)）、`landed` assert も赤になります（[test_dev_wave_land.py:1736](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_dev_wave_land.py:1736)）。

**失敗シナリオ**

M01 を注入して共通 mutation runner を走らせると、登録済み 2 node に加え `test_land_folds_rotation_inside_lock` も、実 fold commit が C 判定されて rollback するため赤になる。

**成果物影響**

M01 は failed node の過剰集合により `MISMATCH` となる。また実際の退行では valid rotation land が失敗し、canonical 試行台帳と「次の一手」の main 反映が止まる。

**推奨**

M01 の `expected_nodes` に `test_land_folds_rotation_inside_lock` を追加して再凍結する。この実 fixture を C 非検出になるよう弱めるべきではない。

### 4. [must-fix] 禁止 flag 検査は結合短縮形 `-zM/-zC/-zB` を見逃す

**根拠 (file:line)**

テストは各 token の先頭が `-M/-C/-B` 等かだけを検査します（[test_dev_waves_git_state.py:75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_dev_waves_git_state.py:75)、[同:82](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_dev_waves_git_state.py:82)）。Git が受理する結合短縮形 `-zM`、`-zC`、`-zB` はいずれも `-z` で始まるため、この検査を通過します。

Git 2.34.1 の read-only argv probe でも、`--no-renames` より後の `-zM` が rename detection を再度有効化することを確認した。pytest は実行していない。

**失敗シナリオ**

`commit-diff` を `..., "--no-renames", "-zM"` に変更する。`--no-renames` は存在し、`-zM` は現在の禁止 prefix のどれにも一致しないため両 assert を通るが、実際の Git は `-M` を有効化する。`-zC` なら valid rotation が再び C となる。

**成果物影響**

レポートと変異台帳が「移動検出 flag 不在」を証明したと誤記できる。`-zC` 回帰なら valid rotation の受理集合が縮小し、canonical 台帳の land が再停止する。

**推奨**

single-dash token 内の `M/C/B` も禁止するか、安全な短縮形を `-r/-m/-z` に限定する。少なくとも `--no-renames` の後ろへ `-zM` を加える変異を追加し、この抜けを固定する。

## 総括

Must-fix:

- M03 の typechange fixtureを valid rotation path へ移し、診断差ではなく受理集合変化で kill する。
- P01 を archive-count より後へ再照準し、two-archive 負例の偽赤を除く。
- M01 の expected node に実 land rotation テストを追加する。
- command 契約テストで結合短縮形 `-zM/-zC/-zB` を排除する。

Nit:

- なし。

本体の 2 ハンクは裁定どおりで、`_landed_fold_output_path` の R 分岐と `_diff_entries` の二 path parse は残っています。テストは 9 本純増で、既存テスト名・期待値・helper は変更されていません。M01〜M09・P01 の `old` はすべて対象実装にちょうど 1 回存在します。

C100 fixture の bytes 同一性、R/C の 2 レコード入力、two-archive fixture の README 非変更、`T` の対照生成、R 分岐の直接発火、および実 land テストが real `plan_fold`/`apply_fold`・lock・commit・shape 検査を通る構成自体には追加所見はありません。pytest は実行しておらず、緑は主張しません。