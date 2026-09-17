---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2758-recent-cc-candidates
seq: 1
title: [T-2758] 近年 CC 手法の候補表を docs/related-work に起こした — 優先調査候補 3 (Rebirth-Retire / Bamboo 対照 / Polaris)、追加対象の確定 0 件、未確認を合否へ倒さない三値記録 (docs のみ、branch worktree-dev-wave-t2758-recent-cc-candidates、変異 matrix = 実装面差分ゼロにつき免除)
---

## 本文

- ユーザー依頼は「[T-2758] (P2、D2114 項 4) 近年 CC 手法の候補表を docs/related-work に起こす — 一次資料・実装可用性・
  ライセンス・YCSB 適合・trace 移植費用・証明面・既存 CC (Silo / MOCC / TicToc / Cicada) との差、追加対象と棄却理由。
  入口 = literature map (NeurCC 2503.10036 SIGMOD 2026 / ATCC 2026)。D2095 の軸 1 登録済み検索とは重複取得しない
  (通常の文献調査、D1760 が許す範囲)。CCBench への実装追加とは分け、A (mocc 第 2 例) に従属させない。docs のみ。
  規律 2 を緩めない。本題の候補表だけ。framework・一般化は scope 外」。
- **閉じた。** 成果物は `docs/related-work/cc-candidates-2026-09-17.md` (日付付き凍結物、README 7.1 から引ける)。
  一次資料の取得記録・レビュー逐語・是正対応表は `output/insights/2026-09-17/t2758-recent-cc-candidates/README.md`。
  実装追加・pin 前進・変異探索面化は認可していない (D2114 項 3 / D1603 / D579 の別件)。共通契約の設計は scope 外で、
  候補表 §6 は確認課題の列挙に留めた。
- **判定 (候補表上)。** 17 候補を「充足確認 / 不適合確認 / 未確認」の三値で記録し、優先調査候補 = Rebirth-Retire
  (PVLDB 2025、ISC、DBx1000 系)、Bamboo (SIGMOD 2021、対照候補)、Polaris (SIGMOD 2023、対照用)。保留 = Plor (公開実装
  未確認)、Tebaldi、Shirakami S-OCC。棄却 (不適合確認) = Brook-2PL / Aria / IC3 / Shirakami S-LTX (事前知識)、Caracal
  (GPL-2.0)。母集合外 = Polyjuice / NeurCC / ATCC (学習型、入口)、CormCC、Sundial、TXSQL、ESSN。
  **四条件の充足を確認できた追加対象は 0 件** — 本調査で決められるのは優先調査候補まで。
- **調査の範囲と限界 (RW1)。** 世界の不在は主張していない。web 検索 3 系統 (走査語は候補表 §1) と入口 2 本の baseline 群、
  候補論文の参考文献から母集合を作り、検索結果全件は再現できないので追加候補の不在は結論しない。Polaris の論文本文は
  ACM 403・著者頁 404 で未読 (機構は公開 source から)。NeurCC / ATCC は WebFetch の抽出要約で読んだ。登録済み索引
  (arXiv API / OpenAlex / DBLP) への request は 0。
- **段 6 = 敵対レビュー 1 本 + 焦点再レビュー 1 本 (read-only codex、`gpt-6-astra` medium)。** 敵対レビューは所見 10 件
  (real 9 / refuted 1、must-fix 8)、最重要 = (1) Rebirth-Retire / Bamboo を「単版、trace 専用 field 1 個」と書いた前提の
  誤り (未 commit の複数版を読む)、(2) Polaris の `validate` の記述が source と不一致、(3) P3 が未確認を合否へ倒していた
  (「公開実装なし」「唯一」)。親は候補表を書き直し (三値化)、焦点再レビューは前巡 closed 6 / partial 4、新規 real 7
  (must-fix 5) を出した (S-OCC / Plor / Caracal の未確認を確定へ倒していた、Polaris の変更範囲の過小限定、DTA 2018 /
  DRP 2019 / SLOG 2019 を年代外と誤記、timestamp 再割当の断定)。全件を逐語で適用し、3 巡目は起こさなかった
  (対応表は insight §4)。段 2 / 3 の子は docs-only につき省略。
- **親の追加照合 (レビュー後):** neurcc の root 直下に LICENSE 系 file なし、RebirthRetire の LICENSE = ISC、aria = MIT。
  焦点再レビューはこれを独立照合していない (資料に含めなかった)。
- 素材: CCBench への追加候補を選ぶ基準として「差が Silo の 1 箇所の改変に収まる手法は stock として持つより izanagi の
  変異の到達点候補として意味がある」という観点を候補表 §2 に置いた (Polaris がその例。親の仮説であり、変異軸の採否基準は
  未確定)。
- 検査: check_docs rc=0 (v1 / v2 / v3)、s8b_holdout_freeze search rc=0、`git diff --check` 0。受入全走は fragment commit
  後の最終 tip に land 前に 1 回 (結果は land の受領証)。
- 工数: codex 子 2 本 (review 1、focus 1)。計測ゼロ、build ゼロ。web 取得 = WebSearch 7、WebFetch 6、GitHub API 14、
  raw / PDF 20。

## 次の一手差分

### 完了

- [T-2758] 候補表を `docs/related-work/cc-candidates-2026-09-17.md` に凍結し、README 7.1 と docs 地図から引けるようにした。
  優先調査候補 3・保留 3・棄却 5・母集合外 7、追加対象の確定 0 件。優先調査候補の未確認 (Rebirth-Retire の source、
  Polaris の本文、CCBench 対話 API への適合) を潰す作業と、候補表 §6 の確認課題を共通契約へ反映する作業は D2114 項 4 の
  B 実装判断 (共通契約 + 固有実装費用) の入力として、起票はその判断を扱う wave に委ねる。
  remaining: none
  base: 1191e235919f10cf974473b4569b35e155b9713fd32e7f9f171e56ea6c52daa7
