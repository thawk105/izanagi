## 所見

### 1. 台帳 validator の型破損が rc=2 にならない

- 判定: **real / must-fix**
- 根拠: entry 自体の型は検査する一方、`commit` を文字列確認せず `re.fullmatch()` に渡し、`expected_finding_kind` も hashable 確認前に集合照合しています。[tools/check_ai_provenance.py:181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:181) 非文字列 SHA、非 hashable kind、非 iterable な台帳は `TypeError` になり、`main()` の捕捉対象外です。[tools/check_ai_provenance.py:1970](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:1970) D-3 は台帳破損を `RuntimeError` → rc=2 と定めています。[s4-adjudication.md:51](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s4-adjudication.md:51)
- 成果物または受理集合への影響: 台帳破損時の終了値が規定の rc=2 ではなく未捕捉例外の rc=1 となり、監査機構破損が「新規違反」と同じ値で receipt に残ります。
- 推奨対処: container、`commit`、kind の型を演算前に明示検査し、全 validator 失敗を `RuntimeError` に統一する。非文字列 SHA・非 hashable kind・非 iterable 台帳の rc=2 テストも追加する。

### 2. off-HEAD の部分 range で正常な既知 entry が stale になる

- 判定: **real / must-fix**
- 根拠: `--range` は任意 revision を列挙できますが、implementation policy epoch は range ではなく暗黙の現在の `HEAD` から取得します。[tools/check_ai_provenance.py:612](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:612) [tools/check_ai_provenance.py:798](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:798) `b0a076…` の `missing-codex-author` は epoch が対象 commit の祖先と判定された場合だけ生成されます。[tools/check_ai_provenance.py:929](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:929) 現在の `HEAD` が policy を含まない別 branch のとき `--range b0a076…^!` を監査すると、selected には台帳 SHA があるのに expected count が 0 となり、stale rc=2 です。[tools/check_ai_provenance.py:1062](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:1062)
- 成果物または受理集合への影響: 本来「既知のみ」で rc=0 の range が rc=2 となり、部分 range の受理集合が branch の現在位置によって不当に縮みます。
- 推奨対処: policy 適用判定を暗黙の `HEAD` ではなく各 selected commit の ancestry に結び付ける。HEAD と監査対象が別 lineage の end-to-end test を追加する。

### 3. D-5 の bounded-child 警告抑止が実装されていない

- 判定: **real / must-fix**
- 根拠: 警告は bounded marker の確認より前に無条件で出ます。[tools/run_tests.py:1652](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/run_tests.py:1652) [tools/run_tests.py:1677](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/run_tests.py:1677) 既存 marker は実在し、bounded 子へ設定されています。[tools/run_tests.py:1204](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/run_tests.py:1204) [tools/run_tests.py:1337](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/run_tests.py:1337) D-5 は marker がある再実行子では表示しないと明記しています。[s4-adjudication.md:59](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s4-adjudication.md:59) 追加テストは marker のない再帰 dispatch で二重表示を固定するだけです。[test_run_tests_preflight.py:301](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_run_tests_preflight.py:301)
- 成果物または受理集合への影響: 非受入の bounded local は receipt に警告 2 行、bounded OOM 後の marker なし compute fallback は最大 3 行となり、裁定した「1 行」の stderr-tail レポート値が変わります。
- 推奨対処: bounded marker を持つ子では警告を抑止し、marker なし dispatch 子の二重表示だけを許す。経路別の現在値は direct=1、bounded=2、dispatch=2、bounded→dispatch=3。marker ありの pin test を追加する。なお `_is_acceptance_run()`、pytest argv、rc、suite fingerprint 自体は差分で変更されていません。[tools/run_tests.py:504](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/run_tests.py:504)

### 4. PR-A02 の rc・stdout 契約が stale 実装と矛盾する

- 判定: **real / must-fix**
- 根拠: docs は「rc は新規だけで決まる」「既知は常に stdout」と断言しています。[docs/provenance/audit.md:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/docs/provenance/audit.md:23) 実装では stale が新規 0 件でも例外となり、`HistoryAudit` を返す前に中断します。[tools/check_ai_provenance.py:1082](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:1082) `main()` は stderr の実行不能行と rc=2 だけを返すため、既に照合済みの known 一覧も stdout に出ません。[tools/check_ai_provenance.py:1970](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:1970)
- 成果物または受理集合への影響: docs 上は新規 0 → rc=0・known 公開ですが、selected-stale では実際は rc=2・known 出力なしとなり、文書化された受理値とレポート値が一致しません。
- 推奨対処: 「正常完了した rc=0/1 監査では新規だけで決定」と限定し、台帳破損・stale は整合性 rc=2 で known 一覧を出さない場合があると明記する。

### 5. PR-A02 は既裁定の default-range 盲点を引き続き全範囲保証として記述する

- 判定: **real / nit（今回の裁定で scope 外）**
- 根拠: docs は導入 commit から `HEAD` までを検査するとしていますが、既定列挙は `--ancestry-path` です。[docs/provenance/audit.md:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/docs/provenance/audit.md:15) [tools/check_ai_provenance.py:801](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:801) policy 導入前 fork 上の commit を後から merge すると、その commit は落ちます。この穴は段 4 でも real・scope 外と裁定済みです。[s4-adjudication.md:25](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s4-adjudication.md:25)
- 成果物または受理集合への影響: 将来この形の branch に新規違反があると、違反数 1・rc=1 であるべき既定監査が違反数 0・rc=0 になり得ます。
- 推奨対処: range ロジックは今回変更せず、少なくとも PR-A02 を ancestry-path の実際の保証へ限定し、裁定パッケージの未解決事項であることを記す。

### 6. 文字列 kind 判定から新規 finding が既知へ吸収される攻撃は成立しない

- 判定: **refuted / nit**
- 根拠: `label` は一度生成され、同じ値を `validate_message()` と比較式へ渡しています。[tools/check_ai_provenance.py:894](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:894) [tools/check_ai_provenance.py:908](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:908) 欠落逐語が片側だけ変わると kind は `None` になり、finding は新規に残ったうえ stale rc=2 となるため fail-open しません。照合は full commit key と kind の連言で、同種 finding が複数なら最初の 1 件だけが既知になり、残りは新規へ落ちます。[tools/check_ai_provenance.py:1067](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:1067) correction の固定 target も現在の 6 entry とは異なります。[tools/check_ai_provenance.py:127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:127)
- 成果物または受理集合への影響: 受理集合の拡大はありません。逐語 drift や将来の correction/ledger 重複では、沈黙ではなく rc=2 の過剰拒否になります。
- 推奨対処: must-fix は不要。ただし文字列依存をなくすなら `validate_message()` の生成時点で構造化 kind を返す。また裁定が要求した correction/waiver composition test は追加する。[s4-adjudication.md:29](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s4-adjudication.md:29)

### 7. rc=0/1、公開位置、既知 0 件時の既存逐語の破壊は成立しない

- 判定: **refuted / nit**
- 根拠: message-file・merge/correction preflight では `known_violations` は空のままで、台帳 validator も呼びません。[tools/check_ai_provenance.py:1930](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:1930) history 正常完了では新規ありだけ rc=1、新規なしは rc=0 です。[tools/check_ai_provenance.py:1987](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:1987) known 行は rc=1 の最後、rc=0 の最終 summary 直前にあり、固定 6 entry は末尾 4 KiB 内です。[tools/check_ai_provenance.py:1996](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:1996) [tools/check_ai_provenance.py:2025](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:2025) known が空なら loop は無出力、qualifier も空なので従来の `件中 N 違反`・`件、違反なし`・waiver 行は逐語不変です。
- 成果物または受理集合への影響: 所見 1・2・4 の rc=2 問題を除けば、既存受理集合・既存逐語・stdout 公開値への追加影響はありません。
- 推奨対処: 現行分岐は維持し、所見 1 の型破損ケースだけ rc=2 pin を補う。

### 8. pin test 内に production 値を読まない恒真 assertion がある

- 判定: **real / nit**
- 根拠: production tuple との exact equality を検査した後、`commits` を production tuple ではなくローカル fixture の `expected` から作っています。[test_check_ai_provenance.py:1356](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1356) したがって直後の集合一致と `3f2c43… not in commits` は fixture の逐語から自動的に真となり、独立した防壁ではありません。[test_check_ai_provenance.py:1358](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1358) D-10 自身も pin は裁定強制機構ではないとしています。[s4-adjudication.md:65](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s4-adjudication.md:65)
- 成果物または受理集合への影響: なし。先行する exact tuple equality が同じ drift を既に検出するため、現行 gate 値は変わりません。
- 推奨対処: 冗長 assertion を削除するか、独立検査を意図するなら production tuple から集合を導出する。ユーザー裁定の機械強制とは記述しない。

## 総括

- 静的結論は **must-fix 4 件**: validator の未捕捉型、off-HEAD stale、bounded-child 二重警告、PR-A02 の rc/stdout 契約です。
- full SHA・kind・1 finding の境界から、新規違反を既知へ過剰吸収する経路は確認できませんでした。
- default `--ancestry-path` の検出盲点は real ですが、今回の差分による退行ではなく段 4 で scope 外と裁定済みです。
- must-fix を解消するまで、この差分の commit は推奨しません。
- 制約どおり pytest は実行しておらず、提示された passed 件数・実測値を独立には再確認していません。