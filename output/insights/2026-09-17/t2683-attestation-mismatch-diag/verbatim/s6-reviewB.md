## 総括

- **must-fix 0 件／nit 1 件／GO（レビュー B の静的評価）**。
- production の子・親配線は正しく、公開済み sidecar は既存 failure receipt の closure から参照できる。
- nit は AST 配線 test の検査範囲。M10・M11 は検出するが、引数・分岐位置までは固定していない。
- 差分は申告どおり 7 hunks、追加テストは 13 関数・24 cases。実体の blob hash は snapshot patch の変更後 hash と一致。
- `focus1-driver.log:14–20` に計算ノードで **65 passed／child rc=0**。受入全走・変異走・consumer files の成功は主張しない。
- 以下、`driver`／`tests` はそれぞれ `orchestrator/qualification/t126_driver.py`／`orchestrator/tests/test_t126_qualification_driver.py`。

## 1. production 配線

**配線漏れ：refuted。**
`driver:1277` は `repo_root=source_root` を渡し、helper の `driver:501` が `_attest(repo_root, contract)` を呼ぶ。旧 `_attest(source_root, contract)` と一致する。`contract`・`capability`・`relative`・`stage`・`round_index` も同じ closure 変数である。親は非ゼロ終了分岐の `driver:1312` で、同じ capability・relative と `layout.attempt_dir` を渡す。

`tests:586–599` は、M10 の固定 message 化で `raises` が 0、M11 の旧インライン処理への復帰で `exits` が 0 になるため、**登録された変異は静的に赤になると判断できる**。変異実走の証拠ではない。

**nit 1：real — AST test は呼出しの存在・形・個数だけを検査する。**
キーワード引数と祖先の分岐を検査しないため、例えば `repo_root=repo_root` への誤変更は通る。逆に、中間変数を介した意味的に同じ呼出しは赤になる。ただし、現実装の引数・分岐は正しく、段 4 が指定した形には合致する。

**是正案：** 任意の補強として、追加した AST test に引数対応と子／非ゼロ終了分岐への所属を検査させる。既存テストの期待値変更は不要。

**成果物への影響：** 現差分に欠落はない。将来の誤配線を見逃すと、比較元や sidecar の保存先・台帳からの診断参照が変わり得る。

## 2. fork 経路

**親 pytest process の汚染：refuted。**

`tests:279–285` の monkeypatch と `raw` の変更は fork 前に完了し、子へ継承される。`tests:605–610` は通常経路も例外経路も `os._exit` で終了するため、子が pytest の実行・fixture teardown に戻る経路はない。helper 自身も `BaseException` を捕捉して返す（`driver:524`）。親は `waitpid` 後に成果物を確認し、親側で通常の teardown を行う。

待機には独自 timeout がないが、現試験で停止した証拠はなく、must-fix にはしない。

**是正案：** 必須変更なし。
**成果物への影響：** 子が同期公開した sidecar を親が読める。fork 継承や teardown による診断消失・親側状態破壊は認められない。

## 3. 台帳契約 test

**post-series に到達しない／payload exact 比較が誤っている：ともに refuted。**

`tests:568–575` の subject=90、reference=100 は既存正例と同じで、bits `[0, 0]` により第 2 round で `lower_boundary` に達する（`tests:825–832`, `:838–864`）。`terminal_monotonic=0` と `monotonic_fn=1800` は必要な gap を満たし、既存 positive control（`tests:898–919`）とも整合する。

`driver:885–895` は境界到達後、`fsm.terminal()` より先に post-series attestation を呼ぶ。この試験ではそこで拒否するため、統計的な境界には到達するが、成功の `series_terminal` は記録しない。意図どおりである。

`SeriesFSM.reject` は指定した 3 keys の payload を作り（`series.py:366–377`）、`_append` は event metadata を外側に置く（同 `:267–282`）。したがって `events[-1]["payload"]` の exact 比較は正しい。replay も拡張 message の固定文言を要求しない（同 `:125–139`）。

**是正案：** 必須変更なし。
**成果物への影響：** message に応じて evidence bytes/hash は変わるが、台帳の形・拒否状態・rc=31 は維持される。

## 4. consumer（collector）

**sidecar が回収されない／receipt schema と衝突する：refuted。**

T5（`tests:620–628`）は実 helper が作った sidecar の path・size・hash record を `_manifest` の結果と照合しており、列挙の正例として妥当。

production の exclusion は二つの receipt 名だけ（`collector.py:1315–1319`）。sidecar は除外されず、`closure_manifest` に入る。`verify_manifest_closure` はファイル全体の path・size・hash を照合し、sidecar 内容の schema を要求しない（`artifacts.py:1131`）。failure receipt schema の exact keys は外側と fileRecord に適用されるため、manifest の要素追加とは衝突しない（`t126_failure_receipt_schema.json:4–16`, `:74`）。

T5 単独は receipt 発行・再検証全体の E2E 証明ではない。その範囲は既存 collector tests の焦点走で補う。

**是正案：** collector・schema の変更は不要。
**成果物への影響：** failure receipt の closure とその hash に診断ファイル参照が加わる。成功成果物や certified 選択の条件は変わらない。

## 5. 波及・registry／allowlist／lineno pin

**既存構造 pin の直接破壊：refuted。**

`orchestrator/tests/` を `rg` で検索し、新規 test/helper/class 名について所有 test file 外の直接参照は見つからなかった。

- `test_t126_pegasus_tools.py:6228` の名前 registry は**同ファイル内**の `test_m8…` 等を抽出する。新規 `test_t2683_*` は対象外。既存 node の存在検査にも追加関数は干渉しない。`validate_qsub_binding` の個数 pin（`:4533`）も変更面外。
- `test_campaign.py:5410`, `:5526` の evaluate 1 call・authorization 引数は変更されていない。
- `test_official_perf_closure.py:254`, `:400`, `:660` の evaluator／perf 配線、`test_artifact_admission.py:280`, `:306`, `:544` の閉包 path 集合も変更されていない。
- 追加で `test_t671_source_binding.py:287` の receipt 実装 path 集合に driver が当たった。ファイル追加ではないため集合は不変。
- `test_env_contract.py:83`, `:1250` の対象 module 集合に driver と所有 test file は含まれない。
- `test_ccbench_spawn_sites.py:30`, `:417`, `:2667` の process inventory は calibrator／campaign 配下が対象。今回追加した test の `os.fork()` は対象外。

今回の行移動を絶対行番号で拒否する pin は検索範囲で発見していない。`test_t126_qualification_artifacts.py` の create-only／capability 契約を変更する差分もない。

**是正案：** 既存期待値・registry の更新は不要。末尾の関連 files を焦点走へ追加する。
**成果物への影響：** 構造 pin に伴う受理集合変更は認められない。driver bytes に依存する新規実行の code identity は変わる。

## 6. 報告と実体の一致

**件数・anchor・未実走申告の不一致：refuted。**

snapshot patch を集計して driver 6＋test 1＝7 hunks、AST から追加 13 test 関数・24 cases を確認した。作業実体の blob hash も patch の変更後 hash に一致する。`author-out.md:50–61` の M1〜M11・E1 の行指定は実体に対応する。

author の「未実走」は自身の実行結果として読めば、後続の親の焦点走と矛盾しない。現時点の統合報告では、`focus1-driver.log:5` の local OOM と、`:14–20` の dispatch 後 65 passed を区別すべきである。log 自体も受入全走ではないと明記している。

**是正案：** 親の統合報告に後続の焦点走結果を追記する。author の時点付き報告を遡って変更する必要はない。
**成果物への影響：** 実装成果物は変わらない。結果を混同すると、検証済み範囲のレポートだけが過大・過小になる。closed 未申告は妥当。

## 7. scope

**scope 逸脱：refuted。**

正本差分は指定の 2 files に限定され、新 gate・validator・schema 登録・台帳形式の追加はない。`execution_guard.py`、`run_series`、`verify()`、成功時の evidence 登録経路も変更されていない。

**B2 の staging 残留：real、ただし段 4 で明示的に scope 外へ裁定済み。**
強制終了時の staging 残留を collector が拒否する経路（`collector.py:238–240`）は残る。親の同期読取り停止も解消していない。`author-out.md:77` はこれを保証対象外と明記しており、解決済みとの虚偽申告はない。

**是正案：** 今回の必須変更なし。既存 staging 拒否を緩めず、裁定済み限界を統合報告に維持する。
**成果物への影響：** 強制終了条件では failure receipt が発行できない可能性が残る。通常の書込み例外で rc=31 を維持する保証と混同してはならない。

## 焦点走に足す test file

driver file の 65 passed に加え、以下を追加対象とする。これらの成功は今回の log からは確認できない。

- `orchestrator/tests/test_t126_pegasus_tools.py`
- `orchestrator/tests/test_t126_qualification_artifacts.py`
- `orchestrator/tests/test_campaign.py`
- `orchestrator/tests/test_official_perf_closure.py`
- `orchestrator/tests/test_artifact_admission.py`
- `orchestrator/tests/test_t671_source_binding.py`
- `orchestrator/tests/test_env_contract.py`
- `orchestrator/tests/test_ccbench_spawn_sites.py`
