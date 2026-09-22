---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-22
wave: worktree-dev-wave-comsys2026-manuscript
seq: 1
title: 論文ストーリー 2026-09-22 版と ComSys 2026 投稿原稿 (日本語・研究報告書式、14 頁) を作った — 版は起点 8fd2a2f5c までの正典 (entry 1796〜1818、D2206〜D2218) を反映し静的 backoff の一事例を機構の新しさとして書かない限定を置き、原稿は日本語草稿 6 組を版に整合させて 1 本へ圧縮して IPSJ の techrep で組版した (docs のみ、台帳 ID 未起票、branch worktree-dev-wave-comsys2026-manuscript)
---

## 本文

- 依頼 (ユーザー直接起動の `/dev-wave`、逐語 = job dir `verbatim-request.md`): ComSys 2026 投稿原稿の統合 (根拠 D2212 項 9) と、同じ wave での論文ストーリー次版、研究報告書式への組版。
  記録 = `output/insights/2026-09-22/comsys2026-manuscript/README.md`。版 = `docs/paper-story/2026-09-22.md`。原稿 = 同 insight dir の `manuscript.tex` と `manuscript.pdf`。
- **組版環境:** IPSJ のスタイル一式 `ipsj_v4-1.zip` (2025-02-06 更新) を取得し、研究報告は UTF8 版の `\documentclass[submit,techrep,noauthor]{ipsj}`。login に TeX が無いので apptainer で
  `ghcr.io/paperist/texlive-ja:debian` を job dir に取得して platex → dvipdfmx で組んだ (ipsj.cls は uplatex 非対応)。スタイルは配布条件の記載が無いので repo に入れず、入手 URL と sha256 を README に書いた。
- **版:** 前版 21c を複製して時点語を機械置換 (前版→2026-09-21b 版 235、この版→前版 222、本版→この版 1) し、冒頭・§0・§10 を親が書き、§1〜§9 は Claude の下書き役 7 本の置換案 136 件を
  親が一次資料で監査して当てた (親の修正 15 件・追加 6 件)。下書き役の置換案は版名と日付を取り違えた文 (「2026-09-22 版で Tier0 を実装」型) を 11 か所含み、親の監査で直した。
- **新事実 2 点を版と原稿に置いた。** D2212 の理由欄 (静的 backoff の成功例は Polyjuice OSDI'21 §4.5 が既に示した内容) に従い一事例を機構の新しさとして書かない。差分分析が挙げた ADRS
  (arXiv 2510.06189、LLM の進化探索で transaction scheduling) は正典 related-work に未収載で、位置づけの 1 文の 3 条件との関係は判定していない (原稿もそう書いた、ユーザー判断へ)。
- **原稿:** 概要と第 1 節を親、他の 5 断片を Claude の下書き役 (opus 3・sonnet 2) が書き、親が全節を監査・修正した。本文に内部 ID を出さず出所は LaTeX コメントに置いた。参考文献 27 件は
  正典が正式題目を持たないため arXiv API と Crossref の取得値で親が書き直した (DBLP はボット判定で取得不能)。14 頁 (本文 13 + 参考文献 1) で brief の目標 13 頁を 1 頁超えた — 限定を削らずには詰められず、
  頁数の判断はユーザーへ返した。
- **段 6 (D2211 項 11 どおり Codex):** レビュー A (版) NO-GO must-fix 3・should 1・nit 2、レビュー B (原稿) NO-GO must-fix 3・should 7・nit 1。親が全件 real と裁定して直した
  (A: K2 の既認可の一括・exact-85 の裁定待ち残り・図の「組み込みはしていない」の現在形継承、B: 長時間検証の失格条件から判定不能の脱落・探索コストの向きが逆に読める表現・今後の課題の「実験なし」)。
  焦点再レビュー 1 巡目は GO (新規 must-fix 0、closed 11 / partial 5 / regressed 0)。その新規 should のうち 1 件は親の編集の誤りで、原稿の文の途中に LaTeX の出所コメントを差し込んだため
  同じ行の後続 3 文が PDF から消えていた。親が同じ型を機械走査して第 1 節にもう 1 か所見つけ、両方を戻した ({{F:latex-comment-swallow}})。partial の書誌の API 未確認の欄と再組版の手順は原稿 README に書き、
  頁数 (14 頁) はユーザーへ返した。
- **採用時点より後の着地:** 着手後に main が `8629f7b3e` へ進み entry 1819〜1823 と D2219 が着地した。特に entry 1823 (K2 の同一 job pair 再投入が成立、4 巡目も両方 certified) と D2219 項 2
  (TPC-C の段 1 → 段 2 の分割を確定) は版と原稿の記述を後から古くした。依頼が起点を着手直前の main に固定したので採用時点は動かさず、README の stale 注記に積み、原稿の該当 2 か所に注釈コメントを置いた。
- 親の誤り (near miss、実害なし): brief と原稿骨格の見出しに推定の時刻 (09:10 / 09:40) を書き、file の mtime (09:04 / 09:07) で直した。
- 工数: Claude の子 = 事実抽出 2 本・§7 要約 1 本 (opus)、版の置換案 7 本 (opus 4・sonnet 3)、原稿の下書き 5 本 (opus 3・sonnet 2)。Codex = review 2 本 (6〜7 分)、focus 1 本 (6 分)。計算ノード = 受入のみ (本 fragment を含む tip で投入、結果は land の受領証)。
  コンテナ取得と組版は login (apptainer)。

## 次の一手差分

### 新規

- {{T:comsys-manuscript-post-origin}} **P1・新規 (docs、ComSys 原稿の改訂)**: ComSys 2026 投稿原稿 (`output/insights/2026-09-22/comsys2026-manuscript/manuscript.tex`) に、採用時点 `8fd2a2f5c` より後の着地を反映する —
  entry 1823 (K2 の同一 job pair 再投入の成立と 4 巡目、原稿 4.7 節・7 節 (d) の「結果は無い」が古くなった)、D2219 項 2 (TPC-C の段分割の確定)。著者・所属・頁数・ADRS の扱いはユーザー手番で、決まり次第同じ改訂で入れる。
  原稿締切は 10/30 (発表申込 10/16)。
