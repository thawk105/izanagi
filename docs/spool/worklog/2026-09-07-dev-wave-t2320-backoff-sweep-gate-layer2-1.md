---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-07
wave: dev-wave-t2320-backoff-sweep-gate-layer2
seq: 1
title: [T-2320] backoff_sweep 経路の条件関門 第 2 層を A-2 と同じ形で直し、A-5 と T-2266 tail を実測した — 関門は 5 job すべてで通過、第 3 層は初実測、T-2266 は 8 点完走 (コード + テスト + 実測、branch worktree-dev-wave-t2320-backoff-sweep-gate-layer2、変異 7/7 + 2/2 KILLED)
---

## 本文

- **ユーザー指示**: 第 2 層 (masstree `config.h` 不在) を A-2 経路と同じ形で直し、着地前に同じ wave で
  A-5 2 job と T-2266 tail 3 job を実測する。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
  段 3 の findings と段 4 裁定を提示した時点でユーザーが「go」と承認した (2026-09-05)。
- 実装は Codex author (`gpt-5.6-sol`、`reasoning=xhigh`) が 2 巡。1 巡目 `0ade09d5e` が本題の 8 file、
  2 巡目 `2177b85aa` が実走で露出した T-2266 report 生成の欠陥 2 file。敵対レビューは各巡 2 本
  (1 巡目 A=GO / B=NO-GO → fix で closed、2 巡目 A=GO / B=GO、must-fix なし)。
- **段 4 で real と裁定しながら不採用にした所見**: 関門の一時 base の masstree `config.h` と計測 build の
  `config.h` は bytes 同一性を束縛しない (A-2 経路も同じ限界)。閉包 hash の束縛は新規 gate に当たり
  ユーザー scope の外なので、裁定パッケージへ回した。
- **段 6 を終えた後に段 5・6 をもう 1 巡した (DW-O12 の逸脱)**。T-2266 tail の 2 回目が 8 点全部を計測した
  直後に `materialize_t2266_report` で決定的に落ち、依頼 (b) の rep 単位 abort 率がこの report 経由でしか
  得られない (rep 値は driver process の memory にしかなく WAL に残らない) ことが判明したため。
  補遺裁定は job dir の `ruling-addendum-1.md`。
- **失敗**: 同じ checkout から A-5 2 job と T-2266 3 job を同時に走らせ、先に終わった A-5 job の
  `git worktree prune` が共有 submodule gitdir 上の他 job の登録を消して 4 job を巻き込んだ (F251 の再発)。
  A-5 投入器は同じ checkout から 2 job を出すので後に終わる job が必ずこの経路で落ちる構造である。
  09-02 / 09-04 は関門で先に落ちていたため顕在化していなかった。
- **A-5 は D1525 に従い未充足のまま**である。2 job (bnode059 / bnode061) とも 8 genome を計測し
  全点 serializable だったが、Pegasus の結果を D1100 の別 boot 再現と読み替えない。
- 素材: 静的 backoff tail の 750 µs と 999 µs を初めて測った。3 workload とも 150 → 999 µs で
  throughput・abort 率が単調に下がり、谷は無い。既測 4 点は 2026-08-26 の値と 0.5% 以内で一致する。
  rep 単位値の正本は `output/insights/2026-09-04_t2266-backoff-static-tail/README.md` §8。
- 設計判断は {{D:backoff-sweep-gate-prebuild-in-gate-context}}、失敗は F251 の再発追記。
  経緯と限界は `output/insights/2026-09-07_t2320-backoff-sweep-gate-layer2/README.md`。
- 工数: Codex 子 8 本 (plan 1、相談 2 + やり直し 1、author 2、review 4、fix 1)。
  計算ノード job は A-5 2 本、T-2266 tail 9 本 (3 回 x 3 workload)、生死確認 2 本 (1 本目は
  queue-wait-timeout の infra 失敗)、変異走 4 本。

## 次の一手差分

### 完了

- [T-2320] `backoff_sweep` 経路の第 2 層を A-2 と同じ形で直した。関門文脈で
  `buildcache.prepare_masstree_fetchcontent` を 1 度呼び `-DFETCHCONTENT_BASE_DIR` を
  configure_args で渡す。検査する木と build する木は同じ patched root。生死確認 (計算ノード) と
  実 job 5 本で第 2 層の消滅を実測し、変異 7/7 KILLED で検出力を確かめた。
  remaining: none
  base: f15e39b167c9f7cd89ac3dee28b48942701ca87c4ea44b2371eb8f4b6887bd75

- [T-2211] A-5 の別 boot 再取得を走らせ、条件関門を通り切ることを確認した。2 job とも 8 genome を
  計測し全点 serializable。第 3 層 (D1611) が backoff_sweep 経路で初めて実測され、inert 比較は
  `stock-inert-preprocess-root-location-only` の緑になった。**A-5 は D1525 に従い未充足のまま残す。**
  remaining: none
  base: 85d389117422e37a375e2d2dbe10da928ce60ae3f5a7b96ba42c366bf9095599

### 更新

- [T-2266] **P1・測定完了 → 解析待ち**: 8 点格子 (none + adaptive + 固定 150/200/300/500/750/999) を
  3 workload とも同一 job 内で完走させ、rep 単位の throughput と abort 率を取得した
  (2026-09-07、job 979843 / 979844 / 979845、`status: complete`)。750 と 999 µs は初測定。
  値は `output/insights/2026-09-04_t2266-backoff-static-tail/README.md` §8。
  **1000 µs は F718 により依然測定不能で、999 は代替であって 6 点目ではない。**
  残るのは T-2216 の歩行 model を実測 tail と rep 単位 abort 率で再計算すること、および機序の直接観測
  ([T-2265]) である。
  base: def6eb4dd4a52d1cef212eedfb3e16780c38b84a582a3b9afdfc4b73fa6051ac

### 新規

- {{T:a5-submitter-shared-checkout-prune}} **P2・新規**: A-5 投入器 (`tools/pegasus/submit_a5_second_boot_backoff_sweep.sh`)
  が同じ checkout から 2 job を出し、job 本体の終了処理が共有 submodule gitdir へ
  `git worktree prune --expire now` を打つため、**後に終わる job と同居する他 job が必ず落ちる**。
  workload ごとに checkout を分けるか、prune を自 path の `worktree remove` に限定するかを決める。
  `tools/pegasus/admission_registry.json` の登録簿と F660 に触れる。B-10 の 3 job も同じ gitdir を
  共有しており、remove が失敗した job が prune へ落ちれば同型が起きる。

- {{T:condition-gate-compiler-input-closure}} **P2・新規・ユーザー裁定待ち**: 条件関門が見た第三者生成 header
  (masstree `config.h` 等) と、計測 build が使う同 header の bytes 同一性を束縛するかを決める。
  現状は同一 pin・同一 toolchain から生成されるが束縛はしておらず、A-2 経路 (`paper_story_a2_certification.py`)
  にも同じ限界がある。束縛するなら buildcache の claim / publish 契約と site gate に触れる。
  併せて、条件関門の他 4 呼び手 (`backoff_overthrottle` / `backoff_profile` / `backoff_requested_us` /
  `backoff_repro`) に同じ prebuild を入れるかも決める (現状は第 2 層が未修正のまま。実測経路ではない)。
