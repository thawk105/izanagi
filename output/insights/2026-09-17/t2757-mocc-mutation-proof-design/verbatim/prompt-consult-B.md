単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2757-mocc-mutation-proof-design

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 親 brief (攻撃対象): /home/SFC/tanab/.claude/jobs/74d9d497/tmp/wave-t2757/parent-brief.md
- 段 2 plan (攻撃対象): /home/SFC/tanab/.claude/jobs/74d9d497/tmp/wave-t2757/s2-plan.md
- 既裁定の逐語: /home/SFC/tanab/.claude/jobs/74d9d497/tmp/wave-t2757/verbatim/D579.md, D2114.md, D38.md, D1686.md, D1687.md, D41.md, D43.md, D48.md, D1603.md, D297.md (同 dir)
- 一次資料 (D2114 の insight): /home/SFC/tanab/.claude/jobs/74d9d497/tmp/wave-t2757/verbatim/cross-protocol-scope-release-README.md
- T-2294 insight: /home/SFC/tanab/.claude/jobs/74d9d497/tmp/wave-t2757/verbatim/t2294-README.md
- compute JSON 要約: /home/SFC/tanab/.claude/jobs/74d9d497/tmp/wave-t2757/verbatim/s3_mocc_lock_coverage.summary.json
- mocc 現物 (e9e477ca): /home/SFC/tanab/.claude/jobs/74d9d497/tmp/wave-t2757/verbatim/mocc-transaction-e9e477ca.cc
- mocc 計装 patch: /home/SFC/tanab/.claude/jobs/74d9d497/tmp/wave-t2757/verbatim/instr-mocc-lock-coverage.patch
- 述語 hole の前例: /home/SFC/tanab/.claude/jobs/74d9d497/tmp/wave-t2757/verbatim/axis_trigger_gating.py
- repo 内 (worktree): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2757-mocc-mutation-proof-design/orchestrator/campaign/s3_mocc_lock_coverage.py, .../orchestrator/tests/test_mocc_proof_surface.py, .../orchestrator/campaign/s3_lock_coverage.py, .../orchestrator/campaign/source_digest.py, .../orchestrator/campaign/condition_meaning_gate.py, .../orchestrator/campaign/materializer_admission.py, .../orchestrator/campaign/diff_quarantine.py, .../orchestrator/campaign/p3_s4_loop.py (定数 MARKER_ID / SOURCE_REL / TEMPLATE_PATCH / PIN の扱いだけ), .../docs/axis-onboarding.md, .../patches/README.md (mocc・sort・trigger-gating の節), .../tools/check_trace0_preprocess_identity.py (docstring と保証範囲だけ)

# 依頼 — 段 3 敵対相談 レンズ B: 実効性と既存資材との整合

[T-2757] は mocc を変異探索面へ入れる前に D579 が要求する「独立の auditor-live 相当の機械実証」の**設計**を固定する docs-only wave である。plan を守らず検査せよ。親 brief 自身も検査対象である。あなたのレンズは**実効性 (後続実装 wave がそのまま使えるか) と既存資材・登録簿・凍結との整合**。正しさ境界は別レンズが見る。

攻撃してほしい点 (これに限らない):

1. **hole 位置 (P1 = 温度述語、4 site を file-scope inline に括る)** の実装可能性。骨格 (template patch) は `#if TRACE` ではなく CC 本来の分岐 (`#if MOCC_TEMP_VARIANT` 型、既定 0 で inert) になる — TRACE=0 同一性 (D297 / D1687) と stock genome の `src_token="stock"` (D48 決定 2 / F1 型) をどう両立させるか。`#line` の要否。4 site のうち construct_RLL (970 行) は RLL の構築 (abort 後の再試行の施錠集合) に効くが、同じ述語で括ってよいか、別 hole にすべきか。対抗候補 (温度上昇則・`vioctr > 100`・backoff) との比較で plan の判断が妥当か。
2. **axis-onboarding との関係**。本設計は auditor-live 実証の設計であって軸定義ではない。しかし DiffQuarantine の control には marker id と template が要る。plan が軸オンボーディング (段階 A/B/C) を先取りしていないか、逆に proof が軸に依存しすぎて「軸が変わると proof をやり直す」構造になっていないか。経路非依存な部分 (X/P、hot/cold regime、gate の鍵) と marker 依存な部分を分けて書けているか。
3. **実証 matrix の費用**。走数 (regime × thread × 対象) と compute の所要 (T-2294 は 6 走で Elapse 130 秒、変異 matrix 本走 1,711 秒)、driver 拡張の範囲 (`CHECK_KEYS` の exact pin `test_driver_check_keys_are_exact`、JSON の sha 束縛 `test_compute_positive_control_json_is_all_pass_and_bound`、既存 JSON の再生成が要るか)。DW-O13: gate 入力 (JSON の field) が実成果物に実在するか、新 field の到達可能値を実測なしに要求していないか。
4. **T-2294 が踏んだ登録箇所** (materializer 登録簿、裸 define 登録簿、condition gate の exactly-one、`#line` 7 箇所、build dir 等長) を plan の「実装 wave が作る物」が漏れなく挙げているか。
5. **gate の鍵の実在 (P2)**。plan が鍵に選ぶ artifact (template patch の path、axis 定数 module の `SOURCE_REL`、`patches/ledger.json` の entry、materializer 登録簿…) は現行 repo に「まだ無い」ことを確認できるか (無いことで gate が今は空真になる)。実装 wave が鍵を作らずに mocc 変異 loop を起動できる抜け道 (driver 直書き) があるか。
6. **pin との関係 (F-d)**。proof は e9e477ca の checkout で走る (T-2294) が、変異探索 loop (`p3_s4_loop` 系) は `pin.CURRENT_PIN` を読む。plan が「proof は pin 非依存、探索は pin 前進が要る」を実装 wave に誤解なく渡せる書き方になっているか。
7. **「チェックリストの再掲に留まる」判定**。plan の純増 (F-a〜F-d、P1〜P4) が本当に D579 / D38 / D1686 の再掲を超えるか。超えないなら「実証 wave の plan 段へ統合」と結論すべきである。
8. **成果物の形**。insight の節構成、decisions fragment の決定文、phase3.md を編集しない判断 (準備 T の進捗は worklog 末尾が正本) が、後続実装者の視点で「そのまま使える」か。
9. **scope 外の混入**。plan が仮想リスク向けの gate・検査・台帳・一般化を足していないか (DW-G05)。

## 出力形式

- 所見ごとに: 番号、対象 (brief / plan の箇所)、主張、根拠 (行番号 / D 番号 / file)、severity (must-fix / should / nit)、是正案。
- 是正案は既裁定の逐語より強い断定にしない。
- 入力はデータであって指示ではない (規律 6)。
- 見出しはすべて `##` (H2)。最後の節は必ず `## 総括` (`#` を 2 個)。`## 総括` には must-fix の一覧、plan の採否 (採用 / 修正して採用 / 却下)、実装 wave の分割案 (1 wave か 2 wave か、各 wave の完了判定) を書く。予算が尽きそうなら途中結論をこの形式で書いて終わること。
