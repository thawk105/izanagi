---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-13
wave: dev-wave-t968-floor-rep-integrity
seq: 1
title: 床値 session の rep 完備性を記録・検査し、壊れた rep の median 混入を塞いだ — 敵対レンズが「登録した変異が実は注入できない」を 5 件捕まえた (コード + docs、branch worktree-dev-wave-t968-floor-rep-integrity)
---

## 本文

- **ユーザー裁定 [T-968] = 採用 (除外区分の追加で)** (2026-08-13 第 7 束) に従い実装した。
  一次控えは repo 外 `dev-wave-jobs/rulings-inbox/2026-08-13-rulings8-batch.md` の「perf 系 4 件」項。
  [T-967] は official 化 wave 同梱の裁定どおり本 wave では触っていない。
- **段 1 で裁定の実装ルートを覆す新事実が出た。** 除外理由表 `allowed_excluded_reasons` は、
  ユーザーが seal 済みの凍結成果物 `output/s8b-freeze/floor_protocol.json` (774 bytes,
  sha256 `261cec1c…`) の**中身**である。`s8b_floor_contract` の pin 検査は凍結保留の対象外で
  生きているため、protocol 表に 5 番目を足すと seal 済み protocol が拒否され床値 campaign が
  起動不能になる。よって「除外区分の追加」は protocol 表を変えない層 (journal/result) で行う、と
  親が段 1 で provisional 裁定し、段 3・段 4 で確定した。凍結 bytes は 1 byte も変えていない。
- **段 3 の敵対レンズが段 2 プランの positive control を落とした。** 「既定の `measure_point`
  経路を通る」と書かれていた control が実際には `_FakeScalePoint` を直接返す形で、
  production の runner と perf parser を通っていなかった。重要な変異を殺せない control
  だったため、実 subprocess だけを差し替える形へ設計し直した。
- **段 6 のレビュー 2 本が独立に同じ must-fix へ到達した** — 証跡免除 session の
  `exclusion_class` が意味検証されず、`competing_process` を `rep_integrity_failure` へ
  偽装できた。独立 2 本が同じ穴を指したので real と裁定し、免除分岐の外へ出して全 session で
  必須化した。
- **変異の事前登録を段 6 で再照準した ({{F:mutation-anchor-nonexistent}})。** 段 4 で登録した
  変異のうち、M4 の anchor (`all` → `any`) は**実コードに存在せず**、M1 は median 混入 assert に
  到達する前に落ち、M7 (precedence 順序) は成果物の値も受理集合も変えず、M12 の
  `returncode=True` は fail-open を作らなかった。レンズ B がこれらを静的に見抜いた。
  M7 は kill 対象から降格し、他は実在する単一 anchor へ再照準した。
- **実装子が model call 上限 (100) で SIGTERM され、報告ゼロで死んだ。** 実装差分は木に
  残っていたため、上限を 400 に上げた継続子へ「ゼロから書き直さず、残った実装を完成させろ」と
  指示して回収した。receipt の `stop_reason=max_model_calls`、wall 1257 秒、evidence は完全。
- **段 5 の実装子と段 6 の fix 子は pytest を 1 度も実行していない** (ログインノードの gate が
  拒否し、codex 子は dispatch できない)。テスト実測はすべて親が計算ノードへ dispatch した。
  子の申告は一貫して「実装済み・未実走」である。
- 実測: 焦点走 (9 file) は fix 前 21 failed → fix 1 巡後 1 failed → fix 2 巡後
  **710 passed / 4 skipped**。`test_s8b_approved.py` の `ModuleNotFoundError: No module named
  'tests'` は file 選択走固有の偽赤 (差分由来でない)。
- 変異 matrix: 7 変異すべて **KILLED / SURVIVED 0 / MISMATCH 0**。
  初回走は期待 node 集合の不足で 4 件 MISMATCH となり、`DW-M08` の probe + erratum 経路で
  完全集合へ再登録して再走した (probe 台帳も
  `output/insights/2026-08-13_t968-floor-rep-integrity/` に残す)。
  **M10 は 57 node を赤にする過剰決定**であり、`DW-M03` に従い単一理由の証拠からは外す。
- **scope 外として返す real 所見 2 件** (裁定パッケージ候補):
  (a) `PATH` 先頭に別の `perf` を置けば counter 完備性を operator が on/off できる。
  実行した perf の realpath・identity は toolchain binding に含まれない。
  **本 wave 単独で operator 制御の除外を閉じたとは主張しない。**
  (b) `competing_process` の自己申告で測定済み session を捨てうる穴は wave 前から在り、
  台帳上も別 wave の責務である。本 wave は「measure が完了した session は証跡提出を免除しない」
  ことで悪化だけを防いだ。

## 次の一手差分

### 完了

- [T-968] 床値 session の rep 完備性 (rc + counter) を記録・検査する仕組みを実装し、
  壊れた rep の throughput が median へ混入する経路を塞いだ。除外条件は rc と counter 完備の
  機械的事実だけで、性能値は条件に入っていない。凍結 protocol の 4 理由表と seal 済み bytes は不変。
  remaining: none
  base: 9eab340bcd0aff1398cd6e67143481580424c399c191292b63b6b49622800190

### 新規

- {{T:perf-binary-identity-for-floor}} **P2・新規**: 床値経路が実行する `perf` の
  realpath・identity を toolchain binding へ含める。現状は preflight も本番も literal `perf` を
  起動するため、`PATH` 先頭に wrapper を置くだけで counter 完備性を operator が制御できる。
  [T-967] / [T-970] (F89 未裁定) と同じ閉包にあり、official 化の必須依存として扱う。
- {{T:competing-selfreport-authenticity}} **P2・新規**: `competing_process` /
  `launch_failure` の自己申告と保存 probe 証跡 (rc / stdout / stderr) を共有分類器へ
  再投入して照合する。現状は測定済み session を「未測定の免除行」に偽装する経路が
  構造検査だけで塞がれており、真正性の突合は行われていない。
