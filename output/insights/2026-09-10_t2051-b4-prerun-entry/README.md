# [T-2051] B-4 分析経路の正式起動口 — 依頼 4 項目のうち 3 項目は着地済みで、実際に空いていたのは裁定済み未実装の D1880 だった

2026-09-09 〜 2026-09-10。branch `worktree-dev-wave-t2051-b4-prerun-entry`。起点 main `7f17e1c63`。
実装 commit `67e835a03`。

**名乗りの上限。** 閉じたのは **formal bootstrap が analysis manifest 外の attempt を拒否すること**
だけである。「B-4 の分析経路が端から端まで通る」「§7.1 の全件報告が実効化した」
「certified 選択へ接続した」とは書かない。理由は §3 の停止地点表に実測で示す。

## 1. 依頼の前提が着手前に覆っていた

依頼は「分析経路の正式起動口、不変な結果 artifact の writer、§7.1 の全件 report generator、
certified 選択への必須配線を実装する。現状は正式起動口が無いため、全件 report を正式経路から
出せない」だった。着手前の実測で、**4 項目のうち 3 項目は既に着地している**と分かった。

| 依頼項目 | 実測 |
|---|---|
| 正式起動口 | `orchestrator/campaign/p3_b4_material_report.py` の CLI が 2026-09-01 ([T-2049]) に着地。`--help` rc=0、不在 root に `publication_rejected: publication_root_invalid` rc=2 |
| 不変な結果 artifact の writer | 2026-08-29 に着地 |
| §7.1 の全件 report generator | 生成器は 2026-09-01 に着地 |
| certified 選択への必須配線 | 未着地。T-2139 (2026-09-01) が「現 checkout では完成できない」と裁定し再開条件を残した |

**ただしこの表の読み方には限定が要る。** 段 3 のレンズ B が指摘したとおり、着地しているのは
`p3_b4_analysis_path.py` の docstring が列挙する 5 語の台帳の中での話であって、
**依頼の文言に照らすと 3 項目とも部分的である。**

- 「不変な writer」は create-only であって不変ではない。同一 path の異 bytes を拒否し
  同一 bytes を idempotent success にするが、削除後の別 bytes 再発行は排除しない。
- 「§7.1 の全件 report generator」は §7.1 を満たさない。生成物自身が
  `section_7_1_four_classifications_operationalized: false` と宣言し、manifest 非選択 attempt には
  ID / path / status しか持たせない。§7.1 が各行に要求する arm・campaign id・各 hash・WAL・
  停止理由・予算・verdict・anomaly class・性能値の有無は揃わない。
- 「正式起動口」は分析 chain 全体の起動口ではない。launcher が覆うのは
  `admission 検証 → context/sidecar → 単一 arm の driver main` までである。

## 2. 実際に空いていたもの — 裁定済みで未実装の決定

親の provisional 裁定 P1 は「本 wave に、今日発火する実装面の純増は無い」だった。
段 3 のレンズ B が manifest membership を実装候補に挙げ、レンズ A は
「母集合を manifest 201 行にするか registry 全行にするかが未裁定だから実装へ送るな」と保留を求めた。

**親が台帳を引いたところ、この点は D1880 (2026-09-09) で裁定済みだった。** レンズ A の保留理由は
現物で refuted である。同じ /rulings 回で D1881 (事前登録が publication root を 1 つ名指しし、
発行器が他を拒否する) も裁定されており、こちらも未実装のまま残っている。

production コード自身が空白を宣言していた —
`orchestrator/campaign/p3_s4_loop.py` の非保証 tuple 項目 3 は
`"manifest membership は検査しない (裁定パッケージ 3)。"` だった。

### 実装した 1 単位

`require_b4_proposal_registry_binding()` は期待 hash を `publication.registry.scheduled_attempts`
から引くだけで `publication.manifest.rows` を見ていなかった。ここへ
**同じ attempt_id が manifest の行にちょうど 1 件存在すること**の要求を足した。
3 driver (base / sort / trigger) の bootstrap すべてに効き、continuation 経路には掛からない。

**放置した場合の成果物影響 (`DW-G05`):** manifest 外の registry 行を attempt id に指定した
formal bootstrap が受理され、build と WAL が進む。その結果は raw record producer の
`_manifest_row()` が後から拒否するため、**走ったのに §7.1 の全件報告に現れない campaign** が作れる。
事前登録 §7.1 が名指しで禁じる file-drawer 経路である。

受理集合は狭まる方向だけで、広げる変更は無い (規律 2)。

## 3. 停止地点 — 6 層 × 3 状態

**状態語を区別する。** `observed stop` = 実際に走らせて拒否を観測した。
`unreached` = 入力を作っていないので拒否も観測していない。
`static expected rejection` = コードから読める予測であって実測ではない。
段 2 plan は L2 を「停止した」と書いたが、両レンズが独立に「それは静的予測であって実測ではない」と
指摘したので、この区別を導入した。

| 層 | 状態 | 実測または根拠 |
|---|---|---|
| 1 規範・admission | **observed stop** | `p3_b4_launcher.py bootstrap --driver base --arm on` を実走。rc=1、`B4AdmissionRecordError: [admission-record] record is unavailable`。`docs/phase3-b4-reflux-ablation-admission-record-{base,sort,trigger}.json` は 3 件とも不在。事前登録 §5 は `未記入` を含む値セルが 7 行 |
| 2 権威ある母集合 → 予定表 producer | **unreached** | 実成果物から `B4ScheduledAttemptInput` を導く production 経路が存在しない。`p3_b4_analysis_ledgers.py` が自ら authoritative producer の不在を宣言する。適格性は `whiteboard_result == REJECTED` + 赤 class を要求する |
| 3 publication 発行 | **unreached** + static expected rejection | `issue_b4_prerun_publication` の production 呼び手は 0 件で CLI も無い。適格 201 行未満なら `design_not_feasible` になるが、**実際の拒否 receipt は存在しない** |
| 4 全 block・全 arm 実行調停 | **unreached** | launcher は単一 arm の driver 起動までしか覆わない。201 block × 2 arm の完走を調停する経路が無い |
| 5 driver 終端 → raw writer | **unreached** | `publish_b4_attempt_result(s)` を呼ぶ production 呼び手が 0 件 |
| 6 report → certified 選択 | **unreached** | `report.complete` 0 件、report 生成後の正規呼び手 0 件、耐久化した判定の置き場 0 件 |

### 母集合の実数

- 3 driver の loop campaign の whiteboard は合計 7 件で、内訳は success 7 / rejected 0。
- `output/campaigns/p3-s4-red-s4-red-consumer-9a1897c4/s4_rejections_digest.txt` に赤が 3 件ある。
  ただし同 campaign には `loop_state.json` が無く whiteboard を持たないため、適格性述語を満たせない。
- **したがって赤 precursor は「0 件」ではなく「最大 3 件、適格確認 0 件」である。** 要求は 201 件。
- `campaign.lock` を `b4_reflux_ablation` marker で走査して hit 0 件。B-4 marker を持つ campaign は
  1 件も無い。

**権威ある母集合が同定されていないため、「母集合全体が厳密に 0」とは書かない。**
検索 root は `/work/1/SFC/tanab/izanagi/output` である。issuer は任意の絶対 root を許すので、
この範囲外の publication を排除する主張はできない。

### 201 の意味

`EXPECTED_BLOCK_COUNT == 201` の機械条件は「**201 件の適格な型付き registry 行**」であって
「201 件の実 precursor file の存在」ではない。実装は元 artifact を再導出しない。
規範側 (事前登録 §5.1.1) が凍結母集合由来であることを要求する。

## 4. 親 brief の訂正

段 3 の 2 レンズと親の追加実測で、段 1 brief の 12 項目を訂正した。主なものは次のとおり。

| ID | 訂正 |
|---|---|
| M4 | T-2139 の再開条件は無条件 3 件 + 順方向を含める場合 1 件 = 4 項目 |
| M8 | 「publication が最初の停止点」は誤り。admission record 検証が先に走る |
| M11 | 201 の機械条件は型付き行であって実 precursor ではない |
| M13 | 赤 precursor は 0 件でなく最大 3 件、適格確認 0 件 |
| M14 | §5 の `未記入` を含む値セルは 6 行でなく 7 行 |
| M18 | 「未 commit 差分の hit 0 ⇒ 編集面重複なし」は commit 済み作業面を見ない。親は全 worktree の `p3_s4_loop.py` を内容 hash で照合し直し、main HEAD と異なる 9 件がいずれも古い基点による差であることを確認した |

## 5. 段 6 の敵対レビューが実装前に潰したもの

production 実装への must-fix は 2 レンズとも 0 件だった。**test への must-fix が 1 件あった。**

段 5 の負例は `monkeypatch.setattr(issuer, "load_b4_prerun_publication", ...)` で loader を
差し替え、`dataclasses.replace` で合成した publication を返していた。レンズ A は
その合成 publication が block_id 重複・sealed hash 未更新のため**正規 loader が受理できない**ことを
示し、「実 issuer が 202 件の適格行を発行すれば 202 番目が manifest 外になるので、差し替えなしの
負例を書ける」と構成まで示した。レンズ B も同じ形を real と判定した (must-fix でなく nit と評価)。

親は A の判定を採り、fix で差し替えを撤去した。現在の負例は実 issuer が発行し実 loader が受理する
202 件 publication を使う。提案 hash と driver は一致させてあるので、拒否理由は membership 1 つに
絞られている。

## 6. 変異

事前登録 5 件。probe を全件 SURVIVED 登録で先に走らせて観測 node を集め、本走 spec は
その実測から作った (`DW-M08`)。

| ID | 変異 | 期待 | 結果 |
|---|---|---|---|
| M1 | membership の要求を削除 | KILLED | KILLED (負例 3 node) |
| M2 | 走査対象を manifest から registry へ替えて恒真化 | KILLED | KILLED (負例 3 node) |
| M3 | 件数要求を `!= 1` から `< 0` へ緩める | KILLED | KILLED (負例 3 node) |
| M4 | 非保証 tuple の項目 3 を旧文言へ戻す | KILLED | KILLED (exact pin test 1 node) |
| M5 | membership 検査を hash 照合の後へ移す | SURVIVED (等価) | SURVIVED |

**本走: baseline PASSED、4 KILLED + 1 SURVIVED、`matching: 5`、MISMATCH 0、rc=0、
`repo_head = 67e835a03`。期待 node は完全一致した。**

M5 は `anchor_counts = {"0": 1}` と `injection_diff_sha256` を持つので、注入は実在したうえで
生存している (`DW-M04`)。順序は拒否理由を変えるが受理集合を変えない、というレンズ A の判定と一致する。

一次資料は `mutation/mutation-spec.json`、`mutation/mutation-report.json`、
probe 側は `mutation/mutation-probe-spec.json`、`mutation/mutation-probe-report.json`。

## 7. セッション異常と手順の失敗

- **変異 harness の起動で 3 回はじかれた。** (a) runner argv に `-rf` が必須 (`DW-M08`)、
  (b) category は `negative` / `positive` / `both-layers` のみで `equivalent` は無い、
  (c) spec の `timeout_seconds` が dispatch 待機契約 (`queue_wait 3600 + grace 600`) より短いと拒否される。
  (c) は D612 の上書きを使うときに必ず当たる不一致で、既知の T-2484 と同型である。
  `timeout_seconds` を 4500 へ上げて通した。
- **焦点走の対象集合を親が取り違えた。** 親は変更 production file の module 名で
  `orchestrator/tests/` を grep して 28 file を得たが、レンズ B が **projection closure 経由の
  間接 consumer 2 件** (`test_p3_b4_admission_record.py`、`test_p3_b4_producer_auth_experiment.py`) と
  collection meta-test 1 件 (`test_acceptance_schedule_order.py`) の漏れを名指しした。
  `p3_b4_closed_critic.projection_closure_manifest` が `p3_s4_loop.py` の bytes を読むためである。
  31 file へ広げて走らせ、**3187 passed / 17 skipped / rc=0**。
- **焦点走を 1 回取り下げた。** レビュー前に投入した 28 file の走行は、fix 子が worktree を編集すると
  計測が汚染される。対象集合も作り直しになるため `qdel` した。orphan hold の残留は無いことを確認した。
- 親の最初の焦点走は Bash の 580 秒 timeout で切れて `rc=124` になった。dispatch は queue 待ちを
  含むため、以後はすべて背景 job + 待ち手にした。

## 8. この wave がしていないこと

- B-4 の正式実走、qsub による campaign 実行、build、性能測定。
- 事前登録 doc の編集。§5 の値セルは 1 つも埋めていない。
- closure 5 file の編集。事前登録 §5 の sha256 pin と現物の一致は着手前に確認済みで、
  1 byte も触っていない。
- `evaluate_analysis` の新規 production caller の追加。exact pin (2 件) は変えていない。
- D1881 (publication root の名指し) の実装。凍結事前登録の編集を伴うため本 wave の scope 外。
- certified 選択への接続。T-2139 の無条件再開条件 3 件が 1 件も成立していない。

## 9. ユーザーへ返す裁定パッケージ

1. **D1881 の実装担当と時期。** 裁定は 2026-09-09 に下りているが未実装である。事前登録に
   publication root を 1 行足す必要があり、凍結文面の編集を伴う。
2. **母集合 201 件をどう作るか。** 適格な赤 precursor は現在 0 件で、3 driver の loop 履歴は
   success 7 件である。事前登録 §5.1 は「予算上 n を確保できないなら『記述統計に留め有意性を
   主張しない』と本書に先に宣言してから実走する」という逃げ道を先に用意している。
   n を下げるのか、precursor の供給源を変えるのかは実験設計の判断である。
3. **陳腐化した非保証 2 件の erratum。** `p3_b4_prerun_issuer.py` の
   `formal_launcher_not_wired_to_require_this_receipt` は、launcher が `cd47c4651` (2026-09-09) 以降
   publication を必須にしたので偽である。`p3_b4_raw_record_producer.py` の
   「`initial_proposal_sha256` を計算・記録する経路が repo に無い」も、T-2101 が再導出と照合を
   実装したので前段が偽になった。後段 (束縛は転記に留まる) はなお真でありうる。
   **後者は report へ射影される**ため、独立の裁定が要る。凍結 receipt field と凍結文面なので
   黙って直さない。
4. **事前登録 §7.2 / §10 の陳腐化。** 「正式 launcher への必須配線も無く」は 2026-09-08 の追記だが、
   配線は 2026-09-09 に着地した。凍結文面なので本 wave では書き換えていない。
5. **T-2139 の持ち主と保存先。** report 生成後の正規呼び手、耐久化した判定の置き場、
   sink からの参照の 3 つを誰が持つか。

## 10. 子の内訳

Codex `gpt-5.6-sol` / `reasoning=xhigh` を plan 1、consult 2、author 1、review 2、fix 1 の計 7 本。
全件 `tools/check_codex_output.py` rc=0。read-only の子は pytest を実走していない。
**子の未実走を緑と記録していない。** 実測はすべて親が行った。
