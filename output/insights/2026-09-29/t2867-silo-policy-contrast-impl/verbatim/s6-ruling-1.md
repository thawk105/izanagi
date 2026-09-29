# [T-2867] 段 6 裁定 1 (親、2026-09-29 15:5x JST)

入力: レビュー R1 `codex/s6-review-r1/out.md` (NO-GO)、R2 `codex/s6-review-r2/out.md`、親の焦点走 `focus-1.log` (278 passed / 6 failed)、親の点検 (P1〜P4)。
対象 commit: `12eb785c0` (段 5 統合)。統合 snapshot の退避: `patches-s5/{x,y,z}.patch` と commit 自身。

## 裁定 (全件 real、下の F 番号で fix へ)

| F | 出所 | 内容 | 所有 | 成果物への影響 |
|---|---|---|---|---|
| F1 | R1-1・R2-1 | `endpoint-fixed` の形を 1 つに: event 直下に `logical_slot`・`variant`・`source_digest`・`fitness_tps`。launcher が書き、driver が読んで出所 slot の結果 (variant・source_digest) と一致を確かめる | Y (launcher)・X (driver) | score job が全系列で測定前に止まる |
| F2 | R1-2・R2-2 | 系列の終了を台帳に 1 度だけ記録する関数 `close_series_if_done(ledger)` を台帳 module に置く (score 5 件完了 → B = 10 なら `b-complete`、そうでなければ `a-exhausted`、参照 10 件完了 → `b-complete`、機械故障 retry 上限 → `machine-retry-exhausted`、job 1 の stock 不成立 → `stock-unestablished`、予算枯渇で endpoint 無し → `b-complete`/`a-exhausted` (report が fallback を当てる))。driver は単位の最後に、launcher は `submit`・`status` の前に呼ぶ | Y (関数と launcher)・X (呼出し) | 完走系列を report が欠測にする |
| F3 | R1-3 | auditor の veto を A の段階で確定する: 対照の `--preview-diff`・`--record-reject` は `{coder}` だけでなく `{coder, auditor}` も受け、auditor があれば既存 `policy_gate` の veto・digest 照合を write=False で掛ける。round の `finalize` は完成 proposal で preview し、拒否なら同じ file で record-reject → `opportunity-end rejected` | X (driver)・Z (round) | veto 候補が B を消費し評価 job を起こす |
| F4 | R1-4・R2-3 | 親の成功判定は、その起動の後に増えた `opportunity-end` のうち `proposed`/`rejected` だけを数え、無ければ `empty` を追記 | Z | 429 の後の正常終了で A が確定しない |
| F5 | R1-5・R2-4 | round・親・report のテストの台帳は `ContrastLedger.create/append` で作る (event file を手で書かない)。各テストが本来の assertion に届くこと | Z | 6 本のテストが検査本体に届かない |
| F6 | R1-6・P1 | job 1 の初期点の履歴 iteration を `logical_slot` の index で決める (seed-0 → −2、seed-1 → −1)。部分 retry で履歴行を重複させない (その seed の行が既にあれば足さない) | X | 部分 retry で coder の履歴の順が狂う |
| F7 | R1-7 | stock 不成立 (outcome が certified でない) の job 1 の後は `series-end stock-unestablished` (F2 の関数に含める)。`next_unit` は終了後 None | Y | 不成立系列で A・B と job を消費する |
| F8 | R1-8 | report は score の各行の variant・source_digest が `endpoint-fixed` と一致することを確かめ、不一致は規約不適合 | Z | 誤った identity の score が比較に入る |
| F9 | R2-5・R2-6・P2 | 原提案番号 a の導出を台帳 module の 1 関数に置く: `open_opportunity(ledger)` = 最後の `opportunity-start` で `outage` 以外の end が無いものの a (無ければ None)、`next_opportunity(ledger)` = A の使用数 + 1。driver の対照 record-reject と launcher と round はこれを使う。A・B と未終端 slot は `series_state` の値を使い、report・driver で数え直さない | Y (関数)・X・Z (呼出し) | 役割の異常終了の後に却下の履歴行と台帳の a がずれる |
| F10 | R2-7 | IR の tagged 変換は生成器 module の `tagged` を driver からも使い、driver の `_tagged_ir` を消す。台帳の書込みを t2849 から import しない点は段 4 裁定どおり (B-5 の event 種類に結合) で refuted | X | 変換規則の二重持ち |
| F11 | R2-8 | 拒否の検査段別の内訳を台帳に残す: 却下の `opportunity-end` に `reject_subtype`・`reject_rule_id` (preview の値、auditor veto なら `auditor-veto`)。report は arm ごとに A の使用数と拒否の内訳を出す | Y (launcher)・Z (round・report) | 草稿 §7.4 の報告項目が欠ける |
| F12 | P3 | G_rand の grow 法: 要求型を返せる**演算子** (条件式・比較・min・max・飽和加算・飽和減算・有界 shift のうち型に合うもの) から一様に選び、比較のときだけ operand の型を許される型 (u32・u64・bool、abort hook では reason も) から一様に選ぶ (草稿 §4.4 の逐語)。現行は比較を operand 型ごとに別の候補に数えている | Y | 生成器の分布が登録と違う |
| F13 | P4 | critic に初期点の性能が届くようにする: driver は評価 slot に加えて seed slot でも `critic_digest` を作る。round の critic 材料は各行に `fitness_tps`・`abort_rate_pct`・`quality`・`outcome` を載せる | X・Z | 草稿 §4.1 (初期点の性能は critic 経由で coder に届く) が成り立たない |
| F14 | P5 | 親の指示文: 各役割の前に out dir の保存済み出力を確かめ、あれば再利用し未完の役割だけを同じ入力で行う (草稿 §5.5) | Z | 429 の後に完了済みの役割をやり直す |
| F15 | P6 | 親は各起動の `out.json` の `modelUsage` の key (model ID) を `opportunity-end` の `models` に記録する (判定は report・人の側、新しい gate は足さない) | Z | 草稿 §5.5 の model 不一致を後から確かめられない |
| F16 | R1 M5 | proposal sha256 不一致の単位で rc=2 かつ `slot-start` が書かれないことのテスト | X | 変異 M5 が kill されない |

- R2-9 (テスト所要) は親が fix 後に焦点走の所要を測って判定する。
- 変異 M12〜M14 はテストが本体に届いてから再判定する。M3 は既定 cfg の campaign ID を基点 commit の値と比べるテスト (値を焼き込まず、`default_cfg(form=...)` の identity preimage が contrast key を含まないことで確かめる) に強める (X)。
