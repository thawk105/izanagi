---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-17
wave: dev-wave-t2590-a1-sized-source-contract
seq: 2
---

## {{D:a1-sized-source-contract}}. A-1 balanced5 sized の source 契約は pilot と別 file で束縛し、attempt を pin しない

**決定:** sized 本走 (`paper-story-a1-20260901-balanced5-sized-v1`) の amended source 契約を
`orchestrator/campaign/paper_story_a1_source.v2.json` (schema `paper-story-a1-source/v2`、11 key) として置き、
module は study_id → (契約 path, sha256, source paths) の**固定 2 要素表**で pilot / sized を選ぶ。

1. pilot の v1 契約 (`paper_story_a1_source.v1.json`) の bytes、pilot の source 閉包 (10+4 / 5+4 path、順序込み)、
   `binding_matches` の既定判定、attempt-0004 の照合は変えない。pilot 公開受領証の判定は不変。
2. v2 契約は sized policy・sized 事前登録・patch・canonical head・sized の source 追補 README
   (`output/insights/2026-09-17/t2590-a1-sized-source-amendment/README.md`) を sha で束縛し、`attempt` key を持たない。
   sized の attempt 名は driver で照合しない。
3. hydrate 入力・依存 source の staging・source binding の生成・consumer の amended admission 発火を
   「pilot か」から「amended source 契約を持つ study か」へ置換する。`_trace0_commands_match` (configure argv の
   受理形) は変えない。
4. `_v3_group_intent` の pilot attempt-0004 条件は既存受領証の再構成に使われるため残し、sized は全 attempt で
   契約検算と hydrate を必須にする。
5. 登録 API・3 study 目の枠組み・bytes 級同一性検査・新 gate は作らない (D1986 前文、D1323)。
6. 受理集合の変化を記録する: 契約なし sized binding (5 / 10 path) は拒否へ、v2 契約入り sized binding
   (9 / 14 path、digest 一致) は受理へ、hydrate なし sized submit は拒否へ、登録条件を満たす sized measurement は
   全拒否から進行可能へ。pilot は不変。

**理由:**

- v1 契約の sha は pilot attempt-0004 の公開 source binding が `binding_matches` で照合する live pin である。
  v1 を書き換えると pilot の公開済み受領証の再検証が落ちる。sized は別 file で束縛するしかない。
- pilot の attempt pin は「走行中の study の attempt-0004 から追補を適用した」経緯の産物で、sized には追補前の
  attempt が存在しない。契約が束縛するのは source (pin + 指定 patch) であって attempt ではない。bench 前の
  infra 失敗のたびに契約版を切る形は、pilot の attempt 1〜3 の経験に照らして採らない。
- 4 点は 1 箇所の限定解除では足りない (D1973 却下案)。段 3 の敵対相談 2 本が、pilot 履歴 binding の互換・両契約
  混入・hydrate の無検査経路のいずれも反例を構成できないことを現物で検算した。
- T-2081 (D1323) は既存 5 境界 (submodule 直接の canonical pin + tracked-clean、build 直前の期待 materialization、
  consumer) が study 非依存に sized を覆うことを test で示して閉じる。sized 専用の検査は足さない。

**却下した選択肢:**

- v1 契約 JSON に sized を追記する — pilot の live pin を壊す。
- sized の attempt を `attempt-0001` に pin する — bench 前失敗のたびに契約版が要る。
- pilot の T-2397 追補 README を sized の `amendment` に流用する — 同 README は pilot study と attempt-0004 に
  自己限定している。
- 汎用の契約登録簿を作る — D1986 前文の「汎用化を足さない」に当たる。
