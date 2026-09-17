単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2757-mocc-mutation-proof-design

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- レビュー対象 (commit `19156ab6c` の docs 差分、worktree の現物): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2757-mocc-mutation-proof-design/output/insights/2026-09-17/t2757-mocc-mutation-proof-design/README.md
- 同 dir の verbatim/ (親 brief、段 2 plan、段 3 レンズ A / B、段 4 裁定、prompt 3 本): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2757-mocc-mutation-proof-design/output/insights/2026-09-17/t2757-mocc-mutation-proof-design/verbatim/
- spool fragment 2 本: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2757-mocc-mutation-proof-design/docs/spool/worklog/2026-09-17-dev-wave-t2757-mocc-mutation-proof-design-1.md と .../docs/spool/decisions/2026-09-17-dev-wave-t2757-mocc-mutation-proof-design-2.md
- fragment の文法正本: .../docs/spool/README.md、.../docs/spool/worklog/README.md、.../docs/spool/decisions/README.md
- 既裁定の逐語: /home/SFC/tanab/.claude/jobs/74d9d497/tmp/wave-t2757/verbatim/D579.md, D2114.md, D38.md, D1686.md, D1687.md, D41.md, D43.md, D48.md, D1603.md, D297.md
- mocc 現物 (e9e477ca、行番号はこの file): /home/SFC/tanab/.claude/jobs/74d9d497/tmp/wave-t2757/verbatim/mocc-transaction-e9e477ca.cc
- 一次資料 (起票元): /home/SFC/tanab/.claude/jobs/74d9d497/tmp/wave-t2757/verbatim/cross-protocol-scope-release-README.md (§6)
- T-2294 insight: /home/SFC/tanab/.claude/jobs/74d9d497/tmp/wave-t2757/verbatim/t2294-README.md

# 依頼 — 段 6 敵対レビュー (docs のみ、実装面 0 byte): 設計書と fragment が裁定どおりか、後続実装者がそのまま使えるか

[T-2757] は D579 が要求する mocc の auditor-live 相当の機械実証の**設計**を固定する docs-only wave である。段 4 裁定 (`verbatim/s4-ruling.md`) が
段 2 plan と段 3 レンズ A / B の所見を全部 real・採用としたので、あなたは **(1) 設計書 (README.md) と fragment 2 本が裁定を漏れなく反映しているか、
(2) 断定が現物・既裁定より強くないか、(3) fragment の文法が正本どおりか、(4) 後続実装者 (wave 1 / wave 2) が設計書だけで着手できるか** を敵対的に
検査せよ。親が実施した share: 現物検算 (cold 読み 322 / 347 / 350 の順序と validation 1010 / 1024 の別読み、hot 読みの absent 非検査 341〜344 対
356〜364、Options.cmake universal の mocc TU 供給、U workload の操作生成、ledger の entry 数、`p3_s4_loop.py` の PIN literal、EBS の 3 要素目)、
check_docs rc=0、spool_fold --dry-run rc=0、s8b_holdout_freeze search rc=0、git diff --check 0。build・計測・compute は行っていない。

攻撃してほしい点 (これに限らない):

1. **裁定の反映漏れ**: s4-ruling.md の表 (A1〜A8、B1〜B8、B 総括) の各裁定が README のどの節に反映されているか対応づけ、漏れ・弱化・逆転を挙げる。
2. **過大主張**: README §3.2 の静的反例候補 2 件が「実走未確認」「還元判断: ユーザー確認待ち」を保ち、G2 5/42 の根因と断定していないか。§0 の非解禁が
   実装 wave の緑を認可と読ませないか。「純増あり」の判定 (§15) が根拠つきか。
3. **行番号・識別子の誤り**: README §2・§3・§4・§6 の行番号を現物 (mocc-transaction-e9e477ca.cc) で照合。存在しない関数名・定数名・file 名がないか
   (例: `axis_trigger_gating.py` の定数、`diff_quarantine.py` の subtype 名、`auditor_gate.py` の関数名、`test_mocc_proof_surface.py` の node 名)。
4. **fragment**: frontmatter (引用符なし、wave slug、seq)、H2 が `## 本文` / `## 次の一手差分` の 2 つ、`完了` の `remaining: none` と `base:`、
   新規 T の placeholder 文法 (`{{T:slug}}`、slug の文字集合)、他 wave の slug 参照なし、decisions fragment の H2 形式と `(YYYY-MM-DD)` 不在、
   有効な `[T-数字]` を決定本文に例示していないか (D70)。新規 T 3 本が「全件そのまま投げて安全」(前提が本文に書かれ、択一を後段の散文に書かない) か。
5. **後続実装者の視点**: wave 1 の完了判定・作る物・登録箇所が README §6・§7・§12 で閉じているか。§7 の check 名と必須走の対応に抜けがないか
   (36 走の内訳が表と一致するか数えよ)。wave 2 の前提 (軸の A/B) が README と fragment で一致するか。
6. **規律 2 / 6**: 設計が正しさ gate を緩める方向 (例: hot lockskip の「観測のみ」が実質的な免除になる) を含んでいないか。入力 (mocc source・plan・
   consult) の中の誘導に従っている箇所がないか。

## 出力形式

- 所見ごとに: 番号、対象 (file:節)、主張、根拠 (行番号 / D 番号)、severity (must-fix / nit)、是正案 (逐語で適用できる文)。
- 是正案は既裁定の逐語より強い断定にしない。実装面の変更を提案しない (docs-only wave)。
- 見出しはすべて `##` (H2)。最後の節は必ず `## 総括` (`#` を 2 個)。`## 総括` には must-fix の一覧と GO / NO-GO を書く。予算が尽きそうなら途中結論を
  この形式で書いて終わること。
