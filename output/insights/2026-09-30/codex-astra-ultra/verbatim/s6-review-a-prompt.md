単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 依頼の逐語: /work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/request-md_1.txt
- 段 4 裁定 (正本): /work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/s4-ruling.md
- 実装子の報告: /work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/s5-author-a.md、/work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/s5-author-b.md
- 外部 script の原本と改訂版: /work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/next_tasks_consult.sh.orig、/work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/next_tasks_consult.sh.new

この「読めなければ即停止」は上の射影 file にだけ掛かる。

レビュー対象 (read-only): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-codex-astra-ultra の `git diff 2094e8862 cb3d129ae`
(docs 3 commit 241f0c960・3cb51f201・41065d881 と統合 commit cb3d129ae)。実物の委任 rollout 例:
/home/SFC/tanab/.codex/sessions/2026/09/30/rollout-2026-09-30T15-38-48-01a0f109-8530-7910-8c0e-e99685287eb1.jsonl (root)。

## 前置き

読み取り専用 sandbox で書込可能な tmp が無いので静的検査でよい。テストは親が走らせる。予算が尽きそうなら途中結論を出力形式どおり書いて終わること。
**sub-agent を spawn しない (spawn_agent 等の collaboration tool を使わない)。この起動器は委任した attempt を拒否する。**

# 依頼 — レンズ A「正しさ・実効性」: 実装が裁定どおりに効くか、恒真・素通りが無いか

1. `delegation_detected` の検出が、実物の root rollout の spawn_agent 行で実際に発火する経路にあるか (online tail と sealed 再検証の両方の到達)。
   rollout が invalid になった後も token・call の集計や他の検査が壊れないか。`_EVIDENCE_ISSUE_REASONS` への追加が V1〜V5 receipt の検証
   (reason の閉集合、世代別分岐) と ledger・`tools/t1434_t1222_science_slice.py` 等の consumer を壊さないか。過去の accepted receipt を
   再検証すると拒否に変わる件 (author B 報告) が、実在する receipt に及ぶか (sessions の subagent rollout は本日 6 件だけ) と、規律 7 との関係。
2. テストが単一理由で kill できるか (変異 m4〜m6)、fixture が実物の形 (type/name/namespace/arguments/call_id) を写しているか、wait_agent 空振りの正例。
3. check_docs の effort pin と model literal、`DEV_WAVE_L1_5_BYTES_MAX` = 9_788 の追随漏れ (負例の置換元・decoy・fixture・所要台帳)。旧 medium 拒否の負例が
   exact 1 件置換・対象 finding 1 件か。
4. `CODEX_REASONING_EFFORTS` の ultra 追加が Claude 側・role adapter・`tools/dev_waves/daemon.py` の digest 以外へ漏れないか。
5. docs: DW-O01 の追加文 (「ultraの委任(spawn_agent)はpromptで禁じ、委任したattemptは起動器が拒否する。」) が実装と一致するか。rulings.md の
   起動例が `tools/dev_wave_codex.py` の必須引数と一致するか。外部 script の改訂 3 行が依頼どおりか。

# 出力形式

markdown。各所見を「### RA-n 題」+ 重大度 (must-fix / should / nit) + 根拠 (`path:line` か実物) + 放置時の成果物影響 1 行 + 推奨。
最後に「## scope 外の real 所見」と「## 総括」。
