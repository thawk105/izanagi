結論は **NO-GO** です。指定8ファイルと統合差分 `+677/-26` を全文静的監査しました。編集・pytest・mutationは行っておらず、既報の実走結果をgreen/KILLとは扱いません。

## 第1再レビューの残る5 fix

ここでの `closed` は静的な修正成立だけを意味し、実走済みという意味ではありません。

| 残るfix | 状態 | 根拠 |
|---|---|---|
| nested sessionを含むcontainment | **partial** | harness groupへのTERM/KILLは追加されたが、nested sessionは明示的に未回収。[integration.py:1750](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1750)、[integration.py:1804](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1804)。裁定どおりT-145のM2〜M4には数えず、過大主張もない |
| exact schema＋専用result channel | **partial** | exact keys・型・canonical outcome/rcは実装済みだが、stdout channelは裁定どおり維持。さらに結果サイズが無制限という新しい穴が残る。[integration.py:1552](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1552)、[integration.py:1767](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1767) |
| 実SignalRelay FDへの束縛 | **closed** | child-local factoryが実生成instanceを登録し、その `fileno()` とreaderを比較する。[integration.py:1416](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1416)、[integration.py:1320](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1320)。ただしreal pathは未実証 |
| KeyboardInterrupt/SystemExitとcleanup帰属 | **closed** | `BaseException` をFAIL payloadへ変換し、type/args/tracebackをchild boundaryに残す。primary存在時にcleanup exceptionを再送出しない。[integration.py:1496](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1496)、[integration.py:1731](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1731) |
| M7 cleanup観測fixture | **closed** | 実装でなく裁定による閉鎖。`NOT_RUN(design-invalid)` とし、telemetryを要求しない。[s6-rereview1-adjudication.md:32](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/output/insights/2026-07-29_t145-join-dichotomy-wave/s6-rereview1-adjudication.md:32)、[s6-fix2.md:55](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/output/insights/2026-07-29_t145-join-dichotomy-wave/s6-fix2.md:55) |

## parser／producer攻撃

| 攻撃 | 静的判定 |
|---|---|
| Python JSONのNaN/Infinity | **fail-closed**。`json.loads` 自体は受理するが、全4 fieldのexact型検査で数値は拒否される。[integration.py:1568](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1568)、[integration.py:1583](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1583) |
| 巨大数 | **fail-closed**。field型に一致しない |
| 巨大文字列・巨大args list・巨大stdout/stderr | **fail-open on resource bound**。長さ上限がなく、`communicate()` が全量をメモリへ保持する |
| duplicate key | **fail-closed**。`object_pairs_hook` で重複を拒否。[integration.py:1560](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1560) |
| bool/int混同 | **fail-closed**。`returncode` は `type(...) is int`、fieldもexact型。[integration.py:1555](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1555) |
| canonical PASS/SKIP/FAIL | **fail-closed**。PASS空field、SKIP単一reason、FAIL非空type/traceback、rc対応を検査。[integration.py:1597](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1597) |
| negative/signal returncode | **fail-closed**。0/1以外は拒否。[integration.py:1622](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1622) |
| pytest.skip／空args Exception／KI／SystemExit | **producerは静的にschema適合**。skipを先に捕捉し、空args FAILを許容、KI/SystemExitもBaseException経路へ入る。[integration.py:1529](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1529)、[integration.py:1731](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1731) |
| `traceback.format_exc()` の位置 | **正しい**。例外handler内からhelperを呼ぶためactive exceptionを取得する。[integration.py:1536](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1536)、[integration.py:1734](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1734) |

## 新所見 — real

### `[must-fix][real]` result/outputがサイズ無制限で、ceiling前にpytest workerを枯渇させられる

Parserは巨大な `exception_type`、`exception_args`、`traceback` をcanonicalとして受理し、親はPIPE出力を無制限に `communicate()` へ蓄積します。[integration.py:1585](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1585)、[integration.py:1777](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1777)

180秒の時間ceilingはメモリ上限ではありません。巨大な例外文字列や異常出力でOOMすると、typed `INFRA_ABNORMAL` に到達せず、外周全走ごと失われます。

**DW-G05 成果物影響:** 異常childが受入結果・mutation台帳をtyped failureとして残さずpytest workerを終了させ、台帳の値または記録自体を欠落させる。

最小案はstdout channelを変えず、stdout/stderrをfile-backedにして上限+1 byteだけ読み、超過を `INFRA_ABNORMAL` にすることです。Parserにもraw/field長上限を置く必要があります。

### `[must-fix][real]` primary-exception cleanupがreap済みPIDを無条件にgroup IDとして使う

`primary_error is not None` なら `process.poll()` を確認せず `killpg(process.pid, …)` します。[integration.py:1781](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1781)、[integration.py:1755](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1755)

`communicate()` 終端付近のKeyboardInterruptやdecode例外など、direct childのreturncodeが既に確定したprimary経路ではPID/PGIDがstaleになり得ます。再利用後なら無関係なprocess groupへTERM/KILLを送ります。

**DW-G05 成果物影響:** 無関係なpytest/受入process groupを終了させ、別nodeの受入結果やmutation台帳を欠落・混同させる。

T-145のfixtureはdescendantを必要としないため、最小案はsignal直前に `process.poll() is None` とsession-leader bindingを確認し、leader消滅後はgroup signalせずpipe close＋typed infrastructure failureへ落とすことです。nested session一般containmentへの拡張は不要です。

### `[nit][real]` capability非依存controlはproducer/parser結合を検査していない

追加controlは生JSONからpure parserだけを呼びます。[integration.py:1636](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1636)。`_serve_child_payload()` と `_serve_child_main()` のPASS/SKIP/FAIL分岐は通りません。[integration.py:1529](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1529)、[integration.py:1731](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1731)

現実装は静的には正しいためblockerへ上げません。ただし、このcontrolをproducer/parser結合やparent mappingの実証として数えてはいけません。最小案はharnessをPASS・skip・`Exception()`・KeyboardInterrupt・SystemExitへ差し替えて `_serve_child_main()` の出力をparserへ戻す小さなparameterized controlです。

## 新所見 — refuted

- SignalRelay constructor failureはserve threadのFAILとなり、複数instanceは明示的に赤になります。[integration.py:1243](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1243)、[integration.py:1421](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1421)
- restoreはthread終端待ちの後、patch適用と逆順に `SignalRelay`→`select` で戻ります。[integration.py:1512](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1512)、[integration.py:1523](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1523)
- 現productionではrelay FDはcontext終了まで開いているため、通常経路のFD番号再利用攻撃はrefutedです。[daemon.py:1592](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/daemon.py:1592)。early-close＋同番号reuse mutationまで防ぐ保証はないものの、M1〜M6の射程を止める新blockerにはしません。
- pipe保持時も親待ちは180秒＋各5秒で有界です。[integration.py:1777](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1777)、[integration.py:1788](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1788)。timeoutは常に `INFRA_TIMEOUT` で、greenにはなりません。
- nested sessionはコメント・修正記録とも未回収と明記され、閉じたという過大主張はありません。[integration.py:1804](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1804)、[s6-fix2.md:56](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/output/insights/2026-07-29_t145-join-dichotomy-wave/s6-fix2.md:56)

## `+677/-26` shadow contract

行数そのものはblockerにしません。今回の追加266行で具体的な成果物影響があるのは、無制限output captureとstale `killpg` の2点です。producer/parser control不足は実証範囲のnitです。

state-machine縮小、専用result FD、env canonicalization、M7 telemetry、nested session一般containmentは再度must-fixへ戻しません。

## 総括

- 判定: **NO-GO**
- blocker: 0
- must-fix: 2件（出力サイズ上限、stale PGIDへのsignal防止）
- mutationへ進めるか: **進めない**
- M7: **`NOT_RUN(design-invalid)` のまま**
- 実証不足: real long-path roundtrip、real relay/select結合、PASS/FAIL producer-parser結合、timeout TERM/KILL実発火、M1〜M6
- pytest・mutation: **このレビューでは未実行**