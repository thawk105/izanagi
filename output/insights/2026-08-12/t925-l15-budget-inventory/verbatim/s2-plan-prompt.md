# 段 2 プラン起草 — docs/dev-wave 予算棚卸し ({{T:l15-budget-inventory}} / [T-925])

あなたは izanagi の dev-wave 段 2 プラン起草担当である。read-only sandbox で静的検査だけを行う。

## 最初に読む (読めなければ即停止し、その旨だけを報告せよ)

`/work/1/SFC/tanab/dev-wave-jobs/t925-l15-budget/brief.md` — 親 brief。
scope、確定済みユーザー裁定、実測値、不変条件、provisional 裁定 (P1)〜(P4) が書いてある。
本 prompt へ内容を複製していない。必ず絶対パスで開くこと。

## 前提 (親が実測済み。再測定に時間を使わないこと)

- 予算実測: L0 入口 `.claude/commands/dev-wave.md` = 9,500/9,500 (余白 0)、
  L1 = 10,624/10,625 (余白 1)、L1.5 = 9,564/9,566 (余白 2)、L2 単節最大 = 997/1,000。
- 層の定義: L1 = 段 dispatch 表で「wave 開始・段 1・段 4・段 7・段 8 preflight・段 9」の U 節、
  L1.5 = 「段 2 preflight・段 3 preflight・段 5・段 6」の U 節から L1 を引いた差、L2 = 残り。
  予算検査の実装は `tools/check_docs.py` の `_check_dev_wave_layer_budget` (3724-3826 行)、
  定数は 182-260 行。
- 節ごとの実測 bytes (L1.5):
  workers.md 全体が L1.5 (preamble 165 / DW-S02 181 / DW-S03 623 / DW-S05-A 463 /
  DW-S05-B 301 / DW-S05-C 1114 / DW-S06-A 325 / DW-S06-B 880 / DW-S06-C 318)、
  mutation.md の DW-M02 294 / DW-M03 344 / DW-M04 405 / DW-M05 765 / DW-M06 258 /
  DW-M07 224 / DW-M08 822、operations.md の DW-O01 942 / DW-O02 508 / DW-O03 261 /
  DW-O05 206 / DW-O13 165。
- 節ごとの実測 bytes (L1): core.md preamble 108 / DW-C00 1079 / DW-CTX 875 / DW-G01 256 /
  DW-G02 263 / DW-G03 256 / DW-G04 227 / DW-G05 466 / DW-S01 1637 / DW-S04 1051 /
  DW-S07 1250 / DW-S08 226 / DW-S09 416 / DW-STOP 577、
  mutation.md preamble 109 / DW-M01 533、operations.md preamble 205 / DW-O23 1090。
- **機械権威 (削除・語順変更とも不可)**: `tools/dev_waves/launch_authority.py` が
  `DW-O01` の `` `<model>`: `` 行、`DW-S06-A` の `reasoning=` 行、`DW-S06-C` の `reasoning=` 行を
  逐語 regex で解析し、節全体の sha256 を起動 receipt へ束縛する。1-70 行と 369-455 行を読め。
- 同 module の `snapshot_authority` は live 実行時に `docs/dev-wave/operations.md` と
  `docs/dev-wave/workers.md` の working tree と authority commit を byte 比較して fail-closed する。

## 読む対象と範囲 (これ以外を網羅読みしない)

1. `docs/dev-wave/core.md`, `workers.md`, `mutation.md`, `operations.md` — 全文 (合計 27KB、短い)。
2. `.claude/commands/dev-wave.md` — 全文 (9.5KB)。
3. `tools/dev_waves/launch_authority.py` — 1-70 行、369-455 行。
4. `tools/check_docs.py` — 182-260 行、3724-3826 行。それ以外は必要な識別子を grep で当たるに留める。
5. `tools/dev_wave_codex.py` — 全文 (265 行)。
6. `hooks/README.md` — 全文 (303 行)。
7. `docs/failures.md` (6,211 行) は**全文を読むな**。dev-wave 4 文書が引用している F 番号
   (例 F23/F24/F25/F27/F28/F29/F30/F31/F32/F33/F34/F35/F36/F37/F39/F41/F42/F43/F48/F71/F78)
   だけを `grep -n "^## F23"` の要領で位置特定し、該当項だけを読め。
8. `tools/mutation_harness.py`, `tools/dev_wave_wait.py`, `tools/check_codex_output.py`,
   `tools/run_tests.py`, `tools/dev_wave_land.py` — 全文を読まず、義務語 (flock, resume,
   pid-file, done, 総括 等) を grep して該当関数だけを読め。

**打ち切り指示:** 上記で判断がつかない義務は「未確定」と書いて次へ進め。網羅読みで
model call を使い切ってはならない。1 つの根拠に 2 回以上 grep を重ねない。

## 課題

`docs/dev-wave/**` の **L1.5 と L1 の全節**について、節を**義務単位**に分解し、
義務ごとに次を file:line 粒度で判定する棚卸し表を作れ。

- **義務**: その文が命じている検証可能な行為 1 つ。
- **機械代替**: その義務違反を fail-closed で止める機械検査が既に実在するか。
  実在するなら `file:line` を必ず示す。「テストがある」ではなく
  「**この義務に違反した状態が rc≠0 になる**」ことを示せ。示せないなら「なし」と書け。
- **発火実績**: その義務が実際に事故を止めた/事故が起きた記録 (F 番号・D 番号) の有無。
- **判定**: 次の 4 つから 1 つ。
  - `A 削除可` = 機械代替あり かつ 発火実績が機械化以降ゼロ (無条件削除候補)
  - `B テスト化可` = 機械代替なしだが、実在する入力から機械検査を新設でき、散文を削れる
    (新設 gate の入力が実成果物のどの field に存在するかを `DW-O13` に従い示すこと)
  - `C 維持` = 機械代替不能な自己申告義務、または機械権威そのもの
  - `D 裁定へ` = 片方だけ真、または判断が割れる

## 併せて答えること

1. 判定 A と B の節を実施した場合に**空く bytes の実測見積り**を層別に出せ。
   削除する逐語を明示し、その byte 数を数えよ (日本語は UTF-8 3 bytes/字で概算せず、
   実際の逐語を引用して親が数えられる形にせよ)。
2. 堰き止められた 4 系統の追記先と**必要 bytes** を最短形の逐語案で示せ。
   - [T-925] (2) 中断した codex 子の部分成果物は素性を明記して保全し次の子に監査させる → `DW-O01`
   - [T-925] (3) 編集量の大きい fix 巡は `--max-model-calls` を見積もって上げる → `DW-O01`
   - [T-916] (c) 親 brief で分類文と実アンカー表を二重管理しない (アンカー表だけを渡す) → `DW-S01`
   - [T-934] (a) 裁定停止 wave の再開契約 (裁定が結論だけを変え変更面の骨格が同一であることの
     確認 + 変更面の再検査を段 6 レビューへ寄せる) → 入口 `.claude/commands/dev-wave.md`
3. 層ごとの収支 (空く bytes − 要る bytes) を出し、**足りない層があればどれか**を明示せよ。
4. 実施順序を file:line 粒度で書け。`operations.md` / `workers.md` を編集すると codex 子が
   起動不能になる制約を順序へ織り込め。

## 禁止

- 予算上限 (`DEV_WAVE_L1_BYTES_MAX` 等) の引き上げを提案してはならない。
- dev-wave 系ファイルへの外出しを提案してはならない (読み込みが leaf 節単位のため削減 0)。
- 意味を変える縮約を提案してはならない。削除かテスト化のみ。
- 機械権威 3 行の削除・語順変更を提案してはならない。
- 正しさゲート・観測者効果・信頼境界の規律を緩める提案をしてはならない。

## 出力の作法

- 日本語で書く。合成済み文字を使い、結合用ダイアクリティカルマーク (U+0300 台) を出力しない。
- 書込可能 tmp が無いため pytest 緑は要求しない。静的検査で足りる。
  テスト実測は親が行うので、**あなたが実走していない結果を緑と書いてはならない**。
  実走していない項目は「未実走」と明記せよ。
- 判断の根拠は必ず file:line で示す。示せない主張は「未確定」と書く。
- 最後に `## 総括` 節を置き、層別収支と実施順序の結論を書く。
