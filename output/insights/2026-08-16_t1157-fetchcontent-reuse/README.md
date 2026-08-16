# [T-1157] — 共有 FetchContent base の再利用挙動を計算ノードで実測する

wave: `dev-wave-t1157-fetchcontent-reuse` / 2026-08-16 / branch
`worktree-dev-wave-t1157-fetchcontent-reuse`

## この材料が答えたこと

依頼は [T-1157]。床値本走の前に、**2 本目以降の configure が既存 masstree source を置換せず、
再 fetch もしない**ことを計算ノードで実測する。それまでの根拠は CMake 3.22.1 の実ソース読解と、
床値 job が `command -v cmake` で同じ実体を引くことだけで、**実測が無かった**。

**結論: 置換も再 fetch も起きない (`verdict=REUSED`)。** 床値本走はこの前提で進めてよい。
ただし下の「射程」を必ず読むこと。

## 権威走行

- `Request 912911.nqsv` / `bnode009` / 2026-08-16 09:43:40〜09:45:24 JST / 所要 103.4 秒 / `errors` 0 件。
- `TMPDIR=/scr/0_912911.nqsv`、`PBS_JOBID=0:912911.nqsv`。
- `mocked=false` — production module を実物で import した
  (`buildcache` / `s8b_floor_campaign` / `patchharness`)。
- 生データ = `probe-result-3-authoritative.json` (618,391 bytes)。probe 逐語 = `verbatim/`。

## 1. 測った形 (production の何を再現したか)

床値は **2 holdout × 6 構成 = 12 cell** で構成集合は全 holdout で一致するため、`sort_best` cell は
**2 個**ある。したがって 1 job 内で共有 base に当たる configure は **prebuild 1 本 + cell build 2 本
= 3 本**である (cold path)。probe はこの 3 本を production seam で再現した。

| leg | 再現した production 経路 |
|---|---|
| base 確定 | `s8b_floor_campaign._canonical_floor_fetchcontent_base(None)` (`$TMPDIR` 配下へ `mkdtemp`) |
| 依存 provisioning | `tools/pegasus/floor_campaign.sh:781-923` を写して gflags/glog を build/install し ambient `CMAKE_PREFIX_PATH` を export |
| configure #1 | `buildcache.prepare_masstree_fetchcontent` (使い捨て CCBench checkout) |
| configure #2 | `buildcache._v2_commands` が組んだ cell build argv を別 checkout・別 nonce build dir で実行 |
| configure #3 | 同上をもう 1 組 (2 個目の `sort_best` cell 相当) |

## 2. 実測 — production の 3 transition で動いた field は 1 つもない

| 観測対象 | 3 transition すべて |
|---|---|
| `masstree-src` の `st_dev` / `st_ino` | **不変** |
| `config.h` (inode + sha256) | **不変** |
| `libkohler_masstree_json.a` (inode + sha256) | **不変** |
| gitclone `-lastrun` / `download` stamp (inode + sha256) | **不変** |
| `FETCH_HEAD` / `packed-refs` / HEAD / refs | **不変** |
| `head_matches_pin` | 全 snapshot で true |

**唯一動いたのは `patch` step stamp の `st_mtime_ns` だけ**であり、これは判定に入れていない
(理由は §4)。追加で回した `masstree_build` target の診断 transition も**変化ゼロ**で、
archive が作り直されないことを裏づけた。

## 3. 検出力の正例 (これが無ければ §2 は無意味である)

「変化しなかった」を主張する前に、**変化を検出できることを同じ job 内で示した。**

| positive control | 何をしたか | 動いた field |
|---|---|---|
| clone (置換) | 別 base で `gitinfo.txt` を lastrun より新しくして再 configure | `src_dir` / `config_h` / `archive` / `gitclone_lastrun` の各 verdict signature |
| fetch (再取得) | populated source へ **直接** `git fetch --tags --force origin` | `git_state.fetch_head.verdict_signature` |
| update checkout | HEAD を pin から外して再 configure | (update step の再入を確認) |

3 本とも発火した (`positive_control_fired` / `fetch_detector_fired` /
`update_checkout_positive_control_fired` = すべて true → `refetch_detection_proven=true`)。

**fetch の正例で動いたのが `FETCH_HEAD` だけ**だった点は重要である。up-to-date な fetch は
HEAD も refs も clone stamp も動かさないので、`FETCH_HEAD` が唯一の信号になる。

## 4. `patch` stamp の mtime を判定から外した理由 (偽 NO-GO を 1 件潰した)

第 2 走 (`Request 912886.nqsv`、`probe-result-2-erratum.json`) では、この mtime が `REFETCHED`
判定に入っていた。実測は次のとおりである。

| snapshot | st_ino | sha256 | st_mtime_ns |
|---|---|---|---|
| after_prebuild | 12884902048 | e3b0c442…b855 (空 file) | 1786840284979654250 |
| after_configure2 | 12884902048 | 同一 | 1786840300211782670 |
| after_cell_build3 | 12884902048 | 同一 | 1786840305491827186 |

inode 同一・内容同一 (空)・path 同一で mtime だけ進む。`PATCH_COMMAND` を持たない no-op patch
step の stamp が populate のたびに touch されているだけで、再 fetch でも置換でもない。

**このまま単独性が通っていれば第 2 走は `REFETCHED` を返し、床値へ根拠のない NO-GO を出していた。**
判定を `exists` / `st_ino` / `sha256` に限定し、mtime は `diagnostic_signature` へ移した。
`FETCH_HEAD` の mtime は判定に残している (§3 のとおりそこだけが fetch の信号のため)。
緩めていないことは、変更後も clone / fetch の positive control が発火することで担保した。

## 5. 単独性

権威走行は 10 秒間隔 4 サンプルで確認し、**全サンプルで他者の compute process ゼロ**、
load1 は `1.05 → 0.89 → 0.75 → 0.78` (閾値 `max(1.0, 48*0.05)=2.4`) だった。

第 2 走は `load1=2.96` で false になったが、そのときも `other_compute_processes` は空だった。
job 開始直後の 1 分平均は**直前にそのノードを使っていた job の残響**を含む。
閾値は変えず、測定時点を複数サンプルの最後へ訂正し、process 条件は全サンプルへ強化した。

## 6. 実測の射程 (一般化しないこと)

- 測ったのは `bnode009` / `0:912911.nqsv` / 2026-08-16 09:43-09:45 JST の **1 job** である。
- **cold path を強制している。** probe は毎回 fresh base と fresh build dir を使う。
  production は binary cache hit があれば configure 本数が 3 本より減りうる。
- **`REFETCHED` が動かなかったことから「fetch していない」を導く推論**には、
  CMake の update step が `fetch_required=YES` のときだけ fetch するというソース読解が入る
  (`ExternalProject-gitupdate.cmake.in`)。完全 SHA pin の object がローカルにある本構成では
  NO の枝に入る。**この 1 点はソース読解であって実測ではない。**
  実測側は「全 snapshot で `head_matches_pin=true`」でその前提の成立を示している。
- configure #2/#3 は `build_or_reuse` 全体ではなく `_v2_commands` の argv を直接実行した。
  admission / cache hit / publish 前照合は通っていない。argv は production と同一である。
- **本 wave は「床値が取れるようになった」と主張しない。** 測ったのは共有 base の再利用挙動だけで、
  本走 (12 cell・測定・report) は別である。
- **[T-1156] (`FETCHCONTENT_FULLY_DISCONNECTED` の可否審査) は scope 外**であり触れていない。
  本 wave の結果は「現状のままでも置換・再 fetch は起きない」であって、
  禁止機構が不要だと裁定したものではない。

## 7. 途中経過 (捨てずに残す)

| 走行 | request | 結果 | 何を学んだか |
|---|---|---|---|
| 第 1 走 | 912848 | `INCONCLUSIVE` / configure #1 が `Could NOT find gflags` で rc=1 | probe が production job の依存 provisioning を再現していなかった。**床値の欠陥ではない** — `floor_campaign.sh` が gflags/glog を build して ambient `CMAKE_PREFIX_PATH` を張り、`buildcache.py` の `_canonical_ambient_dependency_prefix` がそれを読む |
| 第 2 走 | 912886 | `INCONCLUSIVE` / 全 leg 完走・positive control 3 本発火 | §4 の偽 REFETCHED と §5 の load 誤測を摘出 |
| 第 3 走 | 912911 | **`REUSED`** | 権威走行 |

第 1 走で JSON が publish されたことは、budget 打切り・signal 時にも結果が残る設計が
実走で働いた実証でもある。

## 8. 手順

段 1 brief、段 6 敵対レビュー (must-fix 5 件で NO-GO)、焦点再レビュー (blocker 1 件で NO-GO)、
fix 4 巡、裁定は job dir (`wave-t1157-fetchcontent-reuse/`) に残る。
**焦点再レビューが潰した blocker は「update positive control が偽物」** — 完全 SHA pin の object が
ローカルにあるため CMake は fetch せず checkout するだけなのに、probe はその HEAD 変化で
`refetch_detection_proven` を立てていた。実 fetch の正例へ差し替えた (§3)。
