## must-fix

- 対象: [s5-diff.patch](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2227-noinline-meaning/s5-diff.patch:785)、[ruling-s4.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2227-noinline-meaning/ruling-s4.md:31)  
  何が問題か: plan v2 項目 6、7 の insight README、D1490 補遺、worklog fragment が差分に存在しない。  
  放置時の成果物影響: 対照値方式の決定根拠、非配線 driver、既受理成果物の走査範囲を指す正本参照が欠落する。  
  修正の向き: 親統合時に裁定どおりの記録だけを正本へ追加する。

## nit

- 対象: [test_condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2227-noinline-meaning/orchestrator/tests/test_condition_meaning_gate.py:827)  
  `.git` の入力は directory だけで、gitfile は直接検査していない。実装上は file が `file_names` 経路で symlink になるため成果物影響は見当たらない。
- 対象: [s5-author.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2227-noinline-meaning/artifacts/t2227-noinline-meaning/s5-author.md:75)  
  M3 の「要求 1 正例も殺す」は静的には過大申告。旧 shallow shadow が計装 header を operand にしても marker 観測自体は成立しうるため、確実な killer は inert 正例の owner-TU operand assert と shadow 構造 test。M3 自体は殺せるので成果物影響はない。

## 裁定との一致確認

- 依存 file の実読検査、新 reason code、その負例は追加されておらず、削除裁定どおり。
- `shared_branch_build` は `ROUTE_CMAKE_CXX_FLAGS` に限定され、cache route は別 build root のまま。
- 要求 1・既定 0 の供給 green、意味 green、admission true の実 fixture 正例がある。
- 深い鏡像は `followlinks=False` に加え `directory_names.remove()` で dir symlink と `.git` directory への降下を止める。
- `.git` file は通常 file として symlink、`.git` directory は symlink 化して非降下となる。
- 計装 header 以外の file は symlink、owner TU は shadow 側 symlinkを compile operand にする。
- quote include の `..` は shadow の実 directory 階層内で解決され、shadow-to-real の `-ffile-prefix-map` も維持される。
- 走査、作成の `OSError` と `RuntimeError` は `compile-time-branch-instrumentation-failed` に畳まれる。
- 既存 8 macro の `source_rel == owner_tu` 分岐は旧 shadow 作成と operand 差し替えを維持している。
- factory の 0/0 拡張は `BACKOFF_NOINLINE` 限定で、既存 8 macro は 1/0 限定のまま。
- `comparison` は要求 0 のときだけ `"1"`、既存 8 macro では従来の default `"0"`。
- evidence の `default` slot は NOINLINE 0/0 のみ define value `"1"`となり、validator の逆順受理も NOINLINE 限定。
- request 1 の供給済み control 0 を request 0 の meaning に渡す seam は request digest/value 不一致で `compile-command-drift` になる。
- `MeaningWitnessDeclaration` と `--meaning-case` は引き続き `BACKOFF_FIXED` 限定。
- A-2、s1、t1683 は factory に配線され、各 `BACKOFF_FIXED` legacy 上書きも維持される。
- 非配線 driver の記録と decisions、worklog、insight 記録は未実現。

## 総括

- 新しく green になりうる runtime-meaning record は NOINLINE の 0/0 と 1/0 の二型だけ。
- 0/0 は要求 `(0,1)`・対照 `(1,1)`、1/0 は要求 `(1,1)`・既定 `(0,1)` の場合だけ green になる。
- 既存 8 macro に red または unestablished から green へ広がる入力はない。
- M1〜M10 は全て少なくとも一つの実在 test に殺され、実装を空にしても緑になる追加 test は見当たらない。
- M1、M3/M4、M5、M6 には複数の失敗点があり、冗長 gate として扱う必要がある。
- pytest は実行していない。静的検査と `git diff --check` のみで、コード面の must-fix は見当たらない。