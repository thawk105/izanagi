## 変更 file と要旨

指定の7ファイルを変更しました。docs・commit は変更していません。

- `tools/check_docs.py`：model を astra、5節の effort pin を ultra、L1.5 上限を9,788へ更新。
- `test_check_docs.py`：literal・decoy・置換元を追随。旧 medium 拒否を5節の parametrize で追加。上限＋1の負例も9,789へ更新。
- `test_dev_wave_launch_authority.py`：model・現行 effort の期待値を追随。意図的な medium/high/low と過去形式 fixture は維持。
- `effort_levels.py`／`test_effort_levels.py`：Codex のみ ultra を追加。Claude の厳密 tuple は維持。
- `test_dev_wave_codex.py`：既存 matrix を残し、plan／consult 両 lane に ultra 転送正例を追加。
- `tmp-next-tasks/next_tasks_consult.sh`：改訂全文を作成。既定 ultra、astra 指定、委任禁止を追加。締切1800秒・環境変数 override は維持。

## 実走したテスト (nodeid・結果)

**pytest の実走 nodeid はありません。** `tools/run_tests.py` は `qstat -Q preflight rc=1` により rc=16、`child_started=false` で終了しました。

指定した範囲は以下の各ファイル全体です。

- 変更したテスト4本
- `test_plain_runner_coverage.py`
- `test_growth_test_holds_contract.py`
- `test_hold_inventory.py`
- `test_update_acceptance_duration_ledger.py`
- `test_pytest_collection_config.py`

実走できた検査：

- `python3 tools/check_docs.py`：rc=1、後述の期待赤6件。
- `bash -n tmp-next-tasks/next_tasks_consult.sh`：成功。
- 変更Python 6ファイルの構文解析、`git diff --check`：成功。
- byte pin 直接照合：本体・期待値は9,788、超過負例は9,789。三項式の変更対象は L1.5 側と確認。

## 期待赤と回帰

`check_docs.py` の findings は次の6件だけでした。

- DW-S02／S03／S05-A／S06-A／S06-C の effort 不一致。
- L1.5 footprint：`9793 > 9788`。

この検査では期待外の回帰はありません。pytest は未実走なので、テスト全体の回帰有無は未判定です。

## 波及の静的列挙

- `codex_worker_launch.py` の argparse choices は共有定数から ultra を受理。対応する語彙テストの追加は単位B担当。
- `dev_wave_codex.py` は従来どおり文字列を転送。
- `launch_authority.py` と docs を読む共有 fixture は、親の workers 更新後に再検査が必要。
- `dev_waves/schema.py`／`cli.py` の Claude 語彙、Codex role adapter の受理集合は不変。
- `daemon.py::_supervisor_digest()` は今回の変更で変化。親による land 前の稼働確認が必要。
- 新設5 nodeid は所要時間未計測。台帳値は合成していません。
- 外部相談scriptの委任禁止は prompt のみで、起動器による検出はありません。

受理集合の変更は、Codex語彙への ultra 追加、model pin の sol→astra、effort pin の medium→ultra、L1.5 上限の92 bytes増加です。既存の重複・decoy・誤値拒否は維持しています。

## 変異事前登録 m1〜m3・m7 の位置確認

| ID | 現在の位置 | 対応検査 |
|---|---|---|
| m1 | `tools/check_docs.py:372` | model literal期待・drift負例 |
| m2 | `tools/check_docs.py:5858` | DW-S05-A旧medium負例・現行docs正例 |
| m3 | `tools/dev_waves/effort_levels.py:27` | 語彙の厳密tuple検査 |
| m7 | `tools/check_docs.py:364` | 上限literal・実docs予算検査 |

位置を確認しました。**変異は未実走、KILLED未判定**です。m2・m7の単一理由性は親docs統合後に確認が必要です。

## 総括

**実装済み・pytest未実走。** check_docs は期待赤6件のみ確認しました。親docs統合後のテスト・変異検査が残っています。