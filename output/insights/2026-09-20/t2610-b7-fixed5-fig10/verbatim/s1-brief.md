# 段 1 brief — [T-2610] B-7 fixed 5 µs 三 workload 退行の図 fig10 (2026-09-20 07:12 JST)

- 研究前進: 論文の結果節材料稿 `docs/paper-story/results/2026-09-19-b7-fixed5-three-workload-regression.md` (B-7 材料、図は無い) に対応する図 10 を足す。
  完了判定 = `docs/paper-story/figures/fig10_b7_fixed5_three_workload_regression.{png,pdf,provenance.json}` の 3 成果物が rc=0 で出て、
  figures/README.md の fig10 節 (caption 正文・着地 SHA-256 3 行) と test が実 repo で緑、変異 matrix が期待どおり、受入緑、land。
- scope (純増): 新 file `tools/plotting/plot_b7_fixed5_regression.py`、新 test `orchestrator/tests/test_plot_b7_fixed5_regression.py`、fig10 3 成果物、
  `docs/paper-story/figures/README.md` (一覧 1 行 + fig10 節)、`tools/plotting/README.md` (command 例 1 節)、`docs/paper-story/README.md` の
  results 行 (2026-09-19 稿) の「図は無い」を「図 10」へ、insight dir、worklog fragment。
  不変: 既存図 (fig1〜9) と provenance、稿 (results/ 全 file)、`plot_a2_certification.py`、certification 経路、policy、床値 JSON。
- 確定済みユーザー裁定: D2162 (判定規則 v2 = `effect_w < −floor_w` strict、床値 = D1639 JSON `between_run.cv` 全桁、B-7 充足判定なし、追加 gate なし)、
  D2044 項 3、本 wave 引数 (図が言えるのは稿の床値判定まで。B-7 充足・反復 attempt・certification 昇格・有意差判定を含めない)、D95 (実装面は Codex author)。
- 不変条件: 規律 1 (性能値は trace-disabled build)、規律 2 (certified を性能認証と言わない、anomaly 0 の記録を写すだけ)、規律 7 (既存材料と前後比較しない)、
  D1993 項 6 (プールしない)、F36 (稿に provenance hash を書かない = caption_source は稿の SHA-256 を provenance が持つ)、FIGURE_CONVENTIONS §1〜10 (入力からその場で再計算、
  5 反復の t95 CI は標本の記述、基準線は stock median、provenance、計測機の外、fail-closed layout check、実寸 fixture、実データ実走)。
- 入力 (2026-09-20 07:09 JST 実測、全件 稿 §5.1 / raw-manifest と一致): `output/insights/2026-09-19_t1998-b7-fixed5-three-workload/certification.json` `b6493e4e…`、
  同 `raw-manifest.json` `be8163da…`、床値 JSON `output/env/pegasus/calibration/between_run_noise_t48_skew0p9_{rr5,rr50,rr95}_rmw0.json`
  (`25b4d2a0…` / `a94dc83e…` / `23c024e4…`)、policy `orchestrator/campaign/paper_story_b7_fixed5_regression.v2.json` `c6b24050…` (= certification `policy_sha256`)、
  caption_source = 稿 `6585d446…`。durable raw 6 file (`/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-b7-fixed5-20260919/b7f5-20260919a/jobs/<w>/raw/<cell>.json`) の
  SHA-256 は raw-manifest `files` と 6/6 一致、各 `performance.samples_tps` は 5 標本 (certification.json は median だけを持つ)。login pegasus02 に matplotlib 3.10.9 / numpy 2.2.6。
- (P1) 5 標本は durable raw (repo 外) から読み、tracked raw-manifest の SHA-256 で束縛する (fig6 型)。着地 closure は provenance の cells から artist_series / caption を再計算し、
  外部 root を要さない (fig6 の `validate_repo_closure` 型)。外部 root 不在は skip、部分欠落は失敗。
- (P2) 判定は生成器が作らない: 稿 §2.1 の判定 (rr5 / rr50 退行なし、rr95 退行) を定数として写し、`effects[w] < −cv_w` の述語との一致を fail-closed で検査する (fig9 の classification 型)。
  effects は certification の値を写し、raw median の比からの再計算と `abs_tol=1e-12` で照合する (fig6 の `effect_crosschecks` 型)。median は 5 標本から再計算し certification `median_tps` と一致を要求。
- (P3) 図の形: 2 段。上段 3 panel (workload 別、y は workload 別尺度) = cell 2 本 × 5 標本の点、median の短い横棒、mean ± t95 CI (df 4、`t=2.7764451051977987`) の菱形と誤差棒、
  stock median の灰破線。下段 1 panel (3 列を跨ぐ) = workload ごとの `effect_w` (%) を marker + 直接 label、0 線、`−floor_w` (%) の短い破線 + 値 label、判定 label
  (`no regression` / `regression (below −floor)`)。図中ラベルは短く、内部識別子を出さない。
- 成果物の形: provenance schema `izanagi-b7-fixed5-regression-figure-provenance/v1`。`tracked_inputs` (certification / raw_manifest / floor ×3 / policy / caption_source)、
  `external_inputs` (raw 6、root 相対 path + SHA-256)、`cells` (6、samples・median・mean・ci95_half・correctness・src_token・digest)、`effects`、`effect_crosschecks`、`floors`、
  `judgments` (記録値 + 述語一致)、`outer_status` / `a4_noise_floor_status` (写すだけ)、`measurement_conditions`、`artist_series`、`caption` (英文、Figure N は prefix から)、`reproduction`。
- 分割方針: 既定の軽量版 (DW-C00)。段 2・3 省略 (設計択一は稿 §2.5 と fig6 / fig9 の先例で閉じ、正しさ防壁・受理集合に触れない)。段 5 = Codex author 1 本 (生成器 + test)。
  段 6 = 親の焦点走 (計算ノード dispatch) → fix 子 (必要時) → read-only review 1 本 (README fig10 節・caption の事実再抽出) → 変異 matrix (事前登録は段 4) → 受入。段 7〜9 親。
- 受入・実測環境: 作図は login (pegasus02、計測機の外)。焦点走・変異・受入は計算ノードへ dispatch。図の生成に計測は無い。
- DW-G05: 放置時 → 論文の B-7 材料稿に図が無いまま (結果節の図 10 欠落)。certified 選択・レポートの値・受理集合・参照は変わらない。
- 条件 dispatch: O08 / O09 / O10 不成立 (新規 file のみ、freeze・oracle・proof chain・凍結 bytes に触れない。`docs/paper-story/figures/` に列挙型 pin は無いことを test 検索で確認)、
  O11 不成立 (削除なし)、O13 不成立 (gate 新設なし。test は生成器の単体・着地検査で受理集合を変えない)、O20 成立 (背景 job、gate rc=0 済)。
