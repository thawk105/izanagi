---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-19
wave: dw-a1-sized-attempt2
seq: 1
title: A-1 sized attempt-0002 は既存 submit 経路の gate で qsub 前に拒否され投入されなかった — 記録と裁定パッケージ (docs-only、branch worktree-dw-a1-sized-attempt2)
---

## 本文

- ユーザー裁定 (2026-09-19): 「A-1 sized attempt-0002 を独立再現として 1 attempt 認可する。非認証 lane を維持し、formal 昇格は含めない。
  どこかの層で落ちたら再投入せず報告して止める」。既存 submit 経路・同じ policy/n=30/配置・比較可能条件の投入前照合・results 稿と
  2 attempt の並記 (プールしない) を求め、formal lane・要件充足判定・追加 gate を scope 外とした。記録は {{D:a1-sized-attempt-0002-refused-at-submit}}。
- 段 3 相談 B が「既存 submit は `_assert_no_prior_v3_bench_start` (規律 2 由来、commit abff80d1b) で先行 attempt の bench 到達を検出し
  qsub 前に拒否する」を指摘し、親が現物 (durable base の `attempt-0001.intent.json`、`barrier/bench-go.json`、ready 3 本、bench-start 3 本) で確定した。
  段 1 前の親の実測「attempt root が base 直下の未存在 dir なら成立」は部分抜粋からの一般化 (F29 型) で誤りだった。
- 段 4 裁定: 既存経路を 1 回実走して拒否を実測し止める。gate 緩和・先行証拠の移動/削除・policy/base 変更はしない。射程判定 (c)。
- 投入前照合 21 項目 (submit-tree detached a99425b66・lock・clean 0 行、CCBench 511c9538 tracked-clean、束縛 9 file の sha が attempt-0001 と同一、
  third-party 5 pin 一致、hydrate 2 箇所 rc 0、durable base 書込可、attempt-0002 と intent 不在) はすべて成立。
- **submit 実走 22:05:30→22:05:36 JST: rc 2、stderr `paper-story A-1 refused: prior attempt reached the bench barrier; group rerun is prohibited`。**
  副作用なし (base は attempt-0001 のまま、新 request なし、submit-tree clean)。計測 attempt は開始されず、認可された手続は submit 層で
  停止条件に達した。監視・complete・materialize は起動していない。
- 相談 C (裁定パッケージの点検) が起草を 4 点訂正: 択 2 (別 study) は固定表 1 行でなく identity 分岐・job shell・JSON・test の変更を要し
  D2096 項 5 の裁定変更が要る、「結果を見た再投入」の危険は択 1/2 に同じく残る、新 seed でも物理順が変わる保証は無い、
  「認可未消費」は断定できない。停止判断は妥当。
- 成果物は縮小: 測定値が無いので results 系列稿・2 attempt の並記・図は作らず、`docs/paper-story/README.md` の stale 注記に 1 段落だけ足した。
  attempt-0001 の leaf・稿・図 9・事前登録・policy・source 契約の bytes は不変。
- 相談 3 本 (read-only、`reasoning=medium`、model call 8 / 13 / 7、CLI reported token 76,842 / 78,522 / 55,280、全件 accepted)。author 0 本。
  実装面の差分ゼロ (変異 matrix 免除)。一次資料は `output/insights/2026-09-19/a1-sized-attempt2/README.md` と同 `verbatim/`、`MANIFEST.tsv`。
- 専用 handoff は repo 外 job dir の handoff。段 8: 段 1 前の部分抜粋からの一般化 (near miss、段 3 で検出) を F29 の再発として
  failures fragment に追記。DW-S01 へ「入口から副作用点までの gate 呼び出しを棚卸しする」の 1 文を足す案は L1 予算を 55 byte 超過
  (10680 > 10625) したので戻し、候補として記録に留める。改善実装・次 wave・push は行わない。

## 次の一手差分

### 新規

- {{T:a1-sized-replication-route}} **P1・ユーザー裁定待ち**: 同じ sized study の 2 本目 (認可済み独立再現) をどの経路で投入可能にするか。
  択 1 = 認可記録付きの gate 入力 (同 study の attempt-0002、rear gate と公開先 gate の受理集合を exact な認可対象に限って広げる、
  事前登録 §6.1/§6.4 の将来向け追補)、択 2 = 別 study として登録 (identity 分岐・job shell・JSON・test の変更、D2096 項 5 の改訂)、
  択 3 = 行わない。先に研究目的 (同一配置の反復 / 順序を変えた再現) を確定する。推奨は「同一配置の反復 + 択 1 を 1 attempt 限定」。
  一次資料と返答例は `output/insights/2026-09-19/a1-sized-attempt2/README.md` §7。実装は Codex author + 敵対レビュー + 変異 (負例: 別 attempt 名・
  別 study・別 source sha・record 不在は従来どおり拒否)。
