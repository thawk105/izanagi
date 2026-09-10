# [T-2535] 段 4 裁定 — plan v2 と変異事前登録

裁定時刻 2026-09-09 23:40 JST。local main = `7f17e1c63` (wave 開始から不動)。
裁定 inbox 再走査: `docs/worklog.md:1299-1307` の T-2534 / T-2535 / T-2536 を再読。
**T-2534 (認定 launcher の `-DCCBENCH_BACKOFF_FIXED=-1` と条件関門) は「ユーザー裁定待ち」であり、
本 wave の scope 外であることが台帳で確定した。**

## 1. 所見の裁定

### real・採用 (scope 内・must-fix)

| # | 出所 | 所見 | 裁定 |
|---|---|---|---|
| R1 | plan、lens A 反証2、lens B masstree 2 | 永続 cache は `verify` が ignored artifact を見ないため pristine でない | **real・採用。** 親が独立に実測: cache の masstree に ignored artifact が **71 件** (`.deps/*.d` 等)。段 1 brief の (P1) provisional を撤回し、**hydrate 済み staging root を供給元にする** |
| R2 | lens A FULLY_DISCONNECTED 2 | 「SOURCE_DIR token を 1 つ落とせば configure が失敗する」負例は成立しない。copy 先が `<BASE_DIR>/<name>-src` だと既定命名で見つかってしまう | **real・採用。** plan の配置を変える。**copy 先 root と `FETCHCONTENT_BASE_DIR` を別 directory にする。** これで負例が本物になる |
| R3 | lens A 変異帰属1、テスト弱体化4 | `_verify_pristine_floor_dependency_sources` の呼出しを消しても、plan の全テストが緑のまま | **real・採用。** 汚れた staging fixture を入力にして job の copy+verify 断片を実走し、**赤になること**を検査する正負対で登録する |
| R4 | lens A 条件関門3、変異帰属2 | 5 token を `configure_argv` の先頭 5 要素へ動かすと `${configure_argv[@]:5}` から落ち、条件関門へ届かなくなる。これを殺すテストが要る | **real・採用。** gate stub が受け取った argv を snapshot し、silo で 5 token が届くことを検査する。**ただし stub である限り Python gate 側の消費は検査していない**と成果物へ明記する (両層 stub の限界) |
| R5 | plan、lens B 照合1 | 段 1 brief の行番号に 3 件のずれ | **real・採用。** 実アンカーを plan v2 の値へ差し替える |

### real・不採用 (scope 外 → 裁定パッケージ)

| # | 所見 | 不採用の理由 |
|---|---|---|
| P1 | silo 条件関門は masstree の `config.h` を要求するが、pristine copy には無い。D1666/D1784 は関門前に `prepare_masstree_fetchcontent` で prebuild している。本 wave の供給だけでは silo の関門は緑にならない | **T-2534 が同じ関門を対象にユーザー裁定待ち** (`docs/worklog.md:1299`)。発火経路が別タスクで塞がれている条件付き機能を足すのは `DW-G04` に反する。**「offline 供給だけで silo が通る」とは名乗らない** |
| P2 | walltime 式が 3 通り食い違う。冒頭 comment 6910、receipt `frozen_required_s` 6610、実 timeout の直列和は mocc で 7870 | **本 wave が作った不整合ではない。** 親が実測で確認済み。式の再凍結は `test_pegasus_tools.py` の凍結式検査・`calibration_v1.json`・PBS directive を同時に動かす別 wave。**本 wave は式を 1 byte も変えない** |
| P3 | `ccbench.pinned_clean=True` の意味 (CCBench 限定か全 compiler 入力か) が未定義。receipt は第三者依存の pin/commit を 1 つも記録しない | 既存の schema 契約。本 wave は field を増やさない。**「receipt が第三者入力を束縛する」とは名乗らない** |
| P4 | `--repo-root` と `PBS_O_WORKDIR` が束縛されず、repo 外から投入すると別木で job が走る | 既存の launcher 契約欠陥。**運用前提として「repo root から投入する」を成果物へ書き、実測はそれに従う** |
| P5 | CCBench 側に replace-ref 拒否が無く、第三者 verifier より弱い | 既存。本 wave の変更面外 |
| P6 | `submit_certify.sh` へ hydrate/clone を足すと、`local-ok` / `legacy-admitted (未実測)` の根拠と実処理が食い違う | **設計変更で回避する (下記 2.)。submit は clone も hydrate もしない。** よって `admission_registry.json` は 1 byte も変えない |

### refuted / 反例なし

- lens B 「mocc 固有の到達不能条件」→ 反例なし。mocc を維持する。
- lens B 「fragment 境界が壊れる」→ 反例なし。目印文字列は保つ。
- lens B 「三依存以外にネットワーク取得が残る」→ 反例なし。masstree / mimalloc / googletest の 3 本で閉じる。
- lens A 「名前解決成功を clone 成功へ一般化」→ 一般化していない。hydrate の実走で確かめる。

## 2. plan v2 (確定した実装)

**plan からの変更点は 3 つ。いずれも段 3 の real 所見による。**

### (a) `submit_certify.sh` — hydrate しない。構造 precheck だけ置く

plan は submit で `fetch_third_party.py hydrate` を実行する案だった。**採らない (P6)。**
submit は login-side で次だけ行う。git も clone も起動しない。

- `THIRD_PARTY_SOURCE_ROOT="$REPO_ROOT/output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src"`
- 実 directory・非 symlink・`masstree` / `mimalloc` / `googletest` の 3 子がいずれも実 directory かつ非 symlink
- 満たさなければ `qsub` へ進まず rc=2

hydrate は**投入前の独立手順**とする (`fetch_third_party.py hydrate`、既に `local-ok` / `runbook §7.0 実測`)。

### (b) job は staging root を自分で導出する。`qsub -v` を変えない

plan は `-v` へ `IZANAGI_CALIBRATION_THIRD_PARTY_SOURCE_ROOT` を足す案だった。**採らない。**
job は他の全入力 (policy、gflags/glog source、CCBench submodule) と同じく `REPO_ROOT` から導出する。

- `qsub` の export spec と argv が変わらないので、`test_pegasus_calibration_workload.py` の
  exact qsub pin 2 件を書き換えずに済む。
- `-v` の総長 4000 byte 制限と `,` / `=` の分解問題 (lens B) を構造的に回避する。
- 代償は submit の検査木と job の実行木が束縛されないこと。これは **P4 の既存欠陥そのもの**であり、
  本 wave は運用前提 (repo root から投入する) で凌ぎ、裁定へ返す。

### (c) copy 先 root と `FETCHCONTENT_BASE_DIR` を分ける (R2)

```
FETCHCONTENT_SOURCE_ROOT="$TMPDIR/fetchcontent-src"    # <name>-src の copy を置く。verifier の base
FETCHCONTENT_BASE_DIR="$TMPDIR/fetchcontent-base"      # CMake へ渡す。空のまま
```

`FETCHCONTENT_BASE_DIR` が空なので、SOURCE_DIR token を 1 つ落とすと
`FULLY_DISCONNECTED=ON` の下で population が見つからず configure が落ちる。**負例が本物になる。**

### 変更面 (実アンカー、plan v2 の値)

| file | 位置 | 変更 |
|---|---|---|
| `tools/pegasus/certify_calibration.sh` | `:169` protocol 検査の直後 | staging root の導出と構造検査。失敗 stage 名 `third_party_source` |
| 同 | `:535` の `# (iv-c)` comment は文字列も位置も維持。直後・`CCBENCH_BASE=` の直前 | 2 dir 作成、3 依存を `timeout` 付きで `$FETCHCONTENT_SOURCE_ROOT/<name>-src` へ `cp -a` |
| 同 | copy 直後 | `s8b_floor_campaign._verify_pristine_floor_dependency_sources($FETCHCONTENT_SOURCE_ROOT, repo_root=$REPO_ROOT)` を python3 で実行。非 0 で `write_failure 2 third_party_source` |
| 同 | `:576-580` `configure_argv` の `-DENABLE_SANITIZER=OFF` の直後 | 5 token を固定順で挿入 |
| 同 | `:389-403` / `:584-589` / `:600-601` / `:651-735` / `:686-694` | **変更しない** |
| `tools/pegasus/submit_certify.sh` | `:49` protocol whitelist の直後、`:51` job script 検査より前 | staging root の構造 precheck |
| 同 | `:189-195` export spec / qsub argv | **変更しない** |
| `orchestrator/tests/test_pegasus_calibration_workload.py` | `:113-169` | fixture 変数 `FETCHCONTENT_BASE_DIR` / `FETCHCONTENT_SOURCE_ROOT` を追加。gate stub が受領 argv を snapshot |
| 同 | `:318-345` | 名称を `..._match_offline_contract` へ改め、exact pin へ 5 token を追加 |
| 同 | `:252-264` / `:306-315` | **変更しない** (負例として残す) |

### 新規テスト (すべて既存 file 内。新規 test file を作らない)

1. `test_certify_offline_fetchcontent_contract_is_identical_for_all_protocols`
2. `test_certify_condition_gate_receives_the_same_fetchcontent_tokens` (silo のみ。mocc/tictoc は gate 0 回)
3. `test_certify_offline_configure_resolves_three_local_sources_and_fails_without_each`
   — **実 CMake で configure する。** 3 依存名を `.invalid` URL で `FetchContent_Declare` する最小 project を作り、
   copy 先を BASE_DIR と別 dir に置く。全 token あり → 成功かつ解決先が copy と exact 一致。
   SOURCE_DIR を 1 つ落とす 3 通り → **失敗**。`FULLY_DISCONNECTED` を落とす → **失敗** (ネットワーク不在下)。
4. `test_certify_job_copy_leaves_the_staging_sources_untouched_and_writable`
   — 実 fragment を走らせ、上流の bytes と inode が不変、copy 先が書込み可能であることを検査する。
5. `test_certify_job_rejects_a_staging_source_with_ignored_artifacts`
   — 汚れた staging fixture で copy+verify 断片を走らせ、**非 0 で止まる**ことを検査する (R3)。
6. `test_submitter_rejects_a_missing_or_malformed_third_party_staging_root`

## 3. 変異事前登録 (DW-M01、実装前)

| ID | 位置 | 変異 | 殺すテスト |
|---|---|---|---|
| M1 | `certify_calibration.sh` configure_argv | `-DFETCHCONTENT_FULLY_DISCONNECTED=ON` を削除 | 1, 3 |
| M2 | 同 | `-DFETCHCONTENT_SOURCE_DIR_MIMALLOC` の値を存在しない path へ | 3 |
| M3 | 同 copy+verify block | `_verify_pristine_floor_dependency_sources` の呼出しを削除 | 5 |
| M4 | 同 copy loop | masstree だけ copy し他 2 本を落とす | 1, 3 |
| M5 | 同 configure_argv | 5 token を配列先頭 (index 0-4) へ移す | 2 |
| M6 | 同 dir 定義 | `FETCHCONTENT_SOURCE_ROOT` を `FETCHCONTENT_BASE_DIR` と同一にする | 3 |
| M7 | 同 `:169` 付近 | staging root の構造検査を削除 | 6 相当の job 側検査 |

各変異は実装後に「同じ入力を拒否する層が前後にも内側にも無い」ことを確認する。
確認できないものは登録から外し、実効 gate へ再照準する (F28)。

## 4. 名乗らないこと (規律 2 / 3)

- **「offline 供給を入れたので silo の認定が通る」とは言わない。** silo の条件関門は masstree の
  `config.h` を要求し、pristine copy にはそれが無い。関門自体も T-2534 のユーザー裁定待ちである。
- **「acquisition receipt が第三者 build 入力を束縛する」とは言わない。** receipt は
  masstree / mimalloc / googletest の pin を 1 つも記録しない。記録するのは一時 path を含む argv だけである。
- **「条件関門への 5 token 転送を実測した」とは言わない。** mocc 実測は関門を 1 度も呼ばない。
  転送は shell stub 上の検査であり、Python gate 側の消費は検査していない。
- **「受理集合を緩めていない」とだけ書かない。** 判定へ到達する呼出し集合は、
  base 未供給だけを理由に前段で赤になっていた分だけ**制御された拡張**になる (D1721 / D1784 の形)。
- 完了判定は 2 段に分ける。(i) 計算ノードで offline configure と build が通ること、
  (ii) 較正 record が publish されること。(ii) が perf / cooldown / attestation / quality の
  FetchContent と無関係な理由で落ちた場合は、(i) の達成と (ii) の未達を分けて報告する。

## 5. 段 5 の分割

**1 単位。** 3 file を触るが `test_pegasus_calibration_workload.py` が 2 script 双方に掛かるため
所有 path が素集合にならない。分割せず Codex `role=author` 1 子へ渡す。
