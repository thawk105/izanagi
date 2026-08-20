---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t1337-launcher-timing-proof
seq: 1
title: '[T-1337] attempt 分類の時点証明を registry 内で機構化した (コード+テスト+記録、branch worktree-dev-wave-t1337-launcher-timing-proof、変異matrix = baseline PASSED・9/9 KILLED・SURVIVED 0・MISMATCH 0、受入 verdict=non-attributable-only)'
---

## 本文

- command 引数が指した `tools/worklog_carry_resolve.py` は repo に実在しなかった
  (`git log --all` でも履歴に一度も存在せず)。おそらく `tools/spool_fold.py --base-digest`
  ([T-1303]) との混同。carry chain は worklog.md + `docs/archive/` を手動で遡って解決した
  (685→686→…→711、断絶・分岐なし)。
- 段4 親裁定の中心的 scope 決定は {{D:attempt-timing-registry-proof}} のとおり。段6 敵対レビュー
  2レンズが新たに7件の real 所見 (v2 genesis への v1 行混入・report 付き terminal-failure の
  observation-start 迂回等、A5 の retry admission 拒否を実質無効化しうる核心的抜け穴を含む) を
  発見し、2 fix サイクルで全て解消した。段6 焦点再レビューで全所見 closed/partial (partial は
  {{D:attempt-timing-registry-proof}} が明示した scope 外項目のみ)、regressed 0件を確認した。
  一部所見 (レビューB所見2=OS レベル read-first 証明の欠如) は最初から想定内の scope 外だった
  ({{D:attempt-timing-registry-proof}} 決定2/3 参照)。
- worktree の Bash が全滅する既知の不安定挙動を実際に踏んだ (パス非依存の最小コマンドも含め
  全コマンドが同一エラーで拒否、~30分継続)。`ExitWorktree(keep)` → `EnterWorktree(path=同worktree)`
  での能動的復旧をユーザーへ確認し承認を得て実行、即座に復旧した。
- 受入前 local main 取り込み merge (main が87 commit進行) で、`test_trial_registry.py` /
  `test_s8c_preregistration_predicates.py` の2ファイルが両側で独立編集されており、3-way merge の
  結果が両親と異なるため `check_ai_provenance.py` が新規違反と誤検出した。`git diff-tree --cc` が
  実質空 (競合なしの単純結合) であることを確認し、同型の既存 known-violation エントリ7件以上と
  同じパターンとして registry へ追加してよいかユーザーへ確認し、「既存パターンどおり登録する」と
  承認を得た。
- 上記 registry 追加の fix 指示は F290 の再発パターンを踏んだ (対になる meta-test file を
  名指しし忘れ、受入 attempt 1 を1回消費、attempt 2 で解消)。failures fragment 側に
  F290/F357 への「再発」を記録した。

## 次の一手差分

### 完了

- [T-1337] 事前割当 attempt registry の実装・8c 起動受入結線 ([T-1353]) に続く残件「分類の
  時点証明を trusted launcher 層でどう機構化するか」を、registry 内の論理順序偽装不能性
  ({{D:attempt-timing-registry-proof}}) として実装・レビュー・変異matrix・受入まで完了した。
  「OS レベルで launcher 自体が信頼できるかの独立検証」は明示的に scope 外とし、下記の新規
  task 候補として起票した。
  remaining: none
  base: b2d72fe57d713c65dacea972591dfa778aba80e066775e2ad29c8c4be6c8a770

### 新規

- {{T:launcher-read-api-capability-wrap}} **P2・新規 ({{D:attempt-timing-registry-proof}} が
  scope 外とした残件)**: attempt registry の時点証明機構は「trusted launcher は誠実である」を
  前提とする。この前提自体を機構的に検証する (性能 read API 自体を registry capability で包み、
  read 前に分類が完了していないと物理的に read できないようにする) 拡張は、呼び出し側の広範な
  再設計を要するため見送った。再訪条件 = 完全に敵対的な launcher (プロンプトインジェクション等で
  乗っ取られた variant 生成コード等) からの防御が実際に必要になったとき。
