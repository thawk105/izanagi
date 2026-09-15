# [T-2565] 段 4 裁定 — プラン v2 と変異事前登録

裁定 inbox (`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/`) を段 4 直前に再走査した。
最新 file は 2026-09-08 で、本 wave 開始 (2026-09-16) 以降の更新は無い。
`submit_certify` / `T-2565` / `PBS_O_WORKDIR` / `repo-root` の検索も 0 件。取り込む更新なし。

## 1. 親 brief の訂正 (段 3 の real 所見を採用)

### 1-a. 不変条件を置き換える

**旧 (brief):** 「qsub argv・export spec・receipt schema を 1 bit も変えない」

**新:** qsub の option 構成 (`-o` / `-e` / `-v` とその値の作り方)、export spec、
`pegasus-submit-receipt/v1` / `pegasus-pre-submit/v1` の schema を変えない。
**既定入力および絶対 `--job-script` 入力では argv を 1 bit も変えない。**
相対 `--job-script` 入力に限り、submit が存在確認 (`submit_certify.sh:67`) と
hash (`:117`) を行った file を指し続けるために path 表現を絶対化する。

**理由:** byte 単位の不変条件を優先すると、相対 `--job-script` で「submit が検査した bytes と
qsub が実際に読む bytes が別物」という経路を新設することになる。これは検査を素通りする経路を
増やす向きであり、規律 2 の面で不変条件の方が譲る。段 3 luna も同じ向きを提案した。

### 1-b. DW-G05 の成果物影響を弱める

**旧 (brief):** 「receipt の `source_commit` / `pinned_clean` が実行木の全入力を指さないため、
registry に登録される `calibration_ref` の provenance が偽になる」

**新:** submit 側の検査 (clean・HEAD・policy・third-party staging 構造) が、job が実際に使う木に
掛からない。job 側の再検査は自分の木に対しては効くが、**submit が検査した staging と job が使う
staging の同一性は誰も検査しない。**

**理由:** 段 3 sol の指摘どおり、`pinned_clean` は `certify_calibration.sh:823-825` で CCBench の
属性として書かれる field であり、全入力の checkout path 一致を表さない。job は third-party source を
`:598-630` で pinned-pristine 検証し、CCBench の HEAD と clean を `:632-636` で確認する。
「木が違う」から「既存 receipt の値が偽」は導けない。

### 1-c. 完了判定を観測範囲に合わせる

**旧 (brief):** 「job 側の `PBS_O_WORKDIR` が一致することを実走テストで示す」

**新:** fake qsub で、submit が起動するプロセスの実 cwd が `REPO_ROOT` になることを実測する。
`PBS_O_WORKDIR` = qsub 実行時の cwd という対応は既存実測
(`output/insights/2026-09-07/a1-pilot-attempt-0002/README.md:144` — job `981331.nqsv` の
`pbs_o_workdir` が投入元 `submit-tree` の絶対 path だった) を根拠とし、
**本修正を通した実 scheduler 観測は行わない。** この区別を worklog と insight に書く。

### 1-d. 相対 `--attempts-root` の絶対化は不要

brief の「両引数とも cd 前の絶対化が要る」は過剰だった。リダイレクトを subshell の外に置けば、
`SUBMISSION_DIR` は cd より前に投入元 cwd 基準で開かれる。`:31,125-133` は変更しない。

### 1-e. (P2) の条件を正確にする

brief の「同じ commit・clean なら照合が通る」は十分条件として過大。job 側 `:240-259` は
commit 以外に script hash・request ID・project・queue・nodes・walltime・ratio・protocol・
非 dry-run も照合する。**「submit が検査した木と job の木が別でも照合を通せる入力は存在する」
という存在主張までが real** であり、それが本 wave の動機として十分である。

## 2. プラン v2 (実装する内容)

1. **`submit_certify.sh:223` の qsub 実行を subshell 化する。**
   `( cd -- "$REPO_ROOT" && "${qsub_cmd[@]}" ) >"$SUBMISSION_DIR/qsub.stdout" 2>"$SUBMISSION_DIR/qsub.stderr"`
   リダイレクトは括弧の**外**に置く。`set +e` 配下なので `&&` が必要で、cd 失敗時は qsub を起動せず
   cd の rc が返る。`:224-229` の rc 保存・伝播はそのまま使う。
2. **相対 `--job-script` を argv 構築前に絶対化する。** 絶対化の基準は投入元 cwd
   (= `:67` の存在確認と `:117` の hash が解決した先) とする。既定値は `:13,15` により既に
   絶対なので既定 argv は変わらない。
3. `--repo-root` / `--attempts-root` / preflight / receipt 生成は変更しない。

## 3. scope 外へ送る real 所見 (実装しない。裁定パッケージとして記録する)

- **相対 PATH 要素と qsub の解決先 (段 3 luna、real)。** `PATH=bin:/usr/bin:/bin` のように相対要素が
  あると、cd 後は `REPO_ROOT/bin/qsub` を探す。既定・絶対 `--job-script` でも起こる。
  **不採用の理由:** 実運用の PATH に相対要素は無く、これに備えるのはユーザー裁定が名指しで scope 外と
  した「仮想リスク向けの gate・検査の追加」に当たる。qsub を事前解決する案は、
  `test_pegasus_tools.py:1669-1731` の「dry-run で cluster command を要求しない」既存契約とも衝突する。
  留保として insight に記録する。
- **CDPATH と相対 `--repo-root` / `--repo-root -P` (段 3 luna、real・既存欠陥)。**
  `:30` の `$(cd "${2:?}" && pwd -P)` は `CDPATH` が設定されていると cd の出力と pwd が連結される。
  `-P` はオプションとして解釈される。**不採用の理由:** 本 wave が作る欠陥ではなく、本題 (検査木と
  実行木の束縛) とも別の面である。新規に足す `cd -- "$REPO_ROOT"` は絶対・物理 path を受けるので
  この問題を持たない。留保として insight に記録する。

## 4. real / refuted 裁定表

| 出所 | 所見 | 裁定 | 扱い |
|---|---|---|---|
| sol | (P2) の十分条件が過大 | real | 採用 — 1-e で訂正 |
| sol | DW-G05 の provenance 断定が強すぎる | real | 採用 — 1-b で訂正 |
| sol | 完了判定と観測範囲の差 | real | 採用 — 1-c で訂正 |
| sol | 相対 job-script の bytes 分離 | real | 採用 — プラン v2 の 2 で実装 |
| sol | 束縛の根拠が無い | refuted | 親が独立実測で裏取り済み (1-c の出典) |
| sol | 負例が必然的に恒真 | refuted | `cwd=C` で投入すれば修正前は C を観測する |
| sol | 既定でも argv 維持が不可能 | refuted | `:13` の `pwd -P` で既定は既に絶対 |
| sol | scope 内に成立する第三案がある | refuted | 段 2 の制約衝突は反証されなかった |
| sol | 規律 2 を緩める | refuted | job 側 fail-closed 経路を削除も迂回もしない |
| luna | subshell で rc が失われる | refuted | `:222-229` と整合。ERR trap は未定義 |
| luna | 相対 SUBMISSION_DIR が R へ移る | refuted | 外側リダイレクトで C 基準のまま。1-d で brief を訂正 |
| luna | 相対 PATH 要素の影響 | real | **scope 外** — 3 で記録 |
| luna | CDPATH / `-P` の既存欠陥 | real | **scope 外** — 3 で記録 |
| luna | 既存 fixture で非 dry-run を組めない | refuted | `test:1501-1526,435-448,455-473` で組める |
| luna | helper はそのままでは使えない | real | 採用 — fixture 作成を切り出す。既存 wrapper の引数・返却値・既定動作は保つ |
| luna | 親 brief の実測表現が強すぎる | real | 採用 — 1-c |
| luna | receipt に argv が無い | real | 採用 — 照合を request ID と表示 argv に分ける |
| luna | 相対 script 衝突 file は clean 検査に掛かる | real | 採用 — 両木の `output/custom.sh` を使う |
| luna | registry / runbook の連動変更が要る | refuted | 変更しない |
| luna | `test_pegasus_tools.py` に追加の直接参照 | real | 採用 — qsub の事前解決を入れないことで守る |
| luna | 他 submit / README へ波及 | refuted | 変更しない |
| luna | plan が新 gate を持ち込む | refuted | subshell 化と局所 fixture 共通化は既存経路の修正 |
| luna | argv 不変を優先すると本題が未完 | real | 採用 — 1-a |
| luna | 任意 attempts 配送の新機構が要る | refuted | 作らない |
| luna | 不変条件が衝突している | real | 採用 — 1-a |

## 5. 変異事前登録 (DW-M01)

実装面の差分があるので変異 matrix は免除しない。位置は実装後に anchor (old 逐語) を確定し、
`DW-M07` に従って fix 後の最終 commit で再検証する。期待 node は `DW-M08` の完全集合として
実装後に確定する。単一理由性 (同じ入力を拒否する層が前後・内側に無いこと) は実装後に確認し、
成立しなければ登録せず実効 gate へ再照準する。

| ID | 変異 | 期待 |
|---|---|---|
| M1 | `cd -- "$REPO_ROOT" &&` を削除する (修正前の姿へ戻す) | repo 外 cwd の負例テストが KILLED |
| M2 | `cd -- "$REPO_ROOT"` を `cd -- "$PWD"` にする | 同上 (束縛が投入元 cwd のまま) |
| M3 | 相対 `--job-script` の絶対化を削除する | 相対 script 衝突テストが KILLED |
| M4 | 絶対化の基準を投入元 cwd から `REPO_ROOT` へ変える | 相対 script 衝突テストが KILLED |
| M5 | リダイレクトを subshell の内側へ移す | 相対 attempts テストが KILLED |

## 6. 段 5 の分割

実装面は 1 単位。所有 path は `tools/pegasus/submit_certify.sh` と
`orchestrator/tests/test_pegasus_calibration_workload.py` の 2 file で素集合。Codex 実装子 1 本。
