# 段 4 裁定 — 実装せず、ユーザー再裁定待ちへ返す

wave: `dev-wave-t181-stage6-high` / 起点 main: `6cc3e59a`
段 2 プラン `s2-plan.md` (rc=0)、段 3 敵対相談 `s3a.md` (11 所見) / `s3b.md` (11 所見、NO-GO)。

## 停止理由 (DW-STOP / DW-S04)

段 3 レンズ B の B-09 が、親 brief が把握していなかった**既存ユーザー裁定**を発見した。
親が一次資料で裏を取り、**real と裁定**した。

`docs/archive/worklog-phase3-0801-101.md:18-23` (2026-08-01 裁定):

> **[T-227] は (a) 明記する・値は `max`** — `DW-S06-A` / `DW-S06-C` の reasoning が契約に無く
> 歴史運用が割れている状態をまず止める。値は安全側へ倒し、下げる判断は [T-181] の 10 run 再走で
> 根拠ができてからにする ([T-181] の 1.96 倍は段 6 focused review の測定であり他段へ外挿しない)

> **[T-184] は (a) 再走を待つ** — 工程別 policy の採用は [T-181] の認証再走の後にする。
> 「再走なしに T-184 で引用してはならない」と自ら記録した数値を根拠にしない。

`[T-227]` は現在も **P2・裁定済み → 実装待ち** で `docs/worklog.md:2818` (306) に持ち越し中。

これにより親 brief の前提「段 6 は未規定だから初回確定であり引き下げではない」は **refuted**。
実体は「裁定済み `max` を、その裁定が明示した条件 (10 run 再走) を満たさないまま `high` へ
反転する」変更である。DW-S04 は「承認済み裁定を止めるときも親が不採用にせず、
新事実付きのユーザー再裁定待ちへ戻す」と定める。よって親は採否を決めず返す。

## ユーザーへの選択肢

| | 内容 | 得るもの | 失うもの |
|---|---|---|---|
| **(α)** | **T-227 をそのまま実装** — A/C = `max` を明記し機械 pin する | 歴史運用の割れが止まる。裁定と実装が一致 | トークン消費は現状のまま |
| **(β)** | **今日の指示を採用** — A/C = `high` を明記し機械 pin する。T-227 と T-184 の再走前提を**明示 supersede** したと記録 | 段 6 のトークン消費が下がる (T-181 実測で max は model_calls・token・wall とも一貫して大) | 未認証証拠で検出力側を動かす。敵対レビュー 2 本は T-181 が測っていない (前裁定が「他段へ外挿しない」と明記) |
| **(γ)** | **T-181 の 10 run 再走を先に走らせる** — 認証台帳を得てから (α)/(β) を決める | 前裁定の条件を満たした正規経路 | 再走コストと時間。T-227 の実装もそれまで待つ |

いずれでも実装作業はほぼ同一 (literal 1 語と pin 期待値の差)。段 5 以降は即着手できる。

## 選択肢に依らず確定した設計 (段 3 の must-fix を反映済み)

段 2 プランの 2 行置換案は **採らない**。理由と代替は下記。

1. **A-01/A-03**: 置換案は `実装 wave は` を落とし、docs-only wave へ敵対レビュー 2 本を強制する
   受理集合の拡大になる (`DW-C00`「docs-only は子ゼロでよい」と衝突)。条件節を保存する。
2. **A-02/B-10**: 置換案が削る「全体へ 1 本でよい」の「1 本」は *1 巡あたりの reviewer 本数* の
   許可。導入 commit `7deb54ef` の逐語「fix 単位ごとの個別レビューは不要とする」が原義。
   F146 が stale としたのは *巡回数* と *対応表の担い手* であり「1 本」ではない。削らない。
3. **A-05/A-06/B-05**: `DW-S06-C` にも local literal を置き、A と C を**別々に** exact pin する。
   A だけの pin は C に `max` を書いても通る (メモリ上実測で確認)。
4. **B-02**: `_reference_id_sections()` が raw text で節を切るため、**H2 見出しごと fence /
   HTML comment に入れると pin と必須節検査を同時に迂回できる**。文書全体を先に可視化してから
   節抽出する修正と、hidden whole-section の production 負例が要る。**本 wave と独立の既存欠陥。**
5. **B-04**: `` `reasoning=high/max` `` `` `reasoning=high.max` `` `` `reasoning=high"` `` が
   すべて `['high']` として通る。canonical literal の exact-one 要求か終端 allowlist が要る。
6. **B-07**: 変異 #7 は global H2 uniqueness に mask され実効 kill にならない。両層同時変異へ
   変更するか冗長 gate と明記して外す。B-02 の hidden section と B-05 の C=max を変異に追加する。
7. **A-11/B-10**: byte は `operations.md:3-4` の導入 2 文の縮約 (−67 bytes) で安全に捻出できる。
   危険な削除は byte 上不可避ではない (refuted)。
8. **B-11**: 停止条件に local main の SHA 比較を足す。並行 `dev-wave-t182-luna-stage3` と
   byte 予算・同一 production caller block・同一 fixture を奪い合う。敗者は `DW-O23` の
   stale 経路で再検証する。

## 記録上の必須文面 (B-08、どの選択肢でも)

decision fragment・worklog・insight の三者に同じ 4 点を書く。

- `experiment_complete=false` / `decision=null` / 全 10 run が `snapshot oracle replay mismatch`
- **非劣性・同等性・採用の証明ではない** (T-181 insight の事前登録が禁じている)
- 採用根拠は「ユーザー裁定のみ」と分離する。「方向は支持」という表現は使わない
- (β) を選ぶ場合は「T-227 の `max` と T-184 の再走前提を明示 supersede した」と書く。
  「初回確定」「引き下げではない」とは書かない

## 射程の限界 (B-01、どの選択肢でも)

docs の pin が拘束するのは **docs の drift だけ**である。段 6 の子は
`DW-O01` の雛形どおり親が手で `codex exec -c model_reasoning_effort="<値>"` を組み立てて起動する。
`tools/codex_worker_launch.py` は要求値と実効値の一致しか検査せず、段から値を導出しない。
`.codex/role-adapters/*.json` に段 6 対応 role はなく、`orchestrator/codex_roles/` は
runtime blocked。よって成果物の主張は「**docs 契約 + drift pin**」に留め、
「実際に high で起動することを機械保証した」とは書けない。
機械保証が要るなら launcher 結線 ([T-576] / [T-184] 所有) が別途必要 — 本 wave の scope 外。
