# 段 1 brief — dev-wave token-economy (2026-08-04)

依頼 (ユーザー command 引数): 「トークンの使用量を節約できるところを探して節約して欲しいけど、
品質は落とさないでほしい」。

## 探索の結論 (段 0 実測、ログインノード読み取りのみ・追加計測ゼロ)

- セッション起動時に読む量 ≈ 72KB。うち最大の**無情報**ブロックは worklog の carry 行である。
- `docs/worklog.md` = 98,391 bytes の **64% (63,764 bytes / 1,673 行)** が
  `- [T-NNN] 変わらず ((N) 参照)`。末尾エントリ 15,168 bytes の **59% (9,006 bytes / 237 行)** が同じ形。
  archive 累計 1,061,487 bytes / 24,887 行。
- 生成は `tools/spool_fold.py:1339`、読取は同 `:1151-1155` の `carry_re`。fold が lock 内で自動生成する。
- `prior_ordinal` は常に直前エントリの ordinal (`:1792`, `:1811`)。各行の `((N) 参照)` は
  **構成上 100% 導出可能で情報量ゼロ**である。
- 対象外と確定した経路: (a) campaign 子 (planner/coder/critic/selector) は fresh context・ツールなしの
  構造遮断が D39/D45/D47 の正しさ要件で、session 再利用や cache 化は品質を落とす
  (`claude_projected_provider.py:308` が session_id 重複を赤にしている)。(b) dev-wave docs の外出しは
  D94 却下案 (a) の既往裁定で削減 0。予算引き上げも提案しない。

## scope

`tools/spool_fold.py` が新規エントリへ書き出す carry 行の表現だけを縮める。
過去エントリは凍結のまま、parser は旧書式を受理し続ける。

**scope 外** (実装せず段 4 で裁定パッケージへ): 未消化 T の件数そのものの整理 (237 件)、
archive の遡及圧縮、D70 機構そのものの変更、worklog 以外の docs 縮約。

## 不変条件 (緩めない)

1. **D70 保存則の受理集合を広げない。** `check_docs.py` は無改変とする。
   実測: `TASK_ID_AT_HEAD_RE` (`check_docs.py:521`) と `TASK_HEAD_RE` (`spool_fold.py:35-37`) は
   ともに `(?=$|[ \t])` を持ち、ID 単独行を**既に**受理する。よって新書式は既存受理集合の内側。
2. **`substantive_digest` の carry 連鎖を fail-open にしない。** 参照先の解決不能・循環・
   未来参照は現行どおり赤で止める。digest を「解決できなければ item.block を使う」形へ
   退避させてはならない (base-mismatch 検査の恒真化になる)。
3. 過去エントリを書き換えない。旧書式 carry 行の解決能力を落とさない。
4. carry 行に ID を持たない項目・重複 ID を作らない。

## 成果物影響 (DW-G05)

台帳 (worklog) の bytes 表現だけが変わり、certified 選択・材料レポート・受理集合の値は変わらない。
実装しない場合、次の一手台帳は毎エントリ 9KB の無情報テキストを積み続け、
全クラス 2/3 セッションの起動読み込みを膨らませ、rotation 閾値 (100,000 bytes) を
約 2.5 倍の頻度で叩き続ける (直近 e38ae20 で実際に rotation が発火した)。

## 親の provisional 裁定 (攻撃対象)

- **(P1) 新書式は ID 単独行 `- [T-NNN]` とする。** 削減 237×27 ≈ 6,399 bytes/エントリ。
  対抗案 (P1′) `- [T-NNN] (180)` は 237×22 ≈ 5,214 bytes で、ordinal が行内に残り
  parser が document 順に依存しない。**どちらを採るかは段 3 のレンズに攻撃させる。**
- **(P2) 旧書式の解決能力は `carry_re` を「旧形 | 新形」の 2 択にして維持する。**
  新形の参照先は「直前エントリ」と定義する (P1 を採る場合)。
- **(P3) 本 wave は軽量版にしない。** carry 連鎖は台帳整合の機構であり、
  段 2/3 と段 6 のレビュー子を省かない。

## 成果物の形

`tools/spool_fold.py` の carry 生成・解決の変更、`orchestrator/tests/test_spool_fold.py` の
新旧混在を含む回帰テスト、`docs/worklog.md` 冒頭の書式規約の追随、変異 matrix、受入全走、
spool fragment (worklog / decisions)。

## 並列分割方針

実装面は 1 所有単位 (spool_fold + そのテスト) で分割しない。段 3 と段 6 のレンズだけ並列にする。
