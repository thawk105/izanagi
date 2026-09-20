---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-t2795-pair-launcher
seq: 1
title: [T-2795] K2 手動 loop の同 job pair launcher (driver の stock 対照口 `--stock-control`・job body の stock step) と B-5 §10 の K2 共有部品 (較正動作点 CLI、exact correctness opt-in) を Codex author で実装した (コード + docs、branch worktree-dev-wave-t2795-pair-launcher)
---

## 本文

- ユーザー依頼 (2026-09-20、dev-wave 引数の逐語は insight `verbatim/T-2795-origin.md`) の範囲で 1 wave。裁定 = D2172 項 3 (i) / 項 4 (α)。一次資料は
  `output/insights/2026-09-20/t2795-pair-launcher/README.md` (brief・plan・裁定・追補・consult / review / fix の逐語・変異台帳・走記録)、設計判断は
  {{D:k2-pair-launcher-stock-control}}。専用 handoff は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-pair-launcher/HANDOFF.md`。
- 起点 local main `371674ea6`。起動時の編集面重複検査 = 3 file を全 worktree の commit 済み差分 + 未 commit 差分で走査し hit 0。pin 閉包 = 3 file の
  現行 sha256 の hit は過去 receipt / reservation (歴史記録) のみ、凍結物の bytes pin なし。job 契約 test の逐語 pin は現役で author が更新した。
- 段 2 plan (codex、6 分) と段 3 consult 2 本 (各 4〜5 分) は must-fix 3 件を出し全件採用: 非 STOCK の certified を stock 成功に含めない、候補用 condition
  gate は stock (適応枝) を検査しないので A-1 paired 形 + `--isolate-worktree` 必須、TJ の driver 呼出し箇所数 2 → 3。削った要素 = terminal 復元の
  二層化 (skip = 非成功)、較正・verify の job body env、inert を証明しない token/projection test。
- 段 5 author (Codex、27 分) は 5 file (+947/−41) を実装し、**stock source の build admission が stock-baseline 分岐 (`source.ccbench_commit ==
  CURRENT_PIN` の exact 比較、S4 の full PIN と短縮 pin が不一致) で admission-error になる仕様衝突を未了として正直に報告**。追補 1 で stock 経路限定の
  `capability_resolver` (STOCK evidence にだけ generator receipt、非 STOCK は None → fail-closed) を裁定し、fix1 (8 分) で完成。
- 段 6 レビュー 2 本 (A: 正しさ境界・identity・admission、B: 既定挙動不変・過剰・test の実効) は **must-fix 0 / GO ×2**、should 3 + nit 2。計算ノード焦点走 1
  (15 file、1741 passed / 2 failed) の赤 2 件は本差分に帰属する静的 inventory pin (p3_s4_loop の layout 呼出し 10 → 11・run_campaign 1 → 2、
  静的 import 閉包 47 → 49 = `p2_2` + `genome`)。fix2 (test のみ、9 分) で should 3・nit 1・pin 2 を閉じ、焦点再レビュー 1 本は 6 所見 closed / GO
  (nit 1 = README の digest 条件、親が直した)。焦点走 2b (統合 commit 2、request 12681.nqsv、117 秒) = **1746 passed / 1 skipped**。
- 実装 commit `c6eb77597` (production 2 file + test 3 file)、`46cc32feb` (fix2 の test 3 file + `tools/pegasus/README.md`)。pipeline.py / loop.py /
  ident.py / build_admission.py は変更なし。既定経路 (fixture / proposal) の argv・identity preimage は変更前と bytes 一致 (固定定数で test)。
- 変異 matrix (等価対照 1 + 負例 17、独立 clone @46cc32feb、計算ノード dispatch、runner = TL / TJ / TV): probe (全件 SURVIVED 登録) で観測 node を集め、final で **baseline PASSED・M0 SURVIVED・17/17 KILLED (期待 node 完全一致)・MISMATCH 0**。M7 (非 STOCK の成功拒否)・M10 (stock 形 condition gate)・M16 (resolver の非 STOCK 拒否) は単一 node で殺した。job body の 4 変異は TJ の static contract (mutation 対 test) が連鎖して 56〜61 node、M15 (pipeline の rep 打ち切り) は TL 71 本の連鎖。詳細は insight §5。
- 検査: provenance range 監査 違反なし (2 commit)、`check_docs` 違反なし、`git diff --check` 緑、三軸語走査 (`s8b_holdout_freeze search`) の結果は insight §6。受入: 記録 commit の tip で待ち手経由の全走 (`dev_wave_wait.py acceptance`、3 shard) を門番 loop から 1 回投入する。結果は本 fragment には書かず受領証 (`acceptance-receipt-final-<n>.json`、job dir) と land の記録が持つ。child-green でなければ land しない
- 限界・言わないこと: pair 成立 (同 job で候補と stock の両方が測れた) は主張しない — 本 wave は結線だけで 1 job も投入していない。実 compiler で stock の
  source が STOCK token に解決すること (inert) は未測定 (b10 / A-1 paired の実装先例はある)。stock の admission class は machine-generated (generator
  backoff-sweep) で stock-baseline ではない。B-5 §5.4 の系列開始 stock (planner 前) / block stock / §5.3 の session 品質契約 / §5.5 の残余引数・seed・
  verifier 版の発効束は作っていない。較正・verify の opt-in は job body 未配線。B-5 本走は未認可。`--v` 略記は `--verify-performance` 追加で曖昧になる
  (使用箇所なし)。3 巡目の記録 (identity `409e13f8…`) は保持し、pair 結果は別の実行証拠として追記する。
- 裁定パッケージ候補 (実装せず記録): `build_admission.derive_build_admission` の stock-baseline 分岐が full PIN と短縮 `CURRENT_PIN` を exact 比較する点。
  正規化は admission gate の変更なのでユーザー裁定。
- 事故: 統合 commit 2 直後の provenance range 監査が計算ノードへ dispatch されている間に焦点走 2 を同 worktree から投入し、orphan hold で rc=16
  (DW-O26 どおりの直列違反、走行ゼロ、監査 job 終端後に 2b で再投入)。変異 clone script の引数 SHA を誤記して `update-ref` で止め、dir を消して作り直した。
  段 5〜6 の handoff 時刻を推定で書き 15〜30 分ずれた (mtime で訂正)。
- 工数: codex 8 本 (plan 1、consult 2、author 1、fix 2、review 2、focus 1)、計算ノード job = 焦点走 2 + provenance 監査 1 + 変異 (probe + final) + 受入。

## 次の一手差分

### 更新

- [T-2795] **P1・裁定済み (D2172 項 3、択 (i) + 新択 (iv)) → launcher 実装済み ({{D:k2-pair-launcher-stock-control}}) → pair 投入 (AI)**:
  同 job pair launcher は本 wave で着地 (driver `--stock-control`、job body `IZANAGI_S4_STOCK_CONTROL=1`、同 campaign の stock WAL は
  pipeline 発行、成功条件に source の STOCK 性)。次 = fresh submit-tree + fresh layout で候補 10 + stock を 1 job (`IZANAGI_S4_STOCK_CONTROL=1`)
  で投入 (候補 10 の再評価を認可済み)。最初に実 compiler での STOCK 成立 (stock の `outcome=certified-stock`、admission receipt の
  `src_token`) を確認し、成立しなければその走を対照成立と認定しない。3 巡目の記録は縮小走行として保持し pair 結果を追記。4 巡目 = 新規生成 1 回 +
  同 job stock 対照 1 本 (1 job、再投入なし) を認可済み。(ii) 単独・(iii) 単独は不採用。
  base: 01a018b15d94524ce62e180d85ac71903de9bf2964de41924992ceedf7366362
- [T-2797] **P2・裁定済み (D2172 項 4、段階裁定 (A)) → (α) K2 共有部品は実装済み ({{D:k2-pair-launcher-stock-control}}) → (β) 上限付き試走 (AI)
  → 本走認可は試走後に再提示**: (α) のうち同 job stock (候補後)、較正動作点 CLI (`--calibrated-perf --perf-workload`)、exact correctness opt-in
  (`--verify-performance`) は driver に着地 (本走は未認可)。残る §10 部品 = 系列開始 stock の順序 (planner 前 → `current_perf`)、session 契約の flag
  束縛と品質欠測の分類、B / A 台帳と収束停止の不適用、重複の fresh 評価、random 生成器、sweep の hash 順 B 点、解析 consumer、較正・verify の
  job body 配線 (β の launcher 設計)。(β) 試走 = 1 workload (verifier 所要最短、read-heavy を避ける)・3 arm × 1 系列・16 session / arm + block stock 5
  = 60 論理 session 以下、retry は §3 どおり、主標本外・既知結果台帳へ。verifier wall (3 秒 × 5 rep + verifier) を実測して残す。(γ) 7 項のうち
  1・3・5・7 は v1 の記載どおり確認済み、2 は部分確認 (承認済み扱いにしない)、2 の残部・4 (費用上限)・6 (対象 commit) は試走後の本走認可で。
  発効 commit は本走認可時。
  base: cd71ba72f31d0cc590fdaed99426857c555ecb3da67755cbda2bf168a2d9b9ca
- [T-1872] **P3・裁定済み (D2172 項 4 (α)) → K2 共有部品は実装済み → 残部品の段階実装 (β の launcher 設計と同時)**: B-5 対照の実装対象 = 事前登録 §10
  の「実装が要る」部品。K2 と共有する 3 部品 (同 job 系列開始 stock (候補後の形)、較正動作点の CLI、exact correctness 経路) は本 wave で着地
  ({{D:k2-pair-launcher-stock-control}})。残 = session 契約の束縛、B / A 台帳と停止の不適用、重複の fresh 評価、系列開始 stock の planner 前配置、
  random 生成器、sweep の hash 順 B 点、解析 consumer。本走の認可は [T-2797] の試走後に諮る。
  base: c9c6c8ed348ba0a5a7d13ab49ebdf259ccb3fa9def80bdeb4e21ef3f924cda74
- [T-2632] **P2・裁定済み (D2120 項 5) → 条件待ち + 出所調査 (AI)**: 本 wave の成果は「不足報告 + 空 batch での発行器到達」までと認定。bootstrap 集合の
  定義と固定時点は適格な赤 precursor ≥ 1 を実際に扱う時点で裁定する (今は定義しない、carrier も台帳も作らない)。proposal・走行・参照点の対応証拠の
  出所は AI が現存資料で閉じられるかを先に確かめ、耐久 carrier や D39 決定 3 の変更が要ると分かった時点で別裁定。残る順序のうち **§5 の 2 欄 (校正済み
  PerfConfig / env_tag) は precheck 済み (2026-09-17、`output/insights/2026-09-17/t2632-b4-s5-precheck/`): 今日は記入できない。** 第一の理由は D1483 の
  順序 (§5 全欄は床値の 12 行裁定・測定・採用裁定の後。A-5 は D2120 項 4 で AI の手番になったが測定・採用裁定は未了)。順序が解けた後も、reps の出所
  (D2088 の 5 は床値 spec 用の AI 選択)、B-4 本走の site・契約世代 (g1 active / g2 未発効)・確認者の担当範囲の裁定が要る。**承認済み PerfConfig を
  base CLI が消費する経路の不在 (`default_perf()` 無条件) は 2026-09-20 に解消** — `p3_s4_loop` の `--calibrated-perf --perf-workload` で p2_2 の較正
  動作点を指定でき、identity に動作点が焼かれる ({{D:k2-pair-launcher-stock-control}})。B-4 marker との併用は未検証。tag `pegasus` の機械導出はできる。
  裁定パッケージ 4 項は同 README。通常 base campaign からの自然発生赤の回収は変わらない。
  base: d5548c02188f8c8f1b8bf0e1c0beb52feb1a5b6fb74c59f5a0a43a6c07c8bfa0
