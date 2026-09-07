---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-07
wave: dev-wave-t2232-s4-loop-first-dispatch
seq: 2
---

## {{D:s4-job-body-lacks-gflags-supply}}. 段 4 loop の job body が計算ノードで止まるのは、依存の供給経路が無いためである

**決定:** `tools/pegasus/p3_s4_loop_pegasus.sh` が masstree の FetchContent 事前構築で
`Could NOT find gflags` により失敗するのは、計算ノード環境の偶発ではなく **job body 自身に
gflags/glog の供給経路が無いため**である、と帰属させる。対応は同 job body へ供給経路を足すことであり、
CCBench 側の `find_package` を緩めることでも、計算ノードへ system package を入れることでもない。

**理由:**
- 兄弟 job body `tools/pegasus/floor_scoping.sh` は、policy が指す pin 済み source から
  gflags と glog を `$TMPDIR` へ configure / build / install し、
  `CMAKE_PREFIX_PATH` を両 install prefix へ向けてから CCBench を configure する。
  同 script はこの prologue の出典を `floor_campaign.sh` の同型 prologue と記している。
  **計算ノードで CCBench を建てる経路は、いずれも依存を自前で建てている。**
- `p3_s4_loop_pegasus.sh` は環境 sanitize で `CMAKE_PREFIX_PATH` を `unset` するだけで、
  gflags/glog を建てず prefix path も与えない。login node では system の gflags が拾えるため、
  この欠落は login 側の短走 (stub harness・契約テスト) では露出しない。
- 供給元は実在する。`tools/pegasus/policy.json` の `gflags_source_path` / `glog_source_path` が
  指す 2 source は、HEAD が policy の pin と exact 一致し、tracked / untracked とも clean である
  (2026-09-07 実測)。`fetch_third_party.py` の cache root には無い (masstree / mimalloc /
  googletest の 3 本のみ) ため、hydrate 経路の拡張ではなく policy 経由の prologue が対応する形である。
- 帰属を環境側に置くと、計算ノードへ system package を入れる方向へ流れる。それは pin されない
  依存を build に混ぜることであり、build identity を壊す。

**却下した選択肢:**
- CCBench の `find_package(gflags)` を optional にする — 上流の改変であり、
  かつ依存が実際に要る以上、configure を通しても link で落ちる。
- PATH へ CMake の wrapper を置いて third-party を注入する — F813 が禁じている。
- `fetch_third_party.py` の cache へ gflags/glog を足して hydrate 経路で運ぶ — floor 系が既に
  policy 経由で運んでおり、同じ依存を 2 つの経路で pin することになる。

**保証しないこと:** 供給経路を足せば job body が最後まで通ることは**実測していない**。
attestation の exact 照合と driver 本走は依然として未到達である。
