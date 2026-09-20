# 段 1 brief (handoff からの写し、逐語)

## 段 1 brief (13:40 JST、起動 gate rc=0 の後)

- **研究前進:** 論文ストーリー 2026-09-20 §8 B-8「未取得」を、結果を見る前に固定した規則で取得できる状態にする (完了判定 = 事前登録 v1 が main に着地し、発効束が列挙されている)。B-8 の 3 要件 (対象・種・長時間) の paper-story 仕分けに対し、各要件の操作的定義を本文で固定する。
- **scope:** `docs/b8-final-candidate-longrun-verify-preregistration.md` (新規、v1、未発効) と `docs/README.md` の 1 bullet。実装差分ゼロ。発効・試走・本走・runner の実装・phase doc / paper-story の編集は含めない。仮想リスク向けの gate・検査・台帳・一般化は scope 外。
- **確定済み裁定 (引数):** B-5 (D2158) と同型の別 file。両対象案を択で並記し推奨を付ける。統計文は反例を作ってから書く。段 6 read-only review 1 本を残す (一次資料から不在・数値を書き起こす docs wave、DW-C00)。
- **段 1 実測 (一次資料):**
  - S-1 (iv 付属) の対象 = 系側 gate 構成 g_rl (balanced / read-heavy) / g_rt (write-heavy)。gate 述語は `output/s1-freeze/known_axes_freeze.json` (pin `d706650`、`frozen_at_head 2066ce6b4`) の `entries.<workload>.system_gate.gate_predicate` に逐語。S-1 の 24 verify 本走は実施されておらず、`output/reports/s1_direct_comparison/report.md` 冒頭が「本設計は独立な検証相を持たない」と明記。07-16 の校正 (cygnus、g_rl read-heavy 3 s = 433.3 s / 25.7 GiB、6 s = 974.7 s / 51.4 GiB、両方 serializable・certified) は `output/env/linux-baremetal/calibration/s1_verify_extime.json`。
  - S-1 freeze は `IZANAGI_FREEZE_HOLD s1-known-axes.ccbench-submodule-head-pin` (release = explicit-user-command-only) の下にある (pin が d706650 → 現行へ進んだため)。g_rl / g_rt の build は `axis_trigger_gating` の template patch + `s8a_trigger_sweep._genome(1)` 経路で freeze と独立。現行 pin への template patch は `patch -F0 --dry-run` で transaction.cc の全 hunk が当たる (hunk #10 は offset 13 行、Options.cmake は patch 形式の index 行で GNU patch が判定不能)。driver と同じ厳密適用 (git apply) と trace-enabled build・identity 導出は**未実測** → 発効前の試走条件。
  - 採用候補 2 genome (fixed-5 / fixed-10) は D2160 で 3 s × 8 反復 × 3 workload = 24 + 校正完走 6 = 30 verify / 候補 anomaly 0 (pass)。校正 6 s は 3 workload とも完走・anomaly 0 (read-heavy 807.8 / 864.3 s、maxrss 80.2 / 85.6 GiB、600 s 超で不適格)。10 s は balanced SIGKILL (2 node 再現、node DRAM ≈ 115 GiB)、write-heavy hard timeout 3600 s。本走実消費 6316 / 6134 S (24 verify、≈ 263 S / verify、verifier 平均 ≈ 230 s)。
  - CCBench ycsb の乱数: `include/random.hh` `Xoroshiro128Plus::init()` が `std::random_device` の 1 値 (32 bit) を s[0]、`splitMix64(s[0])` を s[1] にする。`YcsbWorkload` は worker thread ごとに `common/runner.hh` `worker_body` の stack 上に構築され、その constructor で `rnd_.init()`。CLI flag は `ycsb_rmw / max_ope / rratio / tuple_num / zipf_skew` のみで seed は無く、値は log にも出ない。S-1 事前登録 層 2 が「seed×N = 独立 N 反復、決定論的 seed 固定は導入しない (D16)」と登録済み。
  - roadmap §3.2: 検証相 = 最終候補に長時間 trace + 厳密検査、「報告するのは条件、seed、trace 規模、観測 verdict」、数値的信頼度へ変換しない。
  - verifier CLI: `--json --expected-commits --protocol --ccbench-root --lenient --max-report`。hard timeout 3600 s は D2160 runner 側の値。
  - 並行 wave `dev-wave-verifier-capacity` (13:16 開始、handoff は job dir) が 10 s 未完走 2 型の原因同定と省メモリ化を扱う。本 wave は docs のみで編集面は交差しない。本書は同 wave の成果を前提条件にせず、校正規則で吸収する。
- **不変条件:** 規律 1 (trace-enabled build の値を性能に使わない)、規律 2 (anomaly 1 件で即失格、再走なし)、規律 3 (anomaly は構造化して報告)、規律 7 (既存 certified 記録の昇格・降格なし、訂正は追記)、D1789/D1790 (発効後は bytes 不変・erratum・2 つの sha を別定数)、hash 自己参照禁止、pin 値の literal 再掲禁止 (check_docs)、docs 間の行番号参照禁止。
- **提案対象への provisional 裁定 (攻撃対象):**
  - (P1) 対象の推奨 = 案 A (g_rl / g_rt)。理由: paper-story 仕分け (1) は対象 ≠ S-1 最終候補を未取得の理由に数える → 案 B では 種・長さを満たしても B-8 にならない; S-1b 成立の変異はまだ独立検証相を持たない; 案 B は D2160 で 30 verify 済み。
  - (P2) 「種を変えた」= S-1 層 2 の登録定義 (各反復が新 process で自己シード、記録は rep-id・PID・開始時刻・argv・node・binary sha)。seed 注入は前提条件にしない (D16 の改変 + identity が候補と別 bytes になる)。paper-story 仕分け (2) がこれを認めるかは発効時のユーザー確認事項。
  - (P3) 「長時間」= 1 走の extime が開発相・D2160 の 3 s より長いこと (≥ 6 s) を必要条件、値は校正 {6, 10} s 昇順で決める (verifier wall ≤ 1800 s、未完走は indeterminate)。共通部分が空なら「候補なし」で本走を投入せず 3 s へ丸めない。系列長 (N 増) での代替は不採用 (単走内事象を捕まえない、仕分け (3) を満たさない)。
  - (P4) 費用: 6 s の見込みは fixed-5/10 の verifier 実測からの外挿 (≈ 3.6 h / 対象 24 verify)。g_rl / g_rt は commit 数が違うので校正で決め、本書は数値を予測として固定しない。
  - (P5) 判定 = D2160 項 3・5 を継承 (判定集合 = 本走 ∪ 校正完走 verdict、pass / 失格 / 未確定、本走未完走は同一 trace で 1 回再検証)。
- **成果物の形:** B-5 と同型 (§0 版と発効 … §N 本書が閉じないもの)、発効束、既知結果台帳 (D2160 の 6 s 校正 verdict と 07-16 校正を「結果既知」として本走標本から除外)。
- **DW-G05:** 放置時 = B-8 は登録経路の無い「未取得」のまま、paper §8 B-8 の値は変わらない。本 wave は certified 選択・台帳の値を変えない。
- **分割方針:** 軽量版 (段 2・3 省略)。親が docs を書き、段 6 で read-only review 1 本 (gpt-6-astra / medium)、fix、DW-O16 の焦点再レビュー。条件表 08/09/10/13: 08 不成立 (freeze に触れない)、09 = docs path の pin 検索で `docs/README.md` は LIVING_DOCS の lint 対象のみ・sha pin なし、10 不成立、13 不成立 (gate 新設なし)。
- **受入環境:** login node (docs のみ)。計算ノード job 0 件。
