---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-03
wave: dev-wave-sysinsight-related-work
seq: 1
title: SysInsight を related-work へ取り込んだ — 7.11 倍は専業 ML/RL でなく GPTuner に対する数字で、軸 3 は競合として直接接地した (docs のみ、branch worktree-dev-wave-sysinsight-related-work、実装面の差分 0)
---

## 本文

- ユーザー依頼: `2603.22708` (SysInsight, PVLDB 19(6) 2026) を related-work へ取り込み、
  7.1 の knob 系譜エントリが持つ 2 文を一次資料で裁定する。実装面の差分 0、軸 1 の成熟度 `RW1` は動かさない。
- **依頼の前提 1 件が一次資料と食い違い、裁定の中身が変わった。** 依頼は 7.11 倍を
  「専業 ML/RL (SMAC/DDPG++/ResTune/OtterTune) に対する収束速度」としていたが、本文 6.2 の該当文は
  `Compared with GPTuner, SysInsight converges ... 7.11x faster` であり、GPTuner は本文の分類では
  manual-driven だが **LLM を使う手法**である。全文で `faster` が現れるのは 3 箇所だけで、
  専業 ML/RL に対する収束比の数値は無い。abstract の `SOTA baseline` と貢献欄の `second-best baseline`
  は対象名を省いた短縮。**したがって争点 2 の「向きが逆」の根拠は、依頼が想定した形では立たない。**
- 争点 2 の確定した裁定は「無限定には残せない。ただし SysInsight は P2-5 を反証せず、
  **外挿範囲を狭める**」である。P2-5 は silo 8 通りという列挙しきれる空間での否定的結果であり、
  SysInsight は 44 knob に対し online 予算が乏しい側を測っている。**P2-5 の撤回は不要。**
- 争点 1 の確定した裁定は「介入面でしか成立しない」である。SysInsight は
  `rw_lock_x_lock_wait_func()` → `sync_array_wait_event()` / `ut_delay()` を読んで因果を言語化するので、
  **待機は読解の対象になっている。** 落としてはならない限定は 1 つでなく 3 つ (裁定記録 §2.7)。
  依頼の「届かないのはプロトコルの書き換えだけ」という一限定は成立しない。
- **敵対相談 2 本が親の当初裁定を 3 箇所で壊した。** (a)「逐語」と書いたが実体は LaTeXML 表現を
  正規化した転記であり文字列一致ではない、(b)「競合検出・abort は読解の対象にすらなっていない」は
  語の不在からは導けず「正の記述が無い」までしか言えない、(c) `rw_lock_*` を InnoDB の latch と
  同定してトランザクションの record lock から排除するには**一次資料の外の知識が要る**
  (`latch` / `record lock` / `park` はいずれも本文 0 件)。3 点とも成果物へ取り込んだ。
- **親が見落としていた最大の被害を敵対相談が出した: 軸 3 (説明可能性) に対し SysInsight は
  競合として直接接地する。** `structured reasoning chain` / causal link / hypothesis / 定量 rule /
  confidence を中核機構として持つため、「コードから機序を取り出す」「観測に接地した説明を作る」は
  差別化語として使えなくなった。`docs/paper-story/` は差別化の核を説明可能性に置いており、
  その書き換えは本 wave の scope 外なので次の一手へ送る。
- 判定タグを `引用元` から `引用元`+`外部補強` へ変えた。**接地は「LLM 由来方策の性能観測による
  事前検証」であり、直列化可能性の補強ではない** — confidence の定義は「その調整が目的関数を
  改善した割合」、6.3 の信頼性指標も「default より悪い設定の数」と累積改善率である。
  この限定を接地欄から落とすと、izanagi の正しさ verifier と同形の外部証拠があるように読める。
- 併せて既存の「Izanagi は knob 探索をしない (P2-5 で既反証)」も P2-5 の射程を越えていたので
  「研究対象として採らない」と「P2-5 が何を反証したか」に分けた。
- `docs/related-work/README.md` 7.6 の空白域は**現行文言のままなら反例にならない**ので動かしていない。
  破れる短縮形は裁定記録 §4.3 に列挙した。軸 1 は `RW1` のまま、pilot 29 行も動かしていない。
- 工数: 敵対相談 2 本 (codex `gpt-5.6-sol`, xhigh, read-only)。実装子・変異 matrix は
  実装面の差分 0 のため起動していない。
- **手順の瑕疵 (無害だが記録する):** 敵対相談 2 本を投入した後に main が進んだので `--ff-only` で
  追随した結果、子の receipt が持つ base-commit (`ddf8ccca`) と子が実際に読んだ作業木
  (`581a7b65`) がずれた。両者の差分は `docs/related-work/` を含まず、子が読む path は
  すべて同一だったため判定への影響は無い。次から子の走行中は ff を待つ。

## 次の一手差分

### 新規

- {{T:paper-story-axis3-vs-sysinsight}} **P1・新規**: `docs/paper-story/` が差別化の核に置く
  軸 3 (説明可能性) について、SysInsight (`2603.22708`) が競合として直接接地した件を裁定する。
  「コードから機序を取り出す」「観測に接地した説明を作る」は差別化語として使えない。
  残る差別化 (対象がトランザクション CC・action space の拡張・正しさゲートを毎反復) で
  核を書き直すか、核そのものを移すかを決める。根拠は
  `docs/related-work/claim-survey/2026-09-03-sysinsight-adjudication.md` §4.2。
