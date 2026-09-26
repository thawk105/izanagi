起動器を [`.t2847-launcher/launch_si_run.py`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847si-ud/.t2847-launcher/launch_si_run.py) に複写・拡張しました。この 1 ファイルだけが untracked で、tracked file は編集していません。commit も作成していません。

V2 に加えて V29・V28 の patch 列と macro、S1・S2、build ごとの実行セルを持つ J1・J2 を追加しました。stderr の `T2847_FIRED` 行は完走・異常終了・timeout のいずれも run 結果に保存し、負の rc には signal 番号を記録します。dry-run は pin C の一時 checkout に patch を順次適用します。

条件 gate の局所関数は [起動器:137](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847si-ud/.t2847-launcher/launch_si_run.py:137) です。`condition_meaning_gate.py` から `capture_define_inputs`（1052 行）、`make_define_request`（1094 行）、`_configured_define_compile_commands`（2096 行）、`evaluate_define_supply_effectuation`（2797 行）、`declare_define_runtime_meaning`（1202 行）、`evaluate_define_runtime_meaning`（3658 行）、`require_condition_gate_family`（4472 行）を使います。mocc 版と同じ順序・引数で評価し、`driver_id` だけを起動器名にしました。成功記録は build 結果へ保存してから configure します。gate の拒否・例外は当該 build の失敗として記録し、次の build へ進みます。

**検査結果**（指定の repo root、worktree 外の `/tmp/t2847si-ud-check`、指定の third-party cache を使用）:

| コマンド | rc | dry-run の出力 |
|---|---:|---|
| `python3 -m py_compile .t2847-launcher/launch_si_run.py` | 0 | 構文検査成功 |
| `python3 .t2847-launcher/launch_si_run.py --help` | 0 | job 選択肢 `L0,J1,J2` |
| `--job L0 --dry-run` | 0 | V2: v2 patch の逐次適用成功。`K-t1,K-t4,W-t1,W-t4` |
| `--job J1 --dry-run` | 1 | V2: 成功。V29: v2 patch 成功後、壊し patch 不在を `FileNotFoundError` として記録。`S1-t4` |
| `--job J2 --dry-run` | 1 | V2: 成功。V28: v2 patch 成功後、壊し patch 不在を `FileNotFoundError` として記録。`S2-t4` |

元起動器との差分では、L0 の V2 に使う configure 引数、run の argv・env・120 秒 timeout・rc 規則、verifier CLI の argv と呼出条件を維持しています。判定・R4 分類は追加していません。所有外への波及先は、壊し patch 2 本と U-C が登録する `condition_meaning_gate.py` の si owner・target・DefineSpec です。登録前の macro build と実走は未検証です。

## 総括

起動器の実装と指定 dry-run を完了しました。J1・J2 の rc=1 は、現時点で壊し patch が存在しないことを例外で落とさず記録した結果です。