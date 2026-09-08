## 所見ごとの対応表

`closed` は、refuted、意図した変更、または明記済みの保証限界を含む。唯一の `partial` は型契約外入力の既知の nit で、挙動自体は残っている。

| ID | 段 6 の所見 | 判定 | fix 後の根拠 |
|---|---|---|---|
| A-1 | 差分の scope 逸脱なし | `closed` | `orchestrator/verifier/dsg.py:524`、`orchestrator/tests/test_verifier.py:1592-1664` |
| A-2 | 有効な文字列 key では理由順以外は不変 | `closed` | `orchestrator/verifier/dsg.py:520-546,562,572,585` |
| A-3 | 型契約外の mixed key で `sorted()` が `TypeError` | `partial` | `orchestrator/verifier/model.py:320`、`orchestrator/verifier/dsg.py:275,524`。現象は残るが、通常 trace は ASCII `str` へ正規化されるため現行成果物への影響はない。nit のまま。 |
| A-4 | M1 は固定環境で確実に検出される | `closed` | `orchestrator/tests/test_verifier.py:1595,1619,1646,1653-1656` |
| A-5 | 実装と期待値に誤り共有なし | `closed` | `orchestrator/tests/test_verifier.py:1595,1656` |
| A-6 | 残した意味論 assert は不適切な過剰決定ではない | `closed` | `orchestrator/tests/test_verifier.py:1657-1662` |
| A-7 | 既存 assert、golden、skip の弱体化なし | `closed` | `orchestrator/tests/test_verifier.py:1592-1664,1780,1843` |
| A-8 | WR/RW の順序安定性への反証なし | `closed` | `orchestrator/verifier/dsg.py:533-544` |
| A-9 | 同一 key の WW 理由は最大 1 件 | `closed` | `orchestrator/verifier/dsg.py:520-531` |
| A-10 | `certified` を assert しない判断は妥当 | `closed` | `orchestrator/tests/test_verifier.py:1605-1607,1662` |
| B-1 | repo-root `cwd` の `python -c` import 経路 | `closed` | `orchestrator/tests/test_verifier.py:18-38,1625-1627`、`orchestrator/tests/test_s8c_preregistration_predicates.py:2941-2962` |
| B-2 | 30 秒 timeout は短い | `closed` | 120 秒へ変更済み。`orchestrator/tests/test_verifier.py:1631`、先例は `orchestrator/tests/test_pytest_collection_config.py:141-152` |
| B-3 | 非ゼロ終了・timeout 時に stderr が見えない | `closed` | `check=False`、4096-byte tail、seed、rc、stdout、stderr、timeout を実装。`orchestrator/tests/test_verifier.py:1614-1643` |
| B-4 | 失敗時も一時 trace が削除される | `closed` | `orchestrator/tests/test_verifier.py:1602,1612,1663-1664` |
| B-5 | 素の runner が新テストを収集する | `closed` | `orchestrator/tests/test_verifier.py:2869-2892` |
| B-6 | 新 node は通常 node のまま | `closed` | decorator のない `orchestrator/tests/test_verifier.py:1592` |
| B-7 | global な関数名・件数固定 meta-test なし | `closed` | 動的収集は `orchestrator/tests/test_verifier.py:2869-2875` |
| B-8 | 台帳を変更しなくても被覆 gate を維持 | `closed` | `orchestrator/tests/acceptance_duration_ledger.json:20046-20048`、`output/insights/2026-09-08_t2436-ww-reason-order/verbatim/s4-ruling.md:87-97` |
| B-9 | M1からM3は diagnostic sensitivity pin | `closed` | `orchestrator/verifier/dsg.py:517-546` |
| B-10 | M1 の期待失敗集合は新 node 1 件 | `closed` | 直接 pin は `orchestrator/tests/test_verifier.py:1646,1653-1656`。fix は他 nodeを変更していない。 |
| B-11 | M2/M3 に検出力がある | `closed` | `orchestrator/tests/test_verifier.py:1595-1601,1619,1646,1653-1656` |
| B-12 | 変異の単一理由性 | `closed` | `orchestrator/tests/test_verifier.py:1646-1656`、`orchestrator/verifier/dsg.py:523-546` |
| B-13 | JSON、text、critic への順序伝播は意図どおり | `closed` | `orchestrator/verifier/report.py:26-32,144-154`、`orchestrator/critic/digest.py:784-815,1289-1305,1380-1386` |
| B-14 | campaign consumer の意味論破壊なし | `closed` | `orchestrator/campaign/reflux_result_evidence.py:324-407,592-612`、`orchestrator/campaign/mocc_g2_discriminator.py:548-580` |
| B-15 | 追跡済み凍結成果物の再発行不要 | `closed` | `orchestrator/tests/test_verifier.py:1604-1610`、`output/insights/2026-09-08_t2436-ww-reason-order/verbatim/s4-ruling.md:46-51` |
| B-16 | CPython、固定入力、seed 2 本、workers=1 の限界 | `closed` | `orchestrator/tests/test_verifier.py:1595-1607,1619`、`s4-ruling.md:139-145` |
| B-17 | 直接 pin は compact JSON と WW 理由列だけ | `closed` | `orchestrator/tests/test_verifier.py:1604-1610,1646-1656` |
| B-18 | import 保証は非isolated `python -c` と repo-root `cwd` に限定 | `closed` | `orchestrator/tests/test_verifier.py:1625-1627`、`tools/run_tests.py:550-572,2682-2693` |

## fix が検査を弱めていないか

通常の repo 実行形では弱まっていない。

- 子の非ゼロ終了は `completed.returncode == 0` により必ず失敗する。失敗文には seed、rc、stdout末尾、stderr末尾が入る。`orchestrator/tests/test_verifier.py:1639-1643`
- 子が 0 終了でも stdout が空なら、両 seed とも空で bytes 比較を通過しても `json.loads()` が失敗する。壊れた JSON も同様である。構造だけ成立する誤出力は、edge 探索または理由列・verdict・件数・phenomenon の assert で失敗する。`orchestrator/tests/test_verifier.py:1644-1661`
- stdout・stderr は末尾 4096 bytesに制限されている。`orchestrator/tests/test_verifier.py:1614-1617`
- `TimeoutExpired` は捕捉され、seed、timeout、保持された stdout・stderr の末尾を表示する。`orchestrator/tests/test_verifier.py:1633-1638`

ただし、素の `python -O orchestrator/tests/test_verifier.py` では `assert False` と returncode assert は消える。特に第2 seedの timeoutでは前回の `completed` が再利用され、通過しうる。これは fix 前の `check=True` より局所的には弱い。

一方、repo の標準 runner は `[sys.executable, "-m", "pytest"]` を構築し、`-O` を追加しない。`tools/run_tests.py:550-572`。親の自走コマンドも `python3` であり `-O` ではない。さらに本ファイル全体が bare assertを前提とするため、素の最適化実行は既存の保証面ではない。したがって現行受入への must-fix ではなく、最適化付き手動起動だけに残る nit と判定する。

## 実行環境への依存

実機構造との食い違いは見つからなかった。

- `_REPO` は当該 worktree の repo rootとして算出される。`orchestrator/tests/test_verifier.py:18-38`
- 子は現在のテスト processと同じ `sys.executable` を使い、repo rootを `cwd` にして `python -c` を起動する。`orchestrator/tests/test_verifier.py:1624-1627`
- 同じ `sys.executable -c`、repo-root `cwd`、環境複製による hash-seed subprocess の既存先例がある。`orchestrator/tests/test_s8c_preregistration_predicates.py:2937-2965`
- 120 秒の先例は、同じく `sys.executable` と repo-root `cwd` を使う pytest collection subprocessである。`orchestrator/tests/test_pytest_collection_config.py:141-152`
- 親の実機走行では全106件と新 nodeが成功したとの報告があり、現在の interpreter・cwd・subprocess 構造で動作することは実測済みである。ただし親のコマンドは `PYTHONPATH=.` 付きなので、「PYTHONPATH未設定」の条件だけをその実走単独で証明したものではない。この点は `python -c` の repo-root `cwd` と既存同型先例による静的確認で補われる。

120秒は既存のより重い collection subprocessと同じ上限であり、親実測でも timeout は生じていない。真の hang の検出が1子あたり最大90秒遅くなる点以外に、実行環境上の不整合はない。

## 変異期待への影響

M1 の期待失敗集合は変わっていない。

fix は subprocess の待機上限と失敗診断だけを変更し、`dsg.py:524` の変異点、bytes比較、昇順理由列の期待を変更していない。M1では子は正常終了したうえで seed間 bytes比較または昇順理由列で失敗するため、対象 nodeは引き続き次の1件だけである。

`orchestrator/tests/test_verifier.py::test_multi_ww_reason_report_is_hash_seed_deterministic`

根拠は `orchestrator/tests/test_verifier.py:1646,1653-1656`。他のテストには fix 差分がないため、新たな期待失敗 nodeを加える静的経路もない。これは静的判定であり、M1を再適用した実走結果を緑とは報告しない。

## 総括

段6レビューBの must-fix 2件は、通常の repo テスト実行形について逐語どおり `closed`。検査内容やM1の期待失敗集合は弱まっていない。

残るのは、型契約外 mixed-key 入力の既知の `TypeError` という `partial` な nitと、素の `python -O` では新しい assertが無効になる非標準起動上の nitである。現行 trace、標準受入、成果物への must-fix はない。

この再レビューではテストを実走していない。106 passedは親の実測としてのみ採用した。