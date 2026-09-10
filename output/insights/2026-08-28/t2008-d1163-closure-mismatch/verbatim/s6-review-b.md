## 所見

- **LB-01 — real / scope 内 / must-fix**
  - file: [p2_2_report.py:249](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-closure-mismatch-codex-resume/orchestrator/campaign/p2_2_report.py:249)、[p2_2_report.py:270](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-closure-mismatch-codex-resume/orchestrator/campaign/p2_2_report.py:270)
  - 具体的反例: `report_workload()` の戻り値には marker がある一方、`write_summary()` は `campaign_verifier_epoch` しか表示しない。新生成 `p2-2-summary.md` から exact marker が消える。
  - 成果物影響: 詳細 MD/dat には届くが、P2-2 横断 summary は「当時の verifier での判定」を表示しない。
  - 推奨 fix: summary の列または provenance 節へ marker を出し、helper ではなく生成された summary 本文を検査する。

- **LB-02 — real / scope 内 / must-fix**
  - file: [test_backoff_figure_provenance.py:350](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-closure-mismatch-codex-resume/orchestrator/tests/test_backoff_figure_provenance.py:350)、[同:658](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-closure-mismatch-codex-resume/orchestrator/tests/test_backoff_figure_provenance.py:658)、[test_s1_9pair_figure_provenance.py:667](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-closure-mismatch-codex-resume/orchestrator/tests/test_s1_9pair_figure_provenance.py:667)、[同:845](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-closure-mismatch-codex-resume/orchestrator/tests/test_s1_9pair_figure_provenance.py:845)
  - 具体的反例:
    - fig2b 記録 SHA = `bdb3c223…`、現行 `plot_backoff.py` = `f02f682d…`
    - fig4 記録 SHA = `4a76d59c…`、現行 `plot_s1_9pair.py` = `61559d90…`
    - 両記録 SHA は変更前 `HEAD` bytes と一致するが、validator は current source SHA と比較する。
  - 成果物影響: 実走すれば既存 fig2b と fig4 provenance の実在受理 test は source mismatch で必ず赤になる。過去 provenance を現行コードとの差だけで無効化するため、D1163 の撤去対象と同型。
  - 推奨 fix: 既存成果物は生成時 SHA の固定値で照合し、current SHA は新生成 provenance の test で別に検査する。既存 provenance/PNG/PDF を current SHA に合わせて書き換えない。

- **LB-03 — real / scope 内 / must-fix**
  - file: [plot_s1_9pair.py:1489](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-closure-mismatch-codex-resume/tools/plotting/plot_s1_9pair.py:1489)、[test_s1_9pair_figure_provenance.py:934](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-closure-mismatch-codex-resume/orchestrator/tests/test_s1_9pair_figure_provenance.py:934)
  - 具体的反例: 新規 P7 test は `load_campaign()` の返り値までしか検査しない。`build_provenance()` で marker だけ除去する変異は、P7 を通過する。既存 P3 test は marker 無しの旧 provenance を読むため、新生成 serializer の検査にならない。
  - 成果物影響: 変異 DW-M03 の「S1 provenance 伝搬を落とせば赤」が最終 artifact 境界では成立しない。
  - 推奨 fix: production `load_campaign()` の結果から一時 PNG/PDF と `build_provenance()` を通し、全 campaign input の exact marker を検査する end-to-end test を追加する。

- **LB-04 — 疑わしい / scope 内**
  - file: [digest.py:100](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-closure-mismatch-codex-resume/orchestrator/critic/digest.py:100)、[digest.py:1209](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-closure-mismatch-codex-resume/orchestrator/critic/digest.py:1209)
  - 具体的反例: 新 field が既存 `fastest` より前へ挿入されたため、従来の第7 positional 引数は `fastest` でなく marker に束縛される。また既定値 `None` により、`HISTORICAL_RAW` の `WorkloadDigest` を marker 無しで構築して `render_text()` できる。
  - 成果物影響: tracked caller は keyword 構築なので現在は発火しないが、外部・将来 caller は marker 欠落または `GenomeLI` の誤表示を起こせる。
  - 推奨 fix: field を `fastest` の後ろへ置くか keyword-only にし、`__post_init__` で historical⇔exact marker、certified⇔`None` を検査する。

- **LB-05 — 疑わしい / scope 内**
  - file: [test_backoff_figure_provenance.py:384](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-closure-mismatch-codex-resume/orchestrator/tests/test_backoff_figure_provenance.py:384)、[test_plot_backoff_ci.py:205](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-closure-mismatch-codex-resume/orchestrator/tests/test_plot_backoff_ci.py:205)
  - 具体的反例: backoff の実 provenance validator は `read_purpose` と epoch object を検証しない。新しい最終 artifact test は marker を自作 fixture に事前投入している。
  - 成果物影響: marker を欠く provenance も reader が受理する。旧 v2 を残す必要があるため、単純な required 化もできない。
  - 推奨 fix: 新旧を識別できる schema/version 境界を置くか、「旧着地 artifact」と「新 producer 出力」を別 validator/test で扱う。

## consumer ・ schema 照合

| 面 | 静的到達結果 | 補足 |
|---|---|---|
| Layer3 historical | exact marker 到達 | report object、schema、test とも到達 |
| P2-2 詳細 MD/dat | exact marker 到達 | `_epoch_provenance()` 経由 |
| P2-2 summary | **欠落** | LB-01 |
| critic digest | exact marker 到達 | `render_text()` に表示 |
| online digest | exact marker 到達 | digest の間接 consumer。未編集で正しい |
| backoff provenance | exact marker 到達 | `inputs[].campaign_verifier_epoch` に入る |
| S1 provenance | production 上は到達 | 最終 serializer の検出力不足は LB-03 |
| certified view | marker 無し | `hasattr` 負例あり |
| 新 certified Layer3 | marker 無し | historical object を certified epoch projection で上書き |
| plot caption/pixels | exact literal 無し | sidecar provenance には存在。裁定の「figure provenance」範囲なら許容だが、単体画像だけでは表示されない |

Draft-07 conditional は意図どおりです。`certifying_input=true` の場合、epoch object の `not: {required: [verifier_assessment_basis]}` が marker 混入を拒否します。負例は receipt 非 null・admission admitted を満たしており、別条件による恒真失敗ではありません。

互換性も静的には維持されています。

- marker 無しの旧 v3 historical report: 受理
- `CampaignVerifierEpoch` の legacy `recorded-current-closure-mismatch`: 受理
- Layer3 schema enum: 受理
- oracle artifact/judge reader: 受理
- production の旧 literal: dataclass/schema/oracle の3面だけに残存

23件の `FROZEN_MANIFEST` bytes は差分に含まれません。一方、変更 production の新生成 SHA は全て変わります。この区別自体は正しいものの、LB-02 の figure validator だけが生成時 SHA と current SHA を混同しています。

## 変異の検出力

- DW-M01: 有効。比較復活で committed mismatch 正例 1件＋7 parameter が赤になる。
- DW-M02: view、Layer3、P2詳細、critic、backoff、S1 load の exact literal 検査がある。ただし P2 summary は既に欠落。
- DW-M03: Layer3、P2詳細、critic/online、backoff は概ね有効。S1 最終 serializer は LB-03 の逃げ道がある。
- DW-M04: 有効。schema conditional だけを落とすと marker 混入負例が通って赤になる。
- DW-M05: 24 path parameter test が production `_verify_committed_loader_binding()` を通る。
- DW-M06: freeze closure SHA 変異の単独負例あり。
- DW-M07: operation-only mismatch を含む capability test があり、operation 比較の除去を検出する。
- DW-M08: fresh lane が current lookup を使い historical resolver を呼ばないことを spy で固定している。

historical caller 6件を exact に列挙する AST/content-scan meta-testは見当たりません。したがって7件目の caller 追加や新しい手書き projection は黙って漏れ得ます。現行6件の局所 test はあるものの、悉皆性は一覧 pin では保証されていません。

また、変異は事前登録文書に列挙されているだけで、変異適用の自動 harness・実走 receipt はありません。同一主体が gate と期待値を同時変更でき、fixture path/hash を識別する実装も排除できないという D387/D799 の限界は残ります。

## 総括

**must-fix は3件**です。

1. P2-2 summary の marker 欠落
2. 既存 backoff/S1 provenance を current generator SHA 差だけで拒否する回帰
3. S1 の最終 provenance serializerまで届かない変異検査

Layer3 の certified禁止条件、旧 v3、legacy mismatch 3 reader、6 historical production 経路の主要投影は静的には成立しています。

テストは実走しておらず、緑とは報告しません。LB-02 はテスト結果ではなく、記録 SHA・変更前 SHA・現在 SHAと比較コードから静的に確定した不一致です。
