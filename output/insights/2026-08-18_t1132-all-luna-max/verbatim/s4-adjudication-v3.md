# 段 4 裁定 v3 (親) — 2026-08-18 13:30 JST

**v1 (段 2 だけ) と v2 (D' = 段 2/5/fix) を supersede する。**
ユーザー裁定 (2026-08-18): 「sol を luna max に全部置き換えてもいいよ」。
親は事前に「C は段 3 レンズ 1・段 6 敵対レビュー・段 6 焦点再レビューの 3 つの敵対 gate を
すべて luna にする案であり、レンズの多様性が失われる (D241 の論点)」と明示して提示し、
ユーザーはそのうえで許可した。**規律 2 に触れる判断であり、ユーザー裁定にだけ属する
supersede をユーザー自身が行った形である** (D423 が定めた権限どおり)。

## 確定した scope — C (全段 luna@max)

| stage / lane | model (旧→新) | reasoning (旧→新) |
|---|---|---|
| plan (段 2) | sol → **luna** | max (変更なし) |
| consult lane=sol (段 3 の 1 本目) | sol → **luna** | max (変更なし) |
| consult lane=luna (段 3 の 2 本目) | luna (変更なし) | max (変更なし) |
| author (段 5) | sol → **luna** | high → **max** |
| review (段 6) | sol → **luna** | high → **max** |
| fix (段 6) | sol → **luna** | high → **max** |
| focus (段 6) | sol → **luna** | high → **max** |

費用削減の見積り **70.6%** (必要 35.8%)。R=25 (luna は sol の 4%)、token 比 luna/sol=1.05、
high→max の token 増 2.02 倍で計算。token の総量は増えるため wave の所要時間は伸びる。

## この裁定が失うもの (記録として明記する)

- **段 3 の敵対相談 2 レンズが同一 model になる。** D241 が「sol にしか出せない所見を落とす」として
  不採用にした「全 luna」の形である。レンズは prompt だけで分かれ、model 由来の系統的盲点は共通化する。
- **段 6 の敵対レビュー 2 本も同一 model になる。**
- **D266 の認証済み A/B が段 6 focused review について選んだ `high` を `max` へ上書きする。**
  effort を上げる向きなので検出力は下がらないが、認証済みの値を証拠なしで動かしている。
- lane 名 `sol` / `luna` は model を指さないレンズ識別子に退化する。
  145 箇所の `--lane sol` / `--lane luna` 呼び出しの意味は「1 本目 / 2 本目」として保たれる。

いずれもユーザー裁定による受容であり、親の裁定ではない。

## 変更面

### 親が編集する docs (実装統合後・段 6 の前)

1. `docs/dev-wave/operations.md` `DW-O01` 権威行 (89 → 62 bytes、**−27**)

   旧: `` `<model>`: 段 3 のみ 2 本で `gpt-5.6-sol`→`gpt-5.6-luna`、他段 `gpt-5.6-sol`。 ``
   新: `` `<model>`: 全段 `gpt-5.6-luna` (段 3 の 2 本も同じ)。 ``

2. `docs/dev-wave/workers.md` の `reasoning=high` → `reasoning=max` を 3 箇所 (**−3 bytes**)
   - `DW-S05-A` (段 5 author。`DW-S06-B` の継承により段 6 fix にも及ぶ)
   - `DW-S06-A` (段 6 敵対レビュー。`launch_authority` が機械 parse する権威)
   - `DW-S06-C` (段 6 焦点再レビュー。同上)

   `DW-S02` / `DW-S03` は既に `max` なので変更しない。
   L1.5 層予算は差引 **−30 bytes** で余裕が増える (現在の余裕 20 bytes)。

### 実装子が編集するコード・テスト

`tools/dev_waves/launch_authority.py` / `tools/check_docs.py` /
`orchestrator/tests/test_dev_wave_launch_authority.py` / `orchestrator/tests/test_check_docs.py`。
詳細は `prompt-author.md` を正本とする。要点:

- 権威行の文法を v1 (旧) / v2 (新) の 2 本にする。v2 は全段・全 lane が単一 model。
- **live snapshot (`commit=None`) は v2 だけを受理する。** 過去 commit 指定では v1 も受理する
  (過去 receipt の再構成監査 `_audit_receipt_value` が落ちないため)。DW-O13 への閂。
- `AuthoritySnapshot.as_dict()` と `_aggregate_digest` は 1 bit も変えない。
- 既存 assert「段 3 の 2 レンズは異 model」は v2 では成り立たない。**削除ではなく、
  v1 (過去 commit) では異 model・v2 (live) では同一 model という形へ作り替える。**
  無検査にしてはならない。
- `review` / `focus` の effort は `launch_authority` の regex では `max` もそのまま通る
  (`[A-Za-z0-9_-]+` を捕るため)。

### 追補 (13:35 JST 発見) — 段 6 effort は機械 pin されており、張り替えが要る

`tools/check_docs.py` が `DW-S06-A` / `DW-S06-C` の `` `reasoning=high` `` を exact literal で
pin している (`DEV_WAVE_DW_S06_A_REASONING_HIGH_LITERAL` / `..._SENTENCE` / `..._FINDING` ほか)。
さらに `max` へ変えると finding が出ることを名指しで assert するテストが実在する
(`test_dev_wave_reasoning_effort_pin_rejects_dw_s06_a_max` / `..._c_max`)。
D266 の認証済み A/B が選んだ値を凍結する閂である。

**pin の finding 文自身が「変更には採用裁定と pin の同時更新が必要」と手順を定めている。**
ユーザー裁定が採用裁定に当たるので、対処は **pin を消すことではなく `high` → `max` へ張り替えること**。
「pin 値ちょうどでなければ finding」「decoy (comment / fence / blockquote / 併記) を拒否」という
性質は 1 つも減らさない。`max` を拒否するテストは `high` を拒否するテストへ対称に反転する。

`DW-S05-A` の `reasoning=high` は機械 pin されていない (T-667 で pin 拡大を明示的に見送り) ため、
docs 編集だけで足りる。

これは 1 本目の実装子へ渡した prompt の想定を覆すので、**2 本目の実装単位**
(`prompt-author2.md`) として 1 本目の完了後に投入する。同じ file を触るため並列にはしない。

## 変異事前登録 (DW-M01)

| ID | 変異 | 期待する単一理由の赤 |
|---|---|---|
| M-1 | 権威行を v1 へ戻す | live snapshot が v1 を拒否する回帰 |
| M-2 | live でも v1 を受理する | 同上 |
| M-3 | 過去 commit で v1 を拒否する | legacy receipt 再構成の回帰 |
| M-4 | `derive_launch` が consult lane=sol だけ別 model を返す | 全段同一 model の assert |
| M-5 | `check_docs` の literal を旧文言のまま据え置く | `DW-O01` 権威 pin |
| M-6 | `DW-S06-A` の effort 導出を `high` 固定にする | review effort の docs 交差検査 |
| M-7 | v2 regex を model 名非検証 (fail-open) にする | 権威 drift 検査 |
| M-8 | `DW-S06-A` の effort pin literal を `high` へ戻す | 段 6 review effort pin |
| M-9 | `DW-S06-C` の effort pin literal を `high` へ戻す | 段 6 focus effort pin |
| M-10 | effort pin の decoy 検査 (comment / fence / blockquote / 併記) を 1 種削る | 削った decoy の拒否テスト |
| M-11 | effort pin を丸ごと無効化する (finding を出さなくする) | 値不一致の拒否テスト |

正例: 過去 commit の receipt 監査が rc=0 で通ること。

## 裁定パッケージへ返す (scope 外 real)

- **T-1146 の択 (a) (T-189 の妥当な比較実験)** は本裁定により全段について上書きされた。
  実験を後追いで行うかは未裁定のまま残る。
- **同一 model 化で失われた系統的多様性を、prompt レンズ以外の何かで補うか。**
- **token 総量増による wave 所要時間の伸び**の許容範囲。
