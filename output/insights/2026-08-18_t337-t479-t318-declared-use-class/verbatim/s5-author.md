## 変更内容

- `loop.py`: `declared_use_class` を必須 keyword-only 化し、2 値以外を cid/layout 作成前に拒否。
- 公式 caller 8 file、`demo.py` 2 箇所へ `official` を明示。
- 6 producer に `DECLARED_USE_CLASS` を追加し、5 producer の `run_campaign` 呼出しへ配線。
- `test_campaign.py`、`test_dev_wave_land.py`、`test_p3_exploration_namespace.py`、`test_p3_s4_loop_trigger_gating.py` を移行。
- AST 閉包検査を動的 discovery 化し、宣言なし負例・宣言あり正例を追加。
- production の対象呼出しは 15 件、test は 30 件（`test_campaign.py` 29、`test_dev_wave_land.py` 1）。test の 1 件は省略時 `TypeError` 用。
- `s8b_floor_campaign.run_campaign` 1 件と同 test 9 件は別 API の所有外 caller として未変更。
- `py_compile` 18 file、AST/呼出し数、動的閉包 probe、`git diff --check` は成功。旧 keyword の実呼出し残存は 0 件。
- pytest は指定 4 test file と制約 meta-test を runner 経由で試行したが、全て Pegasus の `qstat -Q preflight rc=1`、runner rc=16 で pytest 開始前に停止。nodeid の実走はなく、実装済み・未実走。
- `check_codex_agents.py` は OK、`check_docs.py` は違反なし。docs、output、layout.py、freeze file は変更していない。commit も未実施。

## 挙動差

旧 API の省略時 official 既定は廃止し、`declared_use_class` 省略は `TypeError`。`official` と `exploration` の root は従来どおりで、`qualification`、`dry`、未知値は cid と output directory 作成前に `ValueError`。宣言は `CampaignConfig`、canonical preimage、campaign-id に入りません。

## 総括

- `run_campaign` の selector は `declared_use_class` の一本に統一した。
- 対象 caller は production 15 件、test 30 件を静的確認した。
- 6 producer の宣言由来 AST 閉包と正負 meta-test を実装した。
- official/exploration、拒否、省略、cid 不変、root 不変のテストを追加・移行した。
- pytest は Pegasus dispatch 障害で未実走、回帰赤は未発生。
- 許可範囲外の docs/output/freeze artifact は変更していない。
- 実装変更は作業 tree に残し、commit は作成していない。