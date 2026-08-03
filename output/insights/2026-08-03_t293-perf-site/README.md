# [T-293] 共有 policy `perf_candidates` のサイト依存性 — 計算ノード実測

wave = `dev-wave-t293-perf-site`、base commit = `1a3604b`。
実測環境 = Pegasus (login = pegasus02、計算ノード = gen_S)。

## 結論 (先に書く)

**T-293 が記録していた「`perf_candidates` が stale で、指す 2 本の perf は存在しない」という
前提は、実測により誤りだと判明した。** 破綻は少なくとも **3 つの独立した原因**が重なったもので、
値の書き換えでは 1 つも解けない。

1. **候補 2 本は計算ノードに実在し、実際に動く。** 今日の実測 (bnode005 / bnode009) で
   `perf --version` と production と同じ smoke argv が **rc=0** を返し、実カウンタ値を出した。
2. **それでも production の `_executable` は解決に失敗する。** 候補 path は計算ノードでは
   **symlink** であり、`_executable` は `not Path(found).is_symlink()` を要求するためである。
   一方 shell 側 (`t126_qualification.sh`) は `[[ -x ]]` なので通る —
   **Python 経路と shell 経路で受理集合が食い違っている。**
3. **`prepare_toolchain` は perf に到達しない。** `gcc-13` / `g++-13` が login にも計算ノードにも
   無いため、解決順 (python → cc → cxx → cmake → perf) の **`cc` で落ちる**
   (`failure_stage: "cc"` を実測)。

したがって「perf の値を直す」「perf の読取サイトを移す」のいずれも、単独では T-126 qualification を
動かさない。**恒久対応の設計はこの 3 因を分けて扱う必要がある。**

## 実測値

### ログインノード (pegasus02、2026-08-03、実行を伴わない存在確認)

| 項目 | 値 |
|---|---|
| `uname -r` | `5.15.0-186-generic` |
| `/usr/lib/linux-tools/` | `5.15.0-101-generic` / `5.15.0-136-generic` / `5.15.0-173-generic` |
| policy 候補 2 本 (`135` / `100`) | **いずれも不在** |
| `perf_event_paranoid` | `4` |
| `gcc-13` / `g++-13` | 不在 |

### 計算ノード (gen_S、2026-08-03)

`request 881946` = bnode009 (probe は fail-closed、環境層のみ)、
`request 881960` = bnode005 (全層完走、rc=0)。

| 項目 | 値 |
|---|---|
| `uname -r` | `5.15.0-173-generic` (両 node) |
| `/usr/lib/linux-tools/` | `5.15.0-100-generic` と `5.15.0-135-generic` の **2 つだけ** |
| policy 候補 2 本 | **実在・実行可能。ただし `is_symlink: true`** |
| `perf --version` | `perf version 5.15.178` (135) / `perf version 5.15.143` (100)、いずれも rc=0 |
| production 同一 argv の smoke | **rc=0**、`<not supported>` / `<not counted>` なし |
| per-candidate `functional` | **false** (symlink のため production は拒否する) |
| 実物 `_executable("perf", ...)` | **`resolved: false`** — `required executable unavailable: perf` |
| 実物 `prepare_toolchain` | `ok: false`、**`failure_stage: "cc"`** |
| `perf_event_paranoid` | `0` |
| `gcc-13` / `g++-13` | **不在** |
| 既定 `python3` | `/system/apps/.../oneapi/2022.3.1/intelpython/latest/bin/python3` (3.10 未満) |

**両サイトの linux-tools の版集合は互いに素**である。runbook §1 の「全 node 同構成」前提は、
この package 集合については login と計算ノードの間で成り立たない。

### 標本の射程

この結果は **`hostname` + `observed_epoch` + `policy sha256` の 2 標本** (bnode009 / bnode005) に
限定される。gen_S の全 bnode や将来の allocation へ一般化しない。probe 自身が `sample_scope` に
同じ限定を書いている。

## 測定の妥当性 (なぜこの値を信じてよいか)

- **実コードを呼んだ。** 候補列は committed の `tools/pegasus/policy.json` から読み、
  `qualification.submission` の `_executable` と `prepare_toolchain` を**実物として**呼んでいる
  (F29: pin 対象で模擬を裁定根拠にしない)。per-candidate の smoke だけは argv の再実装であり、
  JSON 内に模擬と明記してある。
- **両側 control が同一 run で成立した** (`control_sensitivity: "two-sided-ok"`)。
  存在する実体 path は解決し (`positive = true`)、存在し得ない候補は解決しない (`negative = false`)。
  したがって perf の `resolved: false` は「resolver が何を渡しても失敗する」故障ではなく、
  **真の測定結果**である。
- **実行 bytes を 5 点で束縛した** — HEAD / policy / probe / pbs / submission の sha256 が
  期待値と一致しなければ測定を始めずに停止する (`binding.matched: true` を実測)。
- **受理述語 5 条件を親が照合した** — binding 一致、`ok: true` かつ必須 field 完備かつ rc=0、
  control 両側成立、done-marker 実在、全測定層 `attempted: true`。

## fail-closed が実際に効いた事例 (1 回目の走行)

1 回目 (`881946`) は **rc=3 / `ok:false` / `control_sensitivity: not-established`** で停止した。
`.pbs` が bare `python3` を呼び、計算ノードでそれが oneAPI 版 (3.10 未満) に解決されたため、
`qualification.submission` の import が
`TypeError: dataclass() got an unexpected keyword argument 'slots'` で失敗したのである。

**段 6 レビュー A の所見 1 を直していなければ、この走行は `ok:true` かつ `resolved:false` を返し、
「計算ノードでも候補は使えない」という誤結論を成果物へ残していた。**
測定器の故障と、正当な否定結果を分離する設計が、初回の実走でそのまま効いた。

## 段 6 の経緯 (レビュー 3 回・fix 4 巡)

敵対レビュー 2 レンズ (`s6-review-A.md` / `s6-review-B.md`) と焦点再レビュー (`s6-refocus.md`) が
**3 度とも NO-GO** を出した。所見は計 14 + 新規 3。fix は 4 巡 (`s6-fix*.md`)。
主要な閉鎖項目は本 README 冒頭の「測定の妥当性」に列挙したものである。

**当初の変異事前登録 (C1 / M1) は撤回した。** ログインノードで probe を走らせる negative control は、
候補が解決すれば login で perf を実行してしまい規律に反する。また `resolved` の反転は rc も `ok` も
変えないため DW-M03 の kill に数えられない。代替として**同一 run 内の両側 control** を probe へ
組み込み、受理述語 5 条件を親が照合する形にした (`s4-adjudication.md`)。
gate もテストも新設しないため、**変異 matrix は対象外**である。

投入前に親がログインノードで実測して 1 件潰した — 正 control に `sys.executable` を使うと必ず失敗する
(`/usr/bin/python3` は symlink で `_executable` に拒否される)。実物の `_executable` で確認し、
`Path(sys.executable).resolve()` へ直した。潰していなければ計算ノードの枠を無駄にしていた。

## 受入

計算ノードへ dispatch した全走を 3 回行い、**3 回目が緑**である。

| # | request | 結果 | 扱い |
|---|---|---|---|
| 1 | `881962` | 1 failed / 5262 passed / 19 skipped | `test_pilot_resume_rejects_launch_certificate_contamination` のフレーク。差分は当該テストへ到達せず、単独再走 (3 passed) で再現しない (DW-O18) |
| 2 | `881967` | 1 failed / 5262 passed / 19 skipped | **親の手順ミス** — fragment の節順序を直す直前に投入し、計算ノードが修正前の版を読んだ |
| 3 | `881995` | **5263 passed / 19 skipped、rc=0** | commit 済みの clean tree での受入 |

`python3 tools/check_docs.py` は違反なし。`python3 tools/spool_fold.py --dry-run` は `planned`。

## 一次資料

- 実測: `output/env/pegasus/t293-perf-site/0_881946.nqsv/` と `0_881960.nqsv/`
  (`probe.json` / `marker` / `done-marker` / `probe.rc` / `interpreter` / NQSV の `.o` `.e`)
- 逐語: 本 dir の `brief.md`、`s4-adjudication.md`、`s5-impl.md`、`s6-review-A.md`、
  `s6-review-B.md`、`s6-fix.md`、`s6-refocus.md`、`s6-fix2.md`、`s6-fix3.md`、`s6-fix4.md`
- **ユーザー裁定パッケージ**は `adjudication-package.md`
