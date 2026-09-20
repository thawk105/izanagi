## 6. 同jobのstock対照 — N1 / P1

**既存S4 job bodyにはstock armがない。候補だけを評価しても、ユーザー要求のstock対照を満たしたことにはならない。**

- shellはproposalまたはfixtureの排他的1起動のみ (`p3_s4_loop_pegasus.sh:580–593`)。
- S4 CLIの値口は `--value` と `--run-iteration`。stock指定口はない (`L:2797–2854`)。
- 値は有限な数学的整数1..1000。`-1` は `value-range` 拒否 (`backoff_hole_grammar.py:745–759`)。
- 候補genomeは `BACKOFF_FIXED=int(coder.value)`、templateとholeを通って評価される (`L:1930,1969–2012`)。`--value -1` をstock代用にはできない。

`tools/pegasus/*.sh` と `orchestrator/campaign/*.py` のCLIを検索し、近い経路を確認した結果は以下。

| 経路 | 本要求の代替にならない理由 |
|---|---|
| A1 paired | stock genomeはあるが、study・acquisition receipt・policyのscaleに束縛される。S4 proposalを追加するCLIではない (`paper_story_a1_paired.py:1467,7107–7128,8917–8928`) |
| B10 grid | 登録sweepを起動する。通常extendedはP2の100万records/48threads/3秒/5repを使う (`b10_backoff_grid.sh:610–635`、`backoff_extended_sweep.py:1384–1389`、`p2_2.py:54–57`) |
| floor campaign | official protocol束縛のdriver起動。S4候補とstockを同一jobへ組み合わせる口ではない (`floor_campaign.sh:1213–1225`) |
| guided `--genome` | 過去landscapeのreplayであり新しいstock実測ではない (`guided.py:225–242`) |
| `loop.run_campaign` | stockを評価し得るPython APIはあるが、既存S4 shellから呼ぶstock CLIではない (`loop.py:347–383`) |

**条件を満たす既存経路は見つからなかった。** 全shellと全CLIのあらゆる組合せについての不在証明までは未確認であり、N1の「他jobではpinも揃えられない」という強い一般化は採らない。確認できた障害は、S4候補と同条件stockを同jobで実行する既存の結線がないことである。

scope外の設計メモは次に限る。

- job bodyに、同allocation・同compiler・同依存prefix・同pinを保持するstock評価stepが必要。
- driver側に、無改変stock源、`BACK_OFF=1`、同 `default_perf()` を既存 `run_campaign` へ渡す評価口が必要。
- trace/perf別build、verifier、admission、排他、receiptを既存pipelineのまま通す。
- stock WALはpipeline自身が発行する。候補WALへ親がrecordを手書き・移植しない。
- stockを同campaignに含めるか別campaignにするかでidentityとdigestの意味が変わる。spec/search_configを変えればIDも変わる (`ident.py:196–229`)。`409e13f8`維持を先に約束しない。

従ってP1は「今回stock未実走として返す」方針にはできるが、**原依頼の完全達成条件としては不成立**。親の裁定にこの未充足を明記する。
