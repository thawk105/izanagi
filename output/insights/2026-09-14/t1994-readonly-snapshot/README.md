# [T-1994] build 中の source 差し替えを封じる sealed snapshot — 実装と実測

- 日付: 2026-09-14
- wave: `dev-wave-t1994-readonly-snapshot` (branch `worktree-dev-wave-t1994-readonly-snapshot`)
- base main: `f5423e2ff`
- 先行: `output/insights/2026-09-01/t1994-readonly-snapshot-design/` (設計と生死確認、実装ゼロ)

## 何を閉じたか

D966 が逐語で名指しした 4 経路のうち残っていた **「build 中の source 差し替え (A→B→A)」** を閉じる。
D1201 が正式受入の前提とした「読み取り専用の束縛または同等の実効的な不変 snapshot を
計算ノードで実証する」に対し、D1439 が裁定した 4 点で実装した。

**閉じていないもの (成果物として明記する):**

- **「汚染 cache binary の再利用」は閉じていない。** D966 の別経路であり、
  D966 自身が別手段 (compiler input manifest の保存) を挙げている。
- capability は **trusted producer の信頼境界内**での実行由来の値である。
  kernel attestation でも電子署名でもない。Python 自身を敵対者に含める型偽造不能性は主張しない。
- **実 CMake の qualification は未完走である。** driver は実装したが、
  一度きりの計算ノード artifact はまだ取れていない。

## 生死確認 (段 5 の最初に実施。DW-G01)

Codex author が書いた使い捨て probe 4 本を、親が **login node と計算ノードの両方**で走らせた。
生証拠は `verbatim/`。

| probe | login (pegasus02, 5.15.0-190) | 計算ノード | 結果 |
|---|---|---|---|
| 最小の read-only 束縛 | 18/18 緑 | bnode046, 5.15.0-173: 18/18 緑 | 成立 |
| root view + 後発 staging + 実 CMake | 44 緑 / 2 赤 | bnode067: 44 緑 / 2 赤 | **欠陥 1 件**、他は成立 |
| 是正案 (capability 落とし + seccomp) | 42/42 緑 | bnode067: 42/42 緑 | 2 機構とも必要十分 |
| nested userns 禁止 filter | 40/40 緑 | bnode067: 40/40 緑 | 成立、正当な子孫生成は壊れない |

**Python から直接 syscall する経路 (identity user/mount namespace + 匿名 tmpfs +
digest 再照合 + recursive read-only seal) が、login と計算ノードの両方で成立する。**
外部 command (`bwrap` / `unshare`) は一切使っていない。
親の `/proc/self/ns/{user,mnt}` は fork 前後で不変である。

### probe が見つけた欠陥 — user namespace 内では mode bits が効かない

`chmod 0444` した自分の file へ、identity map した user namespace の中から**書けてしまう。**
namespace の外では同じ操作が `EACCES` で落ちる (対照を取った)。
原因はその namespace 内で `CAP_DAC_OVERRIDE` を持つこと。

**D1755 (D984) が実装した「判定後の材料再生成の禁止」は `chmod` に依存している。**
T-1994 の user namespace を素朴に導入すると、**守るべき相手である build 子に対してだけ
その保護が無効になる。** 受理集合を広げる後退であり、絶対規律 2 に触れる。

**是正には 2 機構が両方必要だと 4 状態を分離して実測した。**

| 状態 | 実測 |
|---|---|
| (a) capability を落とす前 | **書けてしまう** (欠陥の再現) |
| (b) 全 capability を落とし `NO_NEW_PRIVS` | `EACCES` |
| (c) (b) の後に新しい user namespace を作る | **また書けてしまう** |
| (d) (b) + `CLONE_NEWUSER` を seccomp で禁止 | `EACCES`、userns 作成は `EPERM` |

(d) の状態で通常の `fork` / `execve` / **孫 process の生成**はすべて成功する。
`clone3` を `ENOSYS` で落としても glibc 2.35 は `clone` へ fallback することを ptrace で実測した
(`syscalls: [[435,"enter"],[435,-38],[56,"enter"],[56,559297]]`)。
**この fallback は glibc 2.35 で測った事実であり、他の libc へ一般化しない。**

**段 3 の 2 レンズはどちらもこの欠陥を予測していなかった。** 一方は
「同じ inode を bind すれば親の chmod は子に効く」と refuted に分類しており、
inode と mount についてはそのとおりだが capability の面が抜けていた。**実測でしか出なかった。**

## 実装

| 単位 | 内容 |
|---|---|
| S1 | `s8b_expected_materialization.py` に sealed session を追加。既存の `admitted_build_snapshot` と chmod 防護は残す |
| S2 | `buildcache.py` の fork seam と publish 延期、cache identity |
| S3 | `s8b_binary_admission.py` の受領証 v3 と consumer 追随 |
| S4 | `manual_probes/t1994_readonly_snapshot_qualification.py` (計算ノード一度きり) |

**子の中で行う順序** (契約で固定した):

1. `os.fork()`。namespace の作業は子の中だけ。**親は mount namespace を一度も変えない。**
2. `unshare(CLONE_NEWUSER|CLONE_NEWNS)`、identity uid/gid map (root へ写さない)。
3. `/` を `MS_REC|MS_PRIVATE`。
4. **`/` 直下の component に private tmpfs を被せ、spine だけ再作成し、
   共有枝だけを overmount 前に確保した fd から bind で戻す。**
5. source を exact copy (`.git` は copy しない)。
6. **copy 後の digest を copy 前と照合。**
7. `mount_setattr(AT_RECURSIVE, MOUNT_ATTR_RDONLY)` で source を seal。祖先は非再帰で seal。
8. **全 capability を落とし `PR_SET_NO_NEW_PRIVS`。**
9. **`CLONE_NEWUSER` を含む `unshare`/`clone`、`clone3`、`setns`、`mount` 系を seccomp で禁止。**
   arch 検査で x32 と i386 からの迂回も拒否。
10. seal 後にだけ compiler を exec。

親は mount namespace を変えないので、**既存の full tree 再照合・evidence 再照合・
compiler-input 採取はすべて元 tree を読み続ける。** 元 tree の持続的 drift は従来どおり拒否される。

**保護種別は exact capability の型で受け渡す** (D1439 d)。固定 literal は採らない。
発行記録に載った object だけが有効で、source snapshot / expected materialization /
binary / compiler-input manifest の 4 digest に束縛される。
`SEALED_BUILD` は「trusted producer が build と指定した command が成功し、
指定の出力を新しく作り、その bytes が発行値と一致した」ことを述べる。**compiler の計装ではない。**
cache hit は `SEALED_CACHE_HIT` として別種別で記録し、
**過去に保護された build が実行されたとは主張しない。**

## 敵対レビューと実走が見つけた欠陥 (すべて修正済み)

段 3 の 2 レンズ、段 6 の 2 レンズ + 焦点再レビュー、計算ノードでの焦点走 9 回で見つかった。

| # | 欠陥 | 見つけ方 |
|---|---|---|
| 1 | user namespace 内で `CAP_DAC_OVERRIDE` により D1755 の chmod が無効になる | probe の実測 |
| 2 | seal していたのは source root だけで、**親・祖父は seal されていなかった**。子は親 dir を退避し B を指す symlink を置いて同じ絶対 path で B を読ませられた | 段 6 レビュー (静的) |
| 3 | worker の失敗経路が `os.kill(0, SIGKILL)` に到達し**親 process ごと殺す** | 段 6 レビュー (静的) |
| 4 | cache 枝が session 開始時に未作成だと親子の staging が分離し**正当な build が壊れる**。現行テストは mock 内で cache を先に作って偶然避けていた | 段 6 レビュー (静的) |
| 5 | root view が spine の全段で兄弟 entry を列挙していた。**`/tmp` には 145,596 entry ある** | 焦点走の実測 + 親が独立に entry 数を数えた |
| 6 | 列挙をやめた構成 (親の提案) は**外側 namespace からの rename を防げなかった** | **攻撃テストが実走で捕まえた** |
| 7 | `SEALED_BUILD` が compiler 実行を確かめていなかった | 段 6 レビュー (静的) |
| 8 | 異常系に有限の上限が無かった | 段 6 レビュー (静的) |
| 9 | 受入が cell ごとに実 session を開いていた (静的に 117 関数 130 ケースへ到達) | 段 6 レビュー (静的) |
| 10 | churn helper が停止を伝えられず hang していた (timeout の問題ではなかった) | 焦点走 + 親の切り分け |
| 11 | qualification の wrapper が `build_output` を受け取れず実 build が型エラーで止まる | 焦点再レビュー (静的) |
| 12 | 親の cwd を子へ渡すが、その cwd が子の view に無い配置がある | 焦点再レビュー (静的) |

### 6 番は特筆に値する

**親が提案した設計が、別の攻撃を開き直した実例である。**

列挙が成立しないと分かったとき、親は「祖先を元の inode へ self-bind して非再帰で
read-only にする」構成を提案した。これは子の側からの rename と symlink 作成を止める。
**しかし mount は dentry に付くので、namespace の外にいる親が祖先を rename して
同じ名前で B を置くと、子の絶対 path 解決が B を辿る。**

攻撃テストは「保護の外から同じ reader・同じ絶対 path で読むと B が見える」ことを
**対照として先に確かめてから**「保護の中では A のはず」を測る形になっていた。
対照が成立したうえで保護側が B を返し、login node でも再現した。

正解は最初の probe の構成 (= `/` 直下に private tmpfs を被せて子の view を完全に private にする)
だった。**列挙をやめる過程で、その性質まで落としていた。**

## 焦点走

計算ノードで 9 回実走した。対象は本 wave が触った 12 test file と受領証 v3 の consumer test。

赤の推移: **385 → 116 → 119 → 31 → 7 → 6 → 3 → 0 → 0**

最終: **1,727 passed / 11 skipped / 0 failed、220 秒、rc=0** (request 996452)。

**既存テスト関数は 12 file すべてで 1 つも削除していない** (local main の起点と AST 比較)。
skip・xfail・期待値の反転・機構の stub は行っていない。

## 生証拠

- `verbatim/login-node-probe.txt` / `compute-node-probe-996046.log` — 最小の read-only 束縛
- `verbatim/rootview-login.json` / `rootview-compute-996091.json` — root view と実 CMake
- `verbatim/capdrop-login.json` / `capdrop-compute-996103.json` — 是正案の 4 状態
- `verbatim/seccomp-login.json` / `seccomp-compute-996101.json` — nested userns 禁止 filter
