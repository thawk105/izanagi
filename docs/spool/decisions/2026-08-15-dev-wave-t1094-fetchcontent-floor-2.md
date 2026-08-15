---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-15
wave: dev-wave-t1094-fetchcontent-floor
seq: 2
---

## {{D:measure-floor-fetchcontent-before-wiring}}. 床値 build 経路への FetchContent source 差し替えは実装せず、先に計算ノードで測る

**決定:** `orchestrator/campaign/buildcache.py` へ `FETCHCONTENT_SOURCE_DIR_*` の注入 seam を
実装しない。代わりに repo 外の PBS probe で、床値と同じ形 (使い捨て checkout・`TMPDIR=/scr/$PBS_JOBID`)
における resolver 解決・configure・masstree build を 1 job 内で実測する。
seam の要否は実測を根拠に別 wave で裁定する。

**理由:**

- **起票時の前提が実測で反証された。** 起票文は「計算ノードは直結 network 不可であり、これが
  解けない限り床値は 0 件のままである」を前提にしていた。本 wave の probe は、床値と同じ
  使い捨て checkout に対し `SOURCE_DIR` を 1 つも渡さない configure が
  **rc=0 / 5.520 秒**で通り、`_deps` に 9 entry (3 source × src/build/subbuild) が
  生成されることを実測した。したがって `SOURCE_DIR` 配線は blocker の解除ではなく、
  再現性と offline fallback のための選択肢である。
- **実装案は正しさで現状より劣る。** network 経路の FetchContent は GIT_TAG pin で毎回
  fresh clone するため、汚染された tree を build 入力に持ち込まない。一方 `SOURCE_DIR` 経路は
  共有 source tree を build 入力にするが、その tree は build 自身が生成物を書き込む対象であり、
  実測した共有 cache は既に 71 件の ignored 生成物を抱えていた
  ({{F:pinned-clean-blind-to-ignored}})。**塞ぐはずの穴を新しい経路で作り直す形になる。**
- **敵対 2 レンズが独立に NO-GO を返した。** 一致した指摘は (a) 弱い検証と
  非 hardened な Git driver が D152 の防壁を迂回する、(b) 供給が
  `clone --no-hardlinks --no-checkout` でなく copytree である、の 2 件。
  `tools/pegasus/fetch_third_party.py` は skip-worktree / assume-unchanged / alternates /
  grafts / sparse / shallow / replace refs / `core.fsmonitor` を拒否する強い verifier を既に持ち、
  実装案はその弱い側を再利用していた。
- **`DW-G01` (生死実験先行) が正面から効く場面である。** 共有 build path は全 campaign へ
  波及するため、床値が実際にどこで止まるかを測らずに変更するのは順序として誤りである。

**却下した選択肢:**

- **裁定どおり seam を実装してから測る** — 共有 build path を、両レンズが blocker と判定した
  形で先に変えることになる。前提が反証された後では正当化できない。
- **probe を configure までに限定する** — masstree の `config.h` と archive は configure ではなく
  `cmake --build` の custom command が生成するため、configure だけでは
  「clean な source では oracle が解決できない」という中核の因果を観測できない。
- **共有 staging を SOURCE_DIR へ直接渡す** — build が source tree を書き換えるため、
  並行 job と同一 job 内の後続 cell が互いの tree を汚染する。

## {{D:floor-oracle-and-build-use-different-masstree}}. 床値の oracle 依存 root と build の source root が別 tree である問題を独立の欠陥として起票する

**決定:** 床値が oracle 依存を検証する tree と、build が実際にコンパイルする tree が
別物である構造を、FetchContent 配線の要否とは**独立の欠陥**として扱い、
本 wave では修正せず裁定へ返す。

**理由:**

- probe が同一 job 内で両者を並べて実測した。
  `oracle_dependency_root = <third-party cache>/masstree`、
  `configure_source_root = /scr/<job>/ccbench-c1-build/_deps/masstree-src`、`same_root = false`。
- 床値は `_resolve_floor_oracle_dependency(third_party_cache_root)` の結果を
  `oracle_dependency_root` として prepare へ渡す一方、build は FetchContent が展開した別 tree を使う。
- **oracle が要求しているのは「pin された source」ではなく「build 済みの masstree」である。**
  `resolve_oracle_environment` は `config.h` を探すが、それは pin された clean な source には
  存在せず、build が source tree の中へ生成する。過去に oracle が解決できていたのは
  cache が汚染されていたからであり、これは pin の問題ではなく build 順序の問題である。
- したがって `SOURCE_DIR` を通しても、oracle と build を同一 root へ揃えない限り
  「証拠と実体の不一致」は残る。**seam を入れれば床値が通る、という筋書きは成立しない。**

**却下した選択肢:**

- **本 wave で oracle 側も同時に直す** — 受理集合が変わる変更を、前提が反証された直後に
  測定なしで重ねることになる。probe の実測を材料として別 wave で裁定する。
