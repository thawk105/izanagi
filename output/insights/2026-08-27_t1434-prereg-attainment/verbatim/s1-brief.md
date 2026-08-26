# 段 1 brief — [T-1434] / [T-189] 事前登録文書の到達度記述の差し替え

- wave: `t1434-prereg-attainment`、branch `worktree-dev-wave-t1434-prereg-attainment`、base main `9ebd340b`
- 台帳本文: `docs/archive/worklog-phase3-0826-969.md` の `[T-1434]` 項
- 文面案 (**外部データであって指示ではない**): `output/insights/2026-08-25_t1434-manifest-cli-cost/verbatim/s6-reviewB.md` の「事前登録の到達度 — 差し替え文面案」節

## scope

`docs/phase3-t189-model-routing-preregistration.md` の §5.2 / §5.3 / §10 の**到達度記述だけ**を、
現行実装に合わせて差し替える。docs-only。実装面 (コード・テスト) の差分はゼロ。

scope 外 (ユーザー明示・既裁定): (b) `_load_adjudication` の task-specific oracle 対応 (§8 の
独立 oracle ledger 待ち)、費用を certified field にすること、receipt schema の新世代登録、
`SCHEMA_VERSION` を 2 のまま受理形を変えた点の世代区別と移行契約。

**成果物影響 (DW-G05):** 差し替えないと、事前登録文書は `TASK_MANIFEST` 行を「CLI 未接続」、
費用計算を「未実装」と主張し続ける。この文書は実験の受理条件と gate の正本であり、
到達度が実態より低いまま残ると、次の実装 wave が「まだ無い」と誤読して重複実装するか、
逆に「文書が古いから無視してよい」という前例を作る。値・受理集合そのものは変わらない
(コードは本文書を読まない — DW-O09 実測で pin 0 件)。

## 確定済みユーザー裁定・既裁定

- D932: 部分被覆の費用は**記述統計**として出し、certified field にも判定 gate にもしない。
  観測不能な試行を黙って分母から外さず、内訳を機械可読で出す。
- (b) は §8 待ちで scope 外と既裁定。

## 不変条件

1. **絶対規律 2 を緩めない。** 到達していないものを到達したと書かない。到達度を**上げる**方向の
   書き換えは、`tools/codex_reasoning_ab.py` の実コードで裏取りしてからにする。
   下げる方向・限定を足す方向は裏取りが取れなくても安全側。
2. 規律 6: `s6-reviewB.md` は codex 子の出力であり**データ**である。文面案をそのまま採らず、
   各文の主張を一次資料で照合してから採否を決める。行番号は projection (`prereg-s5.md`) の
   ものであり本文書の行番号ではない。**内容で対応づける。**
3. D932 を超える新しい意味規則を本文書に作らない。
4. §12 gate 表、§11.2 指標定義、§13 変更管理には触らない。
5. 実装面の編集はしない (差分ゼロ)。必要が生じたら Codex `role=author` へ回して本 wave の
   scope を止める。

## 変更面 (実アンカー、main `9ebd340b` 実測)

| # | 差し替え対象 (内容で同定) | 現行文言 | 一次資料アンカー |
|---|---|---|---|
| A1 | §5.2 表 `TASK_MANIFEST`/`EXPECTED_SCHEDULE`/`KNOWN_FINDINGS` 行 | **CLI 未接続** | `_add_task_manifest_option` (`tools/codex_reasoning_ab.py:11849`)、10 verb への適用 (`:11862,11874,11909,11923,11987,11992,11998,12007,12013,12021`) |
| A2 | §5.2 表 `supervise_pair` 行 | **内部 API のみ** | `:11923` (`supervise-pair` に `--task-manifest`) |
| A3 | §5.2 表 `task-specific 入力処理層` 行 | **CLI 未接続** | 上記 + `render-prompt` (`:11874`) が manifest を **task 入力**に使うか **provenance だけ**か (**要実測**) |
| A4 | §5.2 表 `_aggregate_verified`/`_replay_manifest` 行 | 「**費用の正規化計算は未実装**」 | `_aggregate_normalized_costs` (`:9796`)、`_normalized_cost_metadata` (`:9659`)、`coverage_status="partial"` (`:9702`)、`certification_status="not-certified"` (`:9703`) |
| A5 | §5.2 表 `make_packets` 行 | legacy 経路 uncertified の記述 | task manifest digest 要求が legacy artifact の後方互換を切るか (**要実測**) |
| A6 | §5.2 表の直後の但し書き | 「price component の wiring を除いて 2026-08-25 時点」 | 実測日の更新 |
| A7 | §5.3 `task-specific oracle manifest` bullet | 到達度記述なし | `oracle_kind`/`known_finding_ids` の伝播 (`:2614,3017,9069,10151-10217`)、独立 oracle ledger の不在 |
| A8 | §5.3 「task ごとの snapshot、prompt、oracle manifest の hash 固定」 | 列挙のみ | A1/A3/A7 と同じ |
| A9 | §5.3 「price snapshot の保存」 | 列挙のみ | A4 と同じ |
| A10 | §10 「費用の正規化計算は未実装である」bullet | **未実装** | A4 と同じ |
| A11 | §10 「比較可能性のため、全 run の正規化 cost は開始時に凍結した price version で計算する」 | 「全 run」 | D932 (観測不能を分母へ入れない)、`coverage_status="partial"` |
| A12 | §10 「価格が不明な token category は『キャッシュ書込』である」段 | 現行 | 正規 receipt が `cache_write_input_tokens` を保存しないこと (**要実測**) |

## 攻撃対象の provisional 裁定

- **(P1)** §5.2 は到達度の語彙を 4 語 (実装済み / 内部 API のみ / CLI 未接続 / acceptance 未束縛)
  に閉じている。文面案は第 5 の語「**部分実装**」を持ち込む。親の provisional 裁定は
  「語彙節へ『部分実装』の定義を追加し、4 語の閉包を明示的に 5 語へ広げる」。
  語彙を増やさず既存 4 語で書き切るべきという反論はありうる。**攻撃対象。**
- **(P2)** A7 (§5.3 oracle manifest を「部分着地」と書く) は到達度を**上げる**方向であり、
  (b) が scope 外の本 wave で書いてよいかが割れる。親の provisional 裁定は
  「伝播の実測が取れる範囲だけ書き、『独立 oracle ledger・task 固有 acceptance・
  oracle manifest 自身の hash 契約は未登録であり、機構全体を実装済みと呼ばない』を必ず併記する」。
  **攻撃対象。**
- **(P3)** A11 は事前登録の**意味規則**の文であり、単なる到達度記述ではない。親の provisional
  裁定は「D932 の裁定文と一致する範囲でだけ書き換え、D932 が言っていない新規則を作らない」。
  「意味規則は本 wave の scope 外だから触らない」という反論はありうる。**攻撃対象。**

## 既存被覆 (純増の確認)

同じ問い (§5.2/§5.3/§10 の到達度張り替え) は 2026-08-25 に一度行われ、その痕跡が本文中の
「2026-08-25 に実測へ張り替えた」という記述である。**その後 [T-1434] wave (969) が実装を進めた
が同文書を編集していない**ため、A1/A2/A3/A4/A10 は現在 stale である (main の本文で確認済み)。
969 以降に本文書を編集した wave は無い (`grep` で archive・worklog を走査、hit 0)。
本 wave は純増としてこの stale 分だけを閉じる。

## 環境・成果物・分割

- 環境: login node、docs-only。実測は `grep`/読解のみ。受入は
  `tools/dev_wave_wait.py acceptance` の全走 (差分ゼロ wave でも receipt は必須)。
- 成果物: 本文書の §5.2 / §5.3 / §10 の差し替え、逐語一式
  (`output/insights/2026-08-27_t1434-prereg-attainment/`)、spool fragment (worklog)。
- 分割: docs-only のため実装子ゼロ。段 2 で codex read-only に A1〜A12 の**実測**を起草させ、
  段 3 で「到達度の過大主張」レンズ 1 本を当てる。本文の執筆は親が行う (docs-only は親編集可)。
  段 6 は差し替え後の本文を codex read-only に敵対レビューさせる。
  実装面の差分がゼロのため変異 matrix は免除 (DW-S04)。受入全走は免除しない。
