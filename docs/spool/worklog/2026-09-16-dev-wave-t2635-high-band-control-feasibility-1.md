---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2635-high-band-control-feasibility
seq: 1
title: [T-2635] 高域の対照 — 候補設定の到達と共通辺の成立は記録済み走行からは確認できず、新走行は取らずに裁定パッケージを返す (docs + 使い捨て probe、branch worktree-dev-wave-t2635-high-band-control-feasibility、変異 matrix = 実装面差分ゼロで免除)
---

## 本文

- **依頼の scope**: D2044 項 13 (候補設定について高域到達と既存 J1 の共通辺の成立を先に確かめ、既存の事前登録を変えずに対照が
  作れると分かれば新走行、分からなければ改めて諮る)。まず記録済み走行の読取で判定し、job script は稼働中の別 wave が編集中なので
  触らない。gate・検査・台帳・一般化の追加は scope 外 (ユーザー指示)。全 9 段で進め、段 2 plan 1 本、段 3 consult 2 本、段 5 author 1 本、
  段 6 review 2 本 + 焦点再レビュー 1 本 (いずれも gpt-6-astra、plan/consult/review は medium、すべて accepted / completed)。
- **答え: 現制約と記録済み証拠では、既存の事前登録を変えずに高域の対照が作れるとは確認できない。新走行は取らず裁定パッケージを返す**
  ({{D:high-band-control-not-confirmable-from-records}})。「将来も成立しない」とは言わない。
- **根拠は記録済み事実と現物の制約だけ** (模擬は F29 により根拠に入れない)。(1) 既存 J1 は 2 cell を名指しし全軸を固定、初期 `Backoff_` は
  stock で 0 固定で knob が無い — 設定を変える候補はすべて旧登録外。(2) 登録対照の広窓側 `nm-step1-u2560` は 1,170 event すべて 0.0〜12.0 µs
  (`no_high_band_observation`、D2020 の再現。無改変 `_j1_sign_instability` が 12 / 1,168 / 0.4984 / 0.4583 / +0.0402 / `not_supported` /
  `direction_unstable` を完全再現)。(3) main の現物 driver を無改変で import して実測: 広窓 cell の刻みを変えた候補集合は parse できるが
  trace contract が無く投入不能、登録集合だけ contract 有り (rep_index 1 は拒否)。(4) 広窓 walk の水準別移動 (5 µs 以下 273↑/146↓、
  7 µs 以上 196↑/314↓、全水準 588↑/581↓、parity 分岐 2/1,170) — 記述であり到達確率の同定ではない。(5) K_high >= 10 の必要到達水準
  (理想格子 + stock 更新則内) は S=0.5/1/2/25/100 で 55.5 / 61 / 72 / 325 / null、主帯域の非自己遷移辺は 1899 / 949 / 474 / 37 / 9 本。
- **段 3 が親 brief の断定 3 件を訂正した** (段 4 で採用): 「高域へ届く広窓側は必ず別 cell」→「設定を変える候補は旧登録外」、
  「S=100 は 9 本だから構造的に不可能」→ 理想格子と stock 更新則内の結論、「再走は不到達を繰り返す見込みなので取らない」→
  D2044 の条件付き投入許可を満たす根拠が記録に無いから。相談 B が「(b) prefix の共通辺は包含恒真」「S=25 の転写最大 300 では
  主帯域の非自己辺は 9 本」を指摘し、K の 3 値判定は全候補 `K_undetermined` で固定した。
- **段 6 レビュー 2 本**: probe の帰属・帯域分類・格子算術・転写・prefix・driver 受理・selftest はいずれも崩れず、README の数値に不一致なし。
  must-fix は README の文 3 種 (雑音支配の因果断定、集計量の違う u10 対比、裁定案 B の維持条件と C の予測的理由) で、親が README だけを
  直し焦点再レビューで閉じた。probe と JSON は変えていない。
- **probe は Codex author が書き repo 外へ退避** (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2635-high-band-control-feasibility/probe_t2635.py`、
  実効 188 行、sha256 `b4cdcfc34c0c…`)。login node で `--selftest` 12 項目 true (4.13 s、RSS 447,880 KB)、通常出力 rc=0 (5.30 s)。
  実装面の repo 差分はゼロで変異 matrix は `DW-S04` により免除。新しい Pegasus 実測は 0 件。
- 一次資料: `output/insights/2026-09-16/t2635-high-band-control-feasibility/README.md` (§6 が裁定パッケージ: A 見送り〔推奨〕 / B 将来 wave で
  S=25 双子 + 別登録 J1' + driver 登録 / C 登録集合の再走 1 回〔併記のみ〕) と同 `verbatim/` (brief・plan・consult・裁定・probe 逐語・出力 JSON)。
- **受入全走**は本記録 commit を含む tip に対して land 前に 1 回だけ投入し、child-green でなければ land しない。本エントリの作成時点では未実施である。
- 工数: codex 子 7 本 (plan 1・consult 2・author 1・review 2・focus 1)。計算ノード job は 0 件。

## 次の一手差分

### 更新

- [T-2635] **P2・裁定待ち (裁定パッケージ提示済み)**: 高域の対照は記録済み走行と現制約からは成立を確認できない
  ({{D:high-band-control-not-confirmable-from-records}})。択一は A 見送り〔推奨〕 / B 将来 wave で S=25 双子 (刻み 25、更新間隔 10 対 2560、
  他は登録と同じ) を旧 J1 の方法 (完全一致辺・固定共通重み・K >= 10・差 0.10・3 区間) を維持した別登録 J1' で取得し driver / 解析器へ
  cell 集合を登録する / C 登録集合の再走 1 回 (推奨しない)。正本は `output/insights/2026-09-16/t2635-high-band-control-feasibility/README.md` §6。
  base: ebdfb7b08aaee9918f1975aab9721f026c328c014bbce2cbf8f245c45210083b
