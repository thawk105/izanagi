# [T-2625] sealed snapshot の実 CMake qualification — 計算ノードで取得

- 日付: 2026-09-15
- wave: `dev-wave-t2625-sealed-snapshot-qualification`
  (branch `worktree-dev-wave-t2625-sealed-snapshot-qualification`)
- base main: `0600887d9`
- 先行: `output/insights/2026-09-14/t1994-readonly-snapshot/` (実装と生死確認)

## 何を取ったか

D1439(c) が「実 CMake の qualification は毎回の受入から外し、計算ノードでの一度きりの artifact と
する」と定めたその artifact を取った。[T-1994] は実装と変異 10 件 KILLED まで着地していたが、
**qualification は一度も走っていなかった。**

**成立した (job 999363.nqsv、bnode001)。** `overall=true`、check 59 件すべて緑、赤 0 件、
3 build case (`stock_common:aba` / `sort_best:none` / `stock_common:persistent`) が完走。
生証拠は `verbatim/qualification-999363.json`
(原本は `output/insights/2026-09-14/t1994-readonly-snapshot/qualification/run-xeo5_8qs/`)。

| 項目 | 値 |
|---|---|
| CCBench pin | `511c9538e4e8efa54b45cda62e72389ed3b706ec` |
| freeze / holdout | `output/s8b-freeze/holdout_freeze.json` sha256 `315b1eb8…` / `rr80` |
| 環境契約 sha256 | `e576e9cd…` |
| kernel / libc | 5.15.0-173-generic / glibc 2.35 |
| toolchain | `/usr/bin/x86_64-linux-gnu-{gcc,g++}-11`、`/usr/bin/cmake` |

## 攻撃は実際に発火し、阻止された

- **A→B→A (`stock_common:aba`)。** 保護外の compiler が同じ絶対 path で B を読むことを**対照として
  先に確かめた**うえで、封止内の compiler は A を読み続け、build が成功した
  (`:attack_executed_and_blocked`、`:compiler_A`、`:real_build`)。
- **persistent (`stock_common:persistent`)。** B を残したまま build させ、親側が B を拒否し
  (`:parent_rejected_B`)、binary も completion も公開しなかった (`:no_publish`)。
- **封止 (`:seal`)。** source は `ro ... - tmpfs` の mount 上にあり、`chmod` は EROFS、
  書き込みは拒否、内容は不変、`.git` は不在、copy inventory は準備時と一致した。
  capability 集合はすべて空で `NoNewPrivs=1`、seccomp filter 下で `unshare`/`clone` は EPERM、
  `clone3` は ENOSYS になった。

## 主張しないこと (driver 自身が挙げる限界をそのまま転記)

- **汚染 cache binary の再利用は閉じていない。** 測っているのは build 中の source 差し替えだけである。
- capability は **trusted producer の値**であって kernel attestation でも電子署名でもない。
- 敵対的な Python process memory の改変は信頼境界の外である。
- `clone3` の ENOSYS fallback は**観測した libc と command にだけ**及ぶ。
- qualification した freeze entry は各 configuration **1 件**である。

加えて、本 wave の実測から次も主張しない。

- **`chmod` の EROFS を「mount-ro の一意な証明」とは書かない。** 所有者の chmod は mode bits では
  拒否されないので mount-ro の witness として強いが、LSM 等で同じ errno を返す余地は排除していない。
  成立の根拠は `chmod_errno` と mountinfo の `ro` / `tmpfs` と書込み拒否の**連言**である。
- **contract id を再導出へ通したことは、contract id 自体の独立再検証ではない。** 再導出の入力を
  準備側と揃えただけであり、contract id の正当性は準備側の契約一致と oracle PASS 要求が担う。
- **ambient `CMAKE_PREFIX_PATH` は build identity の経路としては本番と同じ**だが、
  本番 job script が別 artifact に残す変更履歴 (`previous_value` / `effective_value` /
  `overwritten` / `recorded_epoch`) の同等記録は driver 側に無い。provenance 全体が同一とは書かない。

## 一度も走っていなかったために残っていた欠陥 4 件 (すべて実走で出た)

| # | 欠陥 | 出た場所 |
|---|---|---|
| 1 | 依存 prefix が無く masstree 事前構築の configure が gflags 不在で落ちる | job 998862 (bnode098)。0.31 秒で `Could NOT find gflags` |
| 2 | `stock_common` の 2 case が base dir と dependency receipt の対必須検査に抵触し build 前に死ぬ | job 998873 (bnode016)。`session_commands=0` |
| 3 | 条件 gate の supply-effectuation に offline 供給が届かず configure が失敗する | 同上。`SORT_VARIANT:supply-effectuation:configure-failed` |
| 4 | 封止内の書込みが EROFS でなく EACCES を返す / oracle 束縛 configuration の src_token が必ず食い違う | job 999210。3 case とも封止 session へ到達したうえで発現 |

**1 は driver の欠陥ではなく供給側の不足**で、親が policy pin の source から gflags/glog を構築して
`env CMAKE_PREFIX_PATH=...` を generic argv に載せて解決した。2〜4 は driver と機構の実在欠陥である。

### 事前検査が偽の緑を出した例 (記録に値する)

最初に login node で `find_package(gflags REQUIRED)` を最小 cmake で試すと緑になった。
これは**別 wave の残骸** (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t756-fn2-trace-v2/emitter-probe2/prefix`)
を CMake の **user package registry** 経由で拾っていただけだった。login にも計算ノードにも system の
gflags/glog は無い。CCBench は自前の `cmake/Findgflags.cmake` を module path の先頭に置くので、
config mode で成立しても module mode の反証にならない。**事前検査は本番と同じ finder で行う。**

### 封止内の書込みが EACCES になる理由

判定後の材料再生成を禁じる既存機構 (`make_snapshot_non_writable`) が **file と directory の
write bit をすべて落とす**ため、`open(O_WRONLY)` は mount の read-only 検査より先に権限検査で
拒否される。封止が効いていないわけではない。require は「書込みが拒否されること」を求める形へ改め、
mount-ro の要求 (`chmod` の EROFS と mountinfo) は据え置いた。

### 封止 snapshot は oracle 束縛 configuration を通せなかった

封止側の evidence 再導出が `sort_oracle_contract_id` を受け取らないため、準備側 token と
**必ず**食い違っていた。[T-1994] 以前からある機構側の限界であり、本 wave で受け渡しを通した。
`src_token` の不一致拒否と evidence 全体の比較は変えていない。

## 検査

- **焦点走 (13 test file):** 1459 passed / 3 skipped / 0 failed、rc=0、79 秒。
- **変異 matrix: 11/11 KILLED、SURVIVED 0、MISMATCH 0、baseline 緑、期待 node 完全一致。**
  spec と ledger は `verbatim/mutation-spec.json` / `verbatim/mutation-ledger.json`。
  緩和した `:seal` の require は、**mode bits だけの状態を拒否する負例** (`[chmod-dac-only]`) と
  **未承認 errno を拒否する負例** (`[unapproved-write-errno]`) が守っている。
- 既存テスト関数の削除・改名、期待値の緩和、skip・xfail の追加はしていない。

## 敵対レビューが親の説明を縮めさせた

`verbatim/s6b-adversarial-review.md` に逐語。親は「`chmod` の EROFS は mount-ro でしか説明できない」
「token 一致は contract id の独立検証になる」と書こうとしたが、どちらも成立しないと指摘された。
**所見は「新たに不正を受理する経路は見つからない」だが、説明の射程は縮める必要があった。**
本 README の「主張しないこと」はその縮約である。

## 運用上の事故 1 件

焦点走の dispatcher を detached でない背景 job として起動したところ走行中に殺され、
計算ノードの job だけが生き残って `pending-qsub` の orphan hold が 1 件残った。
この状態では以後の dispatch が全部止まる。**計算ノードへの投入は必ず `nohup setsid` の
detached 経路から行う。** 復旧は hold 自身が書く手順 (qstat で終端を確認 → source の clean/HEAD を
確認 → 手動削除) に従い、手動 `qdel` は使わなかった。
