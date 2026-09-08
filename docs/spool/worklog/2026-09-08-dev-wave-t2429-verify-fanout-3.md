---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-t2429-verify-fanout
seq: 3
title: [T-2429] 認証の正しさ検査を兄弟ノードへ分割できるようにした — 生死確認 4 本がすべて肯定で、遠隔結果の権威は stdin secret の HMAC に置いた (コード + テスト + insight、branch worktree-dev-wave-t2429-verify-fanout、変異 17 KILLED・1 SURVIVED (等価)・MISMATCH 0)
---

## 本文

- **着手前の生死確認 4 本がすべて肯定だった。** 起票文が求めた「1 回建てた実行ファイルが別ノードで
  同一 bytes のまま動くか」は、A-6 が bnode031 で建てた 4 本を bnode012 で照合・実走して確かめた。
  原本・共有 `/work` 複製・ノード内蔵 `/scr` 複製の 3 か所とも sha256 が記録値と一致し、未解決の
  共有ライブラリは 0、trace 版は rc=0 で trace 4 file と commit 行 512,567 を出し、perf 版は rc=0 で
  trace を出さなかった。続けて `-b 2` の要求で `PBS_NODEFILE` に両ノードが並び head から兄弟へ ssh が
  通ること、CLI の `-b` が job script の directive に優先すること、1 ノード要求でも nodefile が
  自ノード 1 行で実在することを実測した。逐語は
  `/work/1/SFC/tanab/izanagi-job-evidence/t2429/attempt-001/` と insight。
- **段 2 のプランは「ssh 未実測」を理由に重い案 (login 側 supervisor が repetition ごとに別 request を
  投げる) を第一候補にした。** probe が先に走っていたのに結果を子へ渡していなかったのが原因で、
  段 3 のレンズ B が独立にこれを指摘した。親は段 4 で単一 multi-node request + ssh へ裁定し直した。
  段 2 の子へ probe 結果の path を渡す作法は段 8 の改善候補にした。
- **段 3 と段 6 の敵対レビューが、遠隔化で新しく開く正しさの穴を 2 段階で暴いた。** 段 3 は
  「verifier の capability が発行 process に束縛されているので遠隔結果をそのまま COMMIT へ渡せない」
  ことと「兄弟ノードには head の一時 worktree にある patched source tree が見えない」ことを出し、
  段 6 は最初の実装の受領証が公開情報の hash の再計算だけで偽造できることを出した。親は
  {{D:verify-fanout-transport-and-authority}} で、head が task ごとに生成し標準入力だけで渡す
  使い捨て secret の HMAC を権威に据える形へ裁定した。
- **段 6 の焦点再レビューが残した最大の所見は不採用にした。** 「worker と contract loader が自分自身で
  自分の checkout を検査するので、dirty な worker は照合を迂回できる」という指摘は real だが、
  head と worker は同じ共有 checkout を使い head 自身が起動時に同じ closure を照合して生きているため、
  破れるのは照合後・import 前の窓に同じ uid の別 process が checkout を書き換えた場合だけである。
  複製済み実行ファイルの hash 後 TOCTOU と同族で、単独テナントの前提の外にある。閉じるには
  head 供給の二段 bootstrap という新機構が要り、依頼の「本題の実装だけ」に反するので限界として
  明記し裁定パッケージへ送った。
- **段 5 の実装子 1 本が model 呼び出し上限で報告を書かずに死んだ** ({{F:codex-child-dies-at-model-call-cap}})。
  worktree の差分は残っていたので、それを監査対象として引き継ぐ継続子を投げ直して回収した。
- **「ノードを跨いで建て直すと bytes が変わる」という既存の言い切りは一次資料より強い** (F1 再発)。
  一次資料の実測は「別 job で建て直すと job 固有の path が混入して bytes が変わる」であり、2 台の
  計算ノードで建て直して突き合わせた記録は無い。本 wave は配る形を採ったのでこの含意に依拠しない。
- 実機の 5 ノード実走はまだ行っていない。73 分から 16 分から 18 分へという見込みは静的な見積りで、
  次の attempt で確かめる。
- 逐語と実測は `output/insights/2026-09-08_t2429-verify-fanout/README.md`。

## 次の一手差分

### 完了

- [T-2429] 認証の正しさ検査を兄弟ノードへ分割する経路を実装し、生死確認 4 本と変異で裏取りした。
  remaining: none
  base: b4ff1c1104a9a213e306a324f47c21fac20e607267f766c14aff0024a4439382

### 新規

- {{T:verify-fanout-live-run}} **P1・新規**: fan-out を有効にした A-6 の新しい attempt を 5 ノードで
  実走し、実機経路 (ssh の到達・`PBS_JOBID` の運搬・`/scr` の単独性・rep 順の WAL) と、73 分から
  16 分から 18 分への短縮の見込みを実測する。現状の見込みは 1 attempt の検査時間からの静的な計算で、
  実走はしていない。
