# dev-wave の codex を全段 luna@max へ切り替えた (2026-08-18)

wave = `dev-wave-t1132-stage2-luna` / branch = `worktree-dev-wave-t1132-stage2-luna`
逐語一式 = `verbatim/` / 変異記録 = `mutation/`

## 何をしたか

dev-wave が起動する codex の model を、全段・全 lane 単一の `gpt-5.6-luna` にし、
luna を使う段の `reasoning` を `max` に揃えた (段 5 author と段 6 review / fix / focus が
`high` → `max`。段 2 / 段 3 は元から `max`)。

**採用根拠はユーザー裁定であり、品質同等性の証拠ではない。** [T-1146] の現行裁定 (c) が
「体感や速度を理由に切り替えたくなった場合は、証拠に基づく判断ではなく**運用上の選好**として
(b) を明示指示し、その旨を記録する道を残す」と定めており、本 wave はその道を通った。

## 経緯 — scope が 3 度変わった

1. 初回指示は「gpt5.6sol を使っているところを**一箇所** luna max に置き換えろ」だった。
2. 親が段別消費を実測し「一箇所 (段 2) は codex 消費の 16.0% で、削減は最良でも 15.3%。
   必要な 35.8% に届かない」と報告。
3. **親が誤った報告をした。** receipt 170 本の token 数だけを集計し「luna は安くない
   (同一 wave 内 paired 15 wave で luna/sol の token 比は中央値 1.05・合計 +7.2%)。
   全段 max へ広げると +46.5% 悪化する」と結論した。**単価を一度も見ていなかった。**
4. ユーザーの「遥かにモデル料金レートが安い。それはわかってる?」で是正。
   web で確認すると luna は sol の 4% (sol 入力 $5 / 出力 $30 per M、
   luna 入力 $0.20 / 出力 $1.20 per M。2026-07-30 に luna が 80% 値下げ、sol は据え置き)。
5. 「luna は愚かだから luna を使う段は max でなければ受け入れない」という条件が加わり、
   最終的に「sol を luna max に全部置き換えてもいいよ」で確定。

親は確定前に「この案は段 3 レンズ 1・段 6 敵対レビュー・段 6 焦点再レビューの 3 つの敵対 gate を
すべて luna にする案で、レンズの多様性が失われる (D241 の論点)」と明示して提示している。

## 費用の見積りと実測

必要な削減は 35.8% (codex は 200→80 で 120 消費、claude は 200→123 で 77 消費)。

段別シェア (receipt 170 本 / 26 wave / CLI reported 35.8M の集計):
consult 34.6% / plan 16.0% / fix 15.9% / review 13.4% / author 13.2% / focus 3.4%。
sol を使う段が 76.4%。

| 案 | 費用削減の見積り |
|---|---|
| 段 2 だけ luna | 15.3% (未達) |
| 段 2 + 段 5 + 段 6 fix (敵対 gate 不接触) | 42.0% |
| sol 全部 luna max (採用) | 70.6% |

**実測 (本 wave の receipt)**: 段 6 敵対レビュー 2 本が `gpt-5.6-luna` @ `max` で走り、
token は過去平均 (177,057) の 1.89 倍。D207 が観測した `high`→`max` の入力増 2.02 倍と整合する。
同一 token 量なら luna は sol の 4.0%、effort 増を織り込むと旧構成比 7.6%。
**token の数は増える。減るのは単価である。**

## 機械化した内容

- model 権威行の文法を v1 (旧) / v2 (新) の 2 本にした。**live snapshot は v2 だけを受理**し、
  過去 commit 指定では v1 も受理する — 過去 receipt の再構成監査を壊さないため。
  v1 を live 起動へ使える抜け道は作っていない。
- `AuthoritySnapshot.as_dict()` と集約 digest は 1 bit も変えていない。既存 receipt の照合は不変。
- 段 6 の `reasoning` pin は削除せず `high` → `max` へ**張り替えた**。pin の finding 文自身が
  「変更には採用裁定と pin の同時更新が必要」と手順を定めており、削除は手順ではない。
  値ちょうど一致の要求と decoy 4 種の拒否は 1 つも減らしていない。
- 権威行は 89 → 62 bytes。L1.5 層予算の余裕 (実測 20 bytes) はむしろ増えた。

## 敵対レビューが出した must-fix と、レビューが見落とした欠陥

段 6 の敵対レビュー 2 本はともに **NO-GO**。

- **A-01**: v1 権威行の consult 2 レンズが同一 model でも production が通す。
  本 wave の新規欠陥ではなく、変更前も `other == sol` しか見ていなかった。
  安全性を実測 — `operations.md` を触った全 67 commit のうち権威行を持つ 28 版を機械走査し、
  **v1 で 2 レンズが同一だった版はゼロ**。検査を足しても過去 receipt の再構成は壊れない。
- **B-01**: 段 5 author と段 6 fix の effort は `unbound` (caller 指定) なので、
  docs を `max` にしても**呼び出し側が `high` を渡す限り receipt は `luna@high` になる**。
  「変えたつもり」の鎖の切れ目。repo 内の stale な caller 契約 3 箇所を `max` へ更新した。
  `--reasoning` の受理集合は変えていない — 段 5 の effort は T-667 が pin 拡大を明示的に
  見送った意図的な unbound であり、実装側で `high` を拒否するのは見送り裁定の反転になる。

**両レンズが見落とした欠陥を、親の焦点走の範囲拡大が拾った。** 権威行の model slug を
「2 個ある前提」で入れ替える consumer が `test_codex_worker_launch.py` に 1 件あり、
v2 (slug 1 個) で `IndexError` になっていた。レンズ B は同 file の consumer を列挙していたが
この 1 件は挙げていない。親の最初の焦点走もこの file を含めておらず、5 file へ広げて初めて出た。

## 変異 matrix

**baseline PASSED・7/7 KILLED・SURVIVED 0・MISMATCH 0・TIMEOUT 0** (`mutation/mutation-ledger.json`)。

probe → 本走の 2 段で回した。初回 probe は期待 node 2 件が parametrize された実 node ID と
一致せず preflight で fail-closed。`--collect-only` で権威一覧を取って修正した。
2 回目の probe (`mutation/mutation-ledger-probe2.json`) で baseline PASSED・4 KILLED・3 MISMATCH。

- MISMATCH 2 件は期待集合が広すぎたため。差の原因は**恒久保留テストが走らないこと**
  (`test_real_repo_clean` 等が growth-hold で `opted_in:false`)。実測値を完全集合として再登録した。
- 残る 1 件 (段 6 effort pin の**値**を戻す変異) は **265 node が赤になる過剰決定**だった。
  pin 値を変えると実 repo が汚れ、`check_docs` を走らせる全テストへ連鎖する。
  `DW-M03` に従い単独変異の証拠から外した。同じ性質は pin literal の変異
  (実測 7 node、production path 検査を含む) が単一理由で押さえている。

## この裁定が失うもの

- 段 3 の敵対相談 2 レンズと段 6 の敵対レビュー 2 本が同一 model になる。
  レンズは prompt だけで分かれ、model 由来の系統的盲点は共通化する。
  D241 が「sol にしか出せない所見を落とす」として不採用にした「全 luna」の形そのものである。
- D266 の認証済み A/B が段 6 focused review について選んだ `high` を `max` へ上書きした。
  effort を上げる向きなので検出力は下がらないが、認証済みの値を証拠なしで動かしている。
- lane 名 `sol` / `luna` は model を指さないレンズ識別子に退化した。
  145 箇所の `--lane` 呼び出しの意味は「1 本目 / 2 本目」として保たれる。

## 裁定へ返すもの

- 全段同一 model で失われた系統的多様性を、prompt 以外の軸で補うか。
- [T-189] (model routing の妥当な比較実験の設計) を後追いで行うか。
- 段 5 / 段 6 fix の effort に機械強制を入れるか (現在は T-667 の見送り裁定により意図的に無し。
  docs 契約と dispatcher test の記録だけが caller を縛る)。

## エージェント工数

codex 子 6 本 (段 5 実装 1・段 6 敵対レビュー 2・fix 2・焦点再レビュー 1)。
すべて `tools/check_codex_output.py` rc=0。段 5 実装子だけが変更前の `gpt-5.6-sol` @ `high` で走り、
段 6 以降はすべて新権威の `gpt-5.6-luna` @ `max` で走った。
子はいずれも read-only / workspace-write の制約どおり pytest を実走せず「実装済み・未実走」と申告し、
測定はすべて親が計算ノードで行った。
