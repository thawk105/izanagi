## 総括

**実装済み・未実走です。** 新fixはunstagedで追加し、stage・commit・mergeはしていません。

| 所見 | closed / partial / regressed | 状況 |
|---|---|---|
| R1 | **partial** | 不要live read除去・旧実物正例追加済み。実走と変異確認待ち |

変更path（すべて所有範囲内）：

- `orchestrator/campaign/s1_known_axes_freeze.py`：既知旧文書のhistorical閲覧では6種コードをresolver前に除外。generator SHA読取りを比較分岐内へ移動。
- `orchestrator/tests/test_s1_known_axes_freeze.py`：正例1件追加。
- `orchestrator/tests/conftest.py`：新nodeのinventory・両repo reader登録。
- `orchestrator/tests/test_real_repo_serialization.py`：新nodeの既存meta登録。

累計追加はproduction **68/200行**、test/meta **307/450行**。既存テスト本文・期待値・holdは変更していません。

**新testnode：**
`orchestrator/tests/test_s1_known_axes_freeze.py::test_historical_real_artifact_without_live_code_reads`

旧bytesのまま両公開APIを呼び、6種コードだけ不存在へ解決するresolverと実SHA関数のwrapで、コード・generatorの不要読取りがないことを検査します。

**実走状況：** `tools/run_tests.py --force-dispatch`でknown-axes全ファイル、実repo分類・手書きgroup禁止metaの2node、plain-runner coverage全ファイルを指定。`qstat -Q preflight rc=1`でrunnerは**rc=16、child_started=false**。全対象・変異とも未実走です。迂回せず停止しました。`git diff --check`は通過しています。親の全走を代替しません。

**新anchor（本体ファイル）：**

- **M1・897行**：generator直前の`if not known_historical:`を`if True:`へ置換。対象は既存`test_historical_real_artifact_is_readable`のみ。旧generator/live比較による拒否を期待。
- **M7・909行**：`if known_historical and historical and path_rel in _HISTORICAL_CODE_PATHS:`を`if False:`へ置換。対象は新testnodeのみ。`source が存在しない`で失敗することを期待。

所有外への波及確認対象はmeasurement・calibration・oracleのcallerと各consumer test、共有` s8b_v2_freeze_fixture.py`です。これらは未編集で、現行利用の入力検証・意味照合を維持しています。M6 oracleは診断感度のみで、最終`allowed`反転のkillとは扱いません。
