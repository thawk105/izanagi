---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2710-t080-series-inquiry
seq: 1
title: [T-2710] t080 e2e 群の別系列化を諮り直す 3 材料を取り、本 wave では採らず裁定パッケージをユーザーへ返した — 被覆対応表 (述語単位の重複はあるが stub-free の結合は M 固有)、利用時拒否は判定器単体で負例 11/11 だが production 配線前で部分的、移動後の最遅 shard wall は 1 session のモデル値で 228〜265 秒 (docs + 計測成果物、branch worktree-dev-wave-t2710-t080-series-inquiry、実装差分ゼロのため変異 matrix 免除)
---

## 本文

- ユーザー依頼は「[T-2710] (D2104 項 28 → 調査手番) t080 e2e 群の別系列化の採否を諮り直すための調査。受理集合は変えない
  (D2068 維持)、`growth_test_holds.py` 保留の実 repo 直接検査は復帰させない。出すもの = (1) fixture 検査と実 repo 直接検査の
  被覆対応表、(2) 別系列へ移した場合の利用時拒否の実効性 (負例で実測)、(3) 移動後の最遅 shard wall の見積もり (台帳と 2026-09-17 の
  T-2236 実測を使う)。成果物は insight + 裁定パッケージ。実装差分は原則ゼロ (probe は repo へ入れない)。規律 2 を緩めない」。
- **実装しないと裁定した (段 4 → 7 → 8 → 9)。** 一次資料は `output/insights/2026-09-17/t2710-t080-series-inquiry/README.md`
  (段 1 brief・段 2 plan・段 3 の 2 レンズ・段 4 裁定の逐語と probe 出力を同 dir に凍結)。設計判断は {{D:t080-series-deferral}}。
  T-2708 は稼働しておらず編集面重複は無し。peer [T-2750] (shard-0 成分診断) とは解析対象が重なるが code は触っていない。
- **M (t080 e2e 群) = D700 / D701 の 6 function / 11 node** (台帳 2,302 秒、JUnit 2,539.2 秒、最長 252.5 秒)。M は timed real-repo lock を
  持たないが実 repo に依存する (base 構築が git 可視 `output/` を複製、M11 が実 `ROOT` の履歴と `external/ccbench` HEAD を読む)。
  brief の誤り 4 点 (shared-base 群 13 node、`acceptance --check-only` 不在、次点 node 台帳 170 秒、lock union 231.9 秒) を plan が訂正。
- **材料 1 (被覆対応表):** 保留中の実 repo 直接検査は collection に残るが受入では skipped で検出力ゼロ。毎走に残る単体検査との重複は
  述語 (bytes / pin / 履歴 / hash) 単位に限り、「production が正規発行した receipt を持つ忠実な複製上で stub なしに verifier 全体と
  public gate を通し単一原因の拒否が出る」こと、特に M5 の実列挙経路 (git 可視 output の複製 → production scanner) と M11 の実 ccbench
  比較は M 固有 (レンズ A が plan の表を 1 行ずつ検算、D700 の「受理集合が異なる」を具体化)。
- **材料 2 (利用時拒否):** 現行 repo に判定器は無い (CI/cron/timer 不在、production verify CLI は系列記録なしで active-valid、135.5 秒)。
  D2002 条件 1〜3 の最小判定器を repo 外 probe に書き負例 11 型 (不在・期限切れ・commit 不一致・node 集合不一致・finished≠selected・
  failed・skipped・系列版不一致・未来時刻・M 定義縮小・key 欠落) を全部拒否、正例 1 型を受理。**ただし実効性は部分的**: 迂回路 6 経路
  (migration CLI 直叩き、driver Python API / `run_block`、adapter への注入、floor の `receipt_verify_fn`、report の
  `inspect_receipt_history`、旧受領証の land 再利用) と診断→検証済み利用の昇格境界が未設計。束縛先の失効は 7 日 126 遷移で
  HEAD 126 / closure A (orchestrator+tools+external) 59 / closure B (A+output) 96 回、closure A は 8.4 走/日 ≈ 35〜44 分/日の計算ノード
  占有 (仮定つき) で、A/B とも完全閉包でない (output・docs 入力・untracked・ccbench checkout・hold 版)。
- **材料 3 (shard wall):** session `895f300a…` で M の重い 10 node は占有上位 10 worker を 1 本ずつ占める (占有 ≥228.5 秒の worker が
  ちょうど 10 本、2 本入ると最大 272.3 秒を超える)。M 除外後の割付は 3 shard とも 5,285.4 秒で均等。wall はモデル値で α 247.2 秒
  (shard-1 が新最遅) / β 251〜254 秒 (span 外 65.5 + 残り最忙 chain 185.8〜188.7)、感度 228〜265 秒。**300 秒を切るとは断定しない**。
  real-repo lock union 231.9 秒は shared read の和集合 (writer 4 node 0.2 秒、同時 22 本) で直列化下限ではなく、plan の β′ (292〜327 秒)
  は棄却。T-2750 の成分粒度変更だけでは 240〜252 秒 node が残り 305〜318 秒級、両方で負荷 5,285×3・最長 150 秒。
- **親の probe の欠陥をレンズ B が検出した。** T-2750 仮想計算で nodeid を書き換えたため台帳 lookup が外れ全 node 1 秒になり、
  5,165×3 という偽の均等化を段 3 prompt に載せていた。修正後 6,052.7×3 (M は 0/6/5)。{{F:probe-identifier-rewrite-breaks-ledger-lookup}}。
- 段 3 の棄却所見: 「実 git 履歴を作ること自体が e2e 専有」(brief の表現、A3)、「plan が M 全体を単体で代替可能と断言」(A4)、
  「plan が実装済みを装う」(D2)、「shard-1 の逆転を plan が無視」(B3-4)。採用した real 所見と裁定は insight `stage4-ruling.md`。
- 実走: production verify CLI 1 回 (login、135.5 秒)、三軸走査 `s8b_holdout_freeze search` (docs commit 前後)、`check_docs.py`、
  `spool_fold.py --dry-run`。受入全走は段 9 の land 前に 1 回 (結果は land の受領証)。
- 工数: codex 子 3 本 (plan 1、consult 2、`gpt-6-astra` / `medium`、rc=0・受理 OK)。親 probe 6 種 (allocate 再計算 v1/v2、worker 占有、
  lock mode、判定器負例、束縛失効回数、production verify)。計算ノードは受入 1 走以外に使っていない。

## 次の一手差分

### 更新

- [T-2710] **P1・裁定パッケージ提示済み → ユーザー裁定待ち**: 3 材料は
  `output/insights/2026-09-17/t2710-t080-series-inquiry/README.md` §1〜§3、選択肢は同 §5 — (a) 毎走維持 (親の推奨)、
  (b) T-2750 の成分粒度変更を先に実測、(c) 条件付き別系列化 (完走記録の真正発行・独立期限検知・全境界の利用時拒否と昇格境界・
  関連入力の閉包定義・gate 4 の `U = C − M`・D701 維持 + terminal 証跡・hold 解除前の M 完走・起動契約の 8 条件)、(d) (b)+(c)。
  受理集合は変えず ({{D:t080-series-deferral}})、保留検査は復帰させない。
  base: b381d539e54a07555328bdfc96a1f028e6d741b8fbf2c2f24490c55b9bc42209
