## 総括

- 親確定済みの import 不全は再掲しない。
- 別の最重所見は、明示 K=3 が admission のローカル実行判定を迂回し、queue 不可時に実行可能だった受入まで child rc=16 にすること。
- 現在の production caller は acceptance だけだが、注入は caller 境界ではなく共通 launcher 内にあり、将来 caller には漏れる。
- 環境継承、成功時の受理集合、waiter SHA 束縛には、射影範囲内で別の破れを認めない。

## 所見

### 1. queue 不可時のローカル fallback を失う

- 重大度: **must-fix**
- 根拠:
  - D724 の経路として明示 K=3 が admission を迂回する: [s4-adjudication.md:63](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/dev-wave-jobs/dev-wave-t826-acceptance-closure-split/s4-adjudication.md:63>)
  - LOGIN なら child 環境へ無条件に明示値を足す: [tools/dev_wave_wait.py:817](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_wait.py:817>)、[tools/dev_wave_wait.py:844](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_wait.py:844>)
  - 実際に `qstat -Q preflight rc=1` で runner rc=16、pytest child 未起動となっている: [s5-author.md:28](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/dev-wave-jobs/dev-wave-t826-acceptance-closure-split/s5-author.md:28>)
  - child rc=16 は `acceptance-command` 失敗になる: [tools/dev_wave_wait.py:3829](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_wait.py:3829>)
  - 再試行できるのは、child 未起動かつ正規の `queue-wait-timeout` marker が一意にある場合だけ: [tools/dev_wave_wait.py:1121](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_wait.py:1121>)
- 失敗する具体シナリオ:
  1. Pegasus LOGIN、親環境に `IZANAGI_ACCEPTANCE_SHARDS` がない。
  2. login node のメモリ admission はローカル実行可能と判定できる。
  3. queue 停止、`qstat -Q` 失敗、または shard 解決時の queue preflight が利用不能。
  4. 変更前は admission によりローカル実行できたが、変更後は明示 `"3"` が強制 dispatch を選ぶ。
  5. dispatch 前の `ValueError` などで marker がなければ初回で terminal。正規の `queue-wait-timeout` marker が出ても最大二回で終了する。二回とも rc=16 の期待値は [test_dev_wave_wait.py:9625](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/orchestrator/tests/test_dev_wave_wait.py:9625>) にあり、最終結果は `rc=70, stage=acceptance-command, source_rc=16`。
- 成果物影響: pytest は一件も実行されず、acceptance receipt は公開されない。queue 待ち時間を目標外とする裁定とは別に、queue 自体が使えない局面で wave の受入閉包が不能になる。

### 2. caller 限定は現状成立するが構造では保証されない

- 重大度: **nit**
- 根拠:
  - production 参照は default effects 配線 [tools/dev_wave_wait.py:1559](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_wait.py:1559>) と acceptance 起動境界 [tools/dev_wave_wait.py:3796](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_wait.py:3796>) だけ。
  - ただし注入判定は acceptance call site ではなく `_default_launch_launcher` 内にある: [tools/dev_wave_wait.py:834](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_wait.py:834>)
- 失敗する具体シナリオ: 将来、別の経路が `_default_launch_launcher` を直接再利用すると、Pegasus LOGIN では caller の用途を識別せず K=3 が入る。追加テストはその新 caller を通らないので成功したままになる。
- 成果物影響: 現在の production caller では影響なし。将来の構造的漏出だけなので nit。

### 3. `except Exception` は恒久的な実装不全まで無音化する

- 重大度: **nit**
- 根拠: import、`current_site`、`is_pegasus_login` の全処理が一つの広い catch に入る: [tools/dev_wave_wait.py:822](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_wait.py:822>)
- 失敗する具体シナリオ: 既知の import 不全以外にも、API 名変更による `AttributeError`、返り値契約不整合による `TypeError`、site 検出内部の `OSError`、`UnicodeError`、`RuntimeError`、さらに `MemoryError` まで、すべて「非 LOGIN」と同じ無注入へ縮退する。receipt の環境射影にも shard 値は含まれないため、後から縮退を識別できない: [tools/dev_wave_wait.py:453](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_wait.py:453>)
- 成果物影響: 受理集合の誤受理は確認できないが、K=3 の性能契約が無音で失われ、receipt からも判別できない。運用上の site 検出失敗を旧挙動へ戻すこと自体は妥当だが、プログラム/API 不全まで同じ扱いにするのは広すぎる。

### 所見なしとした点

- `env=`:
  - `dict(os.environ)` は存在する key だけを複製するため unset は unset のまま、空文字も保持する。
  - 非 ASCII と surrogateescape を含む値も `os.environ` の通常の subprocess 変換経路を通る。
  - `env` は fd 継承を選ばず、`pass_fds=(outcome_write, completion_read)` の意味論も変えない。
  - 差は snapshot 作成後から `exec` までに別 thread が環境を変更した場合、その変更を child が見ないこと。該当する writer は射影内の起動経路にない。
- 受理集合:
  - 変更は runner argv、collection 引数、選択 node、除外、保留処理に触れていない。runner tail は引き続き固定: [tools/dev_wave_wait.py:803](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_wait.py:803>)
  - K=2/K=3 の実測でも collected 数と選択合計が一致している: [s4-adjudication.md:60](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/dev-wave-jobs/dev-wave-t826-acceptance-closure-split/s4-adjudication.md:60>)
  - したがって、runner が実行された場合の受理集合は不変。queue 不可時は集合変更ではなく、collection 前の到達不能。
- waiter bytes:
  - SHA は起動時に実 bytes から動的に計算される: [tools/dev_wave_wait.py:54](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_wait.py:54>)
  - tested tip blob と実行 bytes を受入前に比較する: [tools/dev_wave_wait.py:2181](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_wait.py:2181>)
  - receipt へ渡す SHA も動的値: [tools/dev_wave_wait.py:3747](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_wait.py:3747>)
  - projected test の `_WAITER_BYTES_SHA256` は合成 fixture であり、現行 file の固定 golden ではない。追加行に伴う固定 SHA 更新は不要。未 commit bytes で受入を起動すれば tip 不一致になるが、これは既存 pin の意図した拒否。

## 追加テストの検出力評価

1. `test_pegasus_login_acceptance_launcher_adds_three_shards_only` — **偽緑**
   - 通る正例署名: `env key absent ∧ current_site=PEGASUS_LOGIN ∧ is_pegasus_login=True` なら、`Popen.env == parent environment + {"IZANAGI_ACCEPTANCE_SHARDS":"3"}`。
   - 発火する負例署名: 注入削除、値 `"2"`/`"4"`、環境継承削除、site gate 恒偽で assertion failure。
   - production import を事前解決し、`current_site` と `Popen` を両方 stub するため、親確定済みの standalone 解決不全を検出しない。これは既知所見の検出力評価であり、新規所見としては再掲しない。

2. `test_non_pegasus_acceptance_launcher_does_not_inject_shards` — **有効**
   - 通る正例署名: `env key absent ∧ current_site=OTHER` で `Popen` に `env` がない。
   - 発火する負例署名: site gate 恒真、または OTHER にも注入すると `"env" not in kwargs` が失敗する。
   - 実 `current_site` 解決の統合検査ではないが、非 LOGIN 分岐の単体検出としては有効。

3. `test_acceptance_launcher_preserves_explicit_shard_request` — **有効**
   - 通る正例署名: 親に `IZANAGI_ACCEPTANCE_SHARDS=1` が存在すると site 解決前に短絡し、`Popen` は継承、親値も `"1"` のまま。
   - 発火する負例署名: presence guard 削除、既存値の `"3"` 上書き、常時 `env=` 指定で失敗する。
   - production の実経路も最初の membership 判定なので、site stub は結果に関与しない。

4. `test_acceptance_launcher_site_error_keeps_inherited_environment` — **有効**
   - 通る正例署名: `current_site()` が `RuntimeError` を送出しても launcher が一度起動され、`env` 指定なし。
   - 発火する負例署名: catch 削除、catch 範囲縮小で RuntimeError が外へ出る、例外時にも K=3 を注入する場合に失敗する。
   - ただし import/API 不全と運用上の site error を区別する検出力はない。

5. `test_acceptance_shards_are_not_injected_into_other_subprocess_paths` — **偽緑**
   - 通る正例署名: 選ばれた `_default_run` 三経路と `_default_run_unbounded` 一経路で、`env` がないか shard key を含まない。
   - 発火する負例署名: この四経路のいずれかへ注入を追加すると loop assertion が失敗する。
   - `_default_run_logged`、trusted blob Git、tip waiter SHA の `Popen` は未検査: [tools/dev_wave_wait.py:729](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_wait.py:729>)、[tools/dev_wave_wait.py:787](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_wait.py:787>)、[tools/dev_wave_wait.py:896](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_wait.py:896>)。将来の非 acceptance caller が `_default_launch_launcher` を使う変異も通るため、「other subprocess paths」全体の証明にはならない。

## 未確認事項

- 単独段の射影に `tools/run_tests.py` と shard resolver 実装が含まれないため、判定表および `_resolve_acceptance_shard_count` の `ValueError` 発生行は直接確認していない。queue 条件は s4 の D724 記述、s5 の `qstat -Q preflight rc=1` 実測、waiter 側の rc=16 処理から確定した。
- 射影外の consumer、golden、inventory は読んでいないため、repository 全体の固定 SHA 参照不存在までは保証しない。射影内には live file SHA の固定値はない。
- 指示どおり pytest は未実走。`git diff --check`、二つの変更 file の AST parse、結合文字検査のみ実施し、いずれも問題を検出しなかった。