# 段 1 brief — silo-intra-txn-fix-line (md_12)、2026-09-30 12:25 JST

- 研究前進: gen-opt の certified の前提 (Silo の取引内の値の照合 D2b が全 key で 0 件) を CCBench 本体へ入れる経路の最後の AI 手番。完了 = branch `izanagi-silo-intra-txn-fix` の新 tip が上流 CI 相当 (format・build) 緑、D297 (b) を取り直した結果、U0 照合器で D1・D2b 0 件、push 依頼文が一次資料にある。
- 確定裁定: D2305 項 5 (択 B) — `7e5fa528` の上に update より後の `#line` 4 本 (635/658/679/700) を各 +3 する 1 commit。CCBench 側は Codex author、上流 CI (build・clang-format 14) を通す。(b) の一致は予測。push は人間 (D2305 項 6)。
- 実測した前提: 主 checkout の submodule (wave 木の origin) で `refs/heads/izanagi-silo-intra-txn-fix` = `7e5fa528037805dfc0459c742e4a21d6114c9799`。tip の `#line` はファイル 669/701/731/755 行に 635/658/679/700 (変化なし)。F→tip の差は read の hunk が行数 ±0、update の hunk が +3 (530 行付近) で、`#line 365/381` は update より前なので対象外。D297 検査器 sha256 `bcd46b29…` は前回 (`8fe87f852`) から変更なし。local main `4f412c67b`、gitlink C `68106660` のまま。
- scope: `cc/silo/transaction.cc` の `#line` 4 本の数値だけ (635→638、658→661、679→682、700→703)。他の行・他 file は変えない。
- 不変条件: gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN`・`patches/` は変えない。branch は fast-forward でだけ進める (force なし)。push しない。変異を外して緑にしない (規律 2)。
- (P1) 親の provisional 裁定・攻撃対象: 新 tip の TRACE=0 は pin + 修正 (合成 P′ `d078f0f0`) と一致する見込み。login の行番号 probe で先に予測を取る (P′・新 tip とも `IZ_ERR_AT(693)`)。前回の検査器は最初の不一致で止まったので、Silo 以外・他文脈の差の有無は未確認 (予測の穴)。
- (P2) 事前登録 D297: (b) 合成 P′ → P‴ (親 P′、tree = 新 tip の tree)、header 4 引数、`--expect-paths` なし、GCC 11・12 → 期待 rc=0 両方。(a) F → 新 tip (`--expect-paths cc/silo/transaction.cc`) → 期待 rc=1 両方、Silo の正規化前処理の不一致 (参考、安価)。結果を見て基準を変えない。
- (P3) 事前登録 trace (前回 R5 と同じ): 対照 F は D1 0・D2b 違反 ≥1、新 tip は D1 0・D2b (i)(ii) 違反 0 かつ各発生条件 ≥1・判定器 certified・取引数 = commit 件数。
- (P4) 上流 CI 相当: format = 新 tip の clean checkout で login clang-format 14.0.0 と image :latest (14.0.6) の `--dry-run --Werror`、build = 計算ノードで image :ci の CI 手順。
- (P5) commit: file 変更と英語 message は Codex author、commit は親 (`commit -F`)。trailer 3 行 (Codex author・Codex reviewer・Claude manager、前回と同形式)、commit 直前に段 4 裁定と行単位で照合 (F1040)。
- 計算見積り: CI build 約 30 秒 + (a) 約 20 秒 + (b) GCC 11・12 各約 970 秒 (2 ノードへ分割) + trace 約 200 秒 → 合計 約 0.6 node 時間 (2 node 時間の線の下)。
- 成果物: 新 tip (commit のみ)、`output/insights/2026-09-30/silo-intra-txn-fix-line/README.md`、spool worklog fragment ([T-2905]・[T-2885] 更新、[T-2917] の前提書き直し)。
- 分割: 段 2 省略、段 3 read-only 相談 1 本 (計算で数値を書く wave の先例)、段 5 author 1 本 (#line 編集 + message 下書き + 前回 script の親 OID 固定を引数化した v3)、段 6 review 1 本 → fix → commit → 計算 3 job。
- 受入・実測環境: 計算は `tools/pegasus/dispatch_compute.py --task generic` (bnode)。repo の差分は insight と spool だけ (知識面) なので land は縮小受入の対象か段 9 前に確かめる。
- 条件 dispatch: DW-O08/O09/O10 (freeze・凍結成果物・proof chain) は非成立 (検査器・凍結物に触れない)。DW-O13 (gate 新設) 非成立。DW-O11 (削除) 非成立。
