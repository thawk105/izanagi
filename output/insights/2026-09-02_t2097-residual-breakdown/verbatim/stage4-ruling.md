# [T-2097] 段 4 裁定 — 21 所見の real/refuted と plan v2

判定者 = 親。段 3 の 2 レンズ (A = 測点の妥当性・観測者効果、B = 既存被覆・裁定境界・射程) の
全 21 所見を裁定する。BLOCKER は A が 5 件、B が 2 件。

## 裁定表

| ID | sev | 判定 | 採否 | 措置 |
|---|---|---|---|---|
| A-1 | BLOCKER | real | 採用 | 名称を改める。A/B/D/C は「w* から見た wall 露出区間」であり原因別費用ではない。加えて**全 worker の report 区間の和集合とその補集合**を出す (どの worker も report 中でない時間 = 真の全体空き) |
| A-2 | BLOCKER | real | 採用 | probe の hook 実行順を実行時に列挙して固定し、取れない区間は `unclassified_outer_protocol` として残す |
| A-3 | MAJOR | real | 採用 | E18 を `workerfinished_received` に改名。probe の書き出しは sessionfinish と unconfigure の 2 回に分け、各々の所要も測る |
| A-4 | BLOCKER | 一部 real | 一部採用 | selector 専用と timing 版を別実体にし hook 登録数も対照する。**複数 job の無作為化・同等性区間は scope 外** (裁定パッケージ候補)。n=2 では同等性を主張せず、対照との差を限界として明記する |
| A-5 | BLOCKER | real | 採用 | **主張を変える。** 本 wave は 2026-09-01 08:15 の走の内訳を出すのではなく、**現行 checkout の残差とその内訳**を出す。旧値は文脈としてのみ引く |
| A-6 | MAJOR | real | 採用 | TMPDIR・fs・`__pycache__` 件数を arm ごとに記録。`PYTHONDONTWRITEBYTECODE` を probe 側で新設しない (production の判断に委ねる)。cold/warm を別 regime として扱う |
| A-7 | BLOCKER | real | 採用 | 単独性の確認は F3 の常設義務。arm 前後と走行中に node 全体の CPU 使用・load・非子孫 process・同居 job を標本し、外乱があればその arm を無効にする |
| A-8 | MAJOR | real | 採用 | zero 走を `instrumented zero-selected calibration` と明記し、D711 の 12.86 秒と同じ量だと主張しない |
| A-9 | MAJOR | real | 採用 | 閉包式は schema 内部の代数検査と明記。独立検査 (外側 wall、terminal の上下限、event 数、phase 数、worker 対応) を別に置く |
| A-10 | MAJOR | real | 採用 | `runner_start_to_pytest_session` へ改名。interpreter/plugin 費用とは呼ばない |
| A-11 | MAJOR | real | 採用 | **親の一次表の誤り。** 14 走の残差を `report.json` の実測最大 occupancy で再計算し、下界残差は別列にする |
| A-12 | MAJOR | real | 採用 | PBS 層 / pytest wall 層 / worker report 層を別 endpoint として維持。内訳計算は丸めのない `report.json` を使う |
| B-1 | BLOCKER | 一部 refuted | 一部採用 | zero 走は受入判定ではなく較正であり、受入の選択・排他・gate を一切変えない (production plugin は全 collection と割付を終えている)。**規律 2 の禁止対象ではない**と裁定する。ただし成果物では必ず較正走と明記し、共有 root へ置く arm dir に較正である marker を置く。**着手前に共有 root を走査する consumer の有無を実測し、在れば停止する** |
| B-2 | BLOCKER | real | 採用 | **shard-1 と shard-2 の両方**を同じ測点で計装し、両方で再現した成分だけを「共通」と呼ぶ。shard-0 は D1384 により対象外 |
| B-3 | MAJOR | real | 採用 | 既存被覆へ D918 / F595 を追加 (テスト 0 件の走は cache 無し 49.32 秒 / 有り 15.40 秒、差 33.9 秒)。**本 worktree は新品で cache が冷たい**ため、最初の実 shard 走で温めてから較正走を置く |
| B-4 | MINOR | real | 採用 | 既存被覆へ D1103 (残差 59.22 秒)・D747 (残余 61.3 秒の候補)・D917 を異同付きで追加 |
| B-5 | MAJOR | real | 採用 | A-1 と同一措置。「固定費」「report 外費用」という呼称を成果物の見出しから外す |
| B-6 | MAJOR | real | 採用 | D1299 の 5 項 (tested tip、K、worker 数、collection digest、growth hold の opt-in 状態) を artifact の field にする |
| B-7 | MAJOR | real | 採用 | 「1 PBS job / 1 hostname / arm ごと n=2 / 当該 checkout 限定」を成果物へ固定し、一般値を出さない |
| B-8 | MAJOR | real | 採用 | 子成分の橋渡し区間に名前を与えて親へ閉じる。閉じられない補助値は非加法の診断値として内訳表から外す |
| B-9 | MINOR | real | 採用 | session 外の値は別表へ隔離し、内訳合計へ入れない |

## plan v2 (確定)

**測る量:** `pytest wall − その走の実測最大 worker report duration 合計` (呼称: 残差)。
これを w* から見た 4 区間 A / B / D / C へ分け、加えて**全 worker のいずれも report 中でない時間**を
独立に出す。原因別の費用とは呼ばない。

**arm 構成 (計算ノード gen_S の 1 job、逐次):**

1. `R2-A1` shard-2・probe 無し (cache を温める対照)
2. `R2-B1` shard-2・probe 有り
3. `R1-B1` shard-1・probe 有り
4. `R1-A1` shard-1・probe 無し
5. `R1-A2` shard-1・probe 無し
6. `R1-B2` shard-1・probe 有り
7. `R2-B2` shard-2・probe 有り
8. `R2-A2` shard-2・probe 無し
9. `Z-S1` 較正走・selector のみ
10. `Z-B1` 較正走・selector + timing

見積り: shard-2 約 135 秒 x 4、shard-1 約 180 秒 x 4、較正 約 30〜60 秒 x 2 で約 22〜26 分。
`elapstim_req=01:00:00` とする。

**停止条件:** shard の `group_to_workers` が想定と違う、affinity が 48 でない、外乱を検知した、
shard-1 と shard-2 の universe が互いに一致しない、時計 offset drift が 5 ms を超える、
`finished != selected`。**collection 件数は実測して記録する量であり、固定値を停止条件にしない**
(本 wave の checkout は比較対象の走より後で、test が増えている)。

**成果物:** `output/insights/2026-09-02_t2097-residual-breakdown/` (README + measurements + probe 逐語)。
worklog / decisions は spool fragment。**実装面の commit は 0。**

## 変異事前登録

本 wave は実装面の差分が 0 byte (probe は commit せず repo 外へ退避する) であるため、
`DW-S04` により変異 matrix を免除する。受入全走は免除しない。

## ユーザー裁定へ返す項目 (実装しない)

1. probe 効果の同等性を複数 job・無作為化で立証する設計 (A-4 の残り)。今回は対照との差を限界として書くに留める。
2. shard-0 固有の約 21.9 秒の計測 (D1384 が今回は採らないと裁定済み)。
3. 旧 checkout での「56 秒そのもの」の再現 (A-5)。今回は現行値の内訳を出す。
