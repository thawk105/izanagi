---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2637-offrepo-scan-yield
seq: 1
title: [T-2637] 到達不能監査の repo 外走査の収量を実測し、並列化を先に置く 2 段の設計を決めた — 親の測定誤りを敵対検証が 3 件倒した (docs のみ、branch worktree-dev-wave-t2637-offrepo-scan-yield、実装面の差分ゼロのため変異 matrix 免除)
---

## 本文

- **抑止の実収量を台帳と実走で確定した。** 2026-08-09 = 2 対、2026-08-25 = 7,050 対、
  2026-08-26 = 292 対、2026-09-15 = 0 対、**2026-09-16 の実走も 0 対** (要確認 30 commit / 53 対、
  bytes 一致 17 file・23 対)。7,050 と 292 の差は D957 の build cache 除外で説明がつくが、
  **292 → 0 は説明できない** (同じ走に抑止 292 対と除外 13,488 対が併存していた)。
  原因未確定として記録した ({{D:offrepo-scan-yield-cause-undetermined}})。
- **親の測定が誤っていた。** `parent-measurements.md` が「C 実装・並列で cold 1583.99 秒」と書いたが、
  `/usr/bin/time` 越しの `find` はシェル関数 (bfs の shim) を迂回して GNU findutils 4.8.0
  (単一 thread) を呼んでいた。**並列は一度も測っていなかった。** 段 3 の両レンズが
  「言語・syscall 形態・並列度が混ざっている」と指摘したのは正しく、実際には混ざってすらいなかった。
- **測り直すと並列は効いた。** 探索根全体 1,761,075 file の warm 走査で、単一 thread 3 走
  230.29〜252.51 秒 (最大/最小 1.10) に対し 16 thread は 43.78 / 66.67 秒。保守的に 3.8 倍、
  平均で 4.4 倍。**D985 の「16 thread で改善 20%」は Python 実装の性質であって、
  この filesystem の性質ではない。** 順序は単一→並列→単一→並列と交互にし、
  単一 thread が悪化していないことで cache 押し出しの交絡が支配的でないことを確かめた。
- **採る案は 2 段にした。** 第 1 段は並列化 (範囲・規則・出力を変えない定数削減、D2034 の順序)。
  第 2 段は用途分離 (掃除では走査 off、救出 triage では full)。設計判断は
  {{D:offrepo-scan-parallel-before-scope}}。cold へ外挿すると第 1 段だけでは監査全体 387〜531 秒で
  D958 の 300 秒に入らない公算が高いが、**cold の並列は測っていない**ので外挿である。
- **親が推していた候補先行案は不採用にした** ({{D:offrepo-candidate-first-not-equivalent}})。
  抑止条件 5 の構造から被覆部分木は dir 数で 13.1% (7.6 倍の縮小) に絞れ、bytes 一致 17 file が
  いずれもその外にあることで監査自身の `suppressions=0` と一致した。しかし段 2 と段 3 が
  厳密等価の反例を 4 型示した — hardlink の owner/alias 交差、hardlink 代表の交代、
  中間 directory symlink、境界 byte を含む path・探索根。**後ろ 2 つは抑止を増やす方向**で、
  不変条件「抑止を広げない」に直接違反する。
- **敵対検証が親の主張を 3 件倒した。** (i)「抑止は構造的にほぼ 0」— main に land 済みの
  `orchestrator/manual_probes/test_t2397_a1_source.py` が job dir path を引用符で囲んで書いており、
  引用符は D248 の境界 byte なので祖先条項が成立する。親自身の被覆データでも同 dir が最大
  (59,723 file) だった。(ii)「D985 の対処は台帳から消えた」— `docs/phase3.md` に D205 で active から
  除外した保留記録と再訪条件がある。正しくは**保留記録あり、実施証拠は未確認**。
  (iii)「これで掃除が回る」— 掃除 98 分の内訳は監査 42.4 分・worktree 68 件の差分検査 14.4 分・
  救出検査 12.6 分・`git cherry` 約 10 分・撤去約 9 分で、監査を 0 にしても約 56 分残る。
- **走査が買っているものが入れ替わった。** 掃除が走査から得ているものは実質ゼロだが、
  `unreferenced_copies` の注記 17 件には実在の consumer がある。ただし機械 consumer ではない —
  `tools/check_branch_rescue.py` は commit 集合・rc・所要しか読まず、D970 の外部控え分類はしない。
  消費しているのは破棄・救出を分類する人・AI の triage である。
- **副産物として実在の欠陥を 4 件見つけた。** (a) 境界照合の helper 2 つ
  (`_has_bounded_path_reference()` と `_bounded_path_reference_matches()`) が、path 内部に
  境界 byte を含む場合に既に非等価。(b) hardlink の alias 全配布が D247 条件 2 (basename 一致) の
  穴になっている。(c) `tools/check_branch_rescue.py` が監査を子プロセスで再実行するため、
  既存の root 環境変数がある環境では掃除 1 回で全走査が 2 回走りうる。(d) 並列実装を静的に禁じる
  `test_initial_patch_contains_no_parallel_execution` が存在し、D985 の結論がテストとして
  固定されている。**いずれも本 wave では直していない。**
- **実装していない。** ユーザー指定の成果物が「収量の実測と、採る案の設計」であり、採る案が
  D985 と衝突するため。実装面の差分がゼロなので変異 matrix は免除した (`DW-S04`)。受入全走は行った。
- 工数: codex 子 3 本 (plan 1・consult 2、いずれも gpt-6-astra / medium、すべて read-only)。
  親の計測は監査 1 走と走査 6 走。
- 一次資料 = `output/insights/2026-09-16/t2637-offrepo-scan-yield/`
  (段 1 brief、親の実測 3 通、段 2 プラン、段 3 の 2 レンズ、段 4 裁定)。

## 次の一手差分

### 更新

- [T-2637] **P2・裁定待ち**: 到達不能監査の repo 外走査の収量を実測し、2 段の設計を決めた
  ({{D:offrepo-scan-parallel-before-scope}})。**D985 は並列化と索引化を却下しており、
  第 1 段の並列化はその射程の限定と、並列実装を静的に禁じる
  `test_initial_patch_contains_no_parallel_execution` の改訂を伴うため、ユーザー裁定を要する。**
  裁定パッケージは一次資料の README §5。
  base: 57a7d4370fd5ecfeb5314a0f2b70c3e59f7a69b4f81b2121818fb5fa069000b0

### 新規

- {{T:offrepo-scan-parallel-walk}} **P2・新規**: `tools/audit_dangling_commits.py` の repo 外走査を
  並列化する。C 実装の warm 実測で 3.8〜4.4 倍。範囲・規則・出力を変えないので受理集合の議論は要らない。
  先行して (a) Python の thread pool で同じ倍率が出るかを小さい prototype で実測し、
  (b) cold の並列倍率を間隔を空けた別日か別 node の 1 走目として取る。
  `test_initial_patch_contains_no_parallel_execution` の改訂裁定が前提。
- {{T:offrepo-scan-purpose-split}} **P2・新規**: 掃除では repo 外走査を明示 off にし、
  救出 triage では full を走らせる用途分離。`findings(full) ⊆ findings(off)` なので findings は
  減らない。付ける条件 5 件 (未実施と否定結果の分離、台帳通知が増えることの開示、
  D970 / D1031 を新規 commit への一般的破棄許可にしない、off/full の入口と実行主体の固定、
  子プロセス環境 allowlist の同時修正) は一次資料の README §5 にある。
  {{T:offrepo-scan-parallel-walk}} の実測後に着手する。
- {{T:bounded-reference-helper-divergence}} **P2・新規**: `_has_bounded_path_reference()` は出現の
  左右だけを見るが、本番の `_bounded_path_reference_matches()` は探索根末尾から最初の境界までを取る。
  path 内部に空白・改行・括弧を含む候補で両者の判定が割れる。どちらが D248 の意図かを決めて揃える。
  **helper 側へ揃えると抑止が増えるので、向きの裁定が要る。**
- {{T:rescue-gate-double-offrepo-scan}} **P2・新規**: `tools/check_branch_rescue.py` は監査を
  子プロセスで再実行し、環境変数 `IZANAGI_DEV_WAVE_JOBS_DIR` を継承する。既存の root 指定がある
  環境では掃除 1 回で全走査が 2 回走りうる。実測で確かめて、要否を決める。
- {{T:hardlink-alias-basename-hole}} **P3・新規**: 候補集約は `(OID, device, inode)` ごとに
  owner と alias を集め、比較成功時に全 owner へ全 alias を配る。異 basename・同 OID・同 inode の
  owner に参照済み alias が配られるため、D247 条件 2 (basename 一致) の穴になっている。
  安全側 (抑止を広げる側) の穴なので急がないが、条件 2 の意味を保つなら塞ぐ。
