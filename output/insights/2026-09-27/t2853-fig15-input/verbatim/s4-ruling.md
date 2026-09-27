# 段 4 裁定 — [T-2853] (5'') fig15 入力 (2026-09-27、base main ad114fba0、wave 開始後の main 進行 0・新規裁定 0)

段 2・3 は軽量版で省いた (brief の段構成)。所見は無いので、brief の provisional 裁定を確定する。

## 採否

- (P1) 採用。生成器に論理名 → 追跡下の写しの file 名の固定対応 (`summary.json`→`summary.json`、`W<n>/result.json`→`W<n>-result.json`) を持たせる。
  読み出しは file ごとに、`--evidence-root` 配下に論理名 (階層) の file があればそれを、無ければ写しの file 名を読む。どちらを読んでも SHA-256 pin で内容を照合する。
  `--evidence-root` の既定と `load_evidence` の既定は `<repo-root>/output/insights/2026-09-19/mocc-witlight-arm-run/verbatim`。
  `EVIDENCE_ROOT` (原保存先) は `summary.json.inputs` の exact 照合と `source_inputs` の値に使い続ける (値不変)。
  禁止 (署名): `EXTERNAL_SHA256` の値・key 集合を変える差分、CLI から pin を渡す引数を足す差分、`external_inputs` の path を写しの file 名へ変える差分。
  通る正例: `python3 tools/plotting/plot_mocc_witlight_four_arm.py <job dir>/fig15_mocc_witlight_four_arm` が rc=0 で 3 成果物を出し、provenance の `arms` が着地 provenance と一致する。
- (P2) 採用。原本 root の有無で skip していた既存 test 2 本は既定入力 (追跡下の写し) を読み、skip 分岐を外す。
  機能そのものの test として、合成 fixture を写しの平坦 layout で tmp の repo-root 配下に置き、`--evidence-root` を渡さない CLI 実行が rc=0 で描けることを 1 本足す
  (新しい gate・検査ではなく、本題の既定入力の動作確認)。
- 着地 fig15 の 3 file、図 README の着地 SHA-256 3 行、稿は変えない。描き直しの出力は repo 外 job dir。

## 変異の事前登録 (DW-M01、位置は実装後に確定)

| id | 変異 | kill 期待 | 単一理由 |
|---|---|---|---|
| M1 | 写しの file 名対応で `W1/result.json` の行き先を `W2-result.json` に替える | 平坦 layout の fixture CLI test と、追跡下の写しを読む既存 test 2 本が赤 (W1 の SHA-256 不一致で拒否) | 同じ入力を拒否する層は SHA 照合 1 つ (対応表の値だけが変わる) |
| M2 | CLI の `--evidence-root` 既定を原保存先 `EVIDENCE_ROOT` に戻す | 平坦 layout の fixture CLI test が赤 (tmp repo の既定入力を読まない) | 原本 root 現存のため実データ test は通る見込み — kill は fixture test だけに期待 |
| M3 | 階層に無いときの写しの file 名への fallback を外す (常に論理名 path を読む) | 平坦 layout の fixture CLI test と追跡下を読む既存 test 2 本が赤 (file 不在) | 読み出し 1 箇所 |

受理集合を狭める wave ではない (既存の階層 layout の受理は不変) ので過剰拒否の正例は、既存の階層 fixture の test 群 (`test_cli_outputs_and_provenance_closure` ほか) が緑のままであることで示す。
