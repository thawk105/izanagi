---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-07
wave: dev-wave-t2320-backoff-sweep-gate-layer2
seq: 2
---

## {{D:backoff-sweep-gate-prebuild-in-gate-context}}. backoff 系 driver の条件関門は関門文脈で masstree を 1 度 prebuild し、同じ base を関門へ渡す — compiler 入力の閉包までは束縛しない

**決定:** `backoff_sweep.run_workload` と `backoff_extended_sweep.run_workload` は、patched root を
canonical 化したうえで、一時 base に対して `buildcache.prepare_masstree_fetchcontent` を 1 度呼び、
同じ base を `-DFETCHCONTENT_BASE_DIR=<base>` として `_require_backoff_condition_gate` の
`configure_args` に渡す。helper は `configure_args` を `capture_define_inputs` へ素通しするだけで、
判定式・受理集合・既定値・stock 比較・meaning arm は変えない。一時 base は関門の直後に閉じる。
不変条件は A-2 (`paper_story_a2_certification.py`) と同じ「検査する木と build する木は同じ patched source 木」
であり、**関門が見た masstree `config.h` と計測 build が使う `config.h` の bytes 同一性は束縛しない。**
この限界は成果物 (`output/insights/2026-09-07_t2320-backoff-sweep-gate-layer2/README.md` §8) に明記する。
他 4 呼び手 (`backoff_overthrottle` / `backoff_profile` / `backoff_requested_us` / `backoff_repro`) は
既定値のままとし、実測経路になった時点で同じ形を入れるかを裁定する。

**理由:**
- 第 2 層 (masstree `config.h` 不在) は、関門の supply arm が configure しか行わず、CCBench が build 時
  custom target で生成する header が build tree に無いことによる。関門文脈で 1 度 prebuild すれば
  関門の preprocess は実物の header を読む。A-2 経路で同じ形が実測済みで、本 wave の生死確認 (計算ノード) と
  実 job 5 本で第 2 層は消え、第 3 層 (D1611) が backoff_sweep 経路で初めて実測された。
- `config.h` は同一 pin・同一 toolchain から生成される第三者 header で、backoff の供給・意味には関与しない。
  閉包 hash の束縛は新規 gate・一般化に当たり、依頼の scope (関門を通す修正と再投入だけ) の外である。
  A-2 先例も同じ限界を持つので、恒久設計は裁定パッケージとしてユーザーへ返す。
- prepare の所要は計算ノードで 20 秒程度 (実測) で、関門 1 回あたりの追加費用として許容できる。
  timeout 900 / 900 秒は A-2 と同値を採る。

**却下した選択肢:**
- 関門の supply arm を「`config.h` が無ければ preprocess を skip する」形に緩める — 関門を通すためだけの
  修正で偽の緑を作る (規律 2)。不採用。
- 関門と計測 build で同じ FetchContent base を共有し bytes を束縛する — buildcache の claim / publish
  契約と site gate に触れる設計変更で、本 wave の scope 外。裁定パッケージへ。
- 他 4 呼び手にも同時に入れる — 実測経路でない driver の変更は本 wave の依頼にない。
