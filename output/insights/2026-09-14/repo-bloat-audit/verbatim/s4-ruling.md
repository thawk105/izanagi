# 段 4 裁定 — repo-bloat-cleanup

## 結論

**本 wave では tracked file を 1 件も削除しない。実装面の差分はゼロとし、段 5・6 を飛ばして
`4→7→8→9` とする。** 変異 matrix は `DW-S04` により免除。受入全走は免除せず実走する。

「削除 0 件」は調査の失敗ではなく、調査の結果である。依頼の仮説のうち、**記録側は概ね偽、
テスト側も「不要な増分」としては未証明**であることが、独立 3 経路 (親・段 2・段 3 の 2 レンズ) で
一致した。

## 所見の real / refuted と採否

| # | 出所 | 所見 | 裁定 |
|---|---|---|---|
| 1 | sol §1 | 親 brief の条件 (a)「repo 内のどこからも参照されない」は過剰。D1941 は歴史的言及と現役 pin を分けている | **real・採用**。基準を「現役の拘束的 consumer / 非拘束の参照 / 歴史的言及 / 未解決」の 4 分類へ是正する |
| 2 | sol §1 | 是正後に削除可能側へ移るのは test 1 件・124 bytes だけ (`test_related_work_search.py:1978`) | **real・不採用 (実装しない)**。下記「削除を実施しない理由」 |
| 3 | sol §4 | 大きい重複 blob 群 (s6-rounds frozen payloads、axis1 retake ledgers) は現物で pin されている | **real・採用**。削除対象から恒久的に外す |
| 4 | sol §4 | 0 byte file 2,838 件は不要の証拠にならない | **real・採用** |
| 5 | sol §3 | AST 本体一致 22〜23 群のうち検分した 10 群はすべて非重複 (入力・module・呼出先が違う) | **real・採用**。AST 一致は削除数でなく調査入口 |
| 6 | sol §5 / luna §4 | (P1-b)「テストについては仮説は概ね真」は不支持 | **real・採用。親の (P1-b) を撤回する** |
| 7 | luna §1 | (P1-a)「output について概ね偽」は飛躍 | **real・採用。(P1-a) を「output の大部分は現役 pin または実測記録であり、削除可能と示せたものは無い」へ弱める** |
| 8 | luna §1 | (P1-c) の「台帳の bytes = 毎セッションの読み込み費用」は現行の部分読み導線と不一致 | **real・採用。(P1-c) を一部撤回**。checkout・検索の所要は未測定と明記する |
| 9 | luna §4 | 不変条件の `DW-O11` 引用は過剰一般化。原文は `output/` 配下の一括削除に対する条件 | **real・採用。brief の誤り** |
| 10 | luna §3 | `output/insights` 直下は「559 日付 dir」ではない。559 entries = 264 dir + 295 file、日付だけの dir は 46 | **real・採用。親の測定の読み違い** |
| 11 | luna §2 | 「lock が撤去不能を作る」は refuted。`tools/dev_wave_cleanup.py:943` は自対象の lock を解除する | **refuted・採用**。原因は land と cleanup の分離 (D702) と、cleanup が親の生存に依存すること |
| 12 | luna §2 | この dev-wave が worktree 18 本を一括撤去してはならない | **real・採用**。D204 / D854 / DW-O28 / cleanup-branches §0 による |
| 13 | luna §4 | 受入・実測環境を login node 限定にしたのは不適切。runner が資源量で実行場所を決める | **real・採用。brief の誤り** |
| 14 | luna §3 | 台帳ローテーション・insights 索引の新設は不要。既存機構で足りている | **real・採用**。新 gate を足さない (DW-G05 / D205) |
| 15 | 親の追加実測 | 「取り込み済み × 非占有 × 非 lock = 18 本」は撤去可能数ではない。26 本中 23 本が dirty | **real**。撤去候補は **1 本**だけ |
| 16 | peer session | `test_s8b_oracle_driver.py` の fixture が git 可視 `output/` 全件を複製し、受入の床を作っている | **real・採用**。親が現物で検算した。本 wave の scope 外だが記録する |

## 削除を実施しない理由 (所見 2 への裁定)

- `DW-G05`: 重複 test 1 件の削除は、成果物 (certified 選択・レポート・台帳) の値・受理集合・参照を
  1 つも変えない。成果物影響を書けない変更は must-fix にせず、追加 review を起動しない。
- luna は「124 bytes を削った実績を作るため、未確認を無影響と扱うべきではない」と明示した。
  nodeid を読む現役 consumer と collection への影響は静的にしか確認されていない。
- 実装面の差分を 1 行でも作れば、Codex `role=author` の実装子・敵対レビュー 2 本・変異 matrix・
  dispatch 本走が必須になる。124 bytes に対して不釣り合いであり、`DW-G02` の趣旨にも反する。
- **したがって候補は「実行可能な形で記録し、実施しない」。** 次に誰かがテスト整理を主目的にする
  wave を立てたとき、そのまま着手できる形で insight へ残す。

## ユーザー裁定へ返す項目 (裁定パッケージ)

1. **worktree 撤去。** 撤去候補は `dev-wave-t1875-delta-min-gate` の 1 本のみ (取り込み済み・clean・
   非占有・非 lock)。`dev-wave-t2267-exec-site-class` は同条件だが locked のため報告限定。
   残り 23 本は未 commit 差分を持つ。実行には対象を限定したユーザー指示と `/cleanup-branches` の
   起動が要る (D204 / D854 / cleanup-branches §0)。
2. **worktree 残置の構造。** land と cleanup の分離 (D702) + cleanup が親の生存に依存する設計により、
   親が途中で落ちた wave の worktree は誰も回収できない。恒久対応を裁定へ返す。
3. **重複 test 1 件の削除。** 上記の理由で本 wave では実施しない。
4. **受入 fixture の全件複製。** peer session の系列が扱う。D1918 との食い違い (最遅 shard が
   shard-2 か shard-0 か) の裏取りが要る。
