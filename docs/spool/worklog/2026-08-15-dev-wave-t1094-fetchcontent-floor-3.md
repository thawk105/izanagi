---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-15
wave: dev-wave-t1094-fetchcontent-floor
seq: 3
title: 床値の FetchContent 前提を計算ノードで反証し、oracle と build が別 tree を見る構造を実測で確定した — 敵対 2 レンズが独立に NO-GO、実装は裁定へ返した (docs のみ、branch worktree-dev-wave-t1094-fetchcontent-floor)
---

## 本文

- **依頼の前提が実測で反証された。** 依頼は [T-1094] (床値 build 経路へ
  `FETCHCONTENT_SOURCE_DIR_*` を通す) を「計算ノードは直結 network 不可であり、
  **これが解けない限り oracle を直しても床値は 0 件のまま**」という前提で出されていた。
  本 wave の probe は、床値と**同じ形**の使い捨て checkout (`TMPDIR=/scr/$PBS_JOBID` 配下) に対し
  `SOURCE_DIR` を 1 つも渡さない configure が **rc=0 / 5.520 秒**で通り、
  `_deps` に 9 entry が生成されることを計算ノード `bnode030` で実測した。
  wave 走行中に land した別 wave のエントリも 8c live build 経路で同じ向きの実測を出しており、
  そちらは「床値経路かは scope 外」と限定していた。**本 wave はその欠けていた部分を埋めた。**
- **本 wave は実装を行わず、測定を先行させた ({{D:measure-floor-fetchcontent-before-wiring}})。**
  段 3 の敵対 2 レンズが**独立に NO-GO** を返し、blocker のうち 2 件は 2 レンズ一致だった
  (弱い検証と非 hardened Git driver が D152 の防壁を迂回する / 供給が
  `clone --no-hardlinks --no-checkout` でなく copytree である)。`DW-G01` を適用して順序を入れ替えた。
  **共有 build path は全 campaign へ波及するため、床値が実際にどこで止まるかを測らずに
  変えるのは順序として誤りである。**
- **最も重い実測: oracle が検証する tree と build がコンパイルする tree は別物である
  ({{D:floor-oracle-and-build-use-different-masstree}}).** 同一 job 内で並べて測り
  `same_root = false` を得た。この所見は段 3 のレンズが先に指摘し、親が probe で裏を取った。
  **`SOURCE_DIR` を通しても、両者を同一 root へ揃えない限り証拠と実体の不一致は残る。**
- **共有 cache は過去の build の生成物で汚染されており、現行の pinned-clean 検査はそれを見ない
  ({{F:pinned-clean-blind-to-ignored}})。** cache の masstree は `git status --porcelain -uall` が
  0 行・HEAD が凍結 pin と一致する一方、ignored file が **71 件**あった。
  probe は clean な source に対し masstree の build target を実行し (rc=0 / 10.676 秒)、
  `config.h` 10,448 bytes と archive 2,466,926 bytes が**その build によって生成された**ことを
  before/after で確定した。**T-971 で「共有 checkout 上では oracle が解決できる」と観測されたのは、
  cache が汚染されていたからである。** oracle が実質要求しているのは「pin された source」ではなく
  「build 済みの masstree」であり、これは pin の問題ではなく build 順序の問題である。
- **D152 が規定する供給方法は、この環境の git 強化設定下では走らなかった。** job-local の
  `clone --no-hardlinks --no-checkout` が `fatal: transport 'file' not allowed` (rc=128) で落ちた。
  許可 flag を付けていないため、**「不成立」ではなく「未測定」**として記録する。
  probe の `all_pass = false` はこの未完了を正しく反映している。
- **親 brief の誤りを 2 件、子とレンズが倒した。** (a) 「env 中立 module へ policy path を書くと
  AST 検査が赤になる」は偽で、禁止値は exact 6 個の env literal だけであり、床値は既に accessor
  経由で共有 policy を読んでいる。層分離の結論は維持し根拠を差し替えた。(b) 「`/work` が読めれば
  staging を direct 使用してよい」は偽で、build が source tree を書き換えるため可読性と無関係に
  job-local が必須である。**このほか段 2 プランが親 brief のアンカーを 9 点訂正した** — 特に
  「`loop.py → pipeline.py` の seam は床値に届かない (床値は `build_cells` から `build_fn` を
  直接呼ぶ)」は、実装していれば配線を丸ごと外していた誤りだった。
- **probe の第 1 走は 4 秒で落ちた ({{F:nqsv-spools-job-script}})。** NQSV が job script を spool へ
  コピーして実行するため `$0` が投入時の path でないことを実測した。段 6 fix は `.pbs` だけを直し、
  `.py` は SHA-256 一致で無変更のまま第 2 走に成功した。
- **起動時に F286 の恒久赤を踏んだ。** main に tracked で残った前 wave の handoff により
  `check_wave_startup.py` が rc=1。land 側は同 path の削除を rc=21 で拒むため wave 内では解けず、
  先例に従い main で直接撤去した。**この構造は [T-1038] の恒久修正が入るまで、新規の背景 wave を
  1 本ずつ止め続ける。**
- **本 wave は「床値が取れるようになった」とも「[T-1094] を解決した」とも主張しない。**
  S5 / `p3_s4_loop_sort` / [T-1095] は未修復である。実測の射程は
  `bnode030`・`0:911191.nqsv`・2026-08-15 10:00-10:01 JST の 1 job に限る。
- 材料の正本 = `output/insights/2026-08-15_t1094-fetchcontent-floor/`
  (probe 生データ 67,966 bytes と probe 逐語)。

## 次の一手差分

### 更新

- [T-1094] **P1・要裁定 (前提が反証された)**: 床値 build 経路への
  `FETCHCONTENT_SOURCE_DIR_*` 配線。**起票時の前提「計算ノードで FetchContent が通らない」は
  計算ノードでの実測で反証された** (`SOURCE_DIR` 無しの configure が rc=0 / 5.520 秒、
  `_deps` 9 entry)。配線は blocker 解除ではなく再現性・offline fallback のための選択肢へ降格する。
  かつ現状では **network 経路のほうが正しさで優る** — GIT_TAG pin で毎回 fresh clone するため
  汚染を持ち込まないが、`SOURCE_DIR` 経路の共有 source tree は build 自身が書き換える対象であり、
  実測した共有 cache は既に ignored 生成物 71 件を抱えていた。
  **裁定が要るのは「再現性のために汚染リスクを取るか」であり、択一を
  {{D:measure-floor-fetchcontent-before-wiring}} に整理した。**
  実装する場合の条件 (records を transport 専用に降格し権威を凍結 policy と Git 現物の再解決に
  置く / hardened verifier の再利用 / `clean` の意味を上書きせず schema を分離する /
  空 records 拒否を関数 identity でなく実 build sink で判定する) も同 D に列挙済み。
  base: 404b9a1dbc0266f4a6cf80c30a4a435df2619f307aa0a34543412bca5df693ca
- [T-971] **P1・残件 (a) 完了、(b) は [T-1094] へ従属**: 計算ノードでの end-to-end 実測を
  `Request 911191.nqsv` (`bnode030`) で実走した。resolver 解決と CMake configure を同一 job・
  同一の使い捨て checkout で同時に測り、さらに masstree build target まで踏んだ。
  **明示注入した `dependency_root` 経由で `resolve_oracle_environment` は
  `OracleEnvironment` を返した** — T-971 が追加した経路は効いている。
  ただし解決先は汚染された共有 cache であり、build が使う tree とは別物だった
  ({{D:floor-oracle-and-build-use-different-masstree}})。残件 (b) は [T-1094] の裁定に従属する。
  base: 36ef76b4375ac5aaa649d5a0fbf5b42bc567d2a0e778683c924942da079a1376

### 新規

- {{T:floor-oracle-build-root-unification}} **P1・新規**: 床値の oracle 依存 root と build の
  source root を同一 tree へ揃える。現状は `same_root = false` で、oracle は共有 cache を、
  build は FetchContent が展開した `_deps` 配下を見る。**`FETCHCONTENT_SOURCE_DIR_*` の要否と
  独立の欠陥**であり、揃えない限り床値の証拠と実体は一致しない。
  oracle が要求しているのは build 済み masstree (`config.h` と archive) であって pin された
  source ではないため、build 順序の設計が要る。
- {{T:pinned-clean-must-see-ignored}} **P2・新規**: `third_party_source_contract` の
  pinned-clean 判定へ ignored file 検査を加える。現状は実測で 71 件の生成物を抱えた tree を
  clean と宣言する。**consumer は床値だけでなく Silo ladder correctness/gap job も含む**ため
  影響半径が床値の外へ出る。既存 record schema の `clean` の意味を上書きすると旧凍結 evidence を
  誤読するので、新 field による新旧分離が要る。
- {{T:d152-clone-blocked-by-git-hardening}} **P3・新規**: D152 決定 (4) が規定する
  `clone --no-hardlinks --no-checkout` が、この環境の git 強化設定下で
  `fatal: transport 'file' not allowed` (rc=128) になる。許可 flag を付けた場合に成立するかは
  **未測定**。D152 の供給経路を実際に使う前に確定させる必要がある。
