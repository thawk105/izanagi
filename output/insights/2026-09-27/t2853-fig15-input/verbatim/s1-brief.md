# 段 1 brief — [T-2853] (5'') fig15 の入力を追跡下の逐語写しへ閉じる (2026-09-27 14:42 JST、base main ad114fba0)

- 研究前進: ComSys 原稿が載せる fig15 (`mocc_witlight_four_arm`) の再現入力を repo 外 job dir から追跡下へ移し、job dir 撤去後も論文図の値を再導出できる proof chain を残す。
  完了判定 = 生成器が既定で追跡下の写しから描け (rc=0・3 成果物)、着地 provenance と値の leaf 差 0 を insight に記録。
- scope: 生成器の入力読み出し (既定 root と平坦な file 名への対応)、既存 test の入力の差し替え、`tools/plotting/README.md` と図 README fig15 節の入力・再現の記述、insight・worklog fragment・phase3 チェック。
- scope 外 (ユーザー指定): R2 の投入、fig15 の観測の再実施 (再認可が要る)、仮想リスク向けの gate・検査・台帳・一般化。
- 実測済みの前提:
  - 追跡下 `output/insights/2026-09-19/mocc-witlight-arm-run/verbatim/` の `summary.json`・`W1-result.json`〜`W4-result.json` の sha256 は生成器の `EXTERNAL_SHA256` 5 pin と一致 (sha256sum、5/5)。JSON は同 dir の NORMALIZATION.md の正規化対象外。
  - 写しの file 名は平坦 (`W1-result.json`)、生成器は階層 (`W1/result.json`) を期待する → 既定入力の切替には名前の対応が要る。
  - 原本 root (`dev-wave-jobs/dev-wave-mocc-witlight-arm-run/arm-W/`) は 2026-09-27 時点で現存。
  - pin 閉包 (DW-O09): 生成器・test・図 README の変更前 sha256 (`5e46ef9a…`・`000f2836…`・`57d93844…`) の git grep hit は過去の insight 記録 2 件のみで、現行 source を縛る pin 無し。生成器 path の参照は docs・insight の記述と test だけ。
- 不変条件:
  - `EXTERNAL_SHA256` の 5 pin と、CLI から pin を渡せないこと。`summary.json.inputs` の exact 照合 (原保存先の絶対 path) と provenance の `source_inputs` の値。
  - provenance の `external_inputs` の path は論理名 (`summary.json`・`W1/result.json` …) のまま (稿 §5.1 の pin 表・既存 provenance と同じ値)。
  - 着地 fig15 の png・pdf・provenance の bytes と図 README の着地 SHA-256 3 行は不変 (凍結物、先例 T-2853 (5') と同じく描き直しは repo 外 job dir にだけ置く)。稿 (caption_source) も不変。
- (P1) 親の provisional 裁定・攻撃対象: 生成器に論理名→写しの file 名の固定対応を持たせ、`--evidence-root` の既定を `<repo-root>/output/insights/2026-09-19/mocc-witlight-arm-run/verbatim` にする。
  原本の階層 layout も `--evidence-root` 指定で読めるまま残す。どちらの layout でも 5 file の内容は SHA-256 pin が束縛するので受理集合は広がらない。
- (P2) 親の provisional 裁定・攻撃対象: 原本 root の有無で skip していた既存 test 2 本 (`test_landed_fig15_external_closure_when_root_present`・`test_real_evidence_matches_results_document_when_root_present`) は既定入力 (追跡下) を読み、skip しない。新しい gate・検査は足さない。
- 成果物: 生成器・test の差分 (Codex author)、README 2 本の記述 (親)、描き直しの 3 成果物 (repo 外 job dir)、insight (sha256 照合・provenance の leaf 比較・PNG bytes 比較)、spool fragment、phase3 のチェック。
- 実測環境: Pegasus login node pegasus02 (計測機の外、FIGURE_CONVENTIONS §7)。python 3.10.12・matplotlib 3.10.9・numpy 2.2.6 (先例の描き直しと同じ版)。受入は `tools/dev_wave_wait.py acceptance`。
- 分割・段構成: 軽量版。設計択一は小さく、正しさ防壁に触れず、受理集合は SHA 束縛で不変 → 段 2・3 を省く。実装子 1 本 (Codex author)。insight に一致・数値を書くので段 6 は read-only review 1 本を残す。
- G05: 放置すると job dir 撤去で fig15 の既定の再現コマンドが入力不在で rc=2 になり、原稿図の値の再導出経路が切れる (図の値そのものは変わらない)。
