# [T-2293] R1/R3 の producer 層 — 結線できた部分とできなかった部分

authority: none
default_effect: no-state-change

可変状態の正本は `docs/worklog.md` 末尾と現行 phase doc である。本書は wave の一次資料で、
逐語は `verbatim/` に凍結してある。

- wave: `dev-wave-t2293-origin-producer-2` / branch `worktree-dev-wave-t2293-origin-producer-2`
- 起点: local main `abbef52d5`。記録前に `12fbe0919` を取り込んだ。
- 実装 commit: `57eeaad54`

## 1. 依頼と、依頼の前提が覆ったこと

依頼は「契約側が着地済みの R1 (lifecycle start の起点専用 optional key `origin_run_plan_sha256`) と
R3 (`execution-provenance/v2`) について producer 層を設計・実装し、実運用 consumer と同じ変更単位で
結線する。結線できないなら何を結線できなかったかを構造化して返す」だった。

**brief 前の実測で、「producer 層が未実装」という前提は成立しないと判明した。**

| 主張 | 実測 |
|---|---|
| R1 の producer が無い | **ある。**`run_trial` が envelope を create-only で書き、sha256 を `record_trial_start_once` へ渡す (`p3_autonomous_workload_trial.py` の origin 分岐) |
| R3 の producer が無い | **ある。**`reflux_result_evidence.issue_campaign_result_evidence` が `execution-provenance/v2` を書き、`loop.run_campaign` が `result_evidence_context` 非 None のとき per-result で呼ぶ (D1853) |
| 欠けているのは executor だけ | **不十分。**欠けているのは 4 つ (下記 §3) |

**本当に欠けていたもの:** 33 本の物理 campaign run を実行する executor が存在せず
(`_execute_origin_topology` は repo に不在)、33 本ぶんの証拠は **test fixture が作り、
呼び手が `OriginProducerInputs.result_record_bytes` として手渡していた**。
つまり起点試行の formal terminal は「実行」ではなく「申告」で成立しうる状態だった。
既存 test は `_run_workload` を観測 wrapper で包み、物理証拠を後付けで materialize している。

## 2. 実装したもの — 証拠の待ち合わせ点を producer 側へ移す

`57eeaad54`。編集面は `orchestrator/campaign/p3_autonomous_workload_trial.py` と
`orchestrator/tests/test_p3_autonomous_workload_trial.py` の 2 file。

1. envelope の member ごとの `evidence_path` を呼び手入力から外し、
   `(capability の origin_id, attempt_0_batch_id, query_ordinal)` から
   `reports/reflux-result-evidence/<origin_id>/<batch_id>/<q>.json` の規則で導出する。
   `OriginMemberPlanInput.evidence_path` を削除した。
2. `_complete_origin_runtime` が `evaluate_formal_origin` へ渡す `evidence_root` を
   `runtime.campaign_output_root` に固定し、`OriginProducerInputs.evidence_root` を削除した。
3. 同関数は 33 件の record bytes を `runtime.campaign_output_root / member.evidence_path` から
   `query_ordinal` 昇順に読む。`OriginProducerInputs.result_record_bytes` を削除した。
4. 回収時の検査は fail-closed — 件数 exact 33、ordinal が 0..32 の昇順、path 相異、
   symlink を追わない regular file、`validate_result_evidence` 通過、
   `result_evidence_relative_path(record)` と `member.evidence_path` の一致。

**名乗りの上限。** 閉じたのは **supervisor 経由の bytes 注入経路と path 申告**である。
同じ場所へ整合 bytes を置ける主体は排除していない (`reflux_result_evidence` と
`reflux_formal_consumer` の冒頭が「create-only は writer 認証ではない」「整合的な lock / WAL の
後置きは拒否できない」と明記している)。唯一 writer 性は trusted harness の**運用前提**である。
`evaluate_formal_origin` を直接呼ぶ経路の受理集合は変わらない。

## 3. 結線できなかったもの (構造化)

| # | 未接続箇所 | 何が無いから届かないか | 本 wave で採らなかった理由 |
|---|---|---|---|
| B1 | 探索 layout → 証拠発行器 | `loop` は `ExplorationCampaignLayout` を作るが、`reflux_result_evidence` の exact-type gate は `CampaignLayout` だけを受理する | 解除は producer の**発行可能型を広げる**変更。D1670 が渡した §G の 3 写像に含まれない未裁定の受理拡大 |
| B2 | disk の record → sealed batch | consumer は sealed member の evidence digest と record の一致を要求するが、reserve→commit→prepare→seal を行う production FSM が無い。遷移は test helper が代行している | 大型機構。依頼の「本題だけ」を超える |
| B3 | q の wire → 実 source | 起点専用の物理 entry point が無い。既存経路は template 適用・検疫・auditor veto・condition gate を通す | 迂回して campaign を直呼びすると従来拒否していた入力が実行・発行される。**規律 2 に抵触するので採らない** |
| B4 | origin 実行 → completion / report | 単数 `campaign_root` 必須、positive cell admission、completeness / Layer-3 chain が単一 campaign 前提 | R2 と受入要件 18。前回 wave で裁定パッケージ済み |
| B5 | 各 q の残時間・実予約 batch・verified calibration | runtime にどれも保持されていない。`ReservationCheck` の preflight 戻り値は捨てられている | executor が無い状態で配線だけ置くのは「発火しない機構」 |
| B6 | 本番 CLI → origin | CLI に origin 引数が無い。fixture provider の real build は拒否され、`--no-build` は手前で戻る | D1853 が既に却下済み |

## 4. 段 3 と段 6 が覆した親の記述

段 3 の 2 レンズはいずれも「plan 作り直し」と判定した。段 6 のレンズ A は must-fix 1・nit 3、
レンズ B は blocker 0・must-fix 0・nit 1 を返した。親が採用した訂正は次のとおり。

- **恒真化の指摘 (段 6 レンズ A N1)。** 事前登録した 5 変異のうち「件数 exact 33」「ordinal 昇順」
  「path 相異」の 3 つは、`RecoveryEnvelope` の member 検査が既に保証しており後段では必ず真になる。
  DW-M01 / F28 に従って登録から外し、実効 gate へ再照準した (§5)。
- **固定名 `reports/execution-provenance.json` は production の配置ではない。** production は
  内容アドレスの `reports/reflux-result-evidence-content/v1/execution-provenance/<sha256>.json` に書く。
  親 brief の生死確認要件を「record の ref が指す先を検証する」へ訂正した。
- **物理 root を作っているのは共有 fixture builder ではなく test 内の materialize helper。**
- 親 brief の行番号 4 件が古かった。ctx の field は 15 でなく 14。
- 「374〜908 秒」「本番 authority 0 件」「発行 3 条件 0/3」は既存記録の**引用**であって
  本 wave の実測ではない。「非 test caller 0 件」は静的な直接参照の確認であり、
  動的呼出しを含む全経路の不存在証明ではない。

**real だが scope 外と裁定した所見 (段 6 レンズ A must-fix M1):** 導出先に writer のいない
名前付きパイプを置かれると、共有 read helper の open が戻らず回収が止まる。
(a) 本 wave が触っていない共有 helper の既存性質、(b) 証拠置き場へ書ける敵対者を仮定して初めて成立し、
その敵対者は本 wave が宣言した運用前提が除外している、(c) 依頼が仮想リスク向けの gate 追加を
scope 外と明示している — の 3 点から積み残しとする。nit 3 件 (symlink 負例が読取り層まで届かない、
親 directory 差替えの競合、受入 duration 台帳への新規 23 ケース未登録) も同じ扱い。

## 5. 変異

`tools/mutation_harness.py --runner-mode dispatch --detached`。
runner = `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_p3_autonomous_workload_trial.py -q -rf`。

- probe (spec sha256 `52007c5ff6468d8b6e19ceae71291e15c166553f60e6e57f875c5bd4acfcb12c`、
  全件 SURVIVED 登録) で観測 node を集めた。台帳は `mutation-ledger.probe.json`。
- 本走 (spec sha256 `a709422d5b3f85c3b0abee062ebf05b63e03f666533cbde44dd2875bdd345e43`、
  repo_head `0047d24db`) は **baseline PASSED、4/4 KILLED、期待 node 完全一致、MISMATCH 0**。
  台帳は `mutation-ledger.final.json`。

| id | 変異 | 観測 node 数 | 意味 |
|---|---|---|---|
| MX1 | record から導いた path と member の宣言の一致検査を無効化 | **1** | 実効 gate。`wrong-query` 負例が単独で担保し、単一理由性が成立する |
| MX2 | `evidence_path` 導出で origin_id と batch_id を入替え | 12 | 導出そのものの破壊 |
| MX3 | consumer へ渡す evidence_root を runtime 所有から外す | 3 | root 固定の破壊 |
| MX4 | ordinal 期待を 1..33 へずらす (positive) | 10 | 正当な 0..32 を過剰拒否すると公開正例が赤になる |

**この wave が足した実効的な新設ゲートは MX1 の 1 本だけである。**
`evidence_path` / `evidence_root` / `result_record_bytes` の削除は型レベルの縮小であって
変異で測れる gate ではない。件数・順序・相異は envelope 側が既に保証している。

## 6. 検査

- 焦点走 (login node): `test_p3_autonomous_workload_trial.py` + `test_reflux_originless_compatibility.py`
  で 291 passed。consumer 拡張分は 937 passed / 5 skipped と 1053 passed。
- `check_ai_provenance.py` 全史 rc=0 (新規違反なし)。
- 受入全走の結果は worklog に記す。

## 7. 発行 3 条件と名乗り

**発行 3 条件は 0/3、本番 authority は 0 件のまま変わらない。**
「8c を結線した」「本番で 33 本を回した」「P6 が発火する」とは名乗らない。
certified 選択・材料レポート・試行台帳の現在値は 1 つも変わらない。
