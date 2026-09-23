**NO-GO。must-fix 1件、should 3件。** 対象は `81745c268`・`16ee35040`。静的レビューのみで、テスト・変異 kill は実測していません。

以下、`H` は `orchestrator/campaign/t2849_comparison_harness.py`、`G` は `orchestrator/campaign/t2849_generators.py` を指します。

### 所見

1. **must-fix — 参照分類が stock 以外の source を受理する。**  
   [H:149](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2849-comparison-harness/orchestrator/campaign/t2849_comparison_harness.py:149) は WAL の `src_token` を使って variant の自己整合を調べますが、`source_digest.STOCK` との一致を要求しません。後段も非 null の確認だけです。`_control_median` の stock identity 検査も `block-stock` 限定です（H:645）。  
   静的な反例は、既存 `_write_attempt` に exact reference genome と `src="d"*64` を渡した証拠です。variant・全 WAL 行をその source に揃えれば、verify・bench が揃った別 source を参照として受理する経路になります。現在の stock-only producer がこれを通常生成するという指摘ではなく、consumer の参照 identity 制約の欠落です。参照にも stock source の一致と負例が必要です。  
   **放置時の影響:** 別 source の測定が参照の certified 集合へ入り、レポートの `reference`・`reference_ratio` が変わります。

2. **should — M12 の名指し試験は、実際の EI 呼出しへの雑音追加を検出しない。**  
   [G:152](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2849-comparison-harness/orchestrator/campaign/t2849_generators.py:152) を単独で `expected_improvement(m, v + NOISE, incumbent)` に変えると、登録された意味の変異になります。しかし `test_ei_latent_variance`（`orchestrator/tests/test_t2849_generators.py:37`）は posterior と EI 関数を直接呼び、`BOGenerator.ask` を通りません。この位置の変異は名指し試験に影響しません。  
   **放置時の影響:** BO の候補列を変える変異について、登録された kill の保証が成立しません。

3. **should — M18 は genome 照合のどちらを変異するかで、名指し試験の効力が違う。**  
   [test_t2849_comparison_harness.py:224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2849-comparison-harness/orchestrator/tests/test_t2849_comparison_harness.py:224) の二つの負例は、いずれも H:110 の sidecar genome 照合で先に拒否されます。そのため **H:151 の WAL build genome 照合だけを削る単一変異**では、この名指し試験は変わりません。別試験の `test_reference_incomplete_or_anomalous_not_certified[identity]` は当該境界を検査しています。登録位置を確定し、必要なら名指し試験へその負例を含めてください。  
   **放置時の影響:** WAL genome 束縛に関する変異台帳が、実際の検出先と食い違います。

4. **should — sweep の生成計算が `generator_wall_s` から漏れる。**  
   [H:512](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2849-comparison-harness/orchestrator/campaign/t2849_comparison_harness.py:512) で hash 計算・順序生成を済ませ、計時は H:534 から始まります。計上されるのは主に既成 tuple の取得です。設計 §5.5 の生成計算時間に初期化分も含める必要があります。  
   **放置時の影響:** sweep の生成器費用が過小報告されます。job Elapse 自体はこの理由では欠落しません。

### 攻撃が不成立だった観点

- **規律1・2・3、保全口:** 不成立。差分は cleanup 前の保全で、verify・anomaly reject・trace/perf の別 build を迂回していません。未設定時の cleanup、保全例外時の原本保持、元の結果・例外を維持する構造を確認しました。inventory を certification に使う接続もありません。
- **参照入口と証拠不足:** 上記 source 束縛を除き不成立。CLI は harness の stock-only に限定されています。genome 不一致、performance verify 欠落、anomaly 混入は certified に到達しません。
- **予算・endpoint・欠測:** 不成立。初期点は B 外、retry は論理 B を一度だけ加算、Tier0 は A のみ。初期点を含めて `select_endpoint` を再利用し、同 workload・cohort の全 ledger の anomaly を集めています。§4.6 の欠測優先と、固定後に次点へ選び直さない処理も確認しました。
- **情報境界・数値仕様:** 不成立。参照・共有対照・score は生成器へ渡らず、自系列の初期点と探索結果だけを tell します。重複は別 slot、`N_eval` と固定5 rep は分離されています。GP の log 座標・Matérn・潜在分散、進化の丸め・真の改善時だけの親置換は設計と整合します。初期点の同点は固定順序 5→10 により小さい値が残ります。
- **producer / consumer・K0役割:** 不成立。request／proposal／inputs／reject／costs／slot の名前と配置、`digest_path`、job env→CLI、driver→評価 CLI は接続しています。2 key の両役割への配送と継承照合も一致します。既存 `b5_llm_round`・`planner_context_payload` の K2 経路は変更されていません。

### M1〜M25 の静的評価

「検出経路あり」は実測 kill を意味しません。

| 変異 | 評価 |
|---|---|
| M1〜M3 | 検出経路あり。CLI 到達・exact genome・入口拒否を直接検査。 |
| M4〜M7 | 検出経路あり。保全物、原本、結果・例外、未設定時の副作用を検査。 |
| M8〜M9 | 検出経路あり。初期点 B=0、retry 後の B と物理呼出し数を検査。 |
| M10〜M11 | 検出経路あり。Tier0 除外、独立した2×2数値 oracle。 |
| M12 | **所見2。変異位置によって名指し試験が生存。** |
| M13〜M17 | 検出経路あり。親保持、初期点 endpoint、他系列失格、品質欠測、最新正常値を検査。 |
| M18 | **所見3。sidecar と WAL の照合を区別する必要あり。** |
| M19〜M22 | 検出経路あり。2 session／5 rep、K0 argv、a≠b、費用の event 転記を検査。 |
| M23〜M25 | 検出経路あり。実 shell の lock・単一起動、両役割の入力を検査。 |

### D1861

正規 renderer を書込みなしで再計算しました。**両 adapter とも bytes が完全一致**しました。基準からの変更 pointer も、両方とも次の4箇所だけです。

- `/developer_instructions`
- `/source/sha256`
- `/review_ledger/source_file_sha256`
- `/semantic_digest`

人手による renderer 外の JSON 編集という攻撃は**不成立**です。

## 総括

**所見4件：must-fix 1／should 3／nit 0。NO-GO。**

参照 source の束縛を修正し、M12・M18 の変異位置と検出先を確定する必要があります。親の焦点走・変異実測結果は本判定に含めていません。