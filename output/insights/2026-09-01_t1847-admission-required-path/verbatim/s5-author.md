## 変更内容

- [p3_b4_admission_record.py:11](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1784-author/orchestrator/campaign/p3_b4_admission_record.py:11): 5 点の非保証を docstring に追記。
- [p3_b4_admission_record.py:62](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1784-author/orchestrator/campaign/p3_b4_admission_record.py:62): 指定された固定例外文言を追加。
- [p3_b4_admission_record.py:96](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1784-author/orchestrator/campaign/p3_b4_admission_record.py:96): 3 literal の immutable mapping を追加。
- [p3_b4_admission_record.py:710](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1784-author/orchestrator/campaign/p3_b4_admission_record.py:710): resolver 直後、bytes 読み込み前に required-path gate を追加。
- [test_p3_b4_admission_record.py:196](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1784-author/orchestrator/tests/test_p3_b4_admission_record.py:196): fixture を driver 対応 path へ移動。
- [test_p3_b4_admission_record.py:765](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1784-author/orchestrator/tests/test_p3_b4_admission_record.py:765): enforcement test を追加。
- [test_p3_b4_admission_record.py:797](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1784-author/orchestrator/tests/test_p3_b4_admission_record.py:797): 独立した mapping literal test を追加。
- [test_p3_b4_closed_critic.py:762](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1784-author/orchestrator/tests/test_p3_b4_closed_critic.py:762): shared fixture、sidecar、projection manifest の期待 path を追随。

## 実走した検査

- 新設 2 node:
  - `test_verifier_enforces_driver_required_path`
  - `test_required_path_mapping_matches_independent_literals`
  - rc=16。Pegasus `qstat -Q` preflight 失敗で child 未起動。
- 焦点 5 file 全 node:
  - admission record、closed critic、launcher、raw record producer、ccbench spawn sites
  - rc=16。同じく child 未起動。
- `py_compile` 対象 3 file、`git diff --check`、`check_codex_agents.py`、`check_docs.py`: rc=0。
- pytest の緑はありません。

## 受理集合の変化

変更前は、repo 内の symlink なし regular file なら任意 path でも、HEAD・schema・文書 binding を通過すれば受理されました。

変更後は、それら全条件に加えて、解決後 path が `driver_kind` 対応 mapping と一致する必要があります。新たに受理される入力はなく、受理集合は狭まる方向だけです。既存の拒否署名は変更していません。

## 波及の静的列挙

- production caller は `p3_b4_closed_critic.py` の 2 箇所と `p3_b4_launcher.py` の 1 箇所。変更せず中央検証器へ収束しています。CLI の `--admission-record` も維持しました。
- shared fixture は `test_p3_b4_launcher.py` と `test_p3_b4_raw_record_producer.py:50` が直接利用します。
- `test_p3_s4_loop.py`、sort、trigger gating は `_production_launch_context` 経由の間接 consumer です。
- `p3_b4_raw_record_producer.py` の独立 projection 列挙は member 増減なしです。
- `test_ccbench_spawn_sites.py` の `_git_call` pin は `1` のままです。subprocess site は増えていません。

## 未了・懸念

- user slice が約 15 GiB 超で local 実行不可、かつ scheduler socket が利用できず pytest は未実走です。環境回復後に焦点 5 file の再実走が必要です。
- 指定で保全対象とされた repo 外 tmp path の独立ケースは、現 checkout の resolver attack test に見当たりませんでした。既存 resolver attack test 自体は変更していません。
- commit、staging、stash、branch 操作は行っていません。

## 総括

required-path gate と分離した 2 本の test を実装しました。  
production caller、CLI、docs、wiring probe は未変更です。  
静的検査は rc=0、pytest は infrastructure failure により未実走です。  
変更は 3 Python fileだけに未 staging で残しています。