---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-12
wave: dev-wave-t748-pilot-path
seq: 6
---

## {{D:attestation-tool-name-is-provenance}}. 取得方法の名前は provenance であって判定に使わない

**決定:** attestation の `effective_clock.method` を verdict の算出から外し、
expected / observed は comparison 行に残す。receipt の消費側 (`execution_guard`) の
独立再計算も同じ扱いに揃える。**物理量の判定は一切変えない** —
`samples_mhz` の許容幅つき比較、`governor`、CPU model、TSC、cache / NUMA / core 数は従来どおりである。

**理由:**

- ユーザー裁定 (2026-08-12): 「ソースコードがこれの時に測定しましたみたいな厳格な一致リストや
  保証みたいなのまではいらない」「参考情報でいい」。
- `method` は環境の性質ではなく**取得実装の名前**である。probe を改良すると文字列が変わり、
  **過去に登録した calibration が構造的に attestation を通れなくなる**。
  実測: 第 1 世代は `proc-cpuinfo`、第 2 世代と現行 probe は
  `proc-cpuinfo-rotating-min/k5/...`。**クロックの実測値は両世代とも 2101.0 MHz で一致**しており、
  機械は同じである。
- 守るべき量 (実効クロック) は許容幅つきの比較で別途守られている。
  道具の名前の一致は測定の公正に寄与しない。

**却下した選択肢:**

- 世代交代を先に通して第 2 世代で測る — floor protocol と予測封印の作り直しを伴い、
  「第 1 世代のうちに測る」という既存裁定と衝突する。
- probe に旧 method の再現能力を持たせる — 改良前の劣る手順をわざわざ再現することになる。
- 登録済み calibration の bytes を書き換える — 凍結成果物の改竄であり採らない。

## {{D:site-resolved-compiler-is-required-argument}}. site 解決した compiler は必須引数で通す

**決定:** 実体化経路 (`prepare_cell` → `source_digest.resolve`) の `cxx` を
**必須のキーワード引数**にし、共有 materializer を使う floor / oracle / S-1 の 3 経路すべてで
site 解決済みの値を渡す。`source_digest` 側の既定値は変更しない。

**理由:**

- 既定値 (`g++-13`) のままの呼び出しが 1 箇所取り残されており、その compiler が存在しない
  環境で fails-closed で停止していた。実測: 床値 campaign が
  `source_digest: マクロ定義状態の照会を起動できない (g++-13: No such file or directory)` で停止。
- **既定値を書き換えて回避してはならない** — どの compiler で照会したかは identity に効く。
  呼び出し側が明示的に渡すのが正しい形である。
- 必須引数にすれば、同じ取り残しが**再び起きたときに黙って既定値へ落ちず、その場で壊れる**。

**却下した選択肢:**

- 既定値を site 解決へ変える — 呼び出し側が何も指定しなくても動くため、
  どの compiler が使われたかが呼び出し地点から見えなくなる。
- optional 引数にして未指定なら既定値 — 取り残しが静かに復活する。
