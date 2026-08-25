---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1156-post-oracle-refetch-ban
seq: 3
---

## 新規

### {{F:argv-token-is-not-effective-value}}. 禁止 token を argv へ置いても実効値は環境から反転できた [恒真ゲート]

- 事象: 段 2 プランと親の段 1 brief は、configure argv に
  `-DFETCHCONTENT_FULLY_DISCONNECTED=ON` を exact 1 本置くことを禁止の実体としていた。
  段 6 の敵対レビューが「argv の本数検査は通るが実効値は OFF にできる」と指摘し、
  親が repo 外 probe で再現した。ambient な `CMAKE_TOOLCHAIN_FILE` が
  `set(FETCHCONTENT_FULLY_DISCONNECTED OFF CACHE BOOL "" FORCE)` を実行すると、
  `CMakeCache.txt` の実効値は `OFF` になり、**削除した source tree が再作成された**
  (再 populate が実際に起きた)。
- 根本原因: 「与えた入力」を「解決された結果」の証拠に使った。argv は要求であって実効値ではない。
  同型の誤りは D425 と D786 が masstree source root について既に潰しており、
  本 wave はその規律を新しい変数へ適用し忘れていた。
- 恒久対応: {{D:disconnected-effective-value}} — configure 後・build 前に `CMakeCache.txt` の
  実効値を読み exact `ON` でなければ拒否する。
- 再発検知: 変異 M03 (実効値検査の削除) を事前登録し、
  `test_v2_post_oracle_effective_disconnected_off_refuses_before_build` が KILLED で殺すことを
  実測した (本 wave の変異 matrix、baseline PASSED・6/6 KILLED)。
- 併せて実測した第 2 の恒真経路: CMake 3.22.1 では source が不在でも
  `FETCHCONTENT_FULLY_DISCONNECTED=ON` の configure は rc=0 で成功し source を再作成しない。
  flag は「材料が無いこと」を咎めない。禁止は izanagi 側の材料検査と対にして初めて fail-closed になる。

### {{F:dual-rule-empty-intersection}}. 同じ規則を 2 箇所で実装し、両方を通る入力が存在しなくなった [恒真ゲート]

- 事象: 本 wave の初版実装は、oracle 判定後の材料検査を build 側に独自実装した。
  build 側の inventory は `.git` を除外し、未宣言の archive を宣言の有無にかかわらず特例受理した。
  oracle 側 (`sort_swo_oracle._verify_dependency_root`) は `.git` 配下の regular file を含め、
  宣言集合と実在集合の exact 一致を要求する。**その結果、oracle を通る manifest は build 側で
  拒否され、build 側を通る manifest は oracle で拒否される** — 両 gate の受理集合の交わりが空。
  gate は存在するが決して成功経路を持たないため、保証としては恒真である。
- 根本原因: 「同じ規則」を 2 実装に分けた。片方だけを後から変えても機械検査が食い違いを教えない。
- 恒久対応: {{D:post-oracle-refetch-ban}} — build 側は独自実装を持たず oracle の検証関数を呼ぶ。
  同一関数であることにより「oracle が受理した直後の未変更の材料は build 側も必ず通る」が
  構造的に成立する。
- 再発検知: 変異 M02 (manifest 権威照合の削除) を事前登録し、
  `test_v2_post_oracle_rejects_self_consistent_rewritten_manifest_authority` が KILLED で
  殺すことを実測した。この負例は tracked file と `SHA256SUMS` の該当行を**同時に**書き換えた
  自己整合的な材料を使うため、per-file digest 照合だけでは通らない。

## 再発

### F24

- **再発: 2026-08-26** — 背景コマンドの偽完了を同一 wave 内で 3 回実測した (段 6 fix 子 1 回、
  変異 probe 2 回)。いずれも `.done` も成果物も無く producer は生存していた。
  **新しい事実は、偽完了が `tools/dev_wave_wait.py producer` に固有ではないことである。**
  ツールを使わない自前の待ちループ (`until [ -f <done> ]`) も同じく走行中に completed 通知を
  返し、うち 1 回は待ち手が自分の `echo` 1 行すら出力せずに終了した。したがって原因は
  待ち手の実装ではなく背景タスク層にある。恒久対応は既存の `DW-O01` (完了は `.done` と
  exit code だけで判定する) で足り、待ち手ツールの差し替えではない。
  本 wave では 3 点照合 (完了マーカー・成果物・producer の生存) が 3 回とも偽完了を検出し、
  実害はゼロであった。
