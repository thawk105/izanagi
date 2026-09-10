# 段 4 裁定 / プラン v2 — [T-1128]

親裁定。2026-08-15 23:40 JST。local main `330f67d0` (0 commit 遅れ)。
裁定 inbox 再走査済み: wave 開始後に増えたのは `2026-08-15-t1116-known-red-registry-no-trust-root.md`
(23:16) のみで、T-1128 の scope に触れない。T-1094 の「実装しない」は不変。

## 0. 総裁定

**CONDITIONAL-GO。** 段 2 プランの**方向** (job-local な `FETCHCONTENT_BASE_DIR` を 1 個作り、
依存 prebuild と cell build が同じ `<base>/masstree-src` を使い、oracle をその root へ明示束縛する)
は採用する。両レンズの NO-GO は方向ではなく**防壁の実効性と consumer 閉包**への指摘であり、
以下の must-fix を折り込んだ **プラン v2** で実装へ進む。

段 2 プランの「親 brief の訂正」表 (`s2-plan.md:127-144`) を**実装アンカーの正本**とする。
親 brief §5 の A2 / A7 / A9 / A11 / A12 は誤りとして撤回する。特に A11 —
「cell ごとの最終 build dir 配下に `_deps` がある」は誤りで、fresh configure は nonce staging で
行われ staging は build 後に削除される (親が独立に検算: `buildcache.py:1471` の
`_discard_build_dir(staging)`)。よって「cell ごとの `_deps` を oracle root にする」代替案は
**構造的に不成立**であり棄却する。

## 1. 所見ごとの裁定

| # | 所見 | 判定 | 採否 | scope |
|---|---|---|---|---|
| sol-1 | ambient `CMAKE_TOOLCHAIN_FILE` から `FETCHCONTENT_SOURCE_DIR_*` を注入でき、argv 検査は恒真 | **real** | 採用 (形を変える) | 内 |
| sol-2 | base 注入が全 cell / 全 FetchContent へ広がり `sort_best` 限定 scope を越える | **real** | 採用 | 内 |
| sol-3 | `submit_floor.sh` が旧共有 cache を必須にしたまま残り、floor が launch 不能になる | **real** | 採用 | 内 |
| sol-4 | 新 private field が binary store の exact-key gate を落とす | **real** | 採用 | 内 |
| sol-5 / luna-2 | dependency marker は SWO PASS 証明ではない。親 brief §3 は事実誤認 | **real** | 一部採用 | 一部外 |
| sol-6 | post-build drift が構造化されず汎用 error に落ちる | **real** | 採用 | 内 |
| sol-7 | 1 job probe を floor 全体へ一般化できない | **real** | 採用 (記述の限定) | 内 |
| sol-8 | `FETCHCONTENT_FULLY_DISCONNECTED` fallback は別審査が要る | **real** | 採用 (禁止として明記) | 外 |
| sol-9 | 親 brief の A2/A7/A9/A11/A12 が実ファイルと不一致 | **real** | 採用 | 内 |
| luna-1 | prebuild 失敗が閉じた `UNAVAILABLE` へ繋がっていない | **real** | 採用 | 内 |
| luna-3 | oracle 後も source tree が書換え可能 | **real** | 一部採用 (検知のみ) | 一部外 |
| luna-4 | cache identity が base path 止まりで masstree の中身を覆わない | **real** | 採用 | 内 |
| luna-5 | 共有 base に所有権 lock が無い | **refuted (blocker として)** | 不採用 | — |
| luna-6 | テスト計画に独立期待値と negative control が不足 | **real** | 採用 | 内 |
| luna-7 | private field と portable 化が exact-key 契約と噛み合わない | **real** | 採用 (sol-4 と同一) | 内 |
| luna-8 | 実行失敗を `outcome="invalid-path"` へ流すのは意味が曖昧 | **real** | 採用 | 内 |

### 裁定の理由 (争点のあるものだけ)

- **sol-1 の採用形を変える。** 「`CMAKE_TOOLCHAIN_FILE` を拒否または hash 固定する」ではなく、
  **build が実際に使った masstree source root を build 自身の成果物から読み取って照合する**
  (`<build>/CMakeCache.txt` の `masstree_SOURCE_DIR` 相当、または compile flags / link 入力)。
  理由: 実効値を見る検査 1 本は、環境変数を個別に禁止する検査の集合を包含する。
  argv 文字列検査だけを合格条件にしないという指摘の核心はこれで満たされ、
  受理集合を環境変数の有無で不必要に縮めずに済む。
  **argv 検査 (`FETCHCONTENT_SOURCE_DIR_*` が 0 個、`FETCHCONTENT_BASE_DIR` が正確に 1 個) は
  残す**が、それは補助であって合格の根拠ではない。
- **sol-2 を採用し、base 注入は `sort_best` cell に限定する。** 非 sort cell へ広げると
  scope 外の 10 cell の cache identity と binary 参照が変わる。今回の欠陥は
  `sort_best` の oracle と build の不一致であり、非 sort cell には oracle が無い。
- **sol-3 を採用し、`tools/pegasus/submit_floor.sh` と
  `orchestrator/tests/test_pegasus_floor_tools.py` を編集面へ加える。**
  `third_party_cache_root` の production 用途は oracle 依存解決ただ 1 箇所
  (`s8b_floor_campaign.py:2020`) であり、それを廃止すると submitter の必須引数は
  「使われないのに launch を止める入力」になる。放置は F319 の再来を招く
  (「cache を指せば動く」と読める入口が残る)。
- **sol-5 / luna-2 は一部採用。** 採用するのは (i) 親 brief §3 の事実誤認の訂正、
  (ii) **oracle が実際に使った依存 identity (root、HEAD、`config.h` sha256、archive sha256) を
  durable record へ束縛し、build 後に再照合する**こと。
  **採用しないのは** `oracle_attempt` / SWO PASS receipt そのものを built record へ束縛する件。
  これは「どの masstree か」ではなく「comparator が通ったか」の証拠経路であり、
  root 不一致とは独立の欠陥である。**裁定パッケージへ返す** (下記 §4)。
- **luna-3 は検知のみ採用。** 再 fetch の**禁止** (`FETCHCONTENT_FULLY_DISCONNECTED=ON`) は
  download 権威を変えるため sol-8 のとおり別審査。本 wave は**検知して fail-closed** に留める。
- **luna-4 を採用し、identity の権威を内容に置く。**
  **`st_dev`/`st_ino` は診断に留め、同一性の権威は内容 (HEAD + `config.h` sha256 +
  archive sha256) とする。** 段 2 プランの inode 一致要求はここで上書きする。
  理由: 再 populate が起きても内容が同一なら証拠は成立する。inode 一致を必須にすると、
  内容が同じでも停止する過剰拒否になる。逆に inode が同じでも archive が差し替われば
  検出できないので、内容照合が必須である。
- **luna-5 を blocker としては refute する。** base は job 一意な `$TMPDIR` 配下へ
  `mkdtemp()` で作られるため、作成時点で排他は構造的に成立している。floor の cell loop は
  同期である。将来 cell build を並列化するときの再審査事項として設計メモに残す
  (`DW-G04`: 発火条件を満たす artifact path を今は書けない)。

## 2. プラン v2 — 実装契約

### 2.1 編集面 (これ以外を編集しない)

1. `orchestrator/campaign/buildcache.py`
2. `orchestrator/campaign/s8b_floor_campaign.py`
3. `tools/pegasus/submit_floor.sh`
4. `orchestrator/tests/test_buildcache_v2.py`
5. `orchestrator/tests/test_build_site_gate.py`
6. `orchestrator/tests/test_s8b_floor_campaign.py`
7. `orchestrator/tests/test_pegasus_floor_tools.py`

**編集しない:** `external/ccbench/cmake/ThirdParty.cmake`、
`orchestrator/campaign/s1_direct_comparison.py`、`orchestrator/campaign/sort_swo_oracle.py`、
`orchestrator/tests/test_sort_swo_oracle.py`、`orchestrator/campaign/silo_ladder_rung1.py`。

### 2.2 実装項目

- **V1 (prebuild)。** production floor で `sort_best` cell が 1 つ以上あるとき、
  job 一意な `$TMPDIR` 配下に `mkdtemp()` で canonical base を 1 個作り、
  pin 済み CCBench checkout に対して 1 回だけ configure し
  `cmake --build <prebuild-dir> --target masstree_build` を実行する。
  実行体は `buildcache` 側の限定 helper に置く (direct CMake 閉集合検査
  `test_s8b_floor_campaign.py:2893` を迂回しない)。`buildcache._run()` を使う。
- **V2 (oracle root)。** oracle の `dependency_root` を `<base>/masstree-src` にする。
  `_verify_floor_oracle_dependency_source` の防壁 (repo 外 canonical root、非 symlink、
  git top-level 一致、HEAD == 共有 policy pin、regular `config.h` の sha256) は維持し、
  **archive (`libkohler_masstree_json.a`) の sha256 を追加**する。
- **V3 (旧経路の撤去)。** `third_party_cache_root` の production 経路と
  `_resolve_floor_oracle_dependency` の cache 解決を廃止する。
  単体テスト用の明示注入 seam (`fetchcontent_base_dir`) は置いてよい。
  CLI・環境変数から共用 cache を受ける production 経路は作らない。
  `submit_floor.sh` の `IZANAGI_PEGASUS_THIRDPARTY_CACHE` 必須検査と export、
  および `test_pegasus_floor_tools.py` の該当 pin を同じ wave で除去する。
- **V4 (cell build への注入と cache identity)。** `sort_best` cell の `build_fn` にだけ
  canonical base を渡す。`buildcache` 側で
  `-DFETCHCONTENT_BASE_DIR=<base>` を**正確に 1 個**生成し、
  **v2 identity preimage には base path ではなく依存 receipt
  (masstree HEAD + `config.h` sha256 + archive sha256) を入れる。**
  base を渡さない既定 caller では preimage を 1 byte も変えない (additive default)。
  *理由:* base path は job ごとに変わるだけで中身を証明しない。receipt を入れれば
  「別の masstree で作った binary が cache hit する」経路が閉じる (luna-4)。
- **V5 (実効 root の照合)。** cell build 後、binary admission より**前**に、
  build が実際に使った masstree source root を build 自身の成果物から取得し、
  期待する `<base>/masstree-src` と一致することを確認する。
  併せて HEAD・`config.h` sha256・archive sha256 を oracle 前の値と再照合する。
  argv に `FETCHCONTENT_SOURCE_DIR_*` が 0 個であることも確認する (補助)。
  不一致は fail-closed。`st_dev`/`st_ino` は診断としてのみ記録する。
- **V6 (閉じた失敗)。** base 作成、CCBench checkout、prebuild configure、prebuild target、
  post-build 照合の各失敗を**段階別の閉じた detail code**へ変換し、
  `_persist_floor_oracle_preflight_failure` 相当の永続化を通してから停止する。
  `OracleStatus.UNAVAILABLE`、oracle 未実行、`build_fn` 未実行を保つ。
  実行失敗に `outcome="invalid-path"` を流用せず、
  `_FLOOR_PREFLIGHT_CANDIDATE_OUTCOMES` へ実行失敗を表す値を追加する
  (閉集合の consumer を全部追随させること)。
  post-build 照合の失敗は preflight ではないので、**postflight 専用の閉じた detail code と
  永続化区間**を設ける。
- **V7 (private field と portable 化)。** `_fetchcontent_base_dir` 等の private runtime field を
  足すなら、**runtime store の exact-key 集合・private field 検証・portable 化前の除去・
  placeholder 置換・durable JSON の raw path 検査を同時に更新**する。
  `/scr/<job>` を durable artifact へ漏らさない。
  `prepare → build → store → project` の通しテストを置く。
- **V8 (予約枠)。** dependency prebuild の configure と target を wall-clock 予約式へ
  1 run 1 回だけ加える。`sort_best` cell が無ければ加算 0。journal に条件と cap を記録する。

### 2.3 gate の禁止 (署名 + 通る正例)

新設する禁止は次の 3 本。各々に**通る正例**を 1 つ添えること。

1. `configure argv に FETCHCONTENT_SOURCE_DIR_* が 1 個でもあれば拒否`
   — 正例: `-DFETCHCONTENT_BASE_DIR=<base>` だけを含む argv は通る。
2. `build の実効 masstree source root が期待 <base>/masstree-src でなければ拒否`
   — 正例: prebuild と cell build が同じ base を使った run は通る。
3. `build 後の masstree HEAD / config.h sha256 / archive sha256 が oracle 前と異なれば拒否`
   — 正例: 内容が同一なら (inode が変わっていても) 通る。

### 2.4 主張してはならないこと

- 「pinned-clean な masstree で build した」とは主張しない (ignored 生成物は T-1129 の範囲)。
- 1 job の実測を floor 全体・他 node・他 profile の可用性へ一般化しない。
- `FETCHCONTENT_FULLY_DISCONNECTED` を本 wave の許可範囲に含めない。

## 3. 変異事前登録 (DW-M01)

実装前に登録する。各変異は「無効化したとき赤の理由が 1 本に絞れること」を段 6 で確認する。

| ID | 変異 | 期待 kill |
|---|---|---|
| M1 | V5 の実効 root 照合を削り、argv 検査だけに戻す | 実効 root 検査の node |
| M2 | V5 の `config.h` sha256 比較を恒真化する (同じ値を両辺へ) | drift 検知の negative control |
| M3 | V4 の依存 receipt を v2 identity preimage から外す | cache identity の node |
| M4 | V6 の prebuild 失敗を握り潰して oracle へ進む | prebuild 失敗の negative control |
| M5 | `-DFETCHCONTENT_BASE_DIR` を 2 個生成する | define 重複の node |
| M6 | base 注入を非 sort cell にも広げる | scope 限定の node |
| M7 | **wave 前の実コードの形**: oracle dependency root を `_resolve_floor_oracle_dependency(third_party_cache_root)` の戻り値へ戻す | 同一 tree 束縛の positive/negative |
| M8 | V2 の archive sha256 の記録を外す | archive identity の node |

M7 は「wave 前の実コードの逐語形」であり、必ず含める (F302 の型)。

## 4. 裁定パッケージ (scope 外の real 所見。ユーザーへ返す)

1. **SWO PASS receipt が durable record へ束縛されていない** (sol-5 / luna-2)。
   `prepare_cell` が返す `oracle_attempt` を `s8b_floor_campaign.py` は一度も読まない
   (親が独立確認: `grep -n oracle_attempt` の hit は `s1_direct_comparison.py` のみ)。
   よって certified 選択の根拠から「どの comparator がどの oracle 実行で通ったか」への
   durable な辺が無い。**推奨: 新規起票 (P1)。** 本 wave は root identity だけを束縛する。
2. **oracle 後の再 fetch を禁止する手段** (`FETCHCONTENT_FULLY_DISCONNECTED=ON` 等) は
   download 権威の変更なので別審査が要る (sol-8 / luna-3)。**推奨: 新規起票 (P2)。**
3. **計算ノードでの 1 job probe。** 別 node / 別 CMake 実体で共有 base の再利用挙動が
   異なる可能性は残る。**推奨: 新規起票 (P2)、床値本走の前に測る。**
   本 wave の land gate にはしない。理由: (i) 設計が fail-closed なので仮定が外れても
   偽の主張は出ず安全に停止する、(ii) 最安の生死確認は静的に済んでいる — 段 2 プランが
   CMake 3.22.1 の実ソース (`FetchContent.cmake` / `ExternalProject.cmake`) を file:line で
   引き、かつ親が `tools/pegasus/floor_campaign.sh:772` は `command -v cmake` で解決すること、
   login の cmake が 3.22.1 であることを確認した、(iii) sol-7 のとおり 1 job の probe でも
   一般化はできないので、land gate にしても得られる保証は限定的である。
4. **共有 base の所有権 lock** は将来 cell build を並列化するときの再審査事項
   (luna-5、`DW-G04` により今は設計メモ)。

## 5. 撤回する親 brief の記述

- §3 の「oracle attempt record と phase marker は『共有 cache の masstree に対して
  comparator の SWO を検証した』と主張する」は**事実誤認**。
  `sort-swo-oracle-dependency.json` は oracle 実行**前**に書かれる attempt marker であり、
  SWO PASS の証明ではない。正しい成果物影響は次のとおり。
  **放置した場合: 床値 `sort_best` cell の binary は、oracle が identity を検証した tree とは
  別の tree の masstree に対してリンクされる。よって「この comparator を、この masstree の上で
  検証した」という主張が binary を覆わない。さらに clean な cache では `config.h` が無く
  oracle が UNAVAILABLE になり、床値 `sort_best` cell は 0 件になる。**
- §5 の A2 / A7 / A9 / A11 / A12 を撤回し、`s2-plan.md:127-144` を正本とする。
- §6 (P4) を限定する: HEAD 照合が覆うのは commit identity だけであり、
  `config.h`・archive・ignored 生成物の bytes は覆わない。
