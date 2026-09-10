# 段 4 裁定 — [T-2067] D1325「戻さない・g1 のみ」の固定

裁定時刻 JST 2026-09-01 01:52。main = HEAD = `24014bdb259d971571f22b54a8f10a49352b825f`。
裁定 inbox 再走査済み (`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/`)。最新の
`2026-09-01-dw-s04-superseding-ruling-boundary.md` は DW-S04 の裁定境界に関する別主題で、
本 wave の scope を動かさない。

## 結論

**実装しない (docs のみ)。** 段 5・6 を飛ばし `4→7→8→9` とする。
実装面 (D95 決定 2) の差分がゼロなので変異 matrix は `DW-S04` の免除に当たり、`DW-M01` の
事前登録は行わない。**受入全走は免除せず、段 7 の記録 commit 後に実走する** (`DW-O12`)。

## real / 採用

- **A1 (real・採用).** `s8b_ratified_freeze.py:3107-3110` の `certificate-generation-scope` を
  D1325 の「g1 のみ」の成立点に数えない。これは launch certificate の scope 拒否であり、
  D1325 の選択・投影方針へ昇格させると「将来 g2 の full validation は拒否する」という
  仕様を先取りする。記録は「HEAD 24014bdb2 の静的検査では、公開経路は選択規則の呼出しに
  到達しない」に限定し、**本記録は g2 の受理・拒否・選択・投影を何も定義しないと明記する。**
- **A2 / B5 (real・採用).** 現 HEAD の tree に v2 generation・approval・active pointer・
  candidate・official floor run はいずれも 0 件で、`s8b_holdout_freeze.py:52` の
  `BUDGET_APPROVAL_SHA256` は `None`。したがって当該検査は**静的に存在するが現に発火していない**。
  「現に守られている」と書かない。本 wave が active g1・official floor・予算承認を生成しないことを明記する。
- **A3 (real・採用).** worklog に測定 commit・静的検査であること・過去 artifact を再判定も
  certified 昇格もしないことを書く (規律 7 / 規律 3)。追加主張は D1313 (a)(b)(c) を
  そのまま参照し、「選択強制」の短縮語で代用しない。
- **A4 / B1 (real・採用).** (P1-1) の**結論は維持、理由は差し替える。**
  「コード変更は何も変えない」は誤り。`s8b_holdout_freeze.py:2062-2064,2077` は同 file の
  blob hash を future candidate の `generator.sha256` に入れるため、docstring 1 行の編集でも
  成果物の値が変わる。正しい理由は「現行の到達可能な挙動が既に D1325 と一致し、必要な実装差分が無い」。
  self-hash の事実は「不要なコード編集をしない理由」として記録する。
- **A5 (real・採用).** 親の実測 3 由来の「非対称」を**新しい次の一手にも裁定事項にもしない。**
  現コードに到達可能な非対称は無い。`DW-G04` の発火 artifact path も書けない。
- **B2 (real・採用).** 本 wave の実効価値は、T-2067 が「裁定済み → 実装待ち」のまま残っている
  記録状態を訂正することである。fold の `更新` (一部完了) とし、`完了` にはしない。
- **B3 (real・採用).** 残余の load-only consumer は s8c judge 1 件ではなく 3 群
  (oracle manifest / s8c floor verifier・publish / s8c C06 予算) として記録する。
- **B4 (real・採用).** 削除経路は通常の campaign API には無いが、当該 namespace は guard の
  防護 tree に含まれず generic な filesystem 操作で消せる。**「削除攻撃を閉じた」と書かない。**
  D1325 はこの残余を受容する裁定である、と書く。
- **B6 (real・採用).** 静的検査で止めず、段 7 の記録 commit 後に受入全走を実走する。
- **B7 (確認).** docs-only と直接抵触する既裁定は無い。予算確定・g2 設計・上限解除を含めると抵触する。

## refuted / 訂正

- **親の実測 3 (refuted).** 「選択が g2 へ伝播する」は誤り。plan・consult-a・consult-b・親の
  4 者が独立に `:3107-3110` の先行 gate を確認した。
- **親の実測 1 の行番号 (訂正).** 列挙は `:1792` ではなく `s8b_holdout_freeze.py:1821`。
- **親の実測 2 (訂正).** 「g2 は黙って非検査」は**静的 loader の投影についてのみ**成立する。
  full validation は先行 gate で止まる。
- **親の追測 2 (訂正).** 「削除経路 0 件」は production API についてのみ正しい。B4 の形へ改める。
- **依頼文の前提 (訂正・非抵触).** 稼働中 t2027 wave が触るのは 4 file ではなく 8 file
  (production 4 + 対応 test 4)。いずれも本 wave の編集面と交差しない。

## 不採用 / scope 外

- 新しい gate・検知機構・台帳・一般化の追加 (ユーザー明示で scope 外)。
- g2 拒否を恒久仕様として裁定へ返すこと。D1325 が「g2 が実在してから設計する」と既に定めており、
  今 g2 の仕様を問うのはその裁定に反する。**裁定へ返す項目は増やさない。**
- 実装面への docstring・コメント追記。A4 のとおり成果物の値を変えるため、docs-only の趣旨に反する。

## 成果物

`docs/spool/worklog/2026-09-01-dev-wave-t2067-d1325-g1-only-1.md` 1 本のみ。
`## 本文` と `## 次の一手差分` (`### 更新` に [T-2067]) の 2 節。
decisions fragment は作らない (D1325 が既に裁定を持ち、新しい設計判断は生じていない)。
