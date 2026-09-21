# 段 1 brief (v2、実測反映) — [T-2812] 旧系列 4 本の新 pin main への整合設計 (裁定パッケージ、実装 0 行)

- **研究前進:** 止めている研究 = 凍結 v2 g1 の W-4 / W-5 (8b oracle → certified 選択)。g1 は新 main (段階 4 の policy 照合) でも pin 前進直前 main `fec4a8187` (T-2810 修正を持たず journal で拒否) でも launch できない。完了判定 = 4 系列それぞれに「現状の拒否 (実測)・走れる経路・新 main 移行に要る ②③⑤ と source/admission・推奨・裁定を要する点」を名指しした裁定パッケージを insight に置き、g1 は実装 wave が着手できる粒度 (file:line・受理集合の変化・負例) で択を並べる。
- **scope:** 設計 + login の read-only 実測だけ。実装・reseal の実行・submit-tree への git 操作・gate / 台帳 / 一般化の追加はしない。依頼の「旧系列は pin 前進前の固定 checkout から走る」は変えない (事実との差は N1 として記すだけ)。
- **既裁定:** D2150 項 1 (②③⑤⑥⑧ は各新系列の着手時、⑨ 旧証拠保持)、D2184 (射程限定。却下 = policy 照合の除去・resolver の曖昧 fallback・**receipt の張り替え**・live への `expected_policy=None`・preimage からの `repo_stock_pin` 切離しは「必要なら別の裁定」)、D1777 (K2 の投入は submodule を PIN へ checkout してから。gitlink の差は commit しない)、D2187 (K2 pair 修復方向)、D2194 項 2 (K2 4 巡目の入力) / 項 4 (exact-63 成果物の再解析は現状維持) / 項 5 (g1 候補文書の削除、並走 wave)。逐語は `verbatim/`。
- **不変条件:** 規律 2 (正しさ gate・policy 照合を外さない)、規律 7 (記録済み判定・凍結 bytes・旧 lock / receipt は不変、新 main での拒否を過去の無効化と読まない)。submit-tree 3 本 (K2 pair / A-1 attempt-0002 / B-4 w1) は読むだけ。
- **実測 (login pegasus02、新 main `5efd69367`、gitlink = submodule = `e9e477ca`。probe = `evidence/probe-1.json`、親の CLI = `evidence/b4-*`, `evidence/g1-gate-check.json`。READONLY: 3 木の status・submodule HEAD・binary store が前後で不変):**

| id | 観測 |
|---|---|
| K2-PIN-NEW / -H | 新 main = `patchharness: HEAD (e9e477ca1b55) が pin (511c9538…) と不一致` / 経路 H (submodule だけ 511c) = **通る** |
| POLICY-CURRENT | 現行 policy sha `db6bc9ea…`、preimage の `repo_stock_pin` = `e9e477c`、registry = generator 7 種 / review 3 種 (`s1-known-axes`, `s8b-floor`, `s8b-oracle`)、`p3_s4_loop.PIN` と A-1 canonical はともに `511c9538…` |
| K2-LOCK-PAIR | **現行 codec が decode を拒否** (`authority.contract_loader_blob_sha256s の exact key 集合が不正`) = T-2344 の enforcement closure 63 → 85 (N7)。pin とは別 epoch |
| A1-BOUNDARY / SOURCE | 新 main = `CCBench login-submit: canonical HEAD mismatch` / `assert_pinned_clean` 不一致。経路 H = 両方**通る** |
| A1-IDENTITY | attempt-0002 の `result.json` の 3 workload の campaign identity preimage は `repo_stock_pin=511c953`、現行との差は**この 1 field だけ** |
| G1-LOAD / LAUNCH | loader 成功 (generation 1、sha `7e1114…`、G `32ba8cae4`) / launch = `[manifest-invalid] binaries[rr20::backoff_fixed_best] … 現行 policy と不一致` (cause `binary-admission`) |
| G1-BINARIES | 12 cell すべて class = **human-reviewed** (review_id `s8b-floor`、現行 registry に登載)、policy `949ddcc2…`、source `511c9538…`、protocol = `…--511c9538….json` (`ccbench_pin` 511c9538、contract `e576e9cd…`) |
| G1-BIN-HIST / CURRENT | 記録 policy で照合 = **12/12 通る** / 現行 policy = **12/12 拒否** (同一文言) |
| B4-PROTOCOL | `resolve_current_floor_protocol` = `current_count=2 head_exact_count=0` (候補 = anchor `d706650…` と versioned `511c9538…`、現行契約 `e576e9cd…`、HEAD gitlink `e9e477ca…`) |
| B4-RECORD-HIST / CURRENT | 記録 policy = 通る (class human-reviewed、review `s8b-floor`) / 現行 policy = 拒否。`place` も同文言で拒否 (書込み 0) |
| B4-W1-HEAD | w1 JSONL 3 本の `loaded_head` = `2ba40008…` = t2288 submit-tree の HEAD。新 main とは不一致 |
| POLICY-SERIES-PIN (probe-2) | 現行 preimage の `repo_stock_pin` を `511c953` (g1 protocol / `p3_s4_loop.PIN` / A-1 canonical の先頭 7 桁、3 者とも同値) に差し替え production の正規化 (`decode_historical_build_admission_policy`) で sha を取ると **`949ddcc2…` = g1 12 receipt の集合と exact 一致・B-4 record と一致・A-1 identity preimage 3 件と dict 一致**。対照 (現行 pin) は `db6bc9ea…` = 現行 policy sha、K2 pair lock の preimage と一致 → **S' の要求値は到達可能 (DW-O13)** かつ registry は g1 admission 時から不変 |
| K2-LOCK-PAIR (probe-2) | 現行 codec = 拒否、**歴史 codec (`decode_historical_campaign_lock`) = 読める**。lock の preimage は現行 policy と同値 (repo_stock_pin `e9e477c`) |
| READMIT-STOCK | 記録済み receipt に **stock-baseline は 1 件も無い** (g1 12 cell と B-4 は human-reviewed、A-1 は machine-generated、K2 候補は coder-authored)。再 admission の障害は class 導出ではない |

- **新事実:** N1 K2 は D1777 の手順 (gitlink 不変・submodule だけ PIN) で新 main から既に走っている (T-2795 pair、HEAD `6a3e158`、候補 certified)。N2 A-1 v3 も同じ経路で境界・source を通る (実測)。N3 g1 段階 4 の source pin は chain の protocol (511c) と照合し、現行に縛られるのは expected_policy だけ (12/12 の対比で確定)。N4 B-4 f1 の w2 / finalize は `loaded_head == HEAD` で t2288 submit-tree に固定。N5 `reseal_protocol()` の出力は `output/s8b-freeze/floor-protocols/` に入り B-10 grid の `EXPECTED_FREEZE_TREES_SHA256` を変える。N6 `build_admission.py` / `pin.py` は pin 前進後無変更 (registry 不変)。**N7 pin とは別に enforcement closure の epoch (T-2344) が旧 lock の live decode を止めている。**
- **(P1) K2:** 追加整合不要。D1777 経路を新 main での正規経路とし、③ PIN は系列の比較可能性のため `511c9538` 据え置き、② campaign ID の epoch 変化は T-2795 どおり受容。未実測は stock arm の admission (pair 再投入で初実測)。旧 lock の再消費は N7 で別途不可 (新 campaign なら無関係)。
- **(P2) A-1 sized v3:** 経路 H で境界は通る (実測)。同 study の attempt 間で campaign identity の `repo_stock_pin` だけが変わる。既定を経路 O (fec4a8187 submit-tree) と経路 H のどちらにするか、H で identity が変わることが study の「独立再現」に与える意味を裁定点にする。
- **(P3) g1 live launch (本題):** 段階 4 を塞いでいるのは policy epoch だけ (12/12 実測)。択 S' = live の期待 policy を「現行 registry + chain protocol の pin」で組み直す (registry の失効は残る。`expected_policy=None` でも receipt 流用でもない。D2184 が「別の裁定」とした `repo_stock_pin` 切離しの consumer 限定版) / O' = `fec4a8187` + T-2810 修正移植 + 候補削除の別 branch / N = 新 pin の新世代 (reseal・再 build・official 床値再測・再凍結・批准)。S' の要求値は到達可能と実測済み (`POLICY-SERIES-PIN`、`949ddcc2…` に exact 一致)。W-5 の live consumer (oracle driver の binary 消費ほか) を全数で洗う。
- **(P4) B-4 床値:** f1 の w2 / finalize は t2288 submit-tree のまま (整合不要、窓は 09-29〜10-07 UTC)。新 main での新 campaign は新 pin 系列 (⑤ reseal + 再 build + A-5 再凍結 + B-10 freeze-tree pin 更新) になり、旧 binary の再配置は place が現行 policy で拒否する。
- **(P5、訂正) 再 admission:** 障害は class 導出ではない (stock-baseline は 1 件も無く、review_id は現行 registry に載っている)。旧 binary に新 policy の receipt を出し直すと receipt bytes が変わり、manifest → floor_source → 批准世代の sha 束縛が崩れる = D2184 が却下した「receipt の張り替え」に当たる。ゆえに「再 admission だけでは解消しない」は実測で裏付く。
- **成果物:** insight `output/insights/2026-09-21/t2812-old-series-realignment/README.md` (系列 × 経路の表、実測、択と推奨、裁定を要する点、実装 wave への申し送り)、`evidence/` (probe 出力。holdout の spec 内容・JSONL 本文は写さない)、`verbatim/` (依頼・brief・plan・相談・probe の逐語は .md)。spool worklog fragment 1 本 (+ 親判断が要れば decisions 1 本)。
- **分割:** 段 2 plan codex 1 本 (系列ごとの設計を file:line で)、段 3 相談 2 本 (sol = 正しさ境界・規律 2/7・S' の失効性、luna = 既裁定整合・scope・費用)。段 4 で「実装しない」→ 4→7→8→9。docs-only だが一次資料から事実を再抽出するので段 6 の独立 read-only レビュー 1 本は残す (DW-C00)。
- **受入・実測環境:** 実測 = login pegasus02 (read-only、probe は Codex author 製で repo 外、sha256 `db193956…`)。受入 = 記録 commit の tip で待ち手経由の全走。
