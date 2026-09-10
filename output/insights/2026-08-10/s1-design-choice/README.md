# 段 7 前提 S1 の設計択一 — 逐語凍結 (2026-08-10)

`dev-wave-s1-design-choice` (branch `worktree-dev-wave-s1-design-choice`) の子出力と裁定
パッケージの逐語。**実装差分ゼロの docs のみ wave**であり、ここにあるのは設計材料であって
計測値でも proof chain でもない。

ccbench pin = `d706650cdb31e442bef45b9b4216951d4fb40969`。

## 経緯

スコープ B 部分再開裁定 (2026-08-10) の Q2 = (a) により、段 7 cross-protocol の前提 S1 について
「別 protocol への trace-hook 移植 (案 A)」と「stock 専用計測経路を規律 2 と整合させる設計 (案 B)」の
設計択一パッケージを作る wave が解禁された。本 directory はその wave の一次資料である。

## 結論 (詳細は `verbatim/ruling-package.md`)

**2 案は同じ目標に対する代替ではなかった。** 案 A だけが段 7 の certified cross-protocol 比較を
成立させる。案 B はどれだけ隔離を厳しくしても比較を作れず、作れるのは正しさ未検証の性能観測で、
それを比較表・順位・headline の片側に置いた時点で規律 2 違反になる。

案 A の実装コストは当初想定より大きい。hook 移植そのものは si の先例で安いが、certified 比較の
成立には登録済み負債 4 件 (trace 形式 v2 化 / observer 防壁の protocol 対応 / 遺伝子空間・較正・
floor / 公式 report・schema・selection consumer 接続) が束で要る。

## ファイル

| file | 何か |
|---|---|
| `verbatim/brief.md` | 段 1 の親 brief。前提の実測 (M1)〜(M7) と provisional 裁定 (P1)〜(P3) |
| `verbatim/s2-plan.md` | 段 2。codex `gpt-5.6-sol` / reasoning=max / read-only。file:line 粒度の 2 案設計 |
| `verbatim/s3-lens1.md` | 段 3 レンズ 1。`gpt-5.6-sol`。正しさ境界との整合 (規律 1/2/3)。blocker 4 件 |
| `verbatim/s3-lens2.md` | 段 3 レンズ 2。`gpt-5.6-luna`。実効性・コスト・層の取り残し。blocker 2 件 |
| `verbatim/ruling-package.md` | 段 4 の裁定パッケージ。3 軸比較と裁定 3 問 |

## 敵対レンズが倒した親の主張 (real 認定)

- **(P1)** 「si に trace-hook がある以上、案 A は 2 本目の展開で安い」→ 一部誤り。hook の構文は
  安いが、si 固有の先例を移植先一般へ一般化していた。ermia には成功 read が `read_set_` に
  入らない分岐があり、si 型の hook をそのまま移すと write-skew の片側の依存辺が消えて
  serializable へ false-green する。
- **(P2)** 「stock を certified の外に出すと明示宣言できれば規律 2 と整合する」→ 誤り。宣言は
  防壁ではない。整合するのは公式受理集合・順位・headline から機械隔離した場合だけで、
  そのとき案 B は段 7 の成果物ではなく別の偵察成果物になる。

## 親が独立に裏取りした事実 (いずれも確認済み)

| # | 事実 | 根拠 |
|---|---|---|
| V1 | ermia の `cstamp<<1` は dormant な `ssn_commit()` のみ。現行 active な `ssn_parallel_commit()` は raw cstamp を格納 | `cc/ermia/transaction.cc:553`–`556`, `:765`, `:905` |
| V2 | verifier が部分履歴を certified にする偽陰性 2 件が、恒久対応を「S1 移植と同時」と宣言したまま残っている | `orchestrator/tests/test_verifier.py:601`–`638` |
| V3 | mocc の変数化された最適化軸は 2 つ (`TEMPERATURE_RESET_OPT`, `KEY_SORT`)。`RWLOCK` は固定 define | `external/ccbench/cc/mocc/CMakeLists.txt:5`–`9` |
| V4 | floor 照合は protocol をキーにせず、複数一致で停止する | `orchestrator/campaign/layer3_report.py:345` |
| V5 | certified-selection consumer はこの checkout に存在しない (関数自身が自認) | `orchestrator/campaign/layer3_report.py:544` |
| V6 | between-run floor の baseline は silo 固定、測定点は 3 つ | `orchestrator/campaign/between_run_floor.py:52` |

## 副産物 — 既存 docs の誤り 3 件

訂正は本 wave の scope 外。worklog の新規項で起票した。

1. `docs/ccbench-anatomy.md:211` — ermia の `cstamp<<1` 警告は dormant 経路の話 (V1)。
   S1 着手時の「必須知識」として書かれているため、従うと誤った写像を実装する
2. `docs/ccbench-anatomy.md:126` — 「mocc 2^4」が現行 CMake と不一致 (V3)
3. `docs/phase3.md:269` — must 表 S1 行の「silo 内に閉じる」が、si に trace-hook が既にある事実
   (`cc/si/transaction.cc:526`–`553`) を落としている

なお親 brief 自身の「silo に 13 箇所」も誤りで、実際の `#if TRACE` は 10 箇所だった。
