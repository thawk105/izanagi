# 段 6 レビュー裁定 — [T-2802] (2026-09-20 08:10 JST 頃、mtime 正)

入力: `codex/s6-review-A.md` (過剰・削除・実効性、NO-GO must-fix 4)、`codex/s6-review-B.md` (正しさ境界、NO-GO must-fix 2)。両レビューとも **production の受理集合変更は未検出**。must-fix は全て検証成果物 (test の期待文書、A/B script、差分 probe の正例) 側。

| # | 所見 | 裁定 | 採否 | 実施 |
|---|---|---|---|---|
| A-M4 / B-MF1 | N1 (`test_cut6_multiclaim_consumption_sequence`) の期待文書が `_floor_expected_marker` → production `_floor_attempt_document_for_state` 経由で、裁定 §4 の固定 literal でない | real | 採用 | fix-impl1 (unit-impl): 期待辞書を test 側で明示 (key 集合・固定値は literal、digest 等は fixture の入力・発行済み値から)。production の文書 constructor を期待値生成に使わない |
| A-S1 | N4 の v1 は `claim_fault=entry/seams` が `none` と同一入力 (重複 2 case) | real | 採用 | fix-impl1: v1 を 1 case に縮約 (99 → 97) |
| A-S2 | 未被覆のうち projection 入口 (claim shape/identity、attempt_ids の型・重複) と main 0/2 件、legacy の N6 (hit coverage・再読) を少数補う | real | 採用 (代表例だけ、各 1〜2 case) | fix-impl1 |
| A-M1 | 集計器が走を slot 別に分割し全体の隣接性・slot 順序 (AB/BA/AB) を検査しない → 非隣接走から有効対を作れる | real | 採用 | fix-probe2 (unit-probe): 全走を時系列で検証、対 = 隣接 2 走、slot の期待順序、無効対の後の取り直しは同 slot・同順序で対全体 |
| A-M2 | 赤の分類・固定終了・12 走上限が系列の受入条件になっていない | real | 採用 | fix-probe2: launcher は lock 内で `runs/` の走数を数え 13 走目を拒否。系列 script は赤で停止し、再開には各赤走の `classification.json` (`kind: infra / impl / unclassified`、`by`、`evidence`) を要求。集計器は無効走ごとに classification を要求 (欠落は系列無効)、`impl` / `unclassified` があれば系列無効、有効 3 対成立後の追加走は系列違反 |
| A-M3 | warm-up と測定 tip の対応・成功証跡が無い | real | 採用 | fix-probe2: `run-warm.sh` が条件別 SHA/path、HEAD/clean 前後、実行場所 (dispatch の request 行)、`PYTHONDONTWRITEBYTECODE` 設定、pyc 件数を `warm-<X>.json` に記録。系列 script は両条件の warm 証跡 (rc=0、tip 一致) を投入条件にする。集計器も検査 |
| B-MF2 | 差分 probe の正例が M1 実変異でない (selftest の候補全体 stub は代用にならない) | real | 採用 | 親: `positive-control-probe.sh M1-hit-trusts-marker-campaign-run-id` (DW-O19、wave worktree、fix 統合後に実施) |
| B-S1 | 差分 probe に 2 claim × 各 2 attempt (marker・A 行双方の hit)、非 target の coverage 不正、legacy claim v1/v2 (正常 hit、membership 不正、無関係 floor 行不正)、同一プロセスの正常→改竄→再呼出しを独立名で | real | 採用 | fix-probe2 |
| B-S2 | M8 の KILL 帰属は「呼出し間保持を読取回数で検出」であり改竄拒否に帰属させない | real | 採用 (記録) | 変異台帳の帰属欄に記す。M8 は親の root-key 形 (test 順序非依存) を使う |
| B-N1 | context の寿命は「戻り値・closure・module state に公開せず次回呼出しで再利用しない」と書く | real | 採用 | insight |
| A nit | `F_long` / `r` / top10 は md の対表から外し JSON に残す。focus log に file/node 別 summary が無い | real | 採用 (集計器の md 出力だけ) / 記録 | fix-probe2 (md の対表を一次 + 裁定指定の補助に限定)。file/node 別は A/B の junit で出る |

規模上限は不変 (production +300/−150、test +900)。fix は既存 test の期待値を変えない。
