# [T-2565] certify 投入の --repo-root / PBS_O_WORKDIR 束縛 — 段 1 brief

- **研究前進 (土台):** 認定較正 (certify) job は `env_contract` registry の `calibration_ref` を生む
  producer であり、その receipt は「どの木で測ったか」を束縛する。submit が検査した木と job が実行する木が
  分離していると、この束縛が実行木を指さない場合がある。最小差分は投入経路 1 箇所。完了判定は、
  repo 外 cwd からの投入でも job 側の `PBS_O_WORKDIR` が submit の検査木と一致することを実走テストで示すこと。
- **scope:** `tools/pegasus/submit_certify.sh` の既存経路の修正と、その正例・負例テスト。
- **scope 外:** receipt / pre-submit schema の field 追加、`certify_calibration.sh` 側の新検査、
  他の submit script への一般化、registry / runbook entry の変更、gate・台帳の新設。
- **確定済みユーザー裁定:** 既存経路の修正に限定する。実装面は Codex `role=author` (D95)。本題の修正だけ。
  仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。規律 2 を緩めない。
- **不変条件:** qsub argv・`-v` export spec・receipt schema (`pegasus-submit-receipt/v1` /
  `pegasus-pre-submit/v1`) を 1 bit も変えない。既存テストの期待値を変えない。
  `docs/pegasus-runbook.md` の submit_certify registry 行を変えない (`check_docs` が連動する)。
- **成果物:** `submit_certify.sh` の修正 + consumer test の追加。worklog / insight / decisions の fragment。
- **分割方針:** 実装面は 1 単位 (submit script + そのテスト)。所有 path が素集合なので段 5 は子 1 本。
  受理集合が変わりうるため軽量版の省略条件に該当せず、段 2・3 と段 6 review 2 本は省かない。

- **(P1) 親の provisional 裁定・攻撃対象:** 最小修正は「qsub を REPO_ROOT を cwd として実行する」。
  `PBS_O_WORKDIR` は qsub 実行時の cwd なので、これで束縛が成立し、argv も schema も export spec も変わらない。
  副作用は相対 path 引数 (`--attempts-root` / `--job-script`) の解決先が変わること。cd 前の絶対化が要る。
- **(P2) 親の provisional 裁定・攻撃対象:** 既存の防御 (job 側の nonce 待ち 60 秒 + `source_commit` 照合 +
  自分の木の clean 検査) は多くの食い違いを fail-closed にする。しかし `--attempts-root` を job 側の木の配下へ
  向け、両方の木が同じ commit で clean なら照合は通る。純増は「submit の検査が実行木に掛かること」に限られる。
- **DW-G05 成果物影響:** 放置すると、submit が検査した third-party staging (output 配下 = clean 検査の除外対象) と
  job が実際に使う staging が別物のまま certify receipt が publish されうる。receipt の `source_commit` /
  `pinned_clean` が実行木の全入力を指さないため、registry に登録される `calibration_ref` の provenance が偽になる。

- **受入・実測環境:** login node の pytest (受入全走)。計算ノードへの実投入は行わない
  (hydrate 済み staging が main checkout にも不在で、本修正の検証には不要)。submit の実走検証は既存 fixture 経路
  (`orchestrator/tests/test_pegasus_calibration_workload.py` が `str(SUBMIT), "--repo-root", str(repo_root)` で
  実走させている) を使う。
- **変更面アンカー:** `tools/pegasus/submit_certify.sh` の 13-14 (SCRIPT_DIR / REPO_ROOT 導出)、
  30 (`--repo-root`)、31-32 (`--attempts-root` / `--job-script`)、125-133 (ATTEMPTS_ROOT 既定と SUBMISSION_DIR)、
  211-223 (qsub 実行)。テストは `orchestrator/tests/test_pegasus_calibration_workload.py`。
- **既存被覆 (純増の確認):** D1291 は qsub の `-o` / `-e` の返り先で別問題。F134 の再発 (2026-08-06) が
  「submitter 側の恒久対応は scope 外として裁定パッケージへ返した」と記録しており、これが本項の前身。
  D1920 の却下欄が「その束縛は `--repo-root` と `PBS_O_WORKDIR` が分離している既存の欠陥」と名指しており、
  本 wave がその射程。先例 `tools/pegasus/paper_story_a1_paired.sh:748` は job 側の照合だが、
  比較対象 `repo` の出所が `PBS_O_WORKDIR` 由来なら恒真になりうる (段 2 で確認する)。
