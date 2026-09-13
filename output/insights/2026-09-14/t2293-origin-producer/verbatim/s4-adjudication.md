# 段 4 裁定 — [T-2293] R1/R3 の producer 層

## 裁定の要旨

段 2 plan と段 3 の 2 レンズは独立に「plan 作り直し」と判定した。親は現物で裏取りし、次を裁定する。

**依頼が求めた「33 本の物理 campaign run を実行する executor」は、本 wave の制約
(「規律 2 を緩めない」「本題だけ」「仮想リスク向けの gate・検査・台帳・一般化は scope 外」) の下では
結線できない。** 結線には、受理集合を広げる変更か、ユーザーが scope 外と指定した層の新設が必要で、
どちらも親が単独で決めてよい範囲にない。したがって executor は実装せず、裁定パッケージで返す。

**代わりに、本 wave では「producer と consumer の待ち合わせ点」を呼び手申告から外す単位 1 を実装する。**
これは executor が入ったときにそのまま使われる契約であり、今日の公開正例で発火し、受理集合を狭める。

## 所見の裁定 (real / refuted、採否)

### 実装できない理由 (すべて real、採用せず裁定パッケージへ)

| # | 所見 | 判定 | 裁定 |
|---|---|---|---|
| B1 | 証拠発行器の exact-type gate が探索 layout を拒否する (`reflux_result_evidence.py:447-448, 1213-1214`)。`loop.py:451-452, 542` は `ExplorationCampaignLayout` を作る | **real** | **scope 外。** 解除は producer の発行可能型を**広げる**変更で、D1670 が渡した §G の 3 写像に含まれない。未裁定の受理拡大を親が入れない |
| B2 | consumer は sealed batch の evidence digest と record の一致を要求する (`reflux_formal_consumer.py:668-682`) が、reserve→commit→prepare→seal を行う production FSM は不在。`p3_autonomous_workload_trial.py:1859-1860` は台帳を読むだけで、遷移は test helper (`test_p3_autonomous_workload_trial.py:10754-10804`) が代行している | **real** | **scope 外。**「仮想リスク向けでない」新層だが、ユーザーが「本題だけ」と限定した範囲を超える大型機構 |
| B3 | q の wire を実 source へ適用する origin 専用 entry point が不在。既存経路 `p3_s4_loop_trigger_gating.py:781-797` は template 適用・検疫・auditor veto・condition gate を通す | **real** | **scope 外。** これを迂回して `run_campaign` を直呼びすると、従来拒否していた入力が実行・発行される。**規律 2 に抵触するので採らない** |
| B4 | 公開経路の返却値・失敗処理・計測集計の契約が無い。`p3_autonomous_workload_trial.py:3051` は単数 `campaign_root` 必須、`3902`/`3920` は completeness と Layer-3 chain を要求 | **real** | **scope 外 (R2・受入要件 18)。** 前回 wave で既に裁定パッケージ済み |
| B5 | 各 q の保守的所要時間・実予約済み batch・verified calibration を保持する場所が runtime に無い (`p3_autonomous_workload_trial.py:475-491`、`4840` は preflight 戻り値を捨てる) | **real** | **scope 外。** executor が無い状態で配線だけ置くのは DW-G04 の「発火しない機構」 |
| B6 | 本番 CLI に origin 経路が無い (`p3_autonomous_workload_trial.py:5475-5498`) | **real** | **既裁定 (D1853)。**本 wave でも置かない |

### 親 brief への所見 (採用)

| # | 所見 | 判定 | 裁定 |
|---|---|---|---|
| A1 | 「欠けているのは executor だけ」は現物と合わない | **real** | **採用。**裁定文と worklog を訂正する。欠けているのは executor・探索 layout 受理・台帳 FSM・source entry point の 4 つ |
| A2 | 物理 root を作っているのは共有 fixture builder ではなく `test_p3_autonomous_workload_trial.py:10634-10696` | **real** | **採用。**brief の記述を訂正する |
| A3 | brief の行番号 4 件が古い (`_run_workload` monkeypatch は 11117、`CampaignSummary` の field は 63-64、golden literal は `test_reflux_result_evidence.py:36-39`、R3 の durable write は 1388-1405) | **real (nit)** | **採用。**記録側で訂正する |
| A4 | ctx の field は 15 でなく 14 | **real (nit)** | **採用** |
| A5 | 374〜908 秒・authority 0 件・発行 3 条件 0/3 は本 wave の実測ではなく既存記録の引用 | **real** | **採用。**引用と明記し、今回の実測として再認定しない |
| A6 | 「非 test caller 0 件」は静的な直接参照の確認であり、動的呼出しを含む全経路の不存在証明ではない | **real** | **採用。**この限定を記録に書く |
| B7 | 固定名 `reports/execution-provenance.json` は production の配置ではない (production は content-addressed `reports/reflux-result-evidence-content/v1/execution-provenance/<sha256>.json`) | **real** | **採用。**brief の生死確認要件を「record の ref が指す先を検証する」へ訂正する。固定名 writer は追加しない |
| B8 | disk 回収は writer 認証ではない (`reflux_result_evidence.py:8-10`、`reflux_formal_consumer.py:20-26` が明記) | **real** | **採用。**名乗りを「API の bytes 注入経路を閉じる」に限定し、唯一 writer 性は運用前提と明記する |
| B9 | `result_record_bytes` の field 削除だけでは、`evaluate_formal_origin` を直接呼ぶ経路の受理集合は変わらない | **real** | **採用。**名乗りを supervisor 経由に限定する |
| B10 | summary の identity/root 一致は評価ループより前に設定される値なので実行完了の証拠にならない (`loop.py:605-614`) | **real** | **採用。**executor を作るときの設計要件として裁定パッケージへ繰り越す |
| B11 | `source_mask=0` の q0/q1 は同一 wire なので、2 本の生死確認は source 適用の欠落に対して恒真 | **real** | **採用。**生死確認の設計要件として繰り越す |

### refuted / 格下げ

| # | 所見 | 判定 | 根拠 |
|---|---|---|---|
| R-a | `generations == 2` 制約が blocker | **refuted (nit へ格下げ)** | `p3_autonomous_workload_trial.py:1520` は 2 を保持すれば通る。設計 §E は 33 本を generation 反復と別物と明記しており、分離を守れば影響しない |
| R-b | P6 そのものの未実装が本 wave の blocker | **refuted (nit)** | 本 wave の到達目標は `P6Unavailable` であって正の P6 判定ではない |
| R-c | 固定名 provenance の不在が consumer 到達の blocker | **格下げ (must-fix)** | 要件側の記述誤りであり、production 出力は ref 経由で到達できる |

## 採用する実装 (単位 1) — 証拠の待ち合わせ点を producer 側へ移す

**目的:** 起点試行の formal terminal が消費する 33 件の証拠について、**所在 (root と 33 個の path) と
bytes を、呼び手の申告から producer の決定的導出へ移す。**

1. **`evidence_path` を導出する。** `_build_origin_recovery_envelope`
   (`p3_autonomous_workload_trial.py:1336`) は、member ごとの `evidence_path` を呼び手入力
   (`OriginMemberPlanInput.evidence_path`) から取るのをやめ、
   `(capability の origin_id, run_plan_input.attempt_0_batch_id, q)` から
   `reflux_result_evidence.result_evidence_relative_path` と同じ規則で導出する。
   `OriginMemberPlanInput.evidence_path` は廃止する。
2. **evidence root を runtime 所有にする。** `_complete_origin_runtime`
   (`p3_autonomous_workload_trial.py:1840`) が `evaluate_formal_origin` へ渡す `evidence_root` を
   `runtime.campaign_output_root` に固定し、`OriginProducerInputs.evidence_root` を廃止する。
3. **record を disk から読む。** `_complete_origin_runtime` は 33 件の record bytes を
   `runtime.campaign_output_root / member.evidence_path` から q 昇順に読む。
   `OriginProducerInputs.result_record_bytes` を廃止する。
4. **回収時の検査 (すべて fail-closed、緩めない):**
   - 件数が exact 33、q が 0..32 の昇順、path が相異。
   - 各 file は symlink を追わない regular file として読む。
   - 読んだ record を `validate_result_evidence` に掛け、
     `result_evidence_relative_path(record)` が envelope の `member.evidence_path` と一致する。
   - 1 件でも欠落・不一致・重複があれば終端へ進まない (既存の失敗境界へ返す)。
5. **名乗りの上限:** 「執行が書いた証拠だけを受ける」とは言わない。閉じるのは **API の bytes 注入
   経路と path 申告**であり、同じ場所へ整合 bytes を置ける主体は排除していない。唯一 writer 性は
   trusted harness の**運用前提**として明記する (B8)。supervisor 経由の受理だけが狭まる (B9)。

**成果物影響 (DW-G05):** 放置すると、起点試行の formal terminal は「envelope が宣言した場所に
存在しない bytes」でも、呼び手が引数で渡せば成立しうる。採用すると、supervisor 経由の受理は
producer が決めた canonical path の現物に限られ、将来の executor はそこへ書けば結線される。
certified 選択・材料レポート・試行台帳の**現在値は 1 つも変わらない**。

## 変異事前登録 (DW-M01、実装前)

harness は `tools/mutation_harness.py`。`loop.py` / `pipeline.py` は enforcement source closure に
載るため登録しない (F923)。全変異の対象 file は `orchestrator/campaign/p3_autonomous_workload_trial.py`。

| # | 変異位置 | 無効化する述語 | 期待する赤 |
|---|---|---|---|
| M1 | `_build_origin_recovery_envelope` の `evidence_path` 導出 | 導出値の代わりに呼び手入力を使う | 呼び手が別 path を宣言する負例が受理される → 負例 test が赤 |
| M2 | `_complete_origin_runtime` の件数検査 | exact 33 を「33 以下」へ緩める | 32 件の負例が赤 |
| M3 | 同 q 順検査 | 昇順比較を集合比較へ変える | q を入れ替えた負例が赤 |
| M4 | 同 path 一致検査 | `result_evidence_relative_path(record) == member.evidence_path` を外す | 別 q の record を置いた負例が赤 |
| M5 | 同 evidence_root | `runtime.campaign_output_root` を呼び手値へ戻す | 別 root を指す負例が赤 |

**単一理由性の確認義務 (F820):** 実装後、各変異について「同じ入力を拒否する層が前後にも内側にも
無い」ことを確認する。確認できない変異は登録から外し、実効 gate へ再照準する。

**受理集合を縮小する wave なので、過剰拒否の正例も登録する:** 正しい 33 件を canonical path へ
置いた公開正例が `P6Unavailable` まで到達し続けること。これが赤なら過剰拒否である。

## 段 5 の分割

**1 単位。** 編集面が `p3_autonomous_workload_trial.py` と対応 test に閉じるため分割しない。
所有: `orchestrator/campaign/p3_autonomous_workload_trial.py`、
`orchestrator/tests/test_p3_autonomous_workload_trial.py`、
`orchestrator/tests/test_reflux_originless_compatibility.py`。
`loop.py` / `ident.py` / `model.py` / `campaign_claim.py` / `s8b_*` /
`reflux_result_evidence.py` / `reflux_formal_consumer.py` / `reflux_origin_topology.py` は変更しない。

## ユーザーへ返す裁定パッケージ (本 wave では実装しない)

| # | 択一 | 親の推奨 | 採らない場合の成果物影響 |
|---|---|---|---|
| **Q1** | 証拠発行器の受理型に探索 layout を加えるか。(a) 加える (受理拡大。維持する拒否述語と負例を同時に確定する) (b) 加えない | **(a)**。ただし受理拡大であることを明記し、探索型でも WAL・witness・attestation の拒否条件が効くことを負例で示す条件付き | (b) なら起点試行の証拠は永久に発行されず、executor を作っても record 0 件のまま |
| **Q2** | 台帳遷移の責任境界。(a) fixture ledger 上の integration に限定する (b) reserve→commit→prepare→seal の production FSM を作る | **(a)** をまず採り、(b) は別 wave | (a) なら「本番台帳まで結線した」とは名乗れない。(b) は大型機構で「本題だけ」を超える |
| **Q3** | q の wire を実 source へ適用する origin 専用 entry point を作るか。既存の検疫・auditor veto・condition gate を保つ形でしか作らない | **作る (別 wave)**。本 wave で迂回実装はしない | 作らないと executor は「候補と無関係な binary の結果」を材料にしうる (規律 2 に抵触) |
| **Q4** | 完了判定の書き換え。(a) 「fixture authority と台帳遷移を許し、空の実行 root から production executor・runner・issuer が 33 本の lock/WAL/provenance/record を生成し、supervisor が disk 回収した証拠で formal consumer が `P6Unavailable` へ到達する」限定 integration (b) 公開 trial の `complete` まで | **(a)** | (b) は R2・受入要件 18・completeness・Layer-3 chain を同時に要する |

**発行 3 条件は 0/3、本番 authority は 0 件のまま変わらない。**
「8c を結線した」「本番で 33 本を回した」とは名乗らない。
