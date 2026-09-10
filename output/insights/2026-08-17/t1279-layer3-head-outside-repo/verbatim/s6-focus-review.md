## 総括

- HEAD `1102b0161a5ccb544ef4521712c8231e8baac969` の最終差分を静的検査した。
- certifying 入口への repo 外 v2 fallback 漏れは閉じており、wave 前の受理集合が維持される。
- 新たに受理されるのは、Git HEAD を取得できない source repo 外の v2 campaignを、非 certifying 入口へ provenance 未指定で渡す場合だけである。
- v1、source repo 内、certifying 入口、CLI、明示 provenance、Git HEAD 成功時には新しい受理差がない。
- `build_v2_campaign_lock` の既定出力と既存呼び手、本体 assert、公開 API の signature は維持されている。
- 残る実問題は裁定済み scope 外の CLI 制約。E2E の Git 非所属前提は低リスクながら明示されておらず partial とした。
- pytest は実行していない。465 passed は親の実測としてのみ参照した。

## 所見対応表

| ID | 所見 | 判定 | 最終差分の根拠と成果物影響 |
|---|---|---|---|
| A-MF1 | path 判定が certifying 受理集合まで広げる | closed | `orchestrator/campaign/layer3_report.py:598` で `build_accepted_report` が先に旧 `_git_head` を要求し、`orchestrator/tests/test_layer3_report.py:908` が repo 外 v2 の拒否を固定。certifying Layer3 成果物は増えない。 |
| A-MF2 | CLI が repo 外 campaign を扱えない | not-applicable | 親裁定どおり scope 外。`orchestrator/campaign/layer3_report.py:685` は `output_root` を渡さず、同 `:397` の拒否が残る。CLI 成果物欠落も残存する。 |
| A-MF3 | M-4 の期待 node に E2E が欠落 | closed | focused の完全一致は `orchestrator/tests/test_layer3_report.py:1751`、E2E は `orchestrator/tests/test_p3_autonomous_workload_trial.py:2473`。hex64 誤 provenance は両成果物経路で検出される。 |
| A-N1 | 探索 campaign は常に repo 外という brief が誤り | not-applicable | 訂正裁定と整合。`orchestrator/campaign/layout.py:293` は明示 root を無検査で返し、同 `:306` は既定 repo root へ戻る。成果物挙動は未変更。 |
| A-N2 | `_git_head` が `UnicodeDecodeError` を変換しない | not-applicable | backlog 裁定どおり `orchestrator/campaign/layer3_report.py:164` と同 `:167` は未変更。異常な Git stdout ではレポートが欠落しうる。 |
| A-N3 | repo 外テストが Git 非所属を固定しない | partial | focused と v1 は `orchestrator/tests/test_layer3_report.py:218` で固定済み。一方 E2E は `orchestrator/tests/test_p3_autonomous_workload_trial.py:2374` の `tmp_path` に同前提 assert がなく、Git 配下では偽赤になりうる。 |
| A-OK1 | v2 authority は exact hex40 | closed | `orchestrator/campaign/campaign_lock.py:167` と同 `:197` が exact keys と lowercase hex40 を要求。fallback provenance の形式は緩まない。 |
| A-OK2 | completeness と certifying gate は維持 | closed | `orchestrator/campaign/autonomous_trial_completeness.py:2091` が object ID を検査し、同 `:2139` は比較時だけ除外、同 `:2352` は certifying 一致を維持。proof chain の他 field は変わらない。 |
| A-OK3 | symlink・`..` 正規化に追加問題なし | closed | `orchestrator/campaign/layer3_report.py:393` で campaign を resolve 後、同 `:436` から利用する。表記差による追加受理はない。 |
| A-OK4 | 既存 tracked Layer3 report は不変 | closed | 最終差分は production 1、test 2ファイルだけで、`output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/reports/layer3_report.json:1` を含む成果物は未変更。 |
| B-MF1 | 探索 campaign 常時 repo 外という主張 | not-applicable | A-N1と同じ訂正対象。`orchestrator/campaign/layout.py:306` と同 `:329` は、既定経路と env 経路が異なることを示す。 |
| B-MF2 | v2 test の pin と source HEAD が同じ | closed | `orchestrator/tests/test_layer3_report.py:1707` が固定 `"b"*40`、同 `:1711` が Git 非所属、同 `:1712` が source HEAD との差、同 `:1751` が成果物値を検査する。 |
| B-MF3 | M-2 の期待 node が不足 | closed | Git-success 値変更は `orchestrator/tests/test_layer3_report.py:1788`、repo 内 fail-open は同 `:1808` と同 `:1812` で検出される。 |
| B-MF4 | M-4 の E2E node が不足 | closed | `orchestrator/tests/test_layer3_report.py:1751` と `orchestrator/tests/test_p3_autonomous_workload_trial.py:2473` が両方とも lock commit 完全一致を要求する。 |
| B-MF5 | 8c E2E が標準 producer を通らない | not-applicable | scope 外裁定と整合。`orchestrator/tests/test_p3_autonomous_workload_trial.py:157` の helper が同 `:209` で直接 v2 lock を書く。標準 producer 退行の単独被覆はない。 |
| B-MF6 | v1 負例の repo 外前提不足 | closed | `orchestrator/tests/test_layer3_report.py:1821` が共通前提を呼び、同 `:1826` が authority 無し、同 `:1833` が元例外送出を固定する。 |
| B-N1 | Git-success の full-chain 被覆消失 | not-applicable | nit のまま。focused 被覆は `orchestrator/tests/test_layer3_report.py:1755` にあるが、E2E `orchestrator/tests/test_p3_autonomous_workload_trial.py:2362` は repo 外 fallback を通る。 |
| B-N2 | build と render が同一 node | not-applicable | nit のまま。`orchestrator/tests/test_layer3_report.py:1747` と同 `:1749` は同一 test 内。受理集合や成果物値は変わらない。 |
| B-P1 | M-1 は focused と E2E の2 node | closed | `orchestrator/tests/test_layer3_report.py:1747` と `orchestrator/tests/test_p3_autonomous_workload_trial.py:2393` がそれぞれ fallback を必要とする。旧実装への復帰は両経路を停止させる。 |
| B-P2 | M-2 は Git優先と repo内拒否の2 node | closed | `orchestrator/tests/test_layer3_report.py:1788` と同 `:1808` が値変更と fail-open を別々に検査する。 |
| B-P3 | M-3 は repo内 fail-closed node | closed | `orchestrator/tests/test_layer3_report.py:1807` で source repo 内 path、同 `:1812` で同一例外を要求する。 |
| B-P4 | M-4 は focused と E2E の2 node | closed | `orchestrator/tests/test_layer3_report.py:1751` と `orchestrator/tests/test_p3_autonomous_workload_trial.py:2473` が完全一致を要求する。 |
| B-P5 | M-5 は repo外 v1 node | closed | `orchestrator/tests/test_layer3_report.py:1825` で v1 化し、同 `:1833` で placeholder 受理を拒否する。 |
| B-P6 | M-6 は明示値優先 node | closed | `orchestrator/tests/test_layer3_report.py:1843` は Git 呼出しを即失敗させ、同 `:1851` が `"fixed"` を完全一致検査する。 |
| B-P7 | source repo HEAD fallback を M-7 で検出 | closed | `orchestrator/tests/test_layer3_report.py:1712` で source HEAD と pin を異ならせ、同 `:1751` で pin を要求するため、source HEAD 退行は生存しない。 |
| B-P8 | `except Exception` の M-8 追加 | not-applicable | 不採用裁定どおり。production は `orchestrator/campaign/layer3_report.py:183` で `Layer3ReportError` のみ捕捉し、予期しない例外を成功へ変換しない。 |
| B-OK1 | helper の解決順は正しい | closed | `orchestrator/campaign/layer3_report.py:179` 明示値、同 `:182` campaign Git、同 `:184` source repo 拒否、同 `:186` 外部 v2 pin の順。意図した成果物値になる。 |
| B-OK2 | authority、v1、元例外の検査が強い | closed | `orchestrator/tests/test_layer3_report.py:1744`、同 `:1826`、同 `:1835` が型・authority・例外 identity を固定する。 |
| B-OK3 | 明示 provenance 優先 test は恒真でない | closed | `orchestrator/tests/test_layer3_report.py:1843` と同 `:1851` により、Git 呼出しまたは値変更のどちらでも赤になる。 |
| B-OK4 | 8c finalizer は絶対 path、引数省略 | closed | `orchestrator/campaign/p3_autonomous_workload_trial.py:1754` で resolve し、同 `:1762` から `generated_from_head` を省略して render する。実 fallback に到達する。 |
| B-OK5 | 成功する campaign-chain は v2 authority 必須 | closed | `orchestrator/campaign/campaign_lock.py:211` の v2 decode と `orchestrator/campaign/autonomous_trial_completeness.py:2357` の certifying admission が維持される。 |
| B-OK6 | tracked lock に v2 がないため既存成果物不変 | closed | `output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/campaign.lock:1` を含む `output/` は最終差分の対象外。既存 bytes は変わらない。 |

変異関連の `closed` は、最終差分の detector topology が指摘された全 node を静的に含むという判定である。変異 ledger の実走結果自体は今回再実行していない。

## fix が壊したもの

- `build_accepted_report`: 公開 signature は `orchestrator/campaign/layer3_report.py:554` で不変。全呼び手は同一 test ファイル内の6箇所だけで、有効な既存正例は `generated_from_head="fixed"` を渡すため `:598` の新分岐を通らない。未指定の既存 unsealed receipt 負例も `orchestrator/tests/test_layer3_report.py:822` で receipt gate が先に拒否する。期待値破壊はない。

- certifying の未指定値: `orchestrator/campaign/layer3_report.py:598` が `_git_head` を先に呼ぶため、受理集合は旧実装と同じ。ただし「Git失敗と admission 不正を同時に持つ入力」では、wave 前より Git エラーが先に見える可能性がある。両方とも拒否で成果物は発行されず、既存 test の期待も壊さないため nit とする。

- `build_v2_campaign_lock`: `orchestrator/tests/test_layer3_report.py:73` の引数は optional で、同 `:92` から同 `:95` が `None` のとき従来の `binding.contract_loader_commit` を使う。既存5呼び手の既定出力は byte 単位で不変で、新しい値を渡すのは同 `:1723` の新規 test だけである。

- 前提 assert: `orchestrator/tests/test_layer3_report.py:218` は source repo 外と `_git_head` 失敗を直接検査する。lock pin 完全一致 `:1751`、certifying 拒否 `:922`、v1 元例外 `:1833` は変更されておらず、本体 assert は弱まっていない。

- masking: `_assert_external_campaign_without_git_head` の `_git_head` 例外は `pytest.raises` が消費して本体へ進む。Git HEAD が成功するか別例外なら前提で赤になり、後続の不合格を緑へ変える経路はない。副作用を持つ monkeypatch は前提検査後の `orchestrator/tests/test_layer3_report.py:1832` で設定されるため干渉しない。

## 残る受理集合の差

wave 前に拒否され、wave 後に新しく受理される集合は、次をすべて満たす入力だけである。

1. `build_report` またはそれを使う `render` への非 certifying 入力である。生成物は `orchestrator/campaign/layer3_report.py:545` により `certifying_input=False`。
2. `generated_from_head` が未指定または `None`。
3. custom `output_root` により `orchestrator/campaign/layer3_report.py:390` の配置検査を通るが、resolved campaign は `_DEFAULT_OUTPUT_ROOT.parent` の外側。
4. `_git_head(campaign_dir)` が `Layer3ReportError` を送出する。
5. lock が正常に decode された v2 で、`decoded_lock.authority` が存在する。
6. その他の admission、WAL、lock identity、schema、artifact 検査をすべて従来どおり通る。

この集合では、旧実装は `_git_head` 例外で拒否し、新実装は `orchestrator/campaign/layer3_report.py:186` から検証済み `contract_loader_commit` を記録して受理する。8c finalizer の `orchestrator/campaign/p3_autonomous_workload_trial.py:1762` が意図された主要 consumer である。

以下は新規受理されない。

- 明示 `generated_from_head` あり: wave 前から受理可能で不変。
- campaign Git HEAD 成功: wave 前後とも Git HEAD を使う。
- source repo 内で Git失敗: `layer3_report.py:184` で拒否。
- repo 外 v1または malformed v2: authority がなく拒否。
- `build_accepted_report` の未指定値: `layer3_report.py:598` で旧 Git 要求を維持。
- CLI: `output_root` を渡せず `layer3_report.py:397` で先に拒否。
- completeness の fresh rebuild: `autonomous_trial_completeness.py:2102` が明示 `"0"*40` を渡すため不変。

したがって、裁定の「repo 外 + v2 lock + 非 certifying」以外の新規受理集合は確認できない。

## must-fix

最終差分に新しい must-fix はない。親裁定の MF-1、MF-2、MF-4 は閉じており、MF-3 の detector topology も最終差分上は閉じている。

残件は must-fix ではなく、裁定済み scope 外の CLI 制約と、A-N3で示した E2Eの Git 非所属前提の未明示である。後者は偽緑ではなく環境依存の偽赤を起こしうる nit で、成果物受理集合は広げない。