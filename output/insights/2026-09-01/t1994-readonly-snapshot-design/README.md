# [T-1994] 実効的な不変 snapshot — 設計、生死確認、閉じられない理由

- 日付: 2026-09-01
- wave: `dev-wave-t822-arm-source-binding` (branch `worktree-dev-wave-t822-arm-source-binding`)
- base main: `259e02209`
- 実装面の差分: **ゼロ** (段 4 で「本 wave では実装しない」と裁定した)

## 何の話か

D863 が 8c 正式系列の着手条件とした証拠欠落 3 件のうち、**第 2 条件 (宣言 arm と実走 arm の
同一性) の残余**である。第 2 条件は 3 段で縮んできた。

| 段階 | 閉じたもの | task | 日付 | 根拠 |
|---|---|---|---|---|
| 1 | 宣言 arm から実 CCBench source への**文字列としての**因果束縛 (E1/E2/E3) | `[T-1749]` | 2026-08-26 | commit `1e10a081f`、worklog 979、D955 |
| 2 | 宣言した述語が build と実走へ**届いたこと**の証明 | `[T-1805]` | 2026-08-27 | worklog 1033、D966 / D1134 |
| 3 | 事前登録契約 C10 の追随 (`proposal_build_source_bindings`) | `[T-1806]` | 2026-09-01 | worklog 1141、D967 |
| **残** | **所有者自身による A→B→A の source 差し替え** | **`[T-1994]`** | 未実装 | **D1201** |

D966 は閉じる対象として 4 経路を逐語で名指しし、そのうち「build 中の source 差し替え」が残る。
D1201 (2026-08-28 ユーザー裁定) は次のとおり。

> **決定:** 所有者自身による A→B→A の差し替えを**閉じる**。読み取り専用の束縛または同等の
> 実効的な不変 snapshot を計算ノードで実証するまで、正式な受入を成立させない。

却下された選択肢は「閉じないことを正式に受理する」と「**検出だけ入れて拒否しない**」である。

## 現行実装の欠落 (実体)

防護は `orchestrator/campaign/s8b_expected_materialization.py` の
`make_snapshot_non_writable` による `chmod(mode & ~0o222)` と、snapshot root の dev/ino
前後照合である。同 module の docstring 自身が射程を逐語で認めている。

> It is not a sandbox boundary: the directory owner can restore write permission, and a
> privileged actor can rename entries despite these mode bits. Those actors remain outside
> the guarantee made here.

**所有者は書込 bit を戻せる。** D1201 の脅威モデルは所有者自身なので、この防護では閉じない。

## 生死確認 — 読み取り専用の束縛は root 権限なしで成立する

D1201 が「計算ノードで実証する」ことを要求しているので、機構を作る前に測った。

### login node (`pegasus02`、kernel 5.15.0-190-generic、2026-09-01 21:14 JST)

- `/proc/sys/user/max_user_namespaces` = 1024868
- `/proc/sys/kernel/unprivileged_userns_clone` = 1
- `bwrap` = `/usr/bin/bwrap`、`unshare` = `/usr/bin/unshare`

`bwrap --dev-bind / / --ro-bind <SRC> <SRC>` の下で、**所有者自身の `chmod u+w` が
`Read-only file system` で失敗し (rc=1)、書込も同じく失敗し、元の内容が保持された。**

### 計算ノード (`bnode024`、kernel 5.15.0-173-generic、2026-09-01 21:27 JST)

qsub Request `965574.nqsv` (queue `gen_S`、5 分枠)。生結果は `compute-node-probe-result.txt`。

- `/proc/sys/user/max_user_namespaces` = 509439
- `/proc/sys/kernel/unprivileged_userns_clone` = 1
- `bwrap` = `/bin/bwrap`、`unshare` = `/bin/unshare` (login node とは path が違う)

| 検査 | 結果 |
|---|---|
| `bwrap --ro-bind` 下で所有者の `chmod u+w` | `Read-only file system`、rc=1 |
| 同じく書き込み | `Read-only file system`、rc=1。内容保持 |
| ro-bind 下の読み取り | 成功 |
| `unshare --mount --map-root-user` + `mount --bind -o ro` | mount rc=0、書込 rc=1、内容保持 |

**独立な 2 経路が計算ノードで成立する。** kernel の版が login node と違う (190 対 173) ので、
転移を仮定せずに測った意味がある。

**ただしこれは command 経由の経路である。** 段 2 が採る「Python process から直接 syscall +
identity mapping + tmpfs + `mount_setattr(AT_RECURSIVE, MOUNT_ATTR_RDONLY)`」は計算ノードで
未検証であり、D1201 の完了にはその経路の実証が要る。

## 段 2 が起草した設計

読み取り専用の**単純な bind では足りない** — 同一 uid の別 mount namespace から下層 inode を
書くと build view にも見えるためである。設計は次になった。

1. process ごとに一度だけ identity user/mount namespace を作る (uid/gid を同じ数値へ map)。
2. snapshot の内容を private namespace 内の**匿名 tmpfs へ exact copy** する。
3. copy 後の tree digest を再照合する。
4. `mount_setattr(AT_RECURSIVE, MOUNT_ATTR_RDONLY)` で recursive read-only 化する。
5. `admitted_build_snapshot` の `yield` は seal 後にだけ進む。

`admitted_build_snapshot` は context manager で、`with` 本体で `_build_v2_impl` 全体が走る
(`orchestrator/campaign/buildcache.py:2977-3009`)。`yield` 前に現 process の mount namespace を
変えれば build と全子孫がその view を継承するので、段 2 は「`buildcache.py` 無変更で実装できる」
と判定した。

### 代案が成立しない理由 (段 2 の実測)

- `unshare` command 経由は exec 後に capability が落ちて mount に失敗する。
  syscall を Python から直接呼ぶ必要がある。
- `squashfuse` / `mksquashfs` は存在するが `/dev/fuse` が無い。erofs tooling も無い。
- `chattr +i` は初期 user namespace の capability を要する。
- checkout は `patchharness` が writable な worktree を作って patch を当てるので、
  初めから読み取り専用 filesystem へ置けない。

private tmpfs が追加 binary なしで成立する最小経路である。

## 段 3 の敵対レビュー — 段 2 の分岐点判定は覆った

2 レンズを別の射影で走らせた。レンズ `sol` は「防壁は本当に閉じるか」、レンズ `luna` は
「爆風半径」。逐語は `s3b-consult-sol.md` と `s3b-consult-luna.md`。

### `buildcache.py` を触らないと閉じない must-fix (4 件)

| 所見 | なぜ `buildcache.py` が要るか |
|---|---|
| 外側の所有者が元 root を rename すると overmount が private namespace から外れ、build は同じ pathname から B を読む。**cache への publish は `with` の cleanup より前**に起きるので、汚染された binary が cache に残り、次走で A の key に hit する | publish (`buildcache.py:2814-2823`) を防護検査の後ろへ動かすか、context manager へ cache key を渡す |
| build の子孫が nested user namespace を作り、snapshot 内へ writable mount を重ねられる。exec 後に capability が落ちても子は新しい namespace を作れる | build subprocess の起動点 (`buildcache.py:3376-3392`) で禁止する。repo 内の別 sandbox は `--disable-userns --assert-userns-disabled` で閉じている (`orchestrator/codex_roles/launcher.py:562-580`) |
| 既存の full tree / evidence 再照合 (`buildcache.py:2423-2428, 2549-2552, 2707-2709, 2760-2766`) が overmount 中は tmpfs を読むため、**元 tree が copy 後に B へ変わったままでも通る**。旧 gate が拒否していた元 tree の持続的 drift を受理する = **受理集合の拡大** | unmount 後に元 tree の full digest / evidence を再照合し、失敗時は publish 済み cache を無効化する |
| user namespace は build 区間で終わらない。元の namespace へ戻れないので、Python parent は以後 binary store、perf、numactl、benchmark、journal の全 subprocess をその中で走らせる (`orchestrator/campaign/s8b_floor_campaign.py:7415-7710`) | build だけを fork した子で隔離する = 起動点の変更 |

**親が独立に裏を取った。** `_build_v2_impl` は `os.rename(clean_name, bdir_name)` で publish して
から return する (`buildcache.py:2814-2823`)。これは `with` の内側なので、context manager の
`__exit__` で検出しても publish 済み binary は取り消せない。

### `buildcache.py` 無しで閉じられる must-fix / should-fix

- snapshot の外へ解決する symlink が閉じていない。tree digest は symlink target を**文字列として**
  hash するだけで target bytes を含まない (`s8b_expected_materialization.py:389-428`)。
  **実測: 現 `external/ccbench` checkout に symlink は 0 件**なので、外向き symlink の拒否は
  今日の受理集合を狭めるだけで正当な build を壊さない。
- 順序は `copy → recursive seal → sealed digest → evidence → yield` にすべき
  (現案は seal 前に digest を計算するので、外側 parent が `/proc/<pid>/root/` 経由で seal 前の
  tmpfs へ到達できる)。
- 単一 thread 検査は `threading.enumerate()` ではなく `/proc/self/task` の実 OS thread 数で行う。
  `orchestrator/` には実際の `ThreadPoolExecutor` と fork がある。
- unmount 失敗後は process を永久 poison し、以後の build を全拒否する。
  floor は同一 process で複数 cell を連続 build する。
- tmpfs の容量根拠。段 2 の「約 12 MB」では足りない。**実測**: `external/ccbench` は
  apparent 12,213,725 bytes、`.git` 除外後 1,438 files / 267 directories / raw 11,111,504 bytes、
  4 KiB page 丸めで 14,434,304 bytes。

### 恒真になる設計 (採用しない)

`proof.source_protection_kind` を固定 literal として receipt へ足す案は、issuer が caller の
渡す 2 digest の形式的一致しか検査しないため (`s8b_binary_admission.py:183-230`)、
**防護 context を実行した証拠にならない。** kind は低レベル context が生成した exact capability
として型で受け渡す必要がある。固定文字列の自己申告を proof に数えてはならない。

### 変異候補の検証

段 2 が挙げた 5 件のうち **4 件は KILLED 見込み**だが、5 件目 (after-build dev/ino 照合の削除) は
**KILLED にならない** — root 交換は dev/ino 検査より先に mount を消し、unmount failure が同じ
拒否を起こすため、記述された replacement test では変異が生存する。

## テスト所要 — 実 CMake canary を受入へ入れてはいけない

段 2 は pytest 内で実 `buildcache.build_v2` を通す統合テストと、`test_s8b_floor_campaign.py` の
canary を実 build へ変える案を出した。レンズ `luna` が正本と実測で否定した。

- D311: 開発を進めるほどテスト時間が増える状況を避ける。非飽和で 1.1 倍なら land しない。
- D678: main への着地は 1 タスクあたり 5 分以内。
- 現 canary が受入台帳で `0.0` 秒なのは**速いからではなく `gcc-13` 不在で skip している**ため。
- 同型実測 (D665): cold CCBench build 単独 17.96〜18.16 秒、受入並列負荷下 42.90〜50.39 秒。
- 概算: `stock_common` + `sort_best` で cold 下限約 60 秒、受入換算 86〜101 秒。
  全 12 cell なら受入換算 515〜605 秒。

**分離案**: 毎回の pytest には「別 process の実防護 + attacker subprocess の正例・負例」だけを
残し、実 CMake は計算ノードで一度きりの qualification artifact へ切り出す。
正しさゲートを弱めずに繰返し費用だけを外せる。

## 正当な build を壊さないか (P3)

レンズ `luna` の静的検査では、**凍結済み 12 cell に snapshot 自体への CMake 書込み経路は無い。**

- `file(WRITE)` の protocol matrix は `${CMAKE_BINARY_DIR}` へ出る。
- source 側へ書く唯一の到達可能な custom command は masstree の `config.h` / object / archive で、
  出力先は `masstree_SOURCE_DIR`。正式経路ではこれが staging の `_deps/masstree-src` か
  外部 dependency tree に解決され、snapshot 内を指す組合せは現 freeze に無い。
- depfile (`-MD -MF`) も staging 側。

残る risk は **ccache** である。CCBench は PATH 上に ccache があれば自動 launcher 化し
(`external/ccbench/CMakeLists.txt:20-29`)、build subprocess は親環境を継承する。
現 login node には ccache も `CCACHE_*` も無かったが、計算ノードで `CCACHE_DIR` 等が
snapshot 内を指せば正当な compile を壊す。計算ノード qualification で実効 ccache 設定を
保存し、snapshot 外であることを要求する必要がある。

## 受領証 v3 の費用 (実測)

- schema literal の実体は `s8b_binary_admission.py:39` の 1 箇所だけ。
- **発行済みの実 v2 受領証は現 worktree / main / 既知 mainprobe の `output/` に 0 件。**
  失われる正式成果物は無い。
- 凍結成果物の再発行は不要。`holdout_freeze.json` と `floor_protocol.json` は receipt を含まず、
  campaign lock の exact 24 閉包に該当 module は無く、C10 の 13 field は S8b receipt の
  内部 schema field を pin していない。
- ただし中央 validator の production consumer は 9 箇所ある (floor の 5 経路、oracle preflight、
  ratified freeze、holdout freeze、historical floor stats)。

## なぜ本 wave で実装しないか

上表の must-fix 4 件が `orchestrator/campaign/buildcache.py` を要求する。同 file は稼働中の
別 wave が所有している (2026-09-01 21:14 JST 実測: `t441-author` が staged `M`、
`worktree-dev-wave-t441-grammar-version-canon`、`fix-dev-wave-t441-1..3`、
`worktree-dev-wave-t1905-b10-formal-run`)。依頼は「重なる file は触らずに報告する」である。

**部分実装は採らない。** 脅威を閉じない機構に防護の名を付けることは、D1201 が却下した
「検出だけ入れて拒否しない」と実質同じで、D955 と絶対規律 2/3 が禁じる恒真な保証になる。

なお `s8b_expected_materialization.py`、`s8b_binary_admission.py`、その consumer 5 module、
対応する test 3 file は**編集面の重複が 0 件**である (branch の三点 diff・全 worktree の
未 commit 差分の両方で確認)。塞いでいるのは `buildcache.py` 1 file だけである。

## ユーザー裁定へ返す設計択一

1. **user namespace の残留をどう扱うか。** 「process ごとに一度だけ unshare」は build 後の
   store / perf / benchmark / journal を全部その中へ入れる。build だけを fork した子で隔離する形へ
   変えるべきか。後者は `buildcache.py` の変更を要する。
2. **`buildcache.py` の所有が空いた後に、上の修正条件を織り込んで実装へ進めてよいか。**
3. **実 CMake の qualification をどこへ置くか。** 毎回の受入から外し、計算ノードで一度きりの
   artifact にする案でよいか。
4. **`proof.source_protection_kind` を型 (exact capability) で受け渡す設計**を採るか。
   固定 literal は恒真なので採らない。

## 一次資料

- `s2-plan.md` — 段 2 のプラン全文
- `s3-consult-sol.md` / `s3-consult-luna.md` — 段 3 前半 (第 2 条件の状態を検査した 2 レンズ)
- `s3b-consult-sol.md` / `s3b-consult-luna.md` — 段 3 後半 (プランを攻撃した 2 レンズ)
- `compute-node-probe-result.txt` — 計算ノードでの読み取り専用束縛の実測生結果
