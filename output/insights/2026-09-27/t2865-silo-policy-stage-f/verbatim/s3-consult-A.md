## 所見

1. **must-fix** — `codex/s2-plan.md:26,65`、`orchestrator/tests/test_p3_s4_loop_job_contract.py:546–559`。既存 test は `p3_s4_loop` を部分文字列で数えるため、`p3_s4_loop_policy` の呼出し追加も 3 件目に数える。「期待値変更不要」は成立しない。**放置時:** 契約 test が赤になり、方策 mode の受入を示せない。**代案:** 既存 driver の呼出しを行末まで識別する検査に直し、方策 driver の件数と前処理後の順序を別に検査する。

2. **must-fix** — `codex/s2-plan.md:28,34,70–71`、`orchestrator/campaign/p3_s4_loop_policy.py:373–405`。現行 `drive_iteration` は例外時に loop state を保存するが、履歴追記へ到達しない。pair が候補の例外を捕えて stock を続行するだけでは、候補の構造化理由は履歴へ戻らない。**放置時:** stock の WAL だけが残り、候補の失敗が自系列履歴から欠ける。**代案:** 候補例外と gate reject を区別し、記録可能な拒否は既存の構造化経路で履歴化する。例外を成功した pair として扱わず、WAL と履歴の対応を受入条件にする。

3. **should-fix** — `codex/s2-plan.md:17,32,47`、`orchestrator/campaign/p3_s4_loop.py:161–184`、`orchestrator/campaign/ident.py:203–232`。`pegasus` 契約の選択だけでは同じ campaign の証明にならない。`measurement_env`、admission policy、用途を含む `search_config`、環境契約の束縛が login と計算側で一致する必要がある。login の実 site を `_admit_env_contract` に渡すと拒否される。**放置時:** emit／reject の履歴と評価 WAL が別 campaign に割れる。**代案:** login の非計測操作に限って同じ構成値を明示生成し、両側の `ident.campaign_id` と canonical preimage を照合する実経路 test を置く。計測の site 判定は実 site のままにする。

4. **should-fix** — `codex/s2-plan.md:21,32,69`、`orchestrator/campaign/loop.py:720–750`、`orchestrator/campaign/p3_s4_loop_policy.py:210–216,330–410`。共有 base の評価 WAL は campaign lock で直列化されるが、方策の loop state と `policy_history.jsonl` の読書きはその lock の外にある。別 checkout の login 操作と計算 job が同時に同一 campaign を扱う場合の単一書き手条件が plan にない。**放置時:** iteration 番号や coder の自系列履歴が WAL と食い違いうる。**代案:** 同一 campaign の emit／preview／reject／run を運用上直列にし、その条件を job と runbook に明記する。

5. **should-fix** — `brief.md:5,16`、`verbatim/D2212-item4.md:3–6`。brief は「検査込み 2 node 時間」を確定済みユーザー裁定としているが、検査費を同じ線で数える部分は原文で親の解釈と明記されている。**放置時:** 投入確認の根拠と見積りの履歴が実際の裁定より強く記録される。**代案:** 実験 job の合計に対するユーザー裁定と、開発検査を加算する親の保守的運用を分けて記す。

6. **nit** — `codex/s2-plan.md:57–63`、`docs/failures.md:1156`。stock genome の flag を変える変異と source に patch を足す変異は、いずれも先行する source identity／admission で落ち得る。「stock source の分類だけ」という単一理由性はまだ示されていない。**放置時:** 変異の kill が狙った判定の証拠にならない。**代案:** 各変異について到達する gate と最初の拒否理由を固定し、実効 gate に照準を合わせる。

## plan / brief への代案

stock の原型 source、`BASE` から方策 flag を除く genome、patch 無しという組合せは、`source_digest.py:2307–2317,2413–2455` の current／HEAD 比較で `STOCK` になる設計と整合する。偵察の stock も同じ原型 source と `BACK_OFF=1` を使う（`silo_policy_recon.py:88–125`）。ただし build option 全体の同一性まで証明したとは記さず、stock の実 configure receipt で確認する。stock 用 context と resolver は候補の coder authority から分離する。

初回 stock を loop campaign に置くと、同じ variant の後続測定は terminal skip になる（`loop.py:770–885`）。bootstrap campaign の分離は妥当。`abort_rate` は CCBench の比率値で、`BENCH_DONE.leading_indicators.abort_rate × 100` を percent にする案も整合する（`common/result.cc:36–41`、`pipeline.py:1538–1551`）。欠損時に baseline を発行しない条件を保つ。再発を警戒する型タグは **[恒真ゲート] [テスト代表性] [consumer 取り残し] [リーク]**、特に F28 と F1020。

## 総括

所見は **6 件（must-fix 2、should-fix 3、nit 1）**。  
親への裁定依頼は bootstrap campaign の分離と R2 run id に加え、同一 campaign 操作の直列化条件を明文化すること。  
静的レビューのみ実施し、build・pytest・実測は行っていない。