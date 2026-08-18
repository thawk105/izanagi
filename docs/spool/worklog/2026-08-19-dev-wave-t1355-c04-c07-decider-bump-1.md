---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-19
wave: dev-wave-t1355-c04-c07-decider-bump
seq: 1
title: 8c 条件7の証拠契約・評価器を machine_checkable へ昇格し DECIDER_VERSION を v4 へ bump した (コード + テスト + docs + 記録、branch worktree-dev-wave-t1355-c04-c07-decider-bump、変異 matrix = baseline PASSED・5/5 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- **段2 codex plan が親 brief の設計を訂正した。** 「契約 JSON の `accept_trial` を
  `assert_trial_registry_acceptance` へ改名する」という親の初期仮説は誤りで、それは C09
  (`trial_registry.py`) 専用の是正だった。C07 の consumer (`s8c_result_judge.py`) には無関係。
  正しい対処は {{D:c07-accept-trial-removal}} のとおり `accept_trial` prefix の完全削除。
- **段3 敵対レンズ2本 (lensA/lensB) が real 所見8件を出した。** 主なもの: (1) DECIDER_VERSION
  bump で壊れる既存テスト3件+doc1箇所の見落とし、(2) phase doc の生きた記述矛盾、(3) 「certified
  selection は変わらない」と「reason_code/digest は変わる」の混同、(4) DECIDER_VERSION/generation
  再確認の TOCTOU、(5) P2 (裁定 digest・8b bytes 束縛) 是正推奨が D458 既存方針と衝突。
  段4裁定は {{D:s8c-p2-current-maintain}} を参照。
- **裁定inbox (`rulings-inbox/2026-08-17-t1202-t1197-decider-version-generation-collision.md`) に
  同型のDECIDER_VERSION世代衝突の先行事例を発見し、解決パターン (次世代番号へ再生成) を確認・採用した。**
- **並行 wave `dev-wave-t1379-c05-activation` (T-1379, C05 activation) と SendMessage で資源調整。**
  DECIDER_VERSION/次世代 record 発行が直接重なると判明し、先方が v4 で先に着地する前提に合意した
  (実際には本 wave が先に v4/g8 を着地させた — 先方は事前調整どおり次の未使用版を使う想定)。
  調整の過程で先方の事実誤認 (「main 上で `_evaluate_c07` 本体が削除済み」) を実測で訂正した
  (実際は staleness — 別 2 branch が C07 追加前の古い main snapshot を最後に取り込んだまま
  止まっていただけ)。
- **変異 harness の node ID 表現に既知の限界を発見した。** `@CANDIDATE_XDIST_GROUP` decorator 付き
  テスト2件は、pytest-xdist の `loadgroup` scheduler が実行時の "FAILED " 行にのみ group suffix
  (`@s8c-preregistration-candidate`) を付け、`--collect-only` には現れない。`_normalize_node`
  はこの suffix を扱わないため、collection 側と outcome 側の両方を満たす単一文字列が存在しない。
  詳細は {{F:mutation-xdist-group-node-id}}。対処は `--deselect` でこの2 test を mutation harness
  の実行対象から除外 (統合 commit 後の焦点走 573 passed で別途緑を確認済み、wave 全体の
  カバレッジからは除外していない)。
- **セッション異常:** wave 開始直後、`EnterWorktree` (fresh 既定) が main でなく別の稼働中 wave の
  branch tip を誤って基点にした (memory `enter-worktree-fresh-base-can-be-contaminated` に記録)。
  技術調査を委任した fork 1本が本来の read-only 調査任務を逸脱し、大量の tool 呼び出しの末に
  無関係な内容 (別セッションの Bash 不調に関する話) しか返さなかったため、その fork の主張は
  信頼せず親が直接 Read/Grep で再検証した。統合 commit の AI-Agent trailer に不備
  (`role=author` が2製品にまたがるのに一方に `scope` が無い) があったが、`check_ai_provenance.py`
  の rc をパイプ越しに確認する誤り (memory `check-rc-not-through-pipe` と同型) で一度見逃し、
  直接確認で気づいて `git reset --hard` → amend → merge 再実行で是正した (wave-local・未 land の
  直近自作 commit のみ、shared history は一切書き換えていない)。

## 次の一手差分

### 完了

- [T-1355] 8c 条件7の証拠契約・評価器を machine_checkable へ昇格し、DECIDER_VERSION を v4 へ
  bump、第8世代 condition-freeze record を発行した。P2 (裁定本文 digest・8b bytes 束縛) は
  {{D:s8c-p2-current-maintain}} により現状維持と裁定し確定した。
  remaining: none
  base: 83b63f465b8667f47950911f3e0a108320dc75f3d569a8782b4643ab5a686e54

### 更新

- [T-1352] **P1・残件 (b) のみ**: (a) 契約 C07 の入口名是正・`_MACHINE_EVALUATORS` 登録・
  新世代発行を束ねる作業は [T-1355] で完了した。残るのは (b) 最終判定層の現用実装から
  旧条件3とscale gateを撤去することだけである。
  base: d3554b5e3748e46b1e7b06febdb1275523fc65f8e710357e4979bfec37048221
