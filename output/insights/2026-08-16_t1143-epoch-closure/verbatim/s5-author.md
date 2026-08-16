## 1. 変更した file と行

- [campaign_lock.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1143-epoch-closure/orchestrator/campaign/campaign_lock.py:27): comment と tuple を exact 12 path 化。既存 8 件の順序を保持し、指定された verifier 4 件を末尾へ追加。
- [artifact_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1143-epoch-closure/orchestrator/campaign/artifact_admission.py:63): scope 2 定数を指定値へ変更。domain は不変。
- [artifact_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1143-epoch-closure/orchestrator/campaign/artifact_admission.py:100): exact 12 と verifier の包含・除外集合を class/API docstring 3 箇所へ反映。
- [contract_loader_binding.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1143-epoch-closure/orchestrator/campaign/contract_loader_binding.py:2): module/class docstring を exact 12 化。
- [test_t671_source_binding.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1143-epoch-closure/orchestrator/tests/test_t671_source_binding.py:22): production から独立した tuple を exact 12 化。
- [test_t671_source_binding.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1143-epoch-closure/orchestrator/tests/test_t671_source_binding.py:123): test 名を `exact_twelve_paths` へ改名。
- [test_artifact_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1143-epoch-closure/orchestrator/tests/test_artifact_admission.py:313): fixture 説明、scope exact equality、件数 assertion を 12 化。
- [test_artifact_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1143-epoch-closure/orchestrator/tests/test_artifact_admission.py:1113): verifier 4 path の fail-closed parametrize test を新設。
- [test_s6_sort_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1143-epoch-closure/orchestrator/tests/test_s6_sort_sweep.py:619)、[test_s8a_trigger_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1143-epoch-closure/orchestrator/tests/test_s8a_trigger_sweep.py:829): fixture docstring を exact 12 化。

docs、`output/**`、`orchestrator/verifier/**` は無変更。commit も作成していない。

## 2. 現行の受理・拒否挙動と、変更後にどう変わるか

現行は `HISTORICAL_RAW` が current closure を検査せず記録 epoch を返す。`CERTIFIED_ACCEPTANCE` は E0 を `v1-authority-absent` で拒否し、未 commit drift を `current-closure-unavailable`、commit 済み drift を `recorded-current-closure-mismatch` で拒否する。

変更後も判定式、reason code、E1 prefix、hash 式は同じ。比較対象だけが exact 8 から exact 12 へ広がり、`core.py`、`dsg.py`、`model.py`、`parse.py` の drift も拒否対象になる。既存の 8-key v2 lock は exact key 検査で拒否されるが、親 brief の実測では該当 corpus は 0 件。

fresh lock 作成前から verifier が変更されていれば、その bytes を新 epoch として記録する挙動は変わらない。また `__init__.py` など excluded 4 file の drift は引き続き束縛しない。

## 3. 固定件数依存の全数調査

`orchestrator/campaign` と `orchestrator/tests` を対象に、次を限定検索した。

- `exact 8 path`
- `exact 8-path`
- `closure 8 path`
- `eight_paths`
- `verifier/* ... 束縛しない`
- `len(...contract_loader...) == 8`

旧表現・test 名・部分一致 assert は15件、固定長 assertion は1件、合計16件を検出し、全16件を修正した。変更後は範囲を `orchestrator/**/*.py` へ広げて同じ検索を再実行し、旧依存は0件だった。関連する固定長 assertion は `== 12` の1件だけ残る。

`CONTRACT_LOADER_RELATIVE_PATHS` の consumer は11ファイル、scope 2 定数の consumer は3ファイルだった。いずれも定数の動的消費か独立 golden であり、追加の `== 8` はなかった。

## 4. 新規テストの設計と nodeid

production tuple から導かない literal 4 path の parametrize testを追加した。各 node は次を確認する。

1. clean な v2 campaign を作成。
2. 対象 verifier file を未 commit drift させ、`current-closure-unavailable` で拒否。
3. drift を fixture repo へ commit し、`recorded-current-closure-mismatch` で拒否。
4. 両方で `E1-stale` と元の epoch を確認。
5. campaign lock と WAL bytes が不変であることを確認。

nodeid は次の4件。

- `orchestrator/tests/test_artifact_admission.py::test_certified_acceptance_rejects_each_verifier_drift_fail_closed[core.py]`
- 同 `[dsg.py]`
- 同 `[model.py]`
- 同 `[parse.py]`

改名した T671 test や新規 nodeidを直接列挙する外部 meta-test は0件。ファイル内 `_run()` はファイル全体を実行するため自動追随し、call-site exact testの期待集合にも変更はない。

## 5. 実走した検査

pytest は未実走。次の範囲を `tools/run_tests.py` で投入したが、`qstat -Q preflight rc=1` により rc=16 の dispatch infrastructure failure となり、node は1件も開始されなかった。

- `test_t671_source_binding.py` 全体
- `test_campaign_lock_codec.py` 全体
- `test_artifact_admission.py` の scope、v2正例、E1正例、既存 stale、新規 verifier drift、closure unavailable の各 node

直接 pytest への迂回はしていない。静的検査は以下が成功した。

- 変更7ファイルの AST parse
- production tuple の exact 12・順序の独立照合
- scope 2定数と domain `/v1` の exact literal 照合
- `git diff --check`
- docs、output、verifier差分ゼロの確認

## 6. 期待される赤 / 回帰の赤の内訳

pytest が開始されなかったため、実測された test failure はない。

統合 commit 前に実 repoを使う certified 経路が `recorded-current-closure-mismatch` または `current-closure-unavailable` で赤になるのは期待された赤である。今回これを xfail化・回避していない。それ以外の赤は回帰として親の統合後実走で判定が必要。

AST検査用の初回補助コマンドには非literal代入まで `literal_eval` したスクリプト側の誤りがあり、対象代入だけを読む形へ修正して再実行し成功した。製品コードの赤ではない。

## 7. 波及可能性の静的列挙

- `campaign_lock` codec: v2 authority の exact key集合が12件になる。
- `contract_loader_binding`、`ident`: capture、live検証、committed検証が verifier 4 fileへ拡張される。
- `artifact_admission`: epoch preimageと certified current-map比較が12件になる。
- 共有fixture: `campaign_lock_test_support.py`、artifact admission、S6、S8a、layer3、bench-first が動的に追随する。
- consumer test: campaign-lock missing-key parametrizeやT671の4組のparametrizeに verifier nodeが増える。
- report consumer: `s8b_oracle_report.py` と対応testは scope定数を動的転送するため変更不要。
- `orchestrator/verifier/__init__.py`、`__main__.py`、`cli.py`、`report.py`、別閉包のqualificationは今回のscope外である。

## 総括

- enforcement source closure を指定どおり exact 12 pathへ実装した。
- verifier 4 fileの未 commit・commit済みdriftを拒否する4 nodeを追加した。
- 固定件数依存16件をすべて修正し、旧8件表現の残存は0件。
- docs・output・verifier bytesは無変更で、commitも作成していない。
- pytestはdispatch障害により未実走であり、親の統合commit後の実走が必要。