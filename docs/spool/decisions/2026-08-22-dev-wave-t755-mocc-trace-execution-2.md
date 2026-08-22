---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-22
wave: dev-wave-t755-mocc-trace-execution
seq: 2
---

## {{D:t755-cpu-model-normalization}}. mocc trace pilotのCPU model環境gateは観測値だけを正規化し比較する

**決定:** `tools/pegasus/mocc_trace_pilot.sh`のCPU model環境gate (実機`/proc/cpuinfo`と
policy期待値の比較) は、観測値だけを`(R)`/`(TM)`除去+空白畳み込みで正規化してから比較する。
policy側の期待値・生値の記録先 (`cpu-model.stdout`、receiptの`cpu_model`/`expected_cpu_model`
field) は変更しない。比較専用の新規変数 (`CPU_MODEL_NORMALIZED`) を追加し、失敗メッセージには
`observed_normalized=`ラベルを明示する。

**理由:**
- 実機初回投入で、観測値`Intel(R) Xeon(R) Platinum 8468`とpolicy期待値
  `Intel Xeon Platinum 8468`が商標記号の有無だけで偽陽性拒否された。sibling script
  `tools/pegasus/t141_region_profile.sh`に既存の正しい正規化パターンがあり、これを移植した。
- 段3敵対相談・段6敵対レビューが独立に、失敗メッセージの`observed=`値を正規化後の値にする際は
  生値 (`cpu-model.stdout`) との混同を避けるため`observed_normalized=`と明示すべきと指摘し採用した。
- 正規化は表記ゆれの吸収に限定し (`(R)`/`(TM)`除去、空白畳み込みのみ)、真に異なるCPU機種は
  引き続きfail-closedで拒否する。段3レンズBが独立レンズで反例 (`AMD EPYC 9654`等) をトレースし
  偽陰性化しないことを確認した。
- 広範囲grep (`tools/pegasus/*.sh`) で同種の厳密比較を行う他scriptは`t141_region_profile.sh`
  (正しい前例) 以外に無いと確認した。`certify_calibration.sh`は`EXPECTED_CPU`をreceipt記録に
  のみ使いgateしない (同種バグなし)。

**却下した選択肢:**
- policy側`expected_cpu_model`の値を実機表記 (`(R)`付き) に合わせて変更する — 一台の実機表記に
  policyを合わせるだけで、逆の表記や別ノードの表記ゆれには対応できず根本解決にならない。
- `gsub`から`sub`への変更を見送る (等価なので不要) — 移植の一貫性を優先しsiblingパターンを
  そのまま採用した。害はないため差分に残した (段3レンズA所見、対応不要と裁定)。

## {{D:t755-verifier-interpreter-gate}}. mocc trace pilotのverifier起動はpython3.10以降を実呼出しと同一環境で解決する

**決定:** `tools/pegasus/mocc_trace_pilot.sh`のverifier起動
(`python3 -m orchestrator.verifier ...`) は、`python3 python3.10 python3.11 python3.12`の順で
候補を試し、**実呼出しと同一環境** (`cd "$REPO_ROOT"`後、`-I`分離モードは使わず
`import orchestrator.verifier`+`sys.version_info >= (3, 10)`を判定) で解決した最初の候補
(`VERIFIER_PY`) を使う。全滅時はfail-closedでexit 2し、既存の`verifier_rc`ベース失敗経路と
同様に`verifier.rc`へ値を書く (一貫性のため)。

**理由:**
- 計算ノードの既定`python3`はmodule `intelpython/2022.3.1`ロードによりIntel Python 3.9系に
  解決され、`orchestrator`パッケージをimportできず`ModuleNotFoundError`で失敗した。
  `tools/pegasus/floor_campaign.sh`等の既存4 sibling scriptに同型の版数gateパターンがあり、
  これを移植した。
- 段2プランは`-I`分離モード+明示的な`sys.path.insert`でprobeを設計したが、段3敵対相談レンズAが
  「probeと実呼出しの環境が異なる (`-I`の有無、PYTHONPATH等の扱いが違う) ため整合性の主張が
  成立しない」と指摘し、段4裁定でprobeを実呼出しと完全に同一の環境 (`cd`のみ、`-I`なし) に
  揃える設計へ変更した。
- 同じくレンズAが、interpreter gate失敗時に既存の`verifier.rc`出力契約が欠落する点を指摘し、
  `write_failure`直後に`verifier.rc`へ値を書く一貫性を追加した。
- 段6敵対レビュー (2レンズ) が独立に、新設テストの1件のassertion誤り (`stage=verifier`を
  誤って`result.stderr`で検査、正しくは`write_failure`が書く`failure`ファイル側) を発見し、
  fixで是正した。本番script側の実装は両レビューとも段4裁定と完全に整合していると確認した。

**却下した選択肢:**
- probeに`-I`分離モード+`sys.path.insert`を維持する (段2当初案) — 実呼出し (`-I`なし) との
  環境差異により、probeが通っても実呼出しが失敗する経路を排除できないため、段4で却下し
  probe設計を変更した。
- interpreter解決不能時に`verifier.rc`を書かない (既存契約のまま) — 「stage=verifierの失敗では
  常に`verifier.rc`が存在する」という一貫性を優先し、書く方針を採用した。
