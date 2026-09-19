## 変更面

**実装済み・未実走です。** 所有する 5 ファイルのみ変更しました。docs 編集・commit はしていません。

- `orchestrator/campaign/paper_story_b7_fixed5_regression.v2.json:1`：plan の JSON と bytes 一致。SHA-256 は `c6b24050d17c4bc552d254ce65e328b3a6edca919387b5720b4e025ea78b0df1`。
- `orchestrator/campaign/paper_story_a2_certification.py:75,363,378,388,569,5176`：定数、canonical path、job 名、環境集合、shape `(3,6)`、説明文を追加・更新。
- `tools/pegasus/submit_paper_story_a2_certification.sh:273,365`：投入環境と receipt 再構成の両方で新 study に POLICY_PATH を渡す。
- `orchestrator/tests/test_paper_story_a2_certification.py:1053,1470,2577`：fixture、receipt helper、policy 正負例、CLI、全件 materialize、partial 不変、bytes pin を追加。
- `orchestrator/tests/test_paper_story_a2_job_contract.py:39,449,1131,1352`：harness、study 別重複検出、3 request 契約を追加。実 qsub wrapper が記録した argv と receipt も比較。

新規・追加 param は計 20 ケースです。

## 受理集合

scope 前は **A-2 が既定、A-6 は明示選択、他 path は拒否**。scope 後は B7 の canonical 1 path を追加しました。

未知 study、非 canonical path、study ごとの shape 検査は維持。partial の exact two-workload 境界、正しさ gate、他の処理関数は変更していません。新しい subprocess 呼出しもありません。

A-2/A-6 の policy bytes は基準 commit と差分なし。指定 SHA と一致し、既存 protocol pin・テスト期待値も変更していません。

## テスト実走

以下を起動しました。

```bash
python3 tools/run_tests.py orchestrator/tests/test_paper_story_a2_certification.py orchestrator/tests/test_paper_story_a2_job_contract.py
```

```bash
python3 tools/run_tests.py orchestrator/tests/test_hooks.py orchestrator/tests/test_ccbench_spawn_sites.py orchestrator/tests/test_official_perf_closure.py orchestrator/tests/test_campaign.py orchestrator/tests/test_plot_a2_certification.py
```

どちらも **rc=16、`qstat -Q preflight rc=1`**。`child_started=false` で pytest 起動前の基盤障害です。

- 実走 nodeid：なし
- 実走件数：0
- テスト由来の赤／緑：未取得
- queue_state：観測不能

別途、`check_codex_agents.py`、`check_docs.py`、Python AST 構文確認、`bash -n`、`git diff --check` は成功しました。

## 変異の実測

各変異を一時適用し、次を起動して復元しました。

```bash
python3 tools/run_tests.py orchestrator/tests/test_paper_story_a2_certification.py orchestrator/tests/test_paper_story_a2_job_contract.py -k b7 -v
```

| 変異 | 結果 | 赤 nodeid 完全集合 |
|---|---|---|
| M1 adopted genome | 未実測：rc=16、子未起動 | 未確定 |
| M2 shape | 同上 | 未確定 |
| M3 canonical path | 同上 | 未確定 |
| M4 job 名 | 同上 | 未確定 |
| M5 env 集合 | 同上 | 未確定 |
| M6 shell 投入条件 | 同上 | 未確定 |
| M7 receipt 再構成条件 | 同上 | 未確定 |
| M8 help 文言 | 同上 | 未確定 |

**KILLED／SURVIVED の判定はありません。** M6/M7 は実 submitter を wrapper 越しに呼ぶテストを追加していますが、検出能力の実証は未完了です。親の期待 node matrix は確定できません。

全変異を復元し、差分に変異が残っていないことを確認しました。

## 波及

所有外の関連面は無変更です。

- `tools/pegasus/paper_story_a2_certification.sh`：POLICY_PATH を読む caller。
- `tools/plotting/plot_a2_certification.py`：producer schema の consumer。`test_plot_a2_certification.py` は起動試行済みですが未実走。
- `test_hooks.py`／admission registry：既存 script path の分類。
- `test_ccbench_spawn_sites.py`／`test_campaign.py`：spawn 数・campaign caller の制約。
- `test_official_perf_closure.py`：reviewed producer の制約。
- 共有 receipt helper は B7 の環境条件を追加。共有 submitter harness は既存 A-2/A-6 ケースを残して拡張。
- A-2/A-6 policy、旧 `output/insights`、plotter、job body は基準 commit から差分なし。

## git status / diff --stat

```text
 M orchestrator/campaign/paper_story_a2_certification.py
 M orchestrator/tests/test_paper_story_a2_certification.py
 M orchestrator/tests/test_paper_story_a2_job_contract.py
 M tools/pegasus/submit_paper_story_a2_certification.sh
?? orchestrator/campaign/paper_story_b7_fixed5_regression.v2.json
```

```text
 .../campaign/paper_story_a2_certification.py       |  11 +-
 .../tests/test_paper_story_a2_certification.py     | 143 ++++++++++++++++++++-
 .../tests/test_paper_story_a2_job_contract.py      |  70 +++++++++-
 .../pegasus/submit_paper_story_a2_certification.sh |   4 +-
 4 files changed, 216 insertions(+), 12 deletions(-)
```

新規 JSON は未追跡のため `git diff --stat` に含まれません。

## 総括

実装と静的検査は完了、pytest と変異検出は基盤障害で未実走です。  
closed とは扱えません。  
所有範囲・既存 pin・partial 境界を維持し、変異は復元済みです。  
commit は作成していません。