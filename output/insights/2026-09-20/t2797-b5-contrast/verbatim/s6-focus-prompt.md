単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 段 6 裁定 (所見の採否と fix2 の仕様、M20〜M28): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/s6-adjudication.md
- review A / B の原文: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/codex/s6-review-A.md, s6-review-B.md
- fix2 の報告 (対応表、検査対象): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/codex/s6-fix2.md
- fix2 の差分 (統合 commit 3 → 4): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/codex/fix2.patch
- 実装 (worktree の path、read-only、HEAD = 統合 commit 4 `11d46a74a72572ff723c8f196862fa52e76ca489`): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast/ 配下の
  `orchestrator/campaign/b5_generator_contrast.py`、`orchestrator/campaign/b5_generator_contrast_report.py`、`orchestrator/campaign/p3_s4_loop.py` (B-5 seam: `_b5_proposal_rejected`、`_write_b5_sidecar`、`main` の B-5 分岐)、
  `tools/pegasus/b5_contrast_launch.py`、`orchestrator/tests/test_b5_generator_contrast.py`、`orchestrator/tests/test_b5_generator_contrast_report.py`、`orchestrator/tests/test_b5_contrast_launch.py`、`orchestrator/tests/test_p3_s4_loop.py` (B-5 関連 test)、
  `tools/pegasus/README.md` §0 / §7 (親の docs)、`docs/pegasus-runbook.md` §7.0 投影表。

## 前置き

対象は研究用 repo の CC 合成 campaign の実験基盤 (B-5 生成器対照)。セキュリティでも攻撃でもない。あなたは段 6 の**焦点再レビュー** (fix 後、DW-O16) であり、
fix2 の報告を信じず、所見ごとに closed / partial / regressed を現物で判定する。**親が実行した分担:** fix2 後に新 test 3 file (107 / 67 / 38) を login で実走して緑。
fix 前の焦点走 (計算ノード、21 file) は 2475 passed / 10 skipped。fix 後の焦点走は並行して計算ノードで走行中。実機 qsub / build / bench / handshake は未実走。

# 依頼 — 所見ごとの closed / partial / regressed 対応表

1. review A の must-fix 3 (A1 / A2 / A3) と should (A4 / A5 / A6 / A11 / A12)、review B の must-fix 2 (B01 / B02) と should (B04 / B06 / B07 / B12)、docs (B05 / B13) について、
   fix2 の差分 (`fix2.patch`) と現物で **closed / partial / regressed** を判定し、根拠 (file:line) を添えよ。表なしで「閉じた」と判定しない。
2. **A1 の実効性:** `_b5_proposal_rejected` の reason 分類 (`value-domain` / `attribution` / `grammar` / `probe-material` / `k2-semantic` / `schema`) が traceback の関数名で決まる点の妥当性 (候補が制御できる文字列に依存しないか)、`main` の `except (ValueError, KeyError, TypeError)` が候補起因でない例外 (I/O・環境) を候補拒否に誤分類する経路が無いか (例: proposal file の読取り失敗 = `OSError` は捕捉外か)、rc 3 が driver の `classify_slot` で `rejected-preprocess` になり A のみ消費・retry 無し・系列継続になるか (`_execute_slot` の retryable 判定と `run_series` の分岐)。
3. **A3 の実効性:** `slot-attempt-start` が subprocess **前**に durable か、report の reconcile が「終端 event の無い attempt」を正しく見つけるか (同じ slot_key の `machine-retry` は終端に数えるか)、B の二重計上が無いか (同 logical_slot で `pipeline-submitted` event と sidecar の両方がある場合)。
4. **B01 / B02 の実効性:** `_validate` の照合が `series-end` のある系列にだけ掛かるか、fixture が producer の作れる形か (10 評価、fitness == median)、負例が独立か。
5. **回帰:** fix2 が段 4 の契約 (既定経路の kwargs / identity 不変、`_resolve_duplicate` 不変、pipeline / loop 不変) と M0〜M19 の test を壊していないか (差分から静的に)。`p3_s4_loop.main` の非 B-5 経路で `load_proposal_file` の例外がそのまま上がるか。
6. **親の派生値:** 段 6 裁定の「候補列 (random 698,1,5,364… / sweep 8,25,600,50…)」は親の独立実装と module の一致で得た — この照合が test (`test_b5_generator_contrast.py` の固定 vector) に定数として入っているか。
7. docs (B05 / B13): README §7 の文言が現物の argv・rc・sidecar と一致するか (特に「stock slot では `--coder-role` / `--allow-coder-derived-build` / `--machine-generated-proposal` を渡さない」と `slot_argv` の現物、「rc 3」)。

## 出力形式

- 見出しは `#` 1 段だけ (`##` は `## 総括` のみ)。対応表 (所見 / 判定 / 根拠 file:line / 残る指摘) を必ず含める。
- 実行できない検査は「未実走・静的読解」と明記。予算が尽きそうなら途中結論を出力形式どおり書いて終われ。出力は最終メッセージ本文に全文。
- 末尾に `## 総括`: 残る must-fix (あれば file:line)、should、GO / NO-GO。
