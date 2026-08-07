## 所見

### 1. 「6違反を報告」の受入判定は成立していない

- 仮判定: **real**
- 深刻度: **高**
- 根拠: 親が実測したのは「指定6件を含む7件」であり、[brief.md:18](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/brief.md:18) はこれを受入条件充足としている。一方、正本の条件は「既定の全走が6違反を実際に報告」である [worklog.md:2987](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/docs/worklog.md:2987)。裁定前の監査にも、6件とは別に `3f2c43d7580b` が既に観測された記録がある [README.md:82](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/output/insights/2026-08-07_red-test-audit/README.md:82)。
- 成果物または受理集合への影響: 「件数が厳密に6」が受理条件なら不合格である。確認できたのは「指定された6 SHA が結果集合の部分集合である」ことだけで、受理述語が静かに弱められている。
- 推奨対処: 段3では「指定6件の包含は確認済み、厳密な6件という条件は不成立」と訂正する。「6件だけ」か「指定6件すべてを含む」かをユーザーへ戻して裁定させる。

### 2. P1 のままでは本 wave の終了条件を満たせない

- 仮判定: **real**
- 深刻度: **致命的**
- 根拠: P1 と plan は、実装後も `3f2c43d7580b` を新規違反として残し、既定監査を rc=1 とする [brief.md:31](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/brief.md:31)、[plan.md:109](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:109)。しかし DW-O17 は commit 後の既定全履歴監査を必須とし、赤なら停止する [operations.md:89](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/docs/dev-wave/operations.md:89)、[core.md:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/docs/dev-wave/core.md:17)。`3f2c43d` に対する過去の例外は一回限りで、恒久緩和ではない [worklog.md:3021](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/docs/worklog.md:3021)。
- 成果物または受理集合への影響: 機構上は、既知6件と `3f2c43d` が分離されるので「既存分への混在」は改善する。しかし運用上は常時赤の原因が6件から1件へ減るだけで、将来の新規違反もその常時赤に再び紛れる。後者の論拠が強く、裁定目的を完遂したとは言えない。
- 推奨対処: 六件台帳の裁定自体は再審議せず維持するが、段5へは進まず、`3f2c43d` の扱いと本 wave の終了方法を追加裁定へ戻す。七件目を黙って台帳へ加えることや一般 waiver 化は不可。

### 3. 「T-300 が既定範囲計算を変えた」という退行説

- 仮判定: **refuted**
- 深刻度: **高**
- 根拠: 現在の既定範囲は policy commit から `HEAD` までの `--ancestry-path` である [check_ai_provenance.py:694](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:694)。この部分は `git blame` 上、初出 commit `50c1ef4e5078ba54e0d00cee18eb01ddb6c2149a` のままである。T-300 系の `97ed862fa45162c220ce4a19a7c7180f7860ff64`、`743aae5f81ae162f02a8812ff16dd217d90cc69a`、`661de100a8ac48adb0ca2d897aad6cdb66d4a4c3`、`498b191d22fb1a764bcafe9655ce90296e496383`、`4ede12998ca7beb83dc070c103dd3146e95b7f04` は範囲式を変更していない。読み取り専用の履歴比較でも、裁定期の `5f2dfaf4`、`8c09dbe5`、`cdde9035`、`b1c4019d`、`c9990bc2` では ancestry-path と素の範囲の集合数が一致し、checker blob も同一だった。
- 成果物または受理集合への影響: T-300 の範囲計算を本 wave で改修対象に加える根拠はない。加えれば裁定外の scope 拡張になる。
- 推奨対処: plan に範囲計算の修正を加えない。ただし、次の所見の実測経路問題まで「解消済み」とは扱わない。

### 4. 元の rc=0 観測を「再現しない」だけで閉じている

- 仮判定: **real**
- 深刻度: **高**
- 根拠: checker は既定走行と明示範囲で異なる dispatch operation key を使う [check_ai_provenance.py:1683](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:1683)。dispatch は commit snapshot ではなく要求中の live `repo_root` へ `chdir` して実行する [dispatch_compute.py:567](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/pegasus/dispatch_compute.py:567)。また `_git` は ambient `GIT_DIR` 等を除去しない [check_ai_provenance.py:212](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:212)。さらに、このリポジトリには `checker 2>&1 | tail ...; echo $?` が producer の失敗を rc=0 と誤認させた同型事故が記録されている [failures.md:787](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/docs/failures.md:787)、[failures.md:3478](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/docs/failures.md:3478)。裁定時の生コマンド、cwd、HEAD、環境、route、producer rc は保存されていない。
- 成果物または受理集合への影響: 範囲退行は否定できても、rc=0 が checker 本体、dispatch、別 checkout、または shell pipeline のどこで生じたかは未解決である。「同 wave で解消する対象はない」という親の結論は過剰。
- 推奨対処: 固定 HEAD・checker blob で、既定/明示範囲 × local/dispatch の行列を producer の standalone rc で比較する。元コマンドが復元できない場合は「退行 refuted、観測原因 unresolved」と記録し、再現なしを解消扱いしない。

### 5. stale 台帳エントリを新規違反にするのは未裁定の gate 拡張である

- 仮判定: **real**
- 深刻度: **中**
- 根拠: 案3の正本は「6 SHA の固定台帳、既知/新規の分離、rc は新規だけ」である [README.md:101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/output/insights/2026-08-07_red-test-audit/README.md:101)。plan はさらに、期待 finding が消えた場合に合成した `known-violation-stale` を新規違反として rc=1 にする [plan.md:30](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:30)、[plan.md:76](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:76)。
- 成果物または受理集合への影響: 実際の新規 provenance 違反がなくても台帳整合性だけで赤になるため、ユーザーが裁定した受理集合より狭くなる。防御的な仕様ではあるが、裁定済み仕様ではない。
- 推奨対処: 初回実装から stale-red を外すか、追加の fail-closed 不変条件として明示的に裁定を求める。

### 6. finding-kind の対応付けが実装可能な粒度まで定義されていない

- 仮判定: **real**
- 深刻度: **高**
- 根拠: plan は finding 文字列と同順の `normal_finding_kinds` を持たせるが [plan.md:16](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:16)、kind の割当を定義するのは missing agent と missing Codex author の二種だけである [plan.md:20](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:20)。現行監査は message、scope、CAB、waiver、implementation author の複数経路から finding を連結する [check_ai_provenance.py:816](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:816)。
- 成果物または受理集合への影響: 平行 tuple の長さ不一致、または同一 SHA に複数 finding がある場合の誤対応により、別種の新規違反を既知扱いするおそれがある。
- 推奨対処: 全 finding を単一の型付きレコードにし、台帳照合可能な二種以外には明示的な `None` を持たせる。長さ不変条件と「台帳 SHA に既知 finding と無関係 finding が同居する」回帰ケースを追加する。

### 7. 一般 allowlist・CLI/config 免除・correction/waiver 拡張の懸念

- 仮判定: **refuted**
- 深刻度: **高**
- 根拠: plan は checker 内部の固定定数に完全 SHA 六件を直接置き [plan.md:3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:3)、correction 後に限定照合する [plan.md:25](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:25)。設定ファイル、CLI 免除、一般 waiver、correction carrier の追加は計画されていない。これは「一般 allowlist・設定・CLI 免除へ拡張しない」という PR-C01 [correction.md:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/docs/provenance/correction.md:13) に抵触しない。
- 成果物または受理集合への影響: 六件限定という境界を守る限り、案3そのものを PR-C01 違反として退ける理由はない。
- 推奨対処: 内部固定六件という境界を維持し、七件目や将来分を correction、CLI、設定経由で吸収しない。

### 8. DW-G05 の「値は不変、変わるのは commit gate だけ」は広すぎる

- 仮判定: **real**
- 深刻度: **中**
- 根拠: brief は影響を commit gate acceptance のみに限定している [brief.md:37](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/brief.md:37)。certified 選択は raw selector 入力だけから決まり [s8b_selector_output.py:88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/campaign/s8b_selector_output.py:88)、材料レポートは checker の stdout/rc を消費しない [layer3_report.py:510](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/campaign/layer3_report.py:510)。試行台帳と proof chain も campaign lock、WAL、report hashes を記録する [trial_registry.py:1622](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/campaign/trial_registry.py:1622)、[layout.py:168](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/campaign/layout.py:168)。したがって研究成果物の値と参照は不変である。一方、checker は dev-wave の既定 check であり [cli.py:188](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/dev_waves/cli.py:188)、その rc は task-run ledger に記録される [task_run_check.py:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/task_run_check.py:52)。runner の警告も dispatch receipt の stderr tail/size を変える [dispatch_compute.py:1658](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/pegasus/dispatch_compute.py:1658)。
- 成果物または受理集合への影響: certified 選択、材料レポート、正式な試行台帳、proof chain は不変だが、開発 task-run の exit status と dispatch receipt/log は変わる。「commit gate だけ」は不正確。
- 推奨対処: DW-G05 を「研究成果物の値・参照は不変。開発 gate、task-run 観測値、dispatch stderr 記録は変化する」と修正する。

## 総括

現状の段2 plan は、そのまま段5へ進める状態ではない。  
最大の問題は、7件観測を「6件の受入条件充足」としたことと、実装後も既定監査が赤のままになることである。  
T-300 による範囲計算退行は履歴上 refuted だが、裁定時の rc=0 の発生経路は未解決である。  
六件固定台帳の裁定自体は有効であり、一般免除へ広げる理由はない。  
`3f2c43d`、受入条件の件数解釈、stale-red を追加裁定へ戻すべきである。pytest は実行しておらず、緑は主張しない。