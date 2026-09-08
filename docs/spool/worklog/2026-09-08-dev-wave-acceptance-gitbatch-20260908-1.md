---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-acceptance-gitbatch-20260908
seq: 1
title: 受入全走の高速化 — contract-loader binding の blob 取得を 62 process から ls-tree + cat-file --batch の 2 process へ (コード + テスト + docs、branch worktree-dev-wave-acceptance-gitbatch-20260908、変異 matrix = baseline PASSED・KILLED 7・SURVIVED 4 (等価、事前登録)・MISMATCH 0・期待 node 完全一致 7/7)
---

## 本文

- 依頼は「受入全走の高速化。テスト所要が伸びている。並列化・賢い手で短縮、過剰実装・過剰ガードレールならオフ・削除も検討」。
  受入走の junit (直近 10 日) で **同じ node 20,873 本の和が 17,091 → 24,247 秒 (+42%)**、新規 node の寄与は 1,093 秒だけと実測し、
  「test が増えた」ではなく「既存 test が重くなった」型と判定した。login profile で 1 test 47.5 秒のうち 36.4 秒が
  `contract_loader_binding._run_git` の git subprocess 704 回 (closure 62 path × capture / verify のたびに 1 path 1 process) だった。
- 一次資料は `output/insights/2026-09-08_acceptance-gitbatch-binding/README.md`。設計判断は {{D:contract-loader-blob-batch}}。
- **land したもの:** blob 取得を `ls-tree -r -z <commit> -- :(literal)<path>...` + OID 指定 `cat-file --batch` の 2 process へ (`6e885df4f`)、
  wiring probe の許可形を production の exact argv に合わせ prelude まで exact 比較 (`c4e7c5f7b`、`66a2ea966`)。受理集合・拒否集合は不変、
  拒否の優先順位だけ契約外へ。login A/B (交互 3 標本): 旧 30.9 / 11.3 / 17.9 秒 → 新 9.6 / 6.4 / 4.6 秒、git 起動 802 → 142 回。
- **計算ノードの実測 (受入形でない全 suite 1 走、1 node × 48 worker):** W 全体 28,734 → 17,236 秒 (0.60)、対象 module は 0.03〜0.40
  (`test_autonomous_trial_completeness` 1,879 → 229、`test_p3_b4_closed_critic` 1,264 → 93、`test_trial_registry` 2,092 → 347)、
  binding を通らない対照 2 module は 0.95〜1.07。profile した node は 56 → 5.7 秒。最遅 shard wall の改善は受入走が取れるまで主張しない
  (insight の `measurements.md`)。改修前の所在: 最遅 shard wall 中央値 286 秒 / p75 350 秒 (09-08 分)。
- **受入が 1 度止まった。** main `c12e25078` ([T-2412]) が `.codex/worktrees/*` 110 本を gitlink として追跡し、
  (a) `git submodule status --recursive` が fatal になり受入の tree 指紋が落ちる、(b) 全史 provenance 監査が `missing-codex-author` (110 path) を
  新規違反として出し land が rc=29 になる、の 2 つで全 wave が止まった。裁定 inbox
  `dev-wave-jobs/rulings-inbox/2026-09-08-main-codex-worktrees-gitlinks-block-acceptance-and-land.md` へ起票してユーザー承認を得たが、
  **起票と並行して別 session が既に `48837186c` で index から除き既知違反へ登録し、`cf837838a` で post-baseline 母集団 pin を 2 → 3 へ
  追従させていた。** 本 wave は自前の是正子を止めて `cf837838a` を取り込むだけにした (重複登録を作らない)。
- **親の起草した `.gitignore` 案は誤りだった。** 「`.codex/worktrees/` を versioned な `.gitignore` へ足して再発を機械的に塞ぐ」を推奨として
  裁定へ載せ承認も得たが、F599 が同型の near miss を既に記録していた — `?? .codex/worktrees/` の 1 行は `tools/mutation_worktree.py` の
  `_observe_shared()` が走行前後で bytes 一致を要求する観測対象そのもので、除外を足すと**並行中の変異走行が `shared_snapshot_matches=false` /
  rc=125 で空振りする**。別 session も `42f2b6d0c` で同じ理由により取り下げていた。**一括承認された推奨でも、AI が起草した機構は
  一次資料 (failures 台帳) で裏を取ってから実装する。**
- gitlink 除去 commit を main へ ff-only しても実体の入れ子 worktree が消えないことは、着手前に使い捨て repo の実験で確かめた
  (`warning: unable to rmdir` が出るだけで残る。他 wave の稼働 worktree 110 本が対象だったため生死実験を先行させた)。
- 段 3 (2 レンズ、blocker 9) の主要 real: `<commit>:<path>` 形の batch は応答が path に束縛されず逆順 + 逆対応 digest で誤受理し得る (→ ls-tree + OID 照合)、
  timeout の per-process → 集約 (→ `GIT_TIMEOUT_SECONDS * n`)、拒否順序と NUL (→ 契約を狭める)、第 2 の `_run_git` fake、所要時間台帳の更新義務。
  段 6 (2 レンズ + 焦点 1、blocker 2 + should-fix 4): wiring probe の許可形 (D-01、親が login で赤を実測)、prelude の非 exact (E-01、旧来の穴)、
  call-site meta-test の第三 caller、ls-tree framing の負例、fake の到達 marker。逐語は insight の `verbatim/`。
- 親の訂正: 親が段 1 で書いた「capture 1 回 = 3 process」は `_validated_root` 固定条件の値で、public capture は 4 process (段 6 D-07)。
  「+42% はこの module に帰属する」とは主張しない (module 最終 commit 09-03、悪化開始 09-05 20:48、caller に変更なし)。
- 変異: 単独証拠 7 件 (OID 照合 / `_blob` 後退 / type 検査 / exact EOF / committed digest / live disk / ls-tree 不在) は期待 node 完全一致で KILLED。
  M9 / M10 / M12 (body EOF・record LF・両層同時) は初回 KILLED 期待 → login probe で 0 赤 → 第 3 層 (exact EOF の `offset = body_end + 1`) が
  末尾 LF 欠落を必ず拒否するため等価と確定し SURVIVED 期待へ改めた (erratum)。M1 (stdin 配線削除) は 263 node を落とすが dispatch 中継の
  末尾 64 KB 上限 (≈ 117 行) を超えるため matrix から外し login probe の junit を補助証拠にした。
- 工数: Codex 子 = plan 1、consult 2、author 1、review 3、fix 2、merge-author 1。親 = Claude 1 context。

## 次の一手差分

### 新規

- {{T:acceptance-gitbatch-compute-effect}} **P1・実測待ち**: 本 wave の受入走 (canonical、K=3) の junit を 09-08 の改修前分布 (最遅 shard wall 中央値 286 秒 /
  p75 350 秒、W 中央値 28,734 秒) と比べ、対象 module (`test_autonomous_trial_completeness` / `test_p3_b4_raw_record_producer` / `test_p3_b4_closed_critic` /
  `test_trial_registry` / `test_layer3_report`) の W と最遅 shard wall を D1714 の読み方で記録する。1 走では wall の改善を主張しない。
- {{T:acceptance-remaining-git-fanout}} **P2・裁定パッケージ候補**: 5 分到達に足りない場合の次の候補。(a) `ident.py` の capture 直後の live verify は
  repository・disk 不変の前提下でだけ冗長 (段 3 A-10、触っていない)、(b) process 内 memo は root identity・object 可用性を束縛しない限り不安全 (A-11)、
  (c) 他 module の path 単位 git 起動 (`trial_registry.py` / `p3_b4_admission_record.py` / `certified_writer_preflight.py` の `cat-file blob`) を同じ形で棚卸しする。
  費用の増加だけでは D1728 (collection 絞り込み) を再訪しない。
