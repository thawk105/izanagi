実装済みです。commit・docs 編集はしていません。

- [submit_certify.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2515-author/tools/pegasus/submit_certify.sh:8): usage、exact gate、error を 5 値化。
- [certify_calibration.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2515-author/tools/pegasus/certify_calibration.sh:154): gate の位置を保ったまま同じ 5 値へ更新。
- [test_pegasus_calibration_workload.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2515-author/orchestrator/tests/test_pegasus_calibration_workload.py:36):
  - 両 gate の集合が exact に同一の 5 要素であることを固定。
  - submitter の負例を `0 / 51 / 100 / 05 / +5 / " 5" / "5 " / ５` に拡張。
  - 5 値すべてについて dry-run の pre-submit、submit receipt、`qsub -v` 伝播を検査。
  - job body を実起動し、`+5` が構造化 `failure.json` の `submit_binding` で拒否されることを検査。
  - 既定 rr50 の完全 argv、no-arg helper、20/80 docs pin は維持。

受理集合は、変更前 `{"20","50","80"}`、変更後 `{"5","20","50","80","95"}` です。省略時は引き続き `"50"`、それ以外の文字列は拒否されます。空文字は `${2:?}` で gate 前に拒否される旨をテストコメントへ明記しました。この閉集合は sanctioned な二つの shell 経路に限り、scope 外の calibrator CLI 直接起動には及びません。

検査結果:

- `bash -n`：両 shell 成功。
- Python AST parse、`git diff --check`：成功。
- pytest：実装済み・未実走。対象 7 nodeid 群を `tools/run_tests.py` へ渡しましたが、計算ノード dispatch の `qstat -Q` が失敗し、子未起動の rc=16 でした。
- 変更は所有 3 path のみ。新規・改名 test はないため file 集合 meta-test の追加対象はありません。

所有外の波及候補は、submitter を呼ぶ dev-wave、job body を起動する qsub、workload を受ける calibrator/schema/report、receipt collector、admission/path を pin する `test_hooks.py`、README を検査する docs checker です。argv の型・receipt schema・path・registry・共有 fixture は変更していません。

## 総括

- 両 shell の受理集合を exact `{5,20,50,80,95}` に統一しました。
- runtime 負例、両側一致、5 値 dry-run 伝播を既存テスト内で固定しました。
- rr50 既定値、job gate の位置、README、品質判定は不変です。
- 親は target test file 全体と通常の完了検査を実走してください。