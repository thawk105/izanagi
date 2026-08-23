---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-24
wave: dev-wave-t1484-floor-restart-registry
seq: 3
title: [T-1505] attempt 状態機械のドメイン非依存 core を抽出して 8c を互換 facade にし、救出経路の残り 5 点をユーザー裁定へ返した (コード + docs、branch worktree-dev-wave-t1484-floor-restart-registry)
---

## 本文

- D672 (共通 core を抽出し 8c は互換 facade、8b は adapter) に従って実装した。
  実装できたのは **core の抽出・8c の facade 化・8b domain profile の生死確認まで**で、
  **8b の production 配線・trusted launcher・再抽選規則は実装せず裁定へ返した**
  ({{D:attempt-registry-core-profile-policy}} と本エントリ「裁定へ返した 5 点」)。
  command が「ユーザー裁定が要ると判明したらそこで返す」と指示していたことに従う。
- **段 3 敵対 2 レンズの所見 16 件はすべて real、refuted ゼロだった。** うち 2 件が
  wave の前提を変えた。(1) terminal を書けるのは分類を実行した pid/tid だけであり
  (`trial_registry.py` 抽出前 `:3366-3370`)、crash で process ごと死んだ attempt を
  別 process が閉じる経路が原理的に無い。(2) 欠測反復は cell を丸ごと失格にするため
  (`s8b_floor_stats.py:288`)、段 2 が安全策とした「観測後 crash を判定不能にする」は
  D496 決定 3 の行き止まり禁止に正面から抵触する。
- **親の provisional 裁定 5 件のうち 4 件が子に反証された。** 親の実測誤りも 4 件あった
  (attempt registry の既定 path、C03 の範囲、「床値が楽観側へ偏る」という不当な一般化、
  grep hit 数を見積り根拠にしていたこと)。段 4 で brief を訂正した。
- **段 4 で親が立てた論証 A18 は段 6 のレビューに反証された。** 親は「未知 event は拒否
  されるので profile の event 表へ足すだけで 8c の受理集合を変えずに拡張できる」と論じたが、
  core の replay が「start / seal / classification / observation-start 以外はすべて terminal」
  という `else` 分岐だったため、**表に名前を足した瞬間に terminal の semantic が付いた**。
  fix で fail-closed へ直し、裁定パッケージの R-a に「recovery は profile だけでは足りず
  core 改修が要る」と訂正を明記した。
- **抽出で 8c の受理集合が広がっていた箇所を 2 件見つけて戻した。** (1) 不正な genesis 入力の
  検査順序が変わり拒否理由が `[json]` から `[attempt-registry-schema]` へ動いていた。
  (2) `retryable_failure_reasons=None` が抽出前は `list(None)` で TypeError だったのに
  受理されるようになっていた。どちらも段 6 のレビューが見つけ、親がコードで検算した。
- **既存 8c の穴を 1 件見つけたが本 wave では直していない** ({{F:terminal-reason-override-after-value}})。
  D672 が「8c の受理集合を変えるな」と定めており、締めると受理集合が狭まるためである。
  代わりに profile の設定項目とし、8b だけ厳格にした。
- **段 8 の自己改善候補は 1 件あったが実装しなかった (予算不足)。** `DW-O09` の pin 閉包検索は
  `grep -rn "<成果物パス>" --include=*.py` を規定するが、本 wave で 8c の受理集合を決めていた
  のは path pin ではなく `s8c_preregistration_evidence.py` の **AST 述語 probe** (関数の実在・
  呼出し関係・到達性を key にする) だった。path grep では見つからない型である。
  `DW-O09` は現に 996 bytes で L2 単節予算 1,000 bytes に対し余裕が 4 bytes しかなく、
  意味等価な最小の縮約でも +34 bytes を要したため収まらなかった。
  `docs/skill-self-improvement.md`「command 入口の編集条件」に従い、
  予算のために安全義務を弱めず、予算値の引き上げは独立審査対象として裁定へ返す。
- 工数: codex 子 9 本 (plan 1、consult 2、author 3、review 2、fix 2)。すべて rc=0。
  子は環境の都合で pytest を実走できず (runner が計算ノードを要求し preflight rc=16)、
  **テストの実走はすべて親が行った**。

## 次の一手差分

### 更新

- [T-1505] **P1**: 共通 core の抽出・8c facade 化・8b profile の生死確認まで実装した。
  8b の production 配線は、下記 5 点のユーザー裁定が出るまで着手しない。
  base: b0f17ec90b3b89820a6cf82f37574ac3eeab209d813f2bf210f1de6b480f1eb8

### 新規

- {{T:floor-rescue-recovery-event}} **P1・ユーザー裁定待ち**: 死んだ process の attempt を
  別 process が外部証拠で引き取る経路を設計する。core の semantic handler 追加を伴う。
- {{T:floor-rescue-estimand-ruling}} **P1・ユーザー裁定待ち**: 観測開始後に落ちた反復を
  永久欠測とするか、次 attempt を主値へ昇格して estimand を変えるか、失敗理由で分けるかを決める。
- {{T:floor-rescue-ledger-authority}} **P2**: claim / journal / consumed marker /
  attempt-ledger / 新 registry の権威分担と crash cut の truth table を起こす。
- {{T:attempt-core-genesis-generalize}} **P2**: core の genesis API に残る 8c 固有の
  manifest 契約 (`manifest_path` / `manifest_sha256` 必須) を外し、8b が使える形へ一般化する。
