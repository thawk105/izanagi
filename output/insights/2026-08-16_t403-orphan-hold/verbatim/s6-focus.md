# must-fix 対応表

| must-fix | 判定 | コード・実測根拠 |
|---|---|---|
| 1. hold 書込み失敗の層 2 検出 | `partial` | receipt の署名は [mutation_harness.py:1370](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:1370) から抽出され、[mutation_harness.py:264](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:264) で停止条件になる。production 統合テスト [test_mutation_harness.py:893](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/orchestrator/tests/test_mutation_harness.py:893) は通り、M12 は 1/1 KILLED、M4 も当該テストを含む 4/4 KILLED。しかし dispatcher と harness が同じ hold path への書込みにともに失敗する場合、harness は error を返すだけで file を残さない [mutation_harness.py:255](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:255)。sidecar は書くが次回 resume の gate には使われないため未閉鎖。 |
| 2. qsub 結果未観測時の順序 | `closed` | qsub 前に unknown を武装 [dispatch_compute.py:1597](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1597)、例外時は hold を discovery より先に作る [dispatch_compute.py:1906](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1906)。M3 は 1/1 KILLED。SIGKILL と、active 経路で request ID discovery 中に再 signal が来る窓 [dispatch_compute.py:1935](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1935) は裁定どおり scope 外。 |
| 3. 元例外の保存 | `closed` | 元例外を捕捉し [mutation_harness.py:1872](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:1872)、origin／verification を併記して cause chain を維持する [mutation_harness.py:1907](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:1907)。停止記録への直列化は [mutation_harness.py:2421](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:2421)。専用テスト [test_mutation_harness.py:1065](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/orchestrator/tests/test_mutation_harness.py:1065) は焦点走で緑、M4 でも赤化。 |
| 4. 通常 ledger と停止記録の分離 | `closed` | sidecar path は [mutation_harness.py:2407](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:2407)、通常 ledger への参照だけを保存 [mutation_harness.py:2446](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:2446)。テストは通常 v4、別 sidecar、`partial_ledger` 不在を固定する [test_mutation_harness.py:878](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/orchestrator/tests/test_mutation_harness.py:878)。hold が実在する通常経路では resume 前提も表示される [mutation_worktree.py:1044](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_worktree.py:1044)。 |
| 5. 配線ごとの検出力 | `partial` | M10、M11、M12、M9b はすべて KILLED。4 consumer の `lstat` 判定不能テストも 1493 件の焦点走に含まれる。ただし裁定で維持・追加された M6 と P1a／P1b／P1d／P1e は台帳に無く、正例変異は P1c だけ。したがって 13/13 は実行した 13 本には完全だが、改訂事前登録全体の完遂ではない。 |
| 6. 既知赤の fixture 隔離 | `closed` | 2 事例は別 root になった [test_pegasus_dispatch_compute.py:2622](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/orchestrator/tests/test_pegasus_dispatch_compute.py:2622)。assert は維持され、親実測 1493 passed／0 failed で既知赤は解消。 |

`regressed` はない。

# land を止める所見

**停止所見: 二重の hold 書込み失敗後、orphan-stop sidecar が resume gate にならない。**

harness 側の create-only も失敗すると、`OrphanHoldStop` と sidecar は残るが hold file は存在しない [mutation_harness.py:255](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:255)。resume loader は通常 ledger しか検査せず [mutation_harness.py:2616](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:2616)、wrapper も file の存在だけで orphan を分類するため、`failure="orphan-hold"` を付けず通常の resume command を表示する [mutation_worktree.py:1167](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_worktree.py:1167)。

**成果物影響 1 行:** sidecar-only 停止後の `--resume` が受理集合へ入り、未解決の旧 job が同じ checkout を読み得る状態で通常 ledger を terminal まで進め、mutation record が参照する source bytes と実際に読まれた bytes の一致を失わせ得る。

sidecar を resume の fail-closed gate にするか、別の独立して永続な latch と明示的な解決証拠を設けるまで land を止めるべきである。

M6／P1a／P1b／P1d／P1e の未実走は裁定との差だが、現コードの成果物値が変わる具体的経路ではないため、上記コード欠陥とは別の検証 backlog とする。fan-out 上位 report の診断不足も値・受理集合を変えないので backlog のままでよい。

# 変異で裏取りできていない行

13 本が直接変異したのは M1、M2、M3、M10、M11、M4、M5、M12、M7、M8、M9、M9b、P1c である。次は直接変異されていない。

- dispatcher receipt から harness への field 投影 [mutation_harness.py:1400](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:1400) と infra receipt 表示 [dispatch_compute.py:1954](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1954)。M12 は下流 predicate だけを殺す。production 統合テストがあるため、単独では非阻止。
- hold を discovery より先に置く正確な順序 [dispatch_compute.py:1906](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1906)。M3 は unknown の武装自体を殺すだけ。直接テストと全走があるため非阻止。
- harness 自身の hold writer、その書込み失敗 branch [mutation_harness.py:215](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:215)、sidecar の resume 非配線。ここは上記 land 阻止所見。
- origin／verification field の収集・直列化 [mutation_harness.py:1872](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:1872)、[mutation_harness.py:2421](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:2421)。M4 は復元 gate を殺すだけだが、専用テストが実測済みなので非阻止。
- harness、worktree、acceptance の `lstat` `OSError` branch [mutation_harness.py:185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:185)、[mutation_worktree.py:616](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_worktree.py:616)、[check_acceptance_reds.py:383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/check_acceptance_reds.py:383)。M11 は dispatch 側だけ。各注入テストは緑なので非阻止だが、直接変異の裏取りはない。
- worktree の復旧案内と wrapper receipt の orphan 分類 [mutation_worktree.py:1044](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_worktree.py:1044)、[mutation_worktree.py:1167](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_worktree.py:1167)。hold 実在経路はテスト済みだが sidecar-only 経路が欠落。
- 改訂事前登録の M6、P1a、P1b、P1d、P1e。特に dispatch／worktree／acceptance detector の常時成立による過剰拒否は、通常テストはあるが mutation proof には含まれない。

# 主張の過大さ

- **latch と lock:** 元裁定、commit message、[dispatch_compute.py:985](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:985) と [dispatch_compute.py:1012](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1012) の docstring は正確。共有 lifecycle lock や完全排他は実装されていない。
- **signal 窓:** qsub 結果未観測 branch は改善されたが、SIGKILL と active branch の discovery 中再 signal は残る。commit message と裁定はこれを明記しており、過大主張ではない。
- **保護範囲:** 変更は `dispatch_compute`、mutation harness／worktree、acceptance checker に限定され、直接 submit script、`patchharness.py`、local runner は対象外。commit messageと裁定の範囲記述はおおむね正確。
- **過大な箇所:** commit の「4 層を fail-closed で止める」と fix 裁定の「層 2 が独立に塞ぐ」は、現 invocation については正しいが、二重書込み失敗後の resume まで含む保証としては強すぎる。
- 実装 docstring は各関数の局所的な挙動しか主張しておらず、それ自体に大きな過大主張はない。

# docs へ書くべき残り

未コミットの runbook 草案 [pegasus-runbook.md:1291](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/docs/pegasus-runbook.md:1291) は、lock ではないこと、解除順序、F47、sidecar、fan-out、signal 窓、scope 外を既に含む。残りは次の修正・追記である。

- 「見送られた job は孤児として残る」ではなく「残り得る」とする。qdel 非ゼロ・例外や dispatch timeout は false positive を許容する保守的署名である。
- sidecar-only 停止を解決するまで、「4 経路が fail-closed」「表示される resume は hold 解除後だけ有効」「wrapper receipt は常に `failure="orphan-hold"`」と断定しない。
- harness 生成 hold は `job_name=None` で、timeout 時は `request_id` と `submission_dir` も null になり得る [mutation_harness.py:224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:224)。receipt、attempt sidecar、submission inventory の参照順を追加する。
- 受入全走で hold が立った場合は acceptance receipt が発行されないことと、受入 lease の解放と probe／evidence cleanup は別であることを追記する。
- fan-out report は hold path、request ID、`hold_error` を上位へ転記せず、preserved container から辿る必要があるという診断上の限界を明記する。
- dispatcher と harness の hold 書込みがともに失敗した場合に sidecar の `reason.hold_error` を見ること、および修正後の sidecar 解決・削除手順を記載する。

## 総括

現状は **land 不可**。1493 passed と 13/13 KILLED は主要な gate と復元・廃棄防止を強く裏付けている。  
ただし同一 storage 原因で二度 hold 作成に失敗すると、sidecar-only 停止後の resume が機械的に拒否されない。  
must-fix 1 と 5 は `partial`、2・3・4・6 は `closed`、`regressed` はない。  
sidecar を次回 invocation の権威ある gate にしたうえで、その経路を変異または統合テストで固定してから land すべきである。