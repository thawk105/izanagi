# [T-1799] oracle 判定後の材料再生成を禁止する (D984) — 実施記録

- wave branch: `worktree-dev-wave-t1799-post-oracle-regen-ban`
- 実施日: 2026-09-07 〜 2026-09-08 (JST)
- 起点 local main: `542bfadb8` (worktree 作成時)。段 2 起動時に `442cb549c` へ ff-only で追随。
- 実装 commit: `5ca382885` (本体)、`1b5dca9d9` (段 6 fix)
- 変異走行時の HEAD: `1b5dca9d9`

## 何をしたか

`buildcache.build_v2(post_oracle_dependency_binding=...)` の build で、configure 後に実効
build 根を `CMakeCache.txt` と `DependInfo.cmake` から読み、binding が指す source 根と
exact 一致することを **build 前に**要求したうえで、その根と配下の全 node を
`cmake --build` の間だけ書込み不能にする。判定済み材料を**同一 bytes で**作り直す build も
EACCES で拒否される。

D953 が塞いだのは判定後の**再取得**であり、判定後の**再生成**は塞がっていなかった。
D953 自身が「実効的な排他は process 間 lock を要し、書込み権威の変更として別審査に属する」と
書いており、D984 がその別審査にあたる。

## 段別の成果物 (逐語)

| 段 | 成果物 | 備考 |
|---|---|---|
| 1 | `verbatim/s1-brief.md` | 親の brief。段 3 が 2 点を反証した (下記) |
| 2 | `verbatim/s2-plan.md` | plan 起草。中心提案は段 3 で差し戻し |
| 3 | `verbatim/s3-lensA.md`, `verbatim/s3-lensB.md` | 敵対 2 レンズ |
| 4 | `verbatim/s4-adjudication.md` | 裁定 15 行 + 変異事前登録 |
| 5 | `verbatim/s5-author.md` | 実装子 |
| 6 | `verbatim/s6-reviewA.md`, `verbatim/s6-reviewB.md`, `verbatim/s6-fix1.md` | 敵対レビュー 2 本 + fix |

## 変異 matrix

`mutation-probe-spec.json` (全件 SURVIVED で観測 node を収集) →
`mutation-main-spec.json` (期待 node 完全集合で本走)。結果は `mutation-matrix.json`。

baseline PASSED / KILLED 5 / SURVIVED 0 / MISMATCH 0、期待 node 完全一致 5/5。

| ID | 変異 | 期待 node 数 |
|---|---|---|
| M1 | 実効根 exact 一致を恒真化 | 1 |
| M2 | `yield` 直前に復元して build 窓を開ける | 2 |
| M3 | `finally` の復元を削除 | 3 |
| M4 | 保護を親 directory まで広げる (過剰拒否の正例) | 1 |
| M5 | 根の書込み可能性の前提条件を恒真化 | 1 |

M2 は段 4 で「write bit 除去を no-op にする」として登録していたが、段 6 レビュー A が
「内側の `post-oracle-write-bits-remain` 検査が `yield` 前に先取りするため、狙った
同一 bytes 再書込みまで到達しない」と実測で示した。単一理由性が立たないため上記へ再照準した
(DW-M01 の「できなければ登録せず実効 gate へ再照準する」)。

M3 の期待 node には既存の `test_v2_post_oracle_cache_hit_rechecks_two_roots_before_return` が
入る。復元されない読取専用 tree が同一 worker の後続 test を巻き込むためで、
この変異に固有の検出ではない。冗長 gate として記録し、単独変異の主たる証拠は
`test_post_oracle_protection_restores_exact_modes_on_success_and_error` とする (DW-M03)。

## 実測値

- 焦点走 (段 5 後): 724 passed / 0 failed / 4 skipped、82.06 秒。
- 焦点走 (段 6 fix 後): 725 passed / 0 failed / 4 skipped、87.43 秒。
- 受入全走 1 回目: `child-green`、21364 passed / 68 skipped / 0 failed。
  claimed_main = `0e02169b0`、受入 tip = `31771b499`。
- 実物の masstree source tree: 144 node、symlink 0 件 (親が
  `/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2043-floor-receipt/evidence-bundle-965563/submission/masstree-payload/masstree-src`
  と `/work/1/SFC/tanab/izanagi-exploration-t2182/configure-probe2/_deps/masstree-src` で実測)。
- この platform で `os.chmod in os.supports_follow_symlinks` は `False`。
  regular file と directory の `chmod(follow_symlinks=False)` は成功し、symlink だけが
  `NotImplementedError` になる (親が実測)。実材料に symlink は無いので発火しない。

## 段 3 が親の brief を反証した 2 点

1. **成果物影響が誇張だった。** brief は「A-2 / A-6 の certification が材料の同一性を主張できる
   ようになる」と書いたが、2 レンズが独立に反証した。A-2 / A-6 は別 driver で generic
   `run_campaign()` を通り、post-oracle binding を渡さない。本変更が直接改善するのは
   **S8b floor の `sort_best` cell の proof chain** (binary、admission receipt、
   `sort_swo_oracle` record) である。
2. **確定裁定の一覧から D954 が落ちていた。** D954 (実効値は build 自身の成果物から読み、
   argv を証拠にしない) は本件の直接前提である。

brief は「buildcache.py の変異は drift mask に必ず吸収される」とも書いたが、
レンズ A が「吸収されるかは選んだ焦点 node 次第」と反証した。変異の狙い先を lock closure 外の
file に置く判断自体は維持した (帰属が確実なため)。

## 段 3 が段 2 案を差し戻した 2 点

1. 段 2 は既存の `s8b_expected_materialization.make_snapshot_non_writable()` を as-is 再利用する
   案だったが、同関数は **root だけでなく parent (= `FETCHCONTENT_BASE_DIR` そのもの)** の
   write bit も外す。`<base>` 直下への新規 entry 作成 (別依存の populate、
   `izanagi-masstree-prebuild`) を巻き添えで壊すため却下し、親を触らない専用の保護を書かせた。
2. 段 2 の「configure 後に読んだ `effective_root` を後段でも再利用する」は、build 後の
   root drift 検査を実質的に消して受理を広げる。絶対規律 2 に触れるため撤回した。

## 段 6 レビューが出した must-fix 2 件

- レビュー A: 上記 M2 の単一理由性 (変異の再照準で閉じた。コード変更なし)。
- レビュー B: **同じ根へ 2 つ目の保護 context が入れる。** 後から入った側が 1 つ目の
  read-only mode を「元の mode」として採取するため、非 LIFO で退出すると根が恒久的に
  読取専用のまま残る。1 つ目が先に退出すると 2 つ目の build 中に保護が消える。
  実測では official floor は cell を逐次 build するのでこの交差は届かないが、
  **本変更が自ら持ち込んだ破れ**なので直した (`1b5dca9d9`)。
  直し方は「保護に入る時点で根 directory 自身が書込み可能であることを要求する」の 1 条件だけで、
  process 間 lock は作っていない (D953 が別審査と裁定済み)。

## 開示する限界 (backlog、この wave では直さない)

- 保護は同一 uid の協調的 process に対する discretionary-mode 保護である。
  owner が自ら chmod を戻す actor と privileged actor は阻止しない。
  build 前に開いた writable fd も阻止しない。
- SIGKILL / OOM / job の壁時計切れで `finally` が走らない場合、保護した根は読取専用のまま残る。
  official floor では base が PBS job ごとの create-only な job-local root であるため、
  影響はその job の scratch に閉じる。復旧機構は作っていない。
- 復元が失敗すると `post-oracle-permission-restore-failed` が build 中の本来の例外を
  最上位から置き換え、build が成功していた場合も staging binary が破棄される
  (レビュー B の実測。診断精度が落ちる)。
- 読取専用 mount・別 owner の node・symlink を含む根は新たに拒否される。
  official staging は current owner の fresh copy なので現材料での発火証拠はない。
- 保護中に node が別 inode へ置換されると、復元は identity 照合の前に旧 mode を書く。
- **protected な実 CMake build は本 wave で実走していない。** 根拠は静的機序と、
  保存済みの非 protected build log の正例である。
