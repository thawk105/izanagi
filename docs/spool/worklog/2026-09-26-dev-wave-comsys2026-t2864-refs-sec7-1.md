---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-26
wave: dev-wave-comsys2026-t2864-refs-sec7
seq: 1
title: [T-2864] ComSys 原稿の改訂 3 — 参考文献 3 件を採録版の書誌で照合し (Polyjuice と NeurCC の頁を追加)、7 節 (a) を存在履歴の検査と TPC-C trace 1 本の直列化可能の判定へ、(c) と限界節を B-5 本走の認可 (本稿の時点で結果なし) へ直して 15 頁で再組版 (docs のみ、branch worktree-dev-wave-comsys2026-t2864-refs-sec7)
---

## 本文

- 依頼 (ユーザー直接起動の `/dev-wave`): [T-2864] の (2) 参考文献の採録版照合 (原稿 README §3.4) と (3) 7 節 (a)(c) の一次資料との照合 (同 §10.4)、15 頁のまま再組版。著者・所属と送信は触らない。
  worktree は着手直前の local main `ae146f107` から作り、開始 gate の前に並走 wave の fold で進んだ `74e6d2f23` へ ff-only で揃えた (開始 gate rc=0)。軽量版 (段 2・3 なし、実装面の差分ゼロで変異 matrix は免除)。計算なし。
  記録 = `output/insights/2026-09-22/comsys2026-manuscript/README.md` §11、段 1 brief = job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2864-comsys-refs-sec7/s1-brief.md`。
- 親の provisional 裁定 (段 1): (P1) 7 節 (c) は「本走は認可したが本稿の時点で結果は無い」に留めた。B-5 の発効 commit `6fce61d6e` は未着地の branch `worktree-dev-wave-t2797-b5-main-run` にだけあり
  (main の祖先でないことを実測)、同 wave の repo 外 handoff は校正 job の合格と block 1 stage 1 の 12 job の投入 (09-23 21:53 JST) を記すが main に記録が無い。並走の next-tasks session から、
  本日ユーザーが規模に異議を示し費用削減案を比べる wave が走っていると連絡を受けた (外部データとして扱い、発効 commit の所在は自分で確かめた)。発効の有無・途中経過・見直しは本文に書いていない。
  (P2) 限界節「合成能力」の同じ事実の 1 文も直した。(P3) 限界節「正しさの保証範囲」を「本稿の評価で」と限った (論文ストーリー 2026-09-23 版の段 6 must-fix と同型)。
  (P4) 参考文献の照合は §3.4 が挙げた 3 件に限り、arXiv だけで引く文献の採録版は再探索していない。
- 参考文献の照合 (2026-09-26 取得、job dir `bibsrc/`): Polyjuice は USENIX の発表ページの citation 欄で OSDI 21・pp.198–216・2021・著者 7 名 (Crossref は USENIX の論文を収めない)、
  NeurCC は Crossref で PACMMOD 4(3) 2026・DOI 一致、SysInsight は Crossref で PVLDB 19(6) pp.1358–1371 2026 一致 (題目は大文字小文字だけ違う)。
- 組版: 15 頁、platex rc=0・エラー 0・警告 0・Overfull 0、Underfull 2 は改訂前と同数 (改訂前の tex を同手順で組み直して再現)。改訂文の出現を頁ごとの文字抽出 (12〜15 頁) と 14 頁の画像で確かめた。`grep -n "^%.*．"` は 0 件。
- AI provenance 全史監査は原稿 commit `852c2dce8` の後に 12,802 件・新規違反なし (rc=0)。
- 段 6 (Codex read-only 1 本、`d8140a6ed` 対象): NO-GO、must-fix 2 = (1) 概要・3.3 節が certified を YCSB に限って定義するのに 7 節 (a) が TPC-C の trace を certified と呼んだ、
  (2) NeurCC の採録版の頁 (Crossref の 1-28) が無い。どちらも real と裁定し、(1) は定義を広げず 7 節 (a) を「直列化可能と判定され」へ、(2) は pp.1--28 を足した。
  should 1 (スコープの「TPC-C は評価していない」が trace の判定まで否定して読める) は採用し「合成・性能を評価していない」へ。should 2 (「結果は無い」が未投入と読まれうる) は不採用 —
  本文は結果の不在だけを言い両方の読みで真で、投入状況は main 未着地の記録に頼ることになる。nit (出所コメントの旧参照) は「改訂 2 までの状態」と明記した。
  親の (P3)「本稿の評価で」だけでは定義との衝突を解消しなかった (レビューの指摘どおり)。記録 = 原稿 README §11.4。
- 工数: Codex 子 1 本 (review)。Claude 子なし。

## 次の一手差分

### 更新

- [T-2864] **P2・一部裁定済み (D2227 項 3〜6、D2235 項 2・3) → 著者・所属の記入 (ユーザー手番) → 差し込み・再組版 (AI) → 発表申込・原稿送信 (人間手番)**:
  ComSys 原稿 (`output/insights/2026-09-22/comsys2026-manuscript/manuscript.tex`) の残り。頁数 15 頁のまま (D2227 項 4)、ADRS の判定 (D2227 項 5) と 4.7 節ほかの 4 巡目の反映は
  改訂 2 で、参考文献の採録版照合 (README §3.4 の 3 件) と 7 節 (a)(c) の一次資料との照合は改訂 3 で済んだ (同 dir `README.md` §10・§11)。(1) 著者・所属 (`\affiliate` / `\author` の差し込み欄) は
  ユーザーの記入内容を受け取ってから差し込む (AI は推定しない)。差し込みでは `\documentclass` の `noauthor` 指定を外して再組版し、頁数を確かめ直す (16 頁以上になれば D2227 項 4 の
  前提が変わるので再提示)。(2) 7 節 (c) と限界節は「B-5 の本走は認可したが本稿の時点で結果は無い」と書いた。送信前に B-5 本走の結果か規模の見直しが着地していれば、同じ 2 文を一次資料と照合し直す。
  (3) 発表申込 10/16・原稿締切 10/30 の送信は人間手番 (収載は送信の承認ではない)。一次資料 同 dir の `README.md` §3.4・§6・§10・§11。
  base: c59c9c475489f496625d226e412b667026e4afe1a9f6a90675cf5f374399d99d
