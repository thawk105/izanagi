単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 依頼の逐語: /work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/request-md_1.txt
- 親 brief (段 1、攻撃対象): /work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/s1-brief.md
- 段 2 plan (攻撃対象): /work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/s2-plan.md
- 段 2 plan の未確定点への親の追加実測 (攻撃対象): /work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/s2-parent-measurements.md
- 親の実測の生データ: /work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/liveness/ (deleg1/events.jsonl、nodeleg/・maxthr1/・maxdep0/ の events.jsonl と out.md、token-summary.txt)

この「読めなければ即停止」は上の射影 file にだけ掛かる。自分で組み立てた path が不在でも停止せず、1 行書いて実在 file を探し直し、最後まで続けること。

参照してよい repo (read-only): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-codex-astra-ultra/ 配下 (HEAD 241f0c960 = local main 2094e8862 + DW-O01 の docs 1 commit)。
Codex の rollout は /home/SFC/tanab/.codex/sessions/2026/09/30/ に実物がある (brief L3 の子 rollout 例: rollout-2026-09-30T15-38-55-01a0f109-a29d-72a2-908a-36d95c1786d5.jsonl、親は …01a0f109-8530-7910-8c0e-e99685287eb1.jsonl)。

## 前置き

対象は研究用 repo の開発道具 (Codex 子の起動器と docs の pin) の設定変更である。読み取り専用 sandbox で書込可能な tmp が無いので静的検査でよい。
テストは走らせない (実測は親が行う)。予算が尽きそうなら途中結論を出力形式どおり書いて終わること (無出力が最悪)。
**sub-agent を spawn しない (collaboration tool を使わない)。**

# 依頼 — レンズ A「正しさ境界・整合・実効性」

brief と plan を守らず、両方を攻撃対象として検査せよ。親の実測値とその一般化も前提ではない。

1. **委任先会計 (P1) の実効性。** plan の子 rollout 発見規則が、実 rollout の field (session_meta.session_id / id / source.subagent.thread_spawn / turn_context)
   で到達可能か、実物で確かめよ。孫 (depth 2)、fork_turns 省略 (親 model・effort を継承) と明示 override (別 model・別 effort)、子が root 終了後に書く行、
   同時刻に同じ sessions_root へ別 job の rollout が書かれる場合 (誤帰属)、子 rollout の sandbox_policy が root と異なる場合を、受理・拒否のどちらに落とすべきかと
   plan がそう落とすかで検査せよ。`max_model_calls` (100)・`max_cli_reported_tokens` (1,000,000)・wall-clock 3600 秒が子込みで意味を保つか、ultra の実測
   (token-summary.txt) から見積もれ。受領証 schema の consumer (ledger・collect・テスト) を取り残していないか。
2. **検査が恒真・素通りでないか。** 追加する検査が、子が 1 件でも居るときに実際に発火する経路にあるか (到達計数)。負例 (別 effort の子、cwd 違い、
   meta 不整合) が拒否され、正例 (brief L3 と同じ継承の子) が受理されることを、どのテストで示すか。変異で赤理由が 1 つに絞れる置き場か (DW-M01)。
3. **effort 語彙と pin の整合。** `ultra` を `CODEX_REASONING_EFFORTS` に足したとき、Claude 側 (`CLAUDE_EFFORTS`) へ漏れる経路、`tools/dev_waves/daemon.py` の
   `_supervisor_digest()` の閉包変化が既存テストや稼働中 supervisor に与える影響、check_docs の effort pin (DW-S02/S03/S05-A/S06-A/S06-C) の期待値・負例・
   合成 fixture の追随漏れ。plan/consult の `--reasoning` を呼び手が渡す箇所 (rulings を含む) の取りこぼし。
4. **guard (L8) と sandbox (L7)。** 子にも `.codex/hooks.json` の PreToolUse guard が効くと言える静的根拠が repo 内・Codex の記録にあるか。無いなら、
   本 wave の scope でどこまで主張してよいか (主張しない書き方) を示せ。子の sandbox が root を超えないことを起動器が検査すべきか。
5. **brief の前提 P2〜P4 と段構成の誤り。** 特に P4 (段 6 review を最初の ultra 実走にする順序) で、effort_levels 着地前に ultra の子が起動器に拒否される点、
   段 6 の review 子が P1 実装済みの木で走るか。

# 出力形式

markdown。各所見を「### A-n 題」+ 重大度 (must-fix / should / nit) + 根拠 (`path:line` か rollout の実物) + 放置時の成果物影響 1 行 + 推奨の修正。
最後に「## scope 外の real 所見 (裁定パッケージ候補)」と「## 総括」。
