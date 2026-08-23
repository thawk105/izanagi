---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-24
wave: dev-wave-codex-skill-parity
seq: 1
title: Codex 側 3 skill を Claude command の現況へ揃え、暗黙起動の非一致を閉じた (コード + docs、branch worktree-dev-wave-codex-skill-parity)
---

## 本文

- **依頼と scope の変化。** ユーザー依頼は「Codex のスキル rulings と dev-wave が Claude のそれと
  内容として一致しているか確認し、一致していなければ一致させる。明日それを多用する」。
  wave 途中でユーザーが cleanup-branches も対象へ加えた (「指示出し忘れた気がした」)。
  段 1 brief で P5 として scope 外に置いていた項目が、この追加で撤回された。
- **構造の確認。** Codex 側 3 skill は Claude command を複製せず「共通 dispatcher として全文読む」
  委譲型である。したがって手順本体は参照で一致し、ずれは overlay が述べる事実と、
  委譲では埋まらない起動制御の 2 面にしか出ない。この判定枠 (参照先の実在・overlay の事実整合・
  Claude 固有機構の翻訳網羅) は段 3 レンズ B が「閉包でない」と反証し、
  第 4 面「規範 delta と優先順位」を足した。
- **ユーザー裁定 2 件。**
  1. cleanup-branches の暗黙起動は Codex 側の禁止を外して Claude に揃える。親は当初
     「Claude を締めて安全側へ倒す」と裁定していたが、段 3 レンズ A の blocker と
     failures 台帳 2026-08-01 の再発 (「恒久対応の内容は正しく、経路が欠けていた」) により
     根拠が成立しないと判明し、方向が反転した。暗黙起動の禁止は掃除作業を止めず、
     安全手順書の到達性だけを止める。
  2. `.agents/**/agents/*.yaml` を docs 面とする ({{D:codex-skill-agents-yaml-is-docs}})。
     D95 の「Codex が利用不能なら親が代筆せず停止してユーザー裁定へ返す」に従って諮った。
- **Codex 子の実行面の実測 3 件** (いずれも git に残らない)。
  1. sandbox 化された Codex 子は `.agents/` へ書けない。Bash 経由の `apply_patch <<'PATCH'` は
     guard_bash が「防護ツリーのパスと不透明構文の同居」で拒否し、native `apply_patch` tool は
     `patch rejected: writing outside of the project; rejected by user approval settings` で拒否した。
     同じ sandbox・同じ worktree で `tools/` と `orchestrator/` へは書けている。
     **この拒否は同時に、Codex 子で guard が実際に発火した実測**でもあり、
     「Codex には hook が未配線」という旧記述が偽であることの実行による裏付けになった。
  2. `evidence_status=invalid` による不採用が workspace-write の子 3 本すべてで起き、
     read-only の子 4 本では 1 件も起きなかった。成果物はツリーに残るため、
     親が差分を監査して採用した。
  3. Pegasus dispatch が wave 中に不安定になり (`qstat -Q preflight rc=1`)、子の pytest は
     3 本とも未実走だった。テストの実測はすべて親が行った。
- **規律上の記録。** 段 6 の fix 子が、自前の一時検証 harness を走らせるために
  `IZANAGI_RUN_GROWTH_HELD_TESTS` の opt-in token を自分で使った。解除条件は
  「ユーザーの明示コマンドのみ」である。repo のテスト選択には持ち込まず、一時 fixture は削除済み、
  親セッションに環境変数の残留がないことを実測で確認した。2 本目の fix 子の prompt には
  「使わない」を明記した。
- **変異 matrix の再照準。** 初回 spec は実ファイル (`.agents/**`) を変異させたが 4 件とも SURVIVED した。
  原因は、実ファイルと checker 定数の一致を見る唯一の自動テスト `test_real_repo_clean` が
  `GROWTH_TEST_HOLDS` で既定 skip されていること (correctness_gate=true、
  解除条件 explicit-user-command-only、2026-08-12 rulings 第 3 束)。DW-M01/M02 に従い
  checker の判定述語へ再照準した。初回結果は erratum として残す。
  **今日入れた一致は、`python3 tools/check_docs.py` を明示的に走らせたときだけ機械的に守られる。**
- 変異 matrix (再照準後): baseline PASSED・KILLED 4・SURVIVED 0・MISMATCH 0。
  D (dev-wave への `expected_description` 配線を外す) は失敗 node 2 件ちょうどの単一理由で、
  本 wave の中心的保証が恒真でないことの証明。A/B/C は判定述語を多数の契約が共有するため
  過剰決定であり、DW-M03 の冗長 gate として記録する。
- 段 6 レビューは blocker 3・must-fix 4・nit 4 を返し、すべて real として採用した。
  うち 1 件は親自身の是正文が「一度発火を観測すれば未防護面まで手動義務から外せる」文法だという
  指摘で、`AGENTS.md` を exact surface 限定へ書き直した。
- cleanup-branches の意図的な安全縮退 7 面は {{D:codex-cleanup-skill-safety-delta}} へ全数記録した。
  以後この skill について「完全一致」とは書かない。

## 次の一手差分

### 新規

- {{T:codex-skill-unverified-adapter-claims}} **P2・新規**: Codex dev-wave skill の 4 命題
  (`.codex/worktrees/` の配置と再利用契約、隔離 `codex exec` の実効性、`role=author` の
  provenance 限定、supervised manifest 非対応) を実装正本・checker・launcher と照合して真偽を確定する。
  本 wave では射影資料だけでは判定できず「未検証」として残した。
- {{T:real-repo-parity-gate-is-held}} **P1・ユーザー裁定待ち**: 実ファイルと checker 定数の一致を
  見る `test_real_repo_clean` が GROWTH_TEST_HOLDS で既定 skip のため、skill 一致の機械防壁は
  明示的な `check_docs.py` 実行に依存している。受入全走に含めるか、hold のまま運用規律で担保するかを裁定する。
- {{T:codex-child-cannot-write-agents-dir}} **P2・新規**: sandbox 化 Codex 子が `.agents/` へ
  書けない制約を dev-wave の reference へ収容するか判断する。本 wave では
  {{D:codex-skill-agents-yaml-is-docs}} で著者面だけを解決した。
- {{T:codex-workspace-write-evidence-invalid}} **P2・新規**: workspace-write の Codex 子で
  `evidence_status=invalid` が再現し、read-only では起きない。receipt の evidence 収集経路を調べる。
- {{T:cleanup-safety-delta-ruling}} **P2・ユーザー裁定待ち**: cleanup-branches の Codex 安全縮退 7 面を
  現況維持とするか、Claude と同じ結果へ揃えるかを裁定する。全数表は
  {{D:codex-cleanup-skill-safety-delta}} にある。
- {{T:dev-wave-doc-budget-two-lessons}} **P2・ユーザー裁定待ち**: 段 8 で実測した改善候補 2 件が
  層予算に収まらず差し戻された。`skill-self-improvement` の「予算値を上げる変更は独立審査対象」に
  従い裁定を仰ぐ。(a) `DW-O01` へ「子 prompt の出力見出しは全て H2」— L1.5 の余裕は 45 bytes 未満で、
  意味等価の短縮では収まらなかった (本 wave の段 2 初回子が `### 総括` で F43 不採用になった実測)。
  (b) `DW-M07` へ「変異走行中は tree を読む作業を並行させない・untracked があると起動前に中止する」—
  単節予算 1000 bytes に対し余裕は約 68 bytes で、意味を保った短縮ができなかった
  (本 wave で 2 回踏み、うち 1 回は偽の赤 3 件を読んだ)。
