---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-07
wave: dev-wave-t2339-b5-prereg
seq: 1
title: [T-2339] 軸 B5 の 7.7.4 検索事前登録を書き、実行を認可しない部分登録として凍結した (docs のみ、branch worktree-dev-wave-t2339-b5-prereg、実装面の差分 0)
---

## 本文

- ユーザー裁定: 引数で scope が「索引 3 つ・検索式・母集合の外・候補 3 群の positive control の
  登録。実行ではない」と限定された。仮想リスク向けの gate・検査・台帳・一般化の追加も scope 外と
  明示された。本 wave は外部 HTTP request を 1 本も出していない。
- **成果物を「部分登録」と位置づけた。** 7.7.4 の事前登録を単独では満たさない。実行を認可しない
  理由は 3 つで、いずれも外部照会または実行器の走行を要し本 wave の範囲外である —
  (a) 候補 3 群 (Cicada 原論文 / 確率近似の適応 step・窓 / STM の適応 contention manager) の
  主キーが 1 つも確定していない、(b) query catalog の bytes と SHA-256 が seal されていない、
  (c) 補助探索の引用・著者経路の起点が (a) に依存して確定しない。
  **軸 B5 は `RW0` のままで、世界の不在を支持しない。本体論文の軸 1〜5 は動かしていない。**
- 棄却 finding 2 件。(1) 段 3 レンズ B が `T∧V` 枝の削除を推奨したが棄却した — 削る理由が
  「候補が増えて手間」であり、不在主張の被覆を狭める向きの変更になるため。(2) 同レンズが
  演算子 control を完走の論理積から外すよう推奨したが棄却した — 外すと gate が緩むため。
- 段 3 レンズ A が親 brief 自身の誤りを 1 件当てた (`A-7`)。brief は「repo 内に候補 3 群の主キーは
  無い」と 1 箇所を見ただけで断定していた。内部の不在の作法 (母集合と走査語を併記する) を
  親自身が破っていたので、母集合・走査語 7 語・主キー正規表現 3 本を明記した実測へ書き直した。
- 段 6 レビュー B が実害のある欠陥を 1 件当てた (`RB-2`)。完走条件 3 で OpenAlex の
  `meta.per_page` を最終ページの実要素数と突き合わせる書き方をしており、正常な部分ページが
  必ず不合格になって軸が永久に `未完走` になる経路があった。軸 1 の古い言い回しを引き写した
  ことが原因で、7.7.4 の定義 (非最終ページは実要素数=要求件数、最終ページは
  位置+実要素数=宣言総件数) へ戻した。
- **軸 1 の未解決状態は継承しない裁定をした** ({{D:b5-inherits-predicate-not-blocker-state}})。
  軸 B5 は軸 1 の厳しい述語そのものを自分の応答へ適用するが、U11 や条件 4/5 の追認といった
  軸 1 側の裁定待ち状態は引き継がない。継承すると軸 B5 が自分では閉じられなくなるためである。
- セッション異常 1 件。段 6 のレビュー子 2 本を `--stage review --lane sol --reasoning xhigh` で
  投入したところ、`--lane` が相談段専用・effort は段 5/6 で指定不可であるため launcher が
  rc=2 で即死し、待ち手が `producer-files rc=70` で落ちた。argv を直して再投入し 2 本とも受理。
  段別 argv 制約は `DW-C01` と `DW-O01` にあるが、段 6 の直前に読む `DW-S06-*` には無いため、
  段直前の再評価では当たらない。段 8 の改善候補として扱った。
- エージェント工数 (codex receipt の実測、`gpt-5.6-sol` / effort=xhigh、全 8 本が `accepted`):
  段 2 plan 1 本 (12 call / 982,265 token / 636 秒)、段 3 相談 2 本
  (8 call / 441,851 token / 443 秒、16 call / 1,042,710 token / 658 秒)、
  段 6 レビュー 2 本 (14 call / 637,778 token / 476 秒、27 call / 1,987,764 token / 748 秒)。
  段 6 焦点再レビュー 2 巡。
- 親の実測: `tools/check_docs.py` = 違反なし、`git diff --check` = rc=0。
  語数と直積の自己検算 (6 ブロック 12/19/10/21/13/10 = 85 語・互いに素、DBLP 直積 1602、
  主 query 総数 1622、control 14 本、venue stream 272) が本文の記載と一致。
  §3.3 の展開規則を実装して照合例と bytes 一致することを確認した。
  候補 3 群の主キー走査は入力 commit の `docs/related-work/` (4 file・5 行・5 occurrence) と
  submodule commit `511c9538e` の `external/ccbench/README.md` (2 行・3 occurrence) で、
  走査語に当たった行のうち主キー正規表現に当たる行は 0 行だった。

## 次の一手差分

### 完了

- [T-2339] 軸 B5 の 7.7.4 検索事前登録を
  `docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md` として
  凍結した。索引 3 つ・検索式・母集合の外・候補 3 群の positive control 契約を登録し、
  実行を認可しない部分登録であることを本文と一覧行に明示した。
  remaining: none
  base: af7359432a12a7066e9f8a6039eee3761168e6953927540f3835f5ce607de942

### 新規

- {{T:backoff-b5-anchor-keys-and-catalog-seal}} **P2・新規**: 軸 B5 の後継凍結物で、
  2026-09-07 の登録が閉じられなかった 3 点を閉じる — 候補 3 群 (`G1-CICADA` / `G2-SA` /
  `G3-STM`) の主キーを一次書誌資料で確定し、`G2-SA` / `G3-STM` は有限 anchor 集合そのものを
  結果を見る前に凍結する。併せて query catalog (1622 主 query + control 14 本 + venue 272 stream)
  を §3.3 の展開規則から生成して bytes と SHA-256 を seal し、引用・著者経路の起点を確定する。
  **3 点が閉じるまで軸 B5 の検索を実行してはならない。**
