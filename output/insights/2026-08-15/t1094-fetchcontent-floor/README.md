# [T-1094] / [T-971](a) — 床値 build 経路の FetchContent と oracle 依存を計算ノードで実測する

wave: `dev-wave-t1094-fetchcontent-floor` / 2026-08-15 / branch
`worktree-dev-wave-t1094-fetchcontent-floor`

## この材料が答えたこと

依頼は [T-1094] (床値 build 経路へ `FETCHCONTENT_SOURCE_DIR_*` を通す) と
[T-971] 残件 (a) (計算ノードで resolver 解決と CMake configure の可否を**同時に**測る PBS probe の実走)。

**実装は行わなかった。** 段 3 の敵対 2 レンズが独立に NO-GO を返し、かつ wave 走行中に land した
worklog エントリ 554 が依頼の前提を反証したため、段 4 で `DW-G01` (生死実験先行) を適用して
順序を入れ替え、**先に測った**。本材料はその実測である。

## 実測 (すべて 1 つの PBS job 内。`Request 911191.nqsv` / `bnode030` / 2026-08-15 10:00-10:01 JST)

- job: `0:911191.nqsv`、`TMPDIR=/scr/0_911191.nqsv`、Elapse 33 秒、exit 0。
- 対象 commit `895d02c56438313b86e19a4fe9c50ad1ea9ef325`。
- `mocked: false` — production module を実物で import した
  (`buildcache` / `patchharness` / `s8b_floor_campaign` / `silo_ladder_rung1` / `sort_swo_oracle`)。
- 生データ = `probe-result.json` (67,966 bytes)。probe 逐語 = `verbatim/`。

### 1. 床値と同じ形で、SOURCE_DIR 無しの FetchContent が通る (leg C1)

使い捨て checkout (`/scr/0_911191.nqsv/izanagi_wt_z7rany0e/wt`) に対し、
`dependency_prefix` を **production seam 経由** (`orchestrator.campaign.buildcache._v2_commands`) で
渡した configure が

- `returncode = 0`、`elapsed_s = 5.520271`
- `source_dir_tokens = []` (`FETCHCONTENT_SOURCE_DIR_*` を 1 つも渡していない)
- `_deps` に **9 entry** (masstree / mimalloc / googletest の src + build + subbuild)

エントリ 554 は同じ事実を **8c live build 経路**で測り「床値経路かは scope 外」と限定していた。
本 probe は**床値の実際の形** (`$TMPDIR=/scr/$PBS_JOBID` 配下の使い捨て checkout) で再現した。

### 2. oracle が検証する tree と build がコンパイルする tree は別物である (leg 0)

```
oracle_dependency_root = /work/1/SFC/tanab/izanagi-thirdparty-cache/masstree
configure_source_root  = /scr/0_911191.nqsv/ccbench-c1-build/_deps/masstree-src
same_root              = false
```

床値は `_resolve_floor_oracle_dependency(third_party_cache_root)` の結果を
`oracle_dependency_root` として prepare へ渡す (`s8b_floor_campaign.py:2019-2021, 2060-2065`) 一方、
build は FetchContent が `_deps` へ展開した別 tree を使う。
**seam の要否と独立に real な構造欠陥である。**

### 3. 共有 cache は過去の build の生成物で汚染されており、現行の pinned-clean 検査はそれを見ない (leg A)

| root | source | `git status --porcelain -uall` | `git ls-files --others --ignored --exclude-standard` |
|---|---|---|---|
| cache | masstree | **0 行** | **71 件** |
| cache | mimalloc / googletest | 0 行 | 0 件 |
| staging (hydrate 出力) | 3 本すべて | 0 行 | **0 件** |

cache の HEAD は凍結 policy の pin (`b3c5d054b66b08374d7a6ff5a0faeaf28b041a38`) と一致する。
つまり `silo_ladder_rung1.third_party_source_contract` の
「pin 一致 かつ `git status` 空」という判定は、**この tree を pinned-clean と宣言する**。
D152 決定 (4) が警告した失敗モードが実データで成立している。

### 4. 汚染の正体は build が source tree の中に吐く生成物である (leg D / C1)

| | build 前 | `cmake --build --target masstree_build` (rc=0 / 10.676 秒) | 共有 cache の現物 |
|---|---|---|---|
| `config.h` | **不在** | **10,448 bytes** 生成 | **10,448 bytes** |
| `libkohler_masstree_json.a` | **不在** | **2,466,926 bytes** 生成 | 2,466,846 bytes |

`generated_by_this_build = {config_h: true, archive: true}`。
`external/ccbench/cmake/ThirdParty.cmake:66-77` が `./bootstrap.sh; ./configure; make -j; ar cr` を
`WORKING_DIRECTORY "${masstree_SOURCE_DIR}"` で実行するため、生成物は source tree の中へ落ちる。

**帰結: `resolve_oracle_environment` は masstree の `config.h` を要求するが、それは
pin された clean な source には存在しない。** T-971 で「共有 checkout 上では oracle が解決できる」と
観測されたのは、**cache が過去の build で汚染されていたから**である。
oracle が実質的に要求しているのは「pin された source」ではなく「**build 済みの masstree**」であり、
これは pin の問題ではなく build 順序の問題である。
かつ `config.h` は `.gitignore` 除外で Git 非管理なので、**HEAD pin はその bytes を証明しない**
(T-971 が既に指摘した点が、ここで因果として閉じた)。

### 5. D152 が規定する供給方法は、環境の git 強化設定下では走らない (leg C2)

C2 (job-local fresh clone → SOURCE_DIR) は hydration 段で失敗した。

```
git --no-replace-objects clone --local --no-hardlinks --no-checkout -c core.hooksPath=/dev/null \
  <staging>/googletest /scr/0_911191.nqsv/c2-third-party-sources/googletest
returncode = 128
stderr     = "fatal: transport 'file' not allowed"
```

D152 決定 (4) が要求する `clone --no-hardlinks --no-checkout` は、この環境の git 強化設定
(`protocol.file.allow`) の下では明示的な許可なしに実行できない。
本 probe は許可 flag を付けていないため、**「C2 は不成立」ではなく「C2 は未測定」**である。
`all_pass = false` はこの未完了を正しく反映している。

## 実測の射程 (一般化しないこと)

- 測ったのは `bnode030`・`0:911191.nqsv`・2026-08-15 10:00-10:01 JST の 1 job である。
- C1 の成功は当該 node の proxy 設定に依存する。`docs/pegasus-runbook.md:744-756` の
  「command・ノード・profile ごとに未確定」は撤回されていない。
- **本 wave は「床値が取れるようになった」と主張しない。** 測ったのは configure と
  masstree build target までで、床値の本走 (12 cell・測定・report) は別である。
- **本 wave は [T-1094] を解決したと主張しない。** seam は実装せず裁定へ返した。
- **S5 / `p3_s4_loop_sort` / [T-1095] は未修復である。** 床値が通ってもこれらは直らない。

## 手順の逐語

- 段 1 brief / 追補、段 2 プラン、段 3 敵対 2 レンズ、段 4 裁定、段 5 / 段 6 の子報告は
  job tmp (`wave-t1094/`) に残る。本 README はその結論だけを持つ。
- probe 第 1 走 (`Request 911131.nqsv`) は 4 秒で exit 3。原因は
  **NQSV が job script を spool へコピーして実行するため `$0` が投入時の path でないこと**。
  段 6 fix が `.pbs` だけを直し (必須 env `IZANAGI_T1094_PROBE_PY` で絶対 path を受ける)、
  `.py` は SHA-256 一致で無変更のまま第 2 走に成功した。
