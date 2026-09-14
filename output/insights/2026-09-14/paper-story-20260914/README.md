# 論文ストーリー 2026-09-14 版の全項目再導出 — wave 記録

`docs/paper-story/2026-09-14.md` を、2026-09-14 時点の正典全体から全項目再導出して追加した wave の
記録である。**新規計測はしていない。** 既存の版・`results/`・`figures/`・`claim-evidence/` は
1 byte も変えていない。

- wave: `dev-wave-paper-story-20260914`、branch `worktree-dev-wave-paper-story-20260914`
- 起点: local main `3b80b5a96`。段 4 直前に `af3762d62` へ ff-only で取り込んだ
  (/rulings 全件 第 18 回の裁定 D1986〜D1988 を含む 16 commit)
- 成果物: `docs/paper-story/2026-09-14.md` (新規、2,310 行 / 229 KB) と
  `docs/paper-story/README.md` の 3 節の更新

## 1. 依頼が挙げた前提の実測

依頼が挙げた 3 件は、いずれも権威 bytes と一致した。

| 対象 | 一次資料 | 実測値 |
|---|---|---|
| A-2 | `output/insights/2026-09-07_t2364-paper-story-a2-certification/certification.json` | attempt `t2364-20260907b`、outer `observed-positive`。rr5 adopted 3,987,794 / stock 2,438,295 (effects 0.6354846316791036)、rr50 adopted 4,297,929 / stock 3,756,230 (effects 0.14421348000521794)。4 cell とも `source_binding_status=bound`、correctness `certified` |
| A-6 | `output/insights/2026-09-08_t2411-paper-story-a6-certification/certification.json` | attempt `a6-20260908b`、outer `reject`。rr95 stock 10,088,796 / adopted 9,505,248 (effects −0.057841193339621455)。2 cell とも `bound`、correctness `certified` |
| balanced stock-inline 対 | `output/insights/2026-09-14_t2589-consumer-real-artifact-repair/README.md` §1 | `accepted`、ratio 1.1122537536191646、improvement_percent 11.225375361916456。baseline median 3,893,509 (cv 0.0227) / target median 4,330,570 (cv 0.0128)。**再測定なし** |

## 2. 依頼に無く、導出で出てきた正典の前進

段 2 の plan が 6 件を挙げ、親がすべて一次資料で検算した。

- **A-1 の反復数は確定していた。** `output/insights/2026-09-13/paper-story-a1-balanced5-sized-preregistration/sizing-certificate.json`
  (`status=selected`) が 3 workload とも n = 30 / df = 29 / t 臨界 2.8315526875186725 を選んでいる。
  **本走 policy は非認証 lane のまま凍結され (D1973)、本番測定の認可は D1986 項5 で据え置かれた。**
- **走行間ばらつきの下限が 3 workload そろっていた。** rr5 0.9536% / rr50 0.7250% / rr95 0.2228%。
  write-heavy と balanced は **2026-09-05** の測定 (request `978588.nqsv` / `978589.nqsv`)。
- **鍵の独立性は成立していなかった。** D1829 §3 の逐語 —「所有 uid は AI の実行主体と同一である。
  したがって D906 の『候補および AI が書ける領域の外に置く』は満たしていない」。
  **前版はこれを「限界は発生していない」と書いており、誤りだった。**
- **B-4 の「専用 driver が無い」は前版の執筆時点で既に偽だった** (D1694)。
- **official 床値 campaign は 2026-09-11 に史上初めて実投入されていた** (job `988501.nqsv`、
  launch certificate で fail-closed、D1341 により未 land)。
- **完了証明層は 1/12 のままだった** (2026-09-14 実測、`SATISFIABLE_CONDITION_IDS` は `{"C10"}`)。

## 3. 前版を訂正した 4 件

**3 件は「当時から誤り」である。** 詳細は新版の冒頭と `docs/paper-story/README.md` の訂正一覧。

1. 鍵の独立性 (D1829)。生成者の分離とアクセス権限の分離の取り違え。
2. B-4 の専用 driver 不在 (D1694)。裁定日の時点で既に偽。
3. backoff の機構名。「内蔵指数」ではなく固定幅の適応制御 ([T-2338])。
4. 旧 4 cell の certified の母集合。**stock 2 cell は `BACK_OFF=0` (無 backoff)** であり、
   「4 cell とも内蔵 backoff 有効の build」は誤り。**段 3 のレンズ A が見つけ、親が旧 attempt の
   権威 bytes で検算した。**

## 4. 子の工数と所見

| 段 | 子 | 結果 |
|---|---|---|
| 2 | plan 1 本 | 再導出地図 + 親の暫定裁定 3 件への評価。(P1-a) に不同意 |
| 3 | consult 2 本 (`--lane sol` / `luna`) | 両者 NO-GO。所見 8 件 + 6 件 |
| 6 | review 2 本 | 両者 NO-GO。報告 15 件、相異なる所見 13 件 (must-fix 11 / nit 2) |

**`--lane` の 2 値は現在同じモデルに解決される (D1987)。「別系統モデル 2 本」とは数えない。**
子は 5 本とも `tools/check_codex_output.py` rc=0 を通した。逐語は `verbatim/` に全文を収める。

**段 3 の 3 者 (plan + 2 レンズ) が一致して親の暫定裁定を 1 件倒した。** 親は
「README が『本節はまだ評価していない』と書いている以上 A-2 は A 群の残件のまま」と起案したが、
D1645 の逐語の解除条件は「正しい identity で取り直した attempt が出るまで」である。
**この撤回が新版の §8 の骨格を決めた。裁定は {{D:a2-a6-release}}。**

**段 6 の所見で最も重いのは、両レンズが独立に指摘した「符号反転の原因を同定したかのように
書いていた」である。** 同じ版の別の箇所と図 6 のキャプション正文が「原因は同定していない」と
書いており、文書内の明示的な矛盾だった。

**レンズ A は、新版が自分の到達点を過小に書いていた箇所も 1 件見つけた** — §2 第 2 幕が
「同一 campaign 内の対比較は write-heavy と read-heavy については取れていない」と書いていたが、
実 WAL では A-2 と A-6 が workload ごとに 1 campaign の中で stock と adopted を測っている。
**D496 が求める形は 3 workload とも満たしている。取れていないのは A-1 の配置と推定対象である。**

## 5. 親の手順違反

**段 6 のレビュー子 2 本が worktree を読んでいる最中に、親が本文を 2 箇所編集した。**
機序帯の abort 率の出所についての追記である。子が torn な状態を読みうる。所見への影響は
確認できなかったが、手順としては誤りなので記録する。

## 6. 導出で見つけた一次資料間の食い違い 1 件

**機序帯の abort 率について、2 つの一次資料が違う値を書いている。**
`output/insights/2026-06-22_p2-case-study-backoff-synthesis.md` は
「abort を半減 (81.8→49.8%)」、`docs/paper-story/notes-2026-07-10.md` は
「『abort 半減』は誇張。実測は 0.815 → 0.494 = 約 4 割減 (相対 39.3%) で、半減 (0.408) には
届かない」と書く。**後者が前者を訂正したものなので後者を採り、食い違いの存在を新版の本文へ
明記した。** 定性的結論 (大幅な abort 減・有用 IPC ほぼ不変) は両者で変わらない。

## 7. 検査

- `git diff --check`: rc=0
- `python3 tools/check_docs.py`: rc=0 (`check_docs: 違反なし`)
- 本文が引く `output/insights/` の path 30 件を機械的に実在確認 (残る 1 件は拡張子なしの図 stem)
- 本文の件数宣言を検算: §0 の動いた事実 13 点、冒頭の訂正 4 件、§2 (g) の 8 点、
  §7 の前半 49 項 + 後半 9 項、§8 の A 群の残件 2 項、§9 の 7 種
- 実装面 (D95 決定 2 = 非 Markdown) の差分はゼロ。**変異 matrix は DW-S04 により免除。**
  **受入全走は免除していない。**
