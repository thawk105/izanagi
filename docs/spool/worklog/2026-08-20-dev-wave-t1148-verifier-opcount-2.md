---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t1148-verifier-opcount
seq: 2
title: [T-1148] verifier の予定操作数不一致 (framing violation) を構造化データとして保持しJSONへ返した (コード+テスト+記録、branch worktree-dev-wave-t1148-verifier-opcount、変異matrix = baseline PASSED・5/5 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- [T-396] 裁定C (verifier の予定操作数検査は起票する) の分離先として entry 568 で起票済みの
  [T-1148] を実装した。段3レンズB (T-396 wave) が「closed-region契約の未実装項目より本丸」と
  指摘した項目であり、規律3 (正しさシグナルを次の一手の入力にする) に直結する。
- **設計判断は {{D:verifier-framing-violation-structured-return}}、
  {{D:verifier-framing-violation-digest-classification-deferred}} を参照。**
- 段2 codex plan・段3敵対相談2レンズ・段4補足調査 (計4本のcodex読取専用子) は real な設計欠陥を
  見つけなかったが、段2 plan が brief 未発見の consumer (silo_ladder_rung1.py の strict
  allowlist・再計算比較、t152_write_intent_coverage.py の counter helper) を発見し、段3レンズAが
  更に tracked ladder artifact の旧schema問題と規律5の観点でのscope絞り込み推奨を発見した。
  段4補足調査でこれらの実害範囲 (現行緑テストが経由するか否か) を確定してから裁定した。
- 段6敵対レビュー2本は real 0件だったが、レビューが拾わない実測依存の凡ミス
  (新設テストの1assertが fixture 値と不整合、`expected_reads: 1` を書くべきところ `0`)
  を焦点走の実測で検出し fix した——静的レビューでは拾いきれない pytest 実走の価値の実例。
- **セッション異常: 段6焦点走 (commit前) で 57件 (10 failed + 47 errors) が赤化し一時的に
  混乱した。** 原因は `orchestrator/verifier/{core,model,report}.py` が
  `campaign_lock.py:CONTRACT_LOADER_RELATIVE_PATHS` (T-1286/T-1287、entry 660 が導入した
  exact 25 path の enforcement source closure) のメンバーであることを段1で見落としており、
  未commitな closure member 差分による `contract-loader-drift` (entry 660 が同型を実測済みの
  既知パターン) だった。統合commit後の再走で解消 (57→0)。詳細は insight
  `output/insights/2026-08-20_t1148-verifier-framing-details/README.md` §3。
- **セッション異常: 変異matrix本走の1回目が `output/pegasus-dispatch` 側の orphan-hold
  (rc=2) で中断し、`orchestrator/campaign/silo_ladder_rung1.py` に変異が残存した。**
  `mutation-harness-orphan-hold-recovery` の既知手順 (qstat内容で対象不在を確認 →
  `git checkout --` で復元 → hold json・sidecar・該当 submission_dir のみを狙い撃ちで削除)
  で復旧し、`--resume` で完了した (baseline=PASSED, 5/5 KILLED)。
- **セッション異常: 段6 fix1 の初回投入が、自分のpromptに書いた「3行以内で要約せよ」という
  指示のせいで出力166 bytesとなり `validator_rc=1` (500 bytes下限、既知memory
  `codex-output-min-500-bytes` と同型) で not_accepted になった。** 木への編集自体は
  正しく適用済みだった。prompt から長さ制約を外して再投入し (新job-id) 解消した。
- **agent 工数:** codex 子 9本 (plan 1・consult 3 (段3レンズ2 + 段4補足調査1)・author 1・
  review 2・fix 2 (1件not_accepted後に再投入))。全て `gpt-5.6-luna`、`reasoning=max`。
  変異matrix probe (親が一時変異→対象testのみ実行→復元、計2回) と本走 (2回、1回目
  orphan-hold・2回目resume) は codex を介さず親が直接実行した (codex子はsandboxがsocket拒否
  のためpytestを実走できない構造的制約)。

## 次の一手差分

### 完了

- [T-1148] verifier の予定操作数不一致 (framing violation) を `Integrity.framing_violation_details`
  として構造化保持し、`result_to_dict()`/`render_text()` から返すようにした。consumer 修正
  (t152_write_intent_coverage.py の counter helper・silo_ladder_rung1.py の schema allowlist)
  と回帰テストを含む。`orchestrator/critic/digest.py` への専用分類行追加 (P2) は
  {{D:verifier-framing-violation-digest-classification-deferred}} により延期。
  remaining: none
  base: bdf479e213e00a34ec4b40b29fffec87a3a79670bdf907bc6931b57635b79349
