---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-17
wave: dev-wave-t1262-submodule-identity
seq: 2
---

## {{D:submodule-raw-bytes-identity}}. submodule の内容同一性は生 bytes で照合する

**決定:** snapshot oracle が initialized submodule に要求するのは
「worktree の bytes が pin された commit の canonical checkout の bytes と 1 byte も違わないこと」
とする。照合は git を起動せず `sha1(b"blob <len>\0" + bytes)` を index の blob id と突き合わせて
行う。canonical checkout から逸脱した bytes を生みうる attributes と config
(`filter.*` / `core.autocrlf` / `core.eol` / `core.fsmonitor` / `include.path` 等) は、
内容照合より前に local config の key 名 allowlist で fail-closed に拒否する。

**理由:**
- gate が守るのは「試行が実際に読んだ bytes が pin どおりか」である。clean filter を通した
  等価性ではこれを測れない。
- clean filter 適用後の hash 比較は、改行コードを一括変換した worktree を受理してしまう。
  生 bytes 照合は拒否する。
- clean filter 適用後の hash 比較は外部 clean driver を起動しうる。封緘済み snapshot の中で
  未検証の外部 program を走らせることになる。生 bytes 照合はどんな filter も起動しない。
- 検証側の config で結果が変わらない。同じ木が環境によって受理・拒否に割れない。
- 偽の拒否が出ないことを実測した。実 snapshot が使う CCBench pin を `--no-local` clone して
  新規 checkout し、index の 404 非 gitlink entry を照合したところ不一致は 0 件、mode 不一致も
  0 件、object format は `sha1`、全件 sha1 の所要は 0.124 秒だった。

**却下した選択肢:**
- **path-aware hash (`git hash-object` で clean filter 適用後の blob id を比較)** — 段 2 の
  プランが推した案。上記のとおり受理集合が緩く、外部 program を起動しうる。
- **`git diff-files` による stat ベースの判定** — size と mtime を保つ改変を見逃す。
  また index の stat cache が有効な構成では発火しない。
- **`git write-tree` で index の tree を作って `HEAD^{tree}` と比較** — 封緘済み object store に
  ref から到達不能な tree object を書き、後続の `git fsck --unreachable` を内容 gate とは別の
  偶発理由で赤くする。

## {{D:submodule-gate-oracle-bytes-unchanged}}. 内容照合の追加で oracle の bytes を変えない

**決定:** submodule の内容同一性 gate は拒否だけを行い、snapshot oracle の document へ
field を 1 つも追加しない。三者照合が通った事実は成果物に保存しない。

**理由:**
- `_replay_manifest` は保存済み oracle の canonical bytes との完全一致を要求する。
  oracle の bytes を変えると過去 manifest の replay が壊れる。
- `submodule_manifest_sha256` を保持する成果物は repo 外の wave 成果物配下に 293 件ある。
  bytes を変えるとこれらの参照を一斉に失効させる。
- 変更前の実装と現実装で、同一の絶対 path に決定的な合成 snapshot を構築して比較した結果、
  oracle の canonical bytes は 917 bytes で完全一致し、key 集合・`submodules` 行・
  `submodule_manifest_sha256` も一致した。この不変は実測で確かめてある。

**却下した選択肢:**
- **三者照合の証拠を manifest の submodule 行へ記録する** — proof chain の証拠力は上がるが、
  正常な snapshot の `submodule_manifest_sha256` と `manifest_sha256` が変わり、
  凍結済み schedule と保存済み manifest の再発行が必要になる。証拠力の向上は
  変異検出力の向上を伴わない (照合そのものは gate が既に行う)。

**残る限界を明記する:** 本決定により、proof chain には「どの照合が通ったか」が残らない。
残るのは「通らなければ oracle が生成されない」という fail-closed の事実だけである。

## {{D:submodule-config-allowlist-seal-boundary}}. config allowlist は封緘の前後で厳しさを分ける

**決定:** snapshot と全 initialized submodule の local config は key 名の allowlist で検査する。
封緘後 (認証側) は `core` の静的 5 key + filesystem probe 3 key だけを許し、
封緘前 (builder 側) に限って `remote.*` / `branch.*` / `submodule.*` の transport 系を追加で許す。
外部 program を起動しうる key は封緘前でも拒否する。
**source root repository には適用しない。**

**理由:**
- 認証の境界は封緘処理ではなく `verify_snapshot` である。封緘処理は自分で config section を
  消す前に repository を列挙するため、そこへ封緘後用の厳格な判定を当てると、まだ正当に残って
  いる transport 設定で必ず落ちる (実測: 計算ノードで 66 node が失敗した)。
- source root には `user.*` と `extensions.worktreeconfig` が正当に存在する。ここへ allowlist を
  掛けると worktree ベースの build がすべて落ちる。source root は本 gate の信頼境界の外であり、
  destination の bytes は source の object database から fresh checkout され、destination 側で
  生 bytes 照合される。

**却下した選択肢:**
- **封緘前後を区別せず一律に厳格** — 実 builder が落ちる (実測済み)。
- **source root にも allowlist を適用** — 段 6 の敵対レビュー A が要求したが、同じ段の
  敵対レビュー B の実測が反証した。裁定パッケージへ回した。
- **denylist (禁止 key の列挙)** — 列挙漏れが fail-open になる。allowlist は未知 key を
  fail-closed で拒否できる。
