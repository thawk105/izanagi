---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-rulings-covered-ids
seq: 1
title: rulings 自己改善 — 覆われた ID の記録規則を索引外の既裁定・移管済み・実測解消へ広げ、出力冒頭で収集時点と「裁定待ち / 裁定済み未実装」の件数を分けた (docs のみ、branch worktree-dev-wave-rulings-covered-ids)
---

## 本文

- ユーザー依頼は「`docs/skill-self-improvement.md` rulings 節の発火条件『正本との食い違い』を実測して、
  `.claude/commands/rulings.md` の 2 箇所だけ直す。(1) 覆われた ID の更新規則を索引から外した既裁定・移管済み・
  実測解消にも及ぶ形へ補い、残作業の有無で `完了` / `更新 (裁定済み (D…) → 手番)` を分け、一律『実装手番』にしない。
  所有 wave が稼働中の ID は書かず控えに残し次回冒頭で書く。base digest は land 先 main の現物から取る。(2) 出力冒頭に
  収集時点 = entry N とユーザー裁定待ち N / 裁定済み未実装 M を分けて出す。byte 予算内で意味等価に縮約し上限は上げない
  (D782 / D730)。Codex 側 SKILL.md も同期。fold への機構追加・新台帳・検査は scope 外」。
- **発火条件は成立した。** 第 20 回 (entry 1596) が既裁定と判定して索引から外した B-1 の 18 行
  (`/work/1/SFC/tanab/dev-wave-jobs/rulings-all-20260917/materials-index.md`) のうち、相談 A が索引へ戻して
  fragment で更新した T-2402 / T-2665 を除く 16 ID (T-2670 / T-2671 / T-1912 / T-2645 / T-2701 / T-2690 / T-2393 /
  T-2394 / T-2442 / T-2450 / T-2451 / T-2459 / T-2478 / T-2693 / T-2696 / T-2290 / T-2291、T-2288 は AI 手番文) は、
  carry 鎖を解決した実体本文が「裁定待ち」「新規 (裁定が要る)」のままだった (親が archive 込みで実測)。同 wave の
  worklog fragment は索引 37 件だけを `完了` / `更新` に書き、B-1 は 0 件だった。
- **command の変更は 2 箇所 + 同期で、機構・台帳・検査は足していない。** 作法節の「1 裁定が複数 ID を覆うとき
  覆われた ID の項も更新する」を、索引外の既裁定・移管済み・実測解消も書く規則 (残作業なし `完了` / あり
  `更新 (裁定済み (D…) → 手番)`、一律 `実装手番` にしない、稼働 wave 所有分は根拠 D と共に inbox へ控え次回冒頭で書く、
  `base` は land 先 main の現物) へ置き換え、出力節冒頭に収集時点と件数分離 (総 open から未実装を消さない) を足した。
  設計判断は {{D:rulings-records-all-covered-ids-and-splits-open-counts}}。
- **予算は 5,623 bytes のまま 5,608 → 5,621 (残 2) に収めた。** 縮約は意味等価に限り安全義務は削っていない:
  frontmatter の description からクラスの再掲を落とす (本文 1 行目に残る)、クラス 1 の括弧書きを `read-only` だけにする
  (handoff・追記・編集なしは `CLAUDE.md` のクラス 1 定義が正本)、理由句 2 つ (「定型句 grep は変種を落とす」
  「T-ID 無しは台帳側にしか無い」) を落として命令だけ残す (D1868 と同じ型)、bold 全 40 個・見出しの「(発火条件つき)」・
  斜線と em dash 前後の空白・二重鉤括弧を backtick へ、を行った。
- **Codex 側 `.agents/skills/rulings/SKILL.md` は 3,000 bytes のまま 2,999 → 2,982 (残 18) で同じ 2 点を同期した。**
  literal 12 語は全部保持。ついでに同 Skill の「交差意見」節が command に存在しない節名 (「交差意見」節) を指していた
  食い違いを「作法節の相談義務」へ直した (節見出しは D1868 が参照するので据え置き)。intro の 1 文は description と
  重複するので落とした。
- 検査: `python3 tools/check_docs.py` 違反なし、`python3 tools/check_codex_agents.py` OK、
  `orchestrator/tests/test_check_docs.py` 574 passed / 3 skipped (growth hold、計算ノード request 2749.nqsv、18 秒)。
  実装面の差分は 0。
- **データ側 (B-1 の状態語訂正 fragment) は本 wave の scope 外で、並行 wave `worklog state spool correction` が担当した。**
  本 wave の worklog fragment は既存 T-ID の `完了` / `更新` を 1 件も書かない (peer と編集面を照合済み)。
  F35 の再発記録は本 wave が書く (新 F は起こさず F35 へ挿入)。
- scope 外で残る食い違い候補 (未変更): 作法節の「未 push は 20 commit 以上」は可変データで、routing 規則 4
  (裁定待ち・branch 状態・可変データを command へ書かない) に触れる。次回の rulings 自己改善で実測して扱う。
- 工数: codex 子 0 本 (docs-only、DW-C00 の既定軽量版)。計算ノード job 1 件 (焦点走)。
- 一次資料 (brief・候補文・検査 log) は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-rulings-covered-ids/`。

## 次の一手差分
