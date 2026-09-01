---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-02
wave: dev-wave-t1835-t1718-tool-identity
seq: 1
---

## {{D:masstree-nondebug-projection-authority}}. masstree archive の独立期待権威は版付きの非 debug 射影 digest として発行する

**決定:** D668 決定 1 が「archive の sha256」と書いた独立期待 hash を、
**`gnu-ar-elf-nondebug/v1` の非 debug 射影 digest** として発行する。置き場は D668 のとおり
`tools/pegasus/policies/floor_masstree_payload_v1.json` のままとし、schema を v3 へ上げる。
raw archive sha256 は policy へ入れず、run 内 drift と provenance 用として現行のまま残す。

**理由:**

- **素朴な raw bytes は到達不能である。** recipe は `CXXFLAGS=-g` で build するため、
  DWARF の `DW_AT_comp_dir` に build directory の絶対 path が入る。計算ノードは PBS job id を
  含む scratch で build し、生成器は毎回異なる temp directory で build するので、両者は原理的に
  一致しない。これは 2026-08-23 の実機 run (`output/insights/2026-08-23_t1431-floor-pilot-rerun/`)
  と本 wave の probe で、独立に 2 回実測されている。
- **現行の代替は D1076 が却下した形である。** raw pin は 2026-08-24 の実装判断で撤去され、
  代わりに caller が事前観測した realpath + version の toolchain manifest hash が残った。これは
  「検証済み絶対 path への束縛」であり、D1076 が明示的に却下した選択肢に該当する。
  D1076 は撤去より後のユーザー裁定なので、D1076 が優先する。
- **非 debug 射影なら到達可能である。** 本 wave は 6 本の独立 build
  (生成器の二重 build、共有 third-party cache の archive、別 path の login build 2 本) が
  同一の射影値 `844334920db6…` を返すことを実測した。raw sha256 は 6 本すべて相異なる。
  section 単位でも、非 debug section は 1 つも相違しなかった。
- **射影は外部 command を新しい信頼点にしない。** `objcopy` / `strip` / `readelf` を使わず、
  version 管理下の pure-Python parser が no-follow の 1 回読みから raw digest と併せて導出する。

**却下した選択肢:**

- raw archive sha256 をそのまま発行する — 到達不能が 2 回実測されており、恒常 fail-closed になる。
- CCBench の `CXXFLAGS` へ `-ffile-prefix-map` を足して raw bytes を再現可能にする —
  CCBench 改変を伴い、既存 binary digest への波及が広い。射影で足りることを実測した。
- `objcopy --strip-debug` の出力を hash する — 射影が一致することは実測したが、
  ambient に解決される外部 command を新しい信頼点として持ち込む。
- 期待権威を置かず toolchain manifest 束縛だけで済ませる — D1076 が却下した形の維持になる。

**射程の限界 (謳わず明記する):** 検出するのは承認 policy と実行時 archive の非 debug 射影の差である。
同じ射影を出す道具の置換、debug 情報だけの差、発行環境そのものの正当性は保証しない。
適用範囲は S8b `sort_best` の masstree prebuild であり、non-sort floor build、mocc の CCBench build、
通常 buildcache consumer は覆わない。期待値は login node で発行しており、計算ノードで実際に
build した archive の射影を測ったわけではない。食い違えば gate は fail-closed で発火する。

## {{D:mocc-compiler-expected-version-body}}. mocc trace pilot の compiler は policy の期待 version body と照合し launcher 経路を閉じる

**決定:** `tools/pegasus/mocc_trace_v1_policy.json` へ
`expected_compiler_version_body_sha256` を exact key 集合 `{"gcc", "g++"}` の mapping として追加し、
pilot が compiler を記録する地点で fail-closed 照合する。正規化は
`orchestrator/campaign/toolchain_binding.py` の実 `tool_version_body()` を import して再利用し、
複製しない。あわせて policy 読み出しで duplicate key を拒否し、gflags / glog の configure から
未照合の compiler launcher 経路 (`CMAKE_C/CXX_COMPILER_LAUNCHER`、`RULE_LAUNCH_COMPILE`、
`CMAKE_TOOLCHAIN_FILE`) を閉じる。絶対 path は記録用に維持し、受理述語には使わない。

**理由:**

- 現行は CPU model が不一致で fail-closed し、gflags / glog も HEAD pin と照合するのに、
  compiler だけは `command -v` で素の名前から解決した path と `--version` を記録するだけだった。
  計測ノードの既定 toolchain が変われば、同じ policy・同じ source pair の観測値が黙って
  別条件のものになる。
- 期待値は実在し到達可能である。記録済み pilot receipt 37 件と計算ノード calibration receipt の
  compiler version body は、いずれも digest `b713e6ab…` で 1 種類だった。
- 床値 campaign 側の `toolchain_binding.py` (D293 / D601) は receipt と live 観測の realpath を
  突き合わせる設計であり、policy の期待権威とは役割が違う。二度書きにはならない。
  一方 version 正規化の規約は既存権威なので再利用する。
- compiler の身元を照合しても、CMake が環境変数から採用する launcher を閉じなければ、
  照合済み compiler の前に未照合の実行体を差し込める。main CCBench build は既に空 launcher を
  渡しており、依存 library の build だけが開いていた。

**却下した選択肢:**

- 絶対 path で照合する — D1076 が却下した形。
- 正規化を shell 側へ複製する — 既存権威と乖離する経路を増やす。
- gcc と g++ の role 混成まで識別する固定 challenge を作る — 本題を越える新機構であり、
  本 wave は限界として明記するに留める。

**射程の限界 (謳わず明記する):** `tool_version_body()` は起動名の第 1 token を落とすため、
gcc と g++ の body は同一になりうる。したがって role 混成は検出しない。
同じ version body を保った compiler binary の置換も検出しない。
期待値は committed policy に置くが、submit 側の authority へは束縛していない。
