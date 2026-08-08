### 所見 1: 既裁定の状態を逆転し、閉じた T-454 scope を再起票しようとしている
- 深刻度: blocker
- 対象: 親 brief の (P1)、段 2 §3「既裁定」、§5、総括の推奨 3
- 実測: 親 brief `s1-brief.md:40-46` は T-412 を「裁定待ち」、T-454 を「裁定済み・起票可」とする。一方、`docs/archive/worklog-phase3-0806-242-244.md:969-973` は T-412 を「前置は完了。剪定は 0 bytes」、`docs/archive/worklog-phase3-0806-256-261.md:845-866,1146-1152` は T-454 を「部分実施」「回収 0 bytes」「R1 待ち」と記録する。さらに `docs/archive/worklog-phase3-0806-270.md:393-400` で T-576 は単一経路化を終端、T-577 は「207 bytes 内の上位のみ採録し、残りは需要ごと閉じる」と裁定済みである。それでも `s2-plan.md:149-153` は「確定済み scope のまま起票」を推奨する。`docs/failures.md:3654-3669` の F154 は、まさに見送り済み機構を古いタスク記述から再起票した型である。
- なぜ壊れるか: 推論: 最新裁定を無視して旧 scope 全体を再起票すると、T-576/T-577 が閉じた機構まで裁定対象へ復活する。これは棚卸しではなく裁定の巻き戻しであり、P1 のタスク関係も一次資料と逆になる。
- 提案: 候補を殺す — 推奨 3 を削除し、T-412 は「剪定候補ゼロ確定」、T-454 は「部分実施後に T-576/T-577 で残余裁定済み」と再基準化する。

### 所見 2: 親の「repo 全体の意味検索」は jobs を一度も走査せず、狭い完全一致語を数えただけである
- 深刻度: major
- 対象: 親 `s1-evidence.md` 全体、段 2 §0・§2 の hit 数
- 実測: `firing_evidence.py:9-10` は `jobs` を定義するが、`TARGETS` (`:29-35`) に jobs はなく、その後も使わない。`:38-46` は case-sensitive な少数 regex を数え、読めないファイルを黙って skip する。実際の jobs には、親の O10 語彙にない「producer の書き出し面」「成功 attempt の staging」「sidecar」が `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/s4-adjudication.md:88-105,215-221` にあり、新 sidecar の列挙漏れを実際に是正している。O12 も「裁定文の誤り」「正しい射程」という別表現で `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t450-t412-preface/s6-adjudication.md:5-13` に発火している。過去の T-412 自身も `docs/archive/worklog-phase3-0804-163-164.md:325-328` で、文書検索だけでは「記録されたか」しか見ないと警告済みである。
- なぜ壊れるか: 推論: この hit 数でゼロを得ても、jobs、git 履歴、同義語、コマンド名による実発火は否定できない。段 2 は個別調査で O10/O12 を拾ったが、それは親実測の正しさを回復せず、数値表を裁定証拠に使えない。
- 提案: 条件を足す — hit 数を裁定根拠から外し、jobs と履歴を含む同義語・英語・コマンド名検索、および直接事例の確認を必須にする。silent skip も禁止する。

### 所見 3: `_OPERATION_NUMBERS` 閉包検査は節の存在検査であって、削除後の義務を代替しない
- 深刻度: major
- 対象: 親 `s1-evidence.md:55-59`、D94 条件 (iii)
- 実測: `tools/check_docs.py:425-466` は `_OPERATION_NUMBERS` から必須 H2 を作り、`:498-559` は段・条件 dispatch 集合を作る。実検査も `:3788-3807` の H2 件数と `:4033-4065` の集合一致である。親自身も `s1-evidence.md:57-59` で、節削除にはこれらの「同時更新」が必要と記録する。D94 `docs/decisions.md:4223-4226` の pin も外延・dispatch の固定であり、節本文が禁止する入力の拒否ではない。
- なぜ壊れるか: 推論: 節を削除し、定数・dispatch 表・pin を同時更新すれば構造検査は新しい外延へ追随する。削除前に義務違反だった操作を与えても、この checker には読む実成果物も拒否述語もない。これを条件 (iii) に数えると「削除した節が存在しないこと」を「義務が機械化されたこと」と取り違える恒真保証になる。
- 提案: 条件を足す — closure checker は「構造専用で条件 (iii) には不算入」と裁定パッケージへ明記し、削除後も同じ違反入力を拒否する独立検査だけを代替証拠にする。

### 所見 4: B1 は独立 oracle が必要だと認めながら、その oracle である規範 prose を削る自己矛盾である
- 深刻度: blocker
- 対象: 段 2 §3 B1、§4 の B1 同梱条件、総括の推奨 1
- 実測: 現行 `docs/dev-wave/operations.md:123-128` は fragment 0 件の no-op、`tracked/index/submodule dirt` と `incoming衝突untracked` の区別、handoff/Git-admin-bound worktree の書式不問 no-touch を明記する。縮約案 `s2-plan.md:86-90` はこれを「dirty/collision/no-touch拒否・postconditionは tool と test の機械契約」に畳み、`s2-plan.md:94-97` は「tool と test を同時に弱める変更には別の独立 oracle が必要」と自認する。`tools/check_docs.py:3962-4008` が検査するのは helper literal と path 件数だけである。実発火例として、F80 `docs/failures.md:2002-2031` は実装とテスト期待値の同時弱化、F81 `:2033-2045` は合成 fixture が実 repo の fold 不成立を検出できなかった事例、F82 `:2072-2100` は説明と実装の食い違いで正規 main 取り込みを禁止した事例、F98 `:2468-2491` は「全 untracked dirty」と正規運用の衝突を記録する。`tools/check_docs.py:165-167` は DW-S07 の安全義務を byte 目的で落とした同型前科を明記する。
- なぜ壊れるか: 推論: tool とそのテストは同じ変更で一緒に弱められるため、互いを独立 oracle にできない。削られる語は過去に実際に効いた受理集合の境界であり、単なる説明重複ではない。被覆は production helper と合成 unit test に限られ、親への事前指示、child prompt、hook、実 repo dogfooding、受入 receipt はその意味を固定しない。違反後に赤くするだけでは、作業者へ「どの dirt は拒否し、どの untracked は許すか」「どう復元するか」も教えない。
- 提案: 候補を殺す — B1 を 449 bytes 候補から外す。独立 oracle と実 repo smoke が先に成立し、no-op・dirt/collision・no-touch の正確な境界を prose に残せる場合だけ再提案する。

### 所見 5: dispatcher 39 行の移管は「唯一経路」と「段 9 でしか実行しない」を混同している
- 深刻度: blocker
- 対象: 親 brief の (P2)、段 2 §4 の `.claude/commands/dev-wave.md:39` 移管
- 実測: 現行 `.claude/commands/dev-wave.md:39` は「local main 取り込みは全条件成立時の共通段 9 operation だけ」と明示する。移管案 `s2-plan.md:106` は、この段 9 限定が `DW-S09:109-111` に既存だと主張する。しかし `docs/dev-wave/core.md:109-111` が持つのは、受入結果固定後に O23 を行うことと helper が「唯一の通常 land 経路」であることだけで、「段 9 以外では呼ばない」という禁止文ではない。`tools/dev_wave_land.py:77-94` の `LandRequest` に stage、段 1〜8 receipt、acceptance receipt はない。`tools/check_docs.py:430-435,3962-3988` も唯一経路 literal と文面順序しか固定しない。
- なぜ壊れるか: 推論: 唯一の helper を早期に呼ぶことは「唯一経路」違反ではない。形式上正しい SHA 群を渡せば helper/checker は「まだ段 9 ではない」を判定できず、入口の事前禁止を削った後は早期 local-main 更新を止める層が消える。親手順・child prompt・hook・CI・受入形のいずれにも stage token がない。
- 提案: 候補を殺す — 39 行移管を 42 行移管から切り離し、「全条件成立時の段 9 だけ」は入口へ残す。

### 所見 6: B2 の receipt には「登録集合」が存在せず、検査名が約束する invariant を観測できない
- 深刻度: major
- 対象: 段 2 §3 B2
- 実測: B2 `s2-plan.md:77` は candidate に file が増えたのに「登録集合が baseline のまま」を赤入力とする。ところが `tools/pegasus/collect_receipt.py:76-91` の manifest は directory 内の全 file を自動列挙し、final payload `:153-179` にあるのは観測された `staging_manifest` と `calibrator_attempt_manifest` だけで、期待集合・producer inventory・登録状態の field はない。既存検査 `orchestrator/tests/test_pegasus_tools.py:899-914` も manifest に `stage.log` が現れることしか見る。実例 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/s4-adjudication.md:215-221` では、prose inventory が新 sidecar を漏らしたまま collector はその file を自動的に manifest 化していた。
- なぜ壊れるか: 推論: candidate receipt から分かるのは「file が存在した」だけで、「登録済みか」は分からない。hard-coded baseline は test fixture であり実成果物の登録 field ではないため、fixture を同時更新すれば不整合を受理できる。被覆はこの collector の合成 fixture に限られ、親 brief、別 producer、child prompt、hook、実 run の事前棚卸しを覆わない。
- 提案: 別経路へ回す — producer が宣言する authoritative expected-output field を先に設計する。それまでは B2 を DW-O10 の代替候補と呼ばず、prose を維持する。

### 所見 7: B3 は `-m` 一綴りを塞ぐだけで、Write＋`git commit -F` 義務を強制しない
- 深刻度: major
- 対象: 段 2 §3 B3
- 実測: B3 `s2-plan.md:78` は protected path を含む `git commit -m` の拒否だけを提案し、同じ行で Codex hook 未配線と Write 実施を証明できないことを認める。現行 `hooks/guard_bash.py:141-147` は `commit` を許可 subcommand に含め、`:1646-1653` は event の `tool_input.command` だけを読む。既存 `orchestrator/tests/test_hooks.py:369-389` は protected path 入り `git commit -m` を許可例にしている。`hooks/guard_bash.py:39-45` と `hooks/README.md:15-24,86-90` は Codex、script、subprocess、IDE、cron、ユーザー端末が射程外だと明記する。
- なぜ壊れるか: 推論: 新しい負例が塞ぐのは Claude Bash PreToolUse の一綴りだけである。bare commit、`--no-edit`、`-C`、`--reuse-message` 等を `-F` へ強制せず、message file が Write 経由で作られたことも相関できない。unit test/CI は hook 関数の文字列判定を検査できても、各 commit の作成経路を受入 receipt として証明しない。
- 提案: 別経路へ回す — Claude hook の限定 hardening としてのみ扱う。全 commit form の affirmative `-F` 強制、Write event 相関、Codex parity が揃うまで DW-O04 の削除・縮約根拠にしない。

### 所見 8: P3 は「byte 指標の失効」を「経路 A 全体の価値喪失」へ誤一般化している
- 深刻度: major
- 対象: 親 brief の (P3)、段 2 §5
- 実測: 親 brief `s1-brief.md:82-84` と `s2-plan.md:132-135` は T-313 後に「経路 A 全体」が予算価値を失うとする。実際の T-313 裁定は `docs/archive/worklog-phase3-0803-138-139.md:376-385` で、総量 cap を外した後の歯止めとして「発火実績と機械検査での義務代替」による剪定を推奨している。続くユーザー裁定 `docs/archive/worklog-phase3-0803-140.md:3-9,67-71` はその述語を正式採用し、「合計上限を持たないが無制限には増えない」を経路 A に担わせている。
- なぜ壊れるか: 推論: T-313 後に失効するのは「解放 bytes」という評価単位だけであり、経路 A はむしろ garbage-control の必須機構になる。「価値を失う」とまとめると、予算効果のない棚卸しを後回しにし、T-313 が要求した陳腐化防止を消す方向へ誘導する。
- 提案: 条件を足す — 「予算 bytes の価値は失うが、剪定・増殖抑制の価値は T-313 の正規 gate として残る」と分離して記載する。

## 総括

blocker は **3 件**。この棚卸しを現状のまま裁定パッケージにするのは **NO-GO**。B1、dispatcher 39 行移管、T-454 再起票を除去し、一次裁定の状態と検索証拠を更新する必要がある。静的検査のみで、テストは実行していない。