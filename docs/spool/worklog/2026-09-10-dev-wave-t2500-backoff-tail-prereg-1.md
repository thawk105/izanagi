---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-10
wave: dev-wave-t2500-backoff-tail-prereg
seq: 1
title: [T-2500] 静的 backoff 右 tail の本格格子と停止基準を事前登録して凍結した — 数値は 3 者が独立に一致したが、規則が判定を一意に決めない欠陥を 3 巡かけて潰した (docs のみ、branch worktree-dev-wave-t2500-backoff-tail-prereg、実装面の差分 0 につき変異 matrix は DW-S04 で免除)
---

## 本文

- 一次資料は `output/insights/2026-09-10_t2500-backoff-tail-prereg/`。逐語 18 本 (投げ文 6・
  子出力 7・裁定・親が書いた計算 script 2) を置いた。設計判断は
  {{D:tail-grid-cap-anchored}} と {{D:tail-saturation-three-way}}。
- 成果物は `docs/b10-backoff-static-tail-preregistration.md` (v1) と `docs/README.md` の地図 1 項。
  **本走の投入は行っていない。** driver も RUN_KIND も書いていない (docs-only)。
- **段 3 が格子の設計を壊した。** 段 2 プランの「1000 起点の半オクターブ + 終端の幾何中点」は、
  終端の短い区間 (対数比 0.11) で **5 rep では真に平坦でも到達できる上限が 9.1%** になり、
  5% の平坦基準に届かない。飽和が最も起こりうる右端でだけ述語が発火しない設計だった。
  表現上限 9999 を起点に下向きへ刻む形へ変え、tail の対数比を 0.34642〜0.34673 に揃えた。
- **段 3 の棄却 finding:** レンズ A は 2 件 (個々の規則の恒真性、binary 相異要求の弱さ) を、
  レンズ B は 4 件 (格子の到達不能、探索値が基準を通る懸念、時間枠超過、既存系列との衝突) を
  自ら refuted と判定した。
- **親の読み違いを段 3 が 3 つ訂正した。** (1) 研究前進を「B-10 の過抑制域」と書いたが、
  D1678 が見送ったのは過抑制域の**機序**であり、本 wave が前進させるのは記述的特性化である。
  (2)「docs に静的 tail の事前登録は無い」は絶対表現では過大で、D1813 が既に 2 段構成を登録している。
  (3) `git grep` 0 件は exact 文字列の不在しか示さない。
- **量子化の根本原因を実装まで辿った。** `external/ccbench/common/result.cc` の
  `Result::displayAbortRate` が abort 率を小数第 4 位までしか印字しない。tail の右端では
  1e-4 の量子が平均の 0.7〜1.4% に当たり、実測で **5 rep の標本標準偏差 (相対 0.39%) が
  量子の半分 (0.44%) より小さい**。丸め値から区間推定を作ると分解能不足が飽和の証拠に化ける。
- **WAL の現物で「再構成できるか」を確かめた。** 正しさ検査の記録は `commits` / `aborts` を
  整数のまま持つが、**性能測定の記録は rep ごとの abort 率を持たず、実行中の in-process 捕捉から
  report へ直接入っている**。したがって本走側の新しい保存が要る。投入前条件に書いた。
- **段 6 と焦点 3 巡が、親の書いた規則の全域性と一意性を順に壊した。** 段 6 は 13 件
  (判定保留が明白な低下継続まで吸収する / 集約 verdict が排他でない / 局所平坦を飽和と呼べる /
  ゼロから正値への遷移が失敗条件に無い ほか)、焦点 1 巡目は 6 件、焦点 2 巡目は 5 件。
  **焦点 2 巡目の 1 件目は親の fix が持ち込んだ致命的欠陥で、3 job の workload 座標を
  cohort 同一性へ入れたために正常な走行がすべて `invalid` になっていた** —
  非 `invalid` の結末が到達不能だった。DW-O16 の 3 巡上限で閉じた。
- **親が自分で見つけて直した 2 件。** (1) spec の JSON に終端 marker の文字列そのものを値として
  置いており、marker 走査型の consumer が JSON を途中で切る。**親自身の抽出が実際に切れて発覚した。**
  (2) **格子の値が生成規則と 2 点ずれていた** (3536 / 7071 と書いたが規則の解は 3535 / 7070)。
  下端から上向きに掛けたのが原因。凍結前に修正し、規則から再生成して照合する手順を本文へ入れた。
  段 4 裁定文に残った誤った literal には erratum を追記し、後続 wave が裁定文を数値の権威に
  しないよう明記した。
- **数値は 3 者が独立に一致した。** 段 3 レンズ B・段 6 レビュー B・親が t 分位点と検出力を
  それぞれ計算し、多重度 18 で t=3.758586、半オクターブ `U_flat`=2.881〜2.884%、
  短区間 8.692% まで一致した。親は正則不完全ベータ関数から t 分位点を自前実装した。
  最終形の両側 36 では t=4.255642、3.256〜3.259% / 9.783%。
- **セッション異常 1:** 段 6 のレビュー 2 本が初回投入で rc=2 即死した。理由は
  `--reasoning は --stage review/focus/author/fix では指定できない`。新しい F は採らない —
  `DW-C01` と `DW-O01` が既に書いており、親の手順漏れ (plan と consult では `--dry-run` で
  argv を検査したのに review では省いた) である。`.done` は消さず新しい path で再投入した。
- **scope 外として裁定パッケージへ返した 2 件。** (1) 正値 `BACKOFF_FIXED` の pointwise meaning
  witness gate の新設 (既に [T-2501] でユーザー裁定待ち)。(2) `check_docs.py` へ新規 prereg 本文の
  検査を足す案 — 代わりに「checker 緑は本文の中身の証拠ではない」を本書へ明記した。
- **本書が現時点で持つ効力を誇張していない。** spec を parse する consumer は存在しないので、
  効力は規範と時点証拠に限る。投入前条件 5 件のうち 4 件は現状の実装で満たされていないことを
  実測で確認した (consumer 不在・性能側の整数カウンタ非保存・出所 field 未発行・
  正しさ記録が 1 cell 1 本)。
- **エージェント工数:** Codex 子 7 本 (plan 1 / consult 2 / review 2 / focus 2)。
  すべて `gpt-5.6-sol`。receipt は job artifact 側にある。

## 次の一手差分

### 完了

- [T-2500] 静的 backoff 右 tail の本格格子・反復数・停止基準・失敗条件を、本走の結果を見る前に
  固定した事前登録として書き、凍結した。探索値は正式標本へ混ぜていない。本走の投入は行っていない。
  remaining: none
  base: 13e3265eb9b6a6a69111140cf8a9eb258067cdc87482e61d127fe85f6c78c8b4

### 新規

- {{T:tail-formal-driver}} **P1・新規**: `docs/b10-backoff-static-tail-preregistration.md` の
  投入前条件 5 件を満たす本走 driver を実装する。spec を parse する consumer、性能測定の rep ごと
  整数カウンタの WAL 保存、observation ごとの出所 field、1 cell 5 本の正しさ記録、
  正しさ mode 座標の記録。RUN_KIND `t2500-tail-formal`、report schema
  `t2500-backoff-static-tail-formal-report/v1`、成果物 stem `t2500-backoff-static-tail-formal` は
  事前登録が固定済み。既存 3 系列の受理集合と `EXTENDED_SWEEP_US` には触れない。
