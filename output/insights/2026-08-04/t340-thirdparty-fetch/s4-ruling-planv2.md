# 段 4 裁定 + プラン v2 — [T-340]

親が段 3 の 2 レンズ (計 18 所見) を real/refuted、採用/不採用、scope 内/外に裁定した。
判断の根拠になった実測は本文中に置く。

## 0. scope の格下げ (最重要 — A4/B6 の帰結)

**本 wave の成果物は operator preflight helper であり、proof chain の一部ではない。**

- レンズ A 所見 4 は real: 取得経路は submit receipt / provenance / evidence のどこにも値として
  漏れない (`silo_ladder_rung1.py:2394` の exact keys、`:954` の third_party_sources、
  evidence の `third_party_rederivation: sha256-chain-consistency-only`)。
  したがって brief の「由来が台帳から追える」は**偽**であり、この主張を取り下げる
- helper は**任意**であり、最終権威は凍結された shell の pin/clean 検査のままとする。
  helper を必須工程と解釈すると受理集合が変わる (helper は origin 等を追加で要求するため)。
  任意と定めることで不変条件 5 (受理集合不変) が成立する
- したがって本 wave が閉じるのは「**worktree を畳んでも消えない、pin 検証つきの取得と
  offline 供給の実行経路を repo 内に持つ**」ことだけである。「取得の由来が証明される」とは
  書かない

## 1. 採用する所見 (scope 内・実装する)

### R1 — hydrate は copytree を廃止し fresh clone にする (レンズ A 所見 1 = real, blocker)

`git status --untracked-files=all` は **ignored file を列挙しない**。masstree の `.gitignore` は
`*.a` と `/config.h` を無視し (実測)、`ThirdParty.cmake:57-78` はまさにその
`libkohler_masstree_json.a` / `config.h` を ExternalProject の OUTPUT として扱い再生成を省く。
cache を `copytree` すると、pin 一致・clean のまま改竄済み archive を staging へ運べる。

**採用する形:** hydrate は cache から `git clone --no-hardlinks --no-checkout <cache> <stage>` →
`git -C <stage> checkout --detach <pin>` で **fresh worktree** を作る。
`copytree` は使わない。これは凍結 submitter (`submit_silo_ladder_rung1.sh:174-183`) と同型で、
transport だけを GitHub から cache に替えたものになる。

### R2 — Git metadata の fail-closed 拒否 (レンズ A 所見 2 = real, blocker)

cache と publish 後 staging の双方で次を拒否する (repo 内の先例:
`t080_freeze_migration.py:619` が shallow/replace/grafts/alternates を拒否、
`submit_t126_qualification.sh:114` が assume-unchanged/skip-worktree を拒否)。

- shallow (`.git/shallow` の存在)
- alternates (`.git/objects/info/alternates` の存在)
- partial/promisor clone (`remote.origin.promisor`, `extensions.partialclone`)
- replace refs (`refs/replace/` が非空)
- grafts (`.git/info/grafts`)
- `.git` が directory でない (linked worktree の `.git` file)
- sparse checkout (`core.sparseCheckout` が真、または `.git/info/sparse-checkout` の存在)
- index の `assume-unchanged` / `skip-worktree` bit (`git ls-files -v` の小文字/`S` tag)

**`ThirdParty.cmake:46` が `GIT_SHALLOW FALSE` を明示している**ことが shallow 拒否の直接の根拠。

### R3 — Git 子プロセスの hardened 環境 (レンズ A 所見 3 = real, blocker)

`core.fsmonitor` / `core.sshCommand` / filter / `include.path` は git 実行時に任意 command を
起こしうる。全 git 呼び出しを次で固定する (先例: `t080_freeze_migration.py:541`)。

- env: `GIT_CONFIG_NOSYSTEM=1`、`GIT_CONFIG_GLOBAL=/dev/null`、`GIT_NO_LAZY_FETCH=1`、
  `GIT_TERMINAL_PROMPT=0`、`GIT_ASKPASS`/`SSH_ASKPASS` 除去、`GIT_ALLOW_PROTOCOL` を
  操作ごとに固定 (fetch = `https`、offline 操作 = `file`)
- `-c core.fsmonitor=` `-c core.hooksPath=/dev/null` `-c protocol.version=2`
  `-c uploadpack.*` は触らない
- cache の `.git/config` を **git を起動する前に**素の text として読み、
  `core.fsmonitor` / `core.sshCommand` / `core.hooksPath` / `filter.` / `include` /
  `includeIf` / `url.*.insteadOf` / `remote.*.uploadpack` / `remote.*.receivepack` が
  現れたら rc=1 で拒否する

### R4 — publish は mkdir 予約 + rename (レンズ B 所見 4 = real, blocker。親の実測でレンズより強い)

親の実測 (2026-08-04、pegasus02):

| base | renameat2(NOREPLACE) on dir | os.link(dir) | rename→空 dir | rename→非空 dir | mkdir 排他 |
|---|---|---|---|---|---|
| /home/SFC/tanab | EINVAL | EPERM | 置換成功 | ENOTEMPTY | EEXIST |
| /work/1/SFC/tanab | EINVAL | EPERM | 置換成功 | ENOTEMPTY | EEXIST |
| /tmp | ok | — | — | — | — |

runbook:508 は `/home` だけを挙げるが **`/work` も EINVAL**。calibrator の link+unlink fallback は
**directory には使えない** (`os.link` が EPERM)。

**採用する形:** publish は `os.mkdir(destination)` で排他予約 (EEXIST = 衝突 → rc=2) し、
その空 directory へ `os.rename(stage, destination)` する。予約と rename の間で落ちた場合は
空 directory が残り、次回の検査が「pinned-clean でない」で必ず止まる (fail-closed)。
`renameat2` は使わない。

### R5 — (P1) 却下。cache root は明示必須 (レンズ A 所見 6 / レンズ B 所見 5 = real)

**却下の決め手 (親の実測):** `~/github/gflags` と `~/github/glog` は **shallow clone** である
(`.git/shallow` が存在)。masstree/mimalloc/googletest とは管理形態が異なり、
「gflags の親 = 5 本共通 cache」という推論は現地の実体に反する。

**採用する形:** cache root は次の順で解決し、どちらも無ければ rc=2 で停止する。

1. `--cache-root <絶対 path>`
2. 環境変数 `IZANAGI_PEGASUS_THIRDPARTY_CACHE`

policy.json からの導出はしない。repo 配下 (repo root の resolve 済み prefix) は rc=2 で拒否する。
Pegasus での具体値は **runbook (機体固有事実の正本) に親が書く**。コードと横断 docs には
machine path を入れない。

### R6 — CLI 表面の整合 (レンズ B 所見 8 = real, must-fix)

- subcommand: `fetch` (network 可) / `hydrate` (offline) / `verify` (offline, cache のみ) /
  `verify-deps` (offline, policy の gflags/glog readiness のみ)
- 成功時は versioned JSON 1 個を stdout へ出す
  (`{"schema_version": "pegasus-thirdparty-fetch/v1", "operation": ..., "cache_root": ...,
  "sources": [{"name","pin","resolved_path","head"}...]}`)。
  `qsub -v IZANAGI_THIRDPARTY_SOURCE_ROOT=$(... | jq -r .cache_root)` が 1 行で書けること
- 失敗は stderr へ 1 行 + rc。rc=1 = source contract 違反、rc=2 = 運用・引数・policy 異常
- `verify` と `verify-deps` を分けるのは、別 host で三 source だけ検査したいときに
  tanab 固定の gflags/glog 欠落で止まらないようにするため

### R7 — 新規テストに自走 harness を付ける (レンズ A 所見 7 = real, must-fix)

`orchestrator/tests/test_plain_runner_coverage.py:60` が、全 `test_*.py` に自走 harness
(`_run()` か実際に走る `__main__`) か allowlist 記載を機械強制する。新規テストには
`__main__` harness を付ける (allowlist へは足さない)。

## 2. real だが scope 外 (実装しない — 裁定パッケージとしてユーザーへ返す)

| # | 所見 | なぜ scope 外か |
|---|---|---|
| X1 | certify / floor / t126 / t141 / t152 は `FETCHCONTENT_SOURCE_DIR_*` を渡さない (A9/B7)。override を渡すのは rung1 driver と T-139 probe だけ (親が grep で実測) | 4 campaign の build 契約変更は凍結ファイルの再発行を伴う。裁定 (a) の対象は取得経路であって build 配線ではない |
| X2 | 取得経路を proof chain へ束縛する (acquisition receipt の新設と evidence 再発行) (A4) | 凍結 evidence の再発行は D96 手続きが要る |
| X3 | hydrate を機械的に強制する経路 (B1/B2) | 凍結 submitter の書き換えが要る |
| X4 | mimalloc の `fetchcontent_ref=v2.3.2` (annotated tag) と `pin` (SHA) の同期 gate が無い (A9/B6)。`silo_ladder_rung1.py:893` は ref が 40-hex のときしか照合しない | 凍結 driver の変更が要る |
| X5 | 同一 UID 敵対者への完全防御 (dirfd + inode pinning) (A5) | preflight helper に対して不釣り合い。R1〜R4 で実行可能な範囲は閉じ、限界を docs に明記する |

## 3. 却下した所見

- **B1 の「probe wrapper を作れ」= 不採用。** 代わりに R6 の stdout JSON で
  `qsub -v IZANAGI_THIRDPARTY_SOURCE_ROOT=...` を 1 行にする。新しい wrapper script は
  未分類 script を 1 本増やすだけで、T-139 probe は一回限りの生死確認用であり常用経路ではない
- **A8/B3 の「実装前に資源分類を裁定せよ」= 不採用 (手順として不要)。**
  runbook §7.0 は分類の**手順**を与えており、裁定ではなく実測で決まる。
  親が実装後に §7.0 の専用 scope + `memory.current` sampling で 4 subcommand を各 3 回測り、
  certified peak = 観測ピーク + max(25%, 128MiB) を規範値 512MiB と比較して分類する。
  測定手順が本機で動くことは親が確認済み (`python3 -c print` で 3.4MiB を取得)

## 4. 変異事前登録 (DW-M01)

実装後、次の一行変異それぞれについて「赤くなるテストが 1 つに絞れる」ことを確認する。
kill = 受理集合か fail-closed 挙動が期待方向へ変わったときだけ数える (DW-M03)。

| # | 変異 (一行) | 期待して赤くなるテスト |
|---|---|---|
| M1 | `third_party_policy()` 呼び出しを raw JSON load に置換 | policy/CMake drift 検出 |
| M2 | hydrate の fresh clone を `shutil.copytree` に戻す | ignored artifact 混入検出 |
| M3 | shallow 拒否を落とす | shallow cache 拒否 |
| M4 | alternates 拒否を落とす | alternates 拒否 |
| M5 | replace refs 拒否を落とす | replace refs 拒否 |
| M6 | `--untracked-files=all` を落とす | untracked dirty 検出 |
| M7 | HEAD == pin 比較を常に真にする | HEAD 不一致検出 |
| M8 | origin url 比較を常に真にする | origin 差し替え検出 |
| M9 | final component の symlink 拒否を落とす | symlink source 拒否 |
| M10 | publish の `os.mkdir` 予約を落とし `os.rename` 直行にする | 既存 destination の非置換 |
| M11 | 既存 source 分岐へ `git fetch` を 1 行足す | 既存 clone を更新しない |
| M12 | hardened env の `GIT_CONFIG_GLOBAL=/dev/null` を落とす | global config 由来の insteadOf 無効化 |
| M13 | cache root の repo 内包含チェックを常に偽にする | repo 内 cache 拒否 |
| M14 | `.git/config` の危険 key 拒否を落とす | fsmonitor 等の拒否 |
| M15 | publish 後の再検証を落とす | publish 後検証 |

## 5. 成果物影響 (DW-G05)

- **R1〜R4 を入れない場合:** cache から staging へ ignored build artifact・shallow/replace 細工・
  config 由来の command 実行が入り、凍結 shell の pin/clean 検査を通過する。
  `third_party_heads` は正しい pin のまま、build 入力だけが pin と異なる tree になりうる。
  certified な選択結果の binary が pin と一致しない可能性が残る
- **R5 を入れない場合:** 既定 cache root が shallow clone の親を指し、fetch が
  他管理主体の directory に repo を作る。別 host では既定自体が成立しない
- **R6/R7 を入れない場合:** consumer (T-139 probe) が cache root を機械的に取れず、
  新規テストが素の runner で偽緑になる
- **X1〜X5 を放置した場合:** rung1 以外の campaign は FetchContent の network 取得へ落ちる。
  取得経路は台帳から追えないままになる。いずれも本 wave の受理集合は変えない
