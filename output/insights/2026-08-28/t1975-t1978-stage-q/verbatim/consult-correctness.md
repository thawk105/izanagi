結論として、plan v1 はそのまま author へ渡せません。must-fix は2件です。特に D987 の比較対象は、現在の provisional 案では保証対象と一致しません。

## Must-fix

1. D987 の「最後の incorporated main 対 tested main」比較は、forward-main 取り込みによる runner 変化と同値ではありません。

Plan は最後の `incorporated_main_sha` の runner entry と receipt の `tested_main` を比較します。[plan-current.md:67](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1975-t1978-stage-q/plan-current.md:67)

しかし既存 topology は各 merge について次を既に保持しています。

- 取り込み前の main 境界 `prior_main_sha`
- 取り込んだ main `incorporated_main_sha`

定義は [dev_wave_land.py:501](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:501)、`prior_main_sha` は merge base から導出されます。[dev_wave_land.py:2115](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:2115) 複数段では次段の `prior_main_sha` と前段の incorporated main を一致させています。[dev_wave_land.py:2121](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:2121)

Plan が根拠にする「main 履歴の単調前進」は commit ancestry だけです。[dev_wave_land.py:2126](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:2126) runner 内容が単調であることは保証しません。

到達可能な差は次のとおりです。

- 過剰拒否: tested main の runner が `r0`、tested tip が `r1`。main が tested tip を取り込んだ後、runner を変えず別ファイルだけ変更して `S` へ進む。forward-main の実際の境界は `T:r1 -> S:r1` で runner 不変ですが、plan は `A:r0 != S:r1` として拒否します。brief の「forward-main は runner 不変なら受理」に反します。[brief.md:14](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1975-t1978-stage-q/brief.md:14)
- 過剰受理: 複数段 main が `r0 -> r1 -> r0` と変更、復元された場合、最後だけを `tested_main:r0` と比べる plan は受理します。各取り込みでの変更を D987 の対象とするなら拒否対象です。Plan はこの受理を明示しています。[plan-current.md:83](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1975-t1978-stage-q/plan-current.md:83)

D987 を文面どおり「取り込んだ main 側の変更」とするなら、各 `_ForwardMainMerge` の `prior_main_sha` と `incorporated_main_sha` の runner entry を比較すべきです。少なくとも次の2ケースを追加しない限り、既存の複数段正例 [test_dev_wave_land.py:6903](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/test_dev_wave_land.py:6903) は D987 の十分な proof になりません。

- `prior_main != tested_main` だが、その取り込み区間では runner 不変の正例
- runner を変更して後段で元へ戻す複数段例

「最終 main と tested main の net 差だけが保証対象」という意味なら、これは実装上の推測ではなく追加裁定が必要です。

2. main と tip が異なる実運用経路の binding report proof がありません。

予定されている launcher 正例は `_launch_with_reports()` の test seam が、実行に渡された `source` から直接 report digest を作ります。[test_acceptance_launcher.py:146](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/test_acceptance_launcher.py:146) したがって「実 runner が main と tip の相違時にも tested-main digest を報告できるか」は通らなくても、この単体テストは緑になり得ます。

既存の real waiter E2E も、runner を main で作成した後、tip 側では waiter だけを追加しており、runner blob は一致したままです。[test_dev_wave_land.py:2019](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/test_dev_wave_land.py:2019)、[test_dev_wave_land.py:2139](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/test_dev_wave_land.py:2139)

成果物 proof には、real waiter と real launcher を通し、次を同時に固定する正例が必要です。

- tip runner は main と異なり、実行されたら失敗する
- tested-main runner だけが実行される
- binding report、outcome、receipt は main digest
- land が同じ receipt を受理する

これは既存の直接 consumer test 内で追加可能です。`tools/run_tests.py` の変更が必要だと判明した場合は scope を黙って広げず、親統合側の裁定事項に戻すべきです。

## 維持される境界

2述語だけを外す限り、次は静的に維持されます。

- Launcher の実行 bytes は最初に読んだ tested main の `source` です。[acceptance_launcher.py:566](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/acceptance_launcher.py:566)、[acceptance_launcher.py:584](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/acceptance_launcher.py:584)
- tip も `git cat-file blob` で独立に読むため、欠落や非blobは引き続き拒否されます。[acceptance_launcher.py:208](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/acceptance_launcher.py:208)
- 実行後に tested main を再読し、実行 digest と再照合します。[acceptance_launcher.py:597](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/acceptance_launcher.py:597)
- report 数、index 集合、nonce、tested main、runner digest は全 shard で検査されます。[acceptance_launcher.py:341](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/acceptance_launcher.py:341)、[acceptance_launcher.py:616](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/acceptance_launcher.py:616)
- Receipt の `runner_executed_sha256` は tested-main source の digest のままです。[acceptance_launcher.py:526](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/acceptance_launcher.py:526)、[acceptance_launcher.py:629](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/acceptance_launcher.py:629)
- Land は main と tip の runner 実在と blob 型を独立検査し、receipt digest は main blob 内容と照合します。[dev_wave_land.py:1065](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:1065)
- Launcher 自身の blob/content 束縛は維持されます。[dev_wave_land.py:1021](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:1021)
- Waiter の tip blob と実行内容 digest は維持されます。[dev_wave_land.py:1054](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:1054)、[dev_wave_land.py:1115](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:1115)
- non-attributable receipt の checker main-tip 等値と receipt 束縛も残ります。[dev_wave_land.py:1093](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:1093)
- Raw receipt digest は検証した同じ bytes から返されます。[dev_wave_land.py:917](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:917)、[dev_wave_land.py:1130](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:1130)

削除対象も production 上は exact 2個です。[acceptance_launcher.py:568](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/acceptance_launcher.py:568) と [dev_wave_land.py:1084](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:1084) 以外の main-tip runner 等値述語は確認できませんでした。

## main と tip が異なる正例

D987 の比較を修正した後であれば、plan の「tip だけ runner 変更、receipt は main digest、main 側は非runner変更」という正例は過剰受理ではありません。tip runner は意図どおり実行対象外ですが、tip の実在/blob、main digest、waiter、checker、forward-main topology と clean replay は残ります。

一方、tip digest を名乗る receipt は main 内容照合で拒否されます。[dev_wave_land.py:1085](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:1085) checker lookup failureが runner 等値拒否の撤去後に retryable へ到達するという plan の ordering 修正も妥当です。

## 裁定候補

- D987 を各 main 取り込み区間の変化として扱うか、tested main から最終 incorporated main までの net 差として扱うか。推奨は既存 topology の `prior_main_sha -> incorporated_main_sha` を使う各区間比較です。
- main と tip が異なる real waiter E2E を author の4ファイル変更に含めるか、親統合 proof として追加するか。production scope は広げないでください。

テスト、build、checkerは実走していません。親 plan 自身も非実走を明記しており、実測値や緑判定はありません。[plan-current.md:5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1975-t1978-stage-q/plan-current.md:5)、[plan-current.md:190](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1975-t1978-stage-q/plan-current.md:190)

## 総括

tested-main bytes 実行、tip 実在/blob、実行後再読、全 shard binding report、receipt main digest、waiter/checker 束縛は、exact 2述語の撤去だけなら弱くなりません。

ただし D987 の終点比較は、実際の forward-main 取り込み境界と同値ではなく、runner 不変取り込みの過剰拒否と変更後復元の受理を作ります。比較対象の裁定と対応テストを先に直し、main と tip が異なる real waiter/launcher/land proof を追加してから author 段へ進めるべきです。