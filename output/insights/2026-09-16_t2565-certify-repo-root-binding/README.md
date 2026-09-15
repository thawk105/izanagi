# [T-2565] certify 投入の検査木と job の実行木を qsub の cwd で束縛した

- 対象 commit: `4a25f5a1c27b38e00d6707f41b4c3d51125f404b` (branch `worktree-dev-wave-t2565-certify-repo-root-binding`)
- base: `61e0e9c4a48d08c92526f5026c4cd017b150b898`
- 実測日: 2026-09-16 (JST)

## 1. 何が壊れていたか

`tools/pegasus/submit_certify.sh` は `--repo-root` で指定された木に対して clean 検査 (`:110`)、
HEAD 取得 (`:105`)、policy 読み込み (`:72-73`)、third-party staging の構造検査 (`:52-65`) を行う。
一方 job 側 `tools/pegasus/certify_calibration.sh:46` は `REPO_ROOT=$(cd "$PBS_O_WORKDIR" && pwd -P)`
であり、`PBS_O_WORKDIR` は qsub を実行した cwd である。**両者を結ぶ機構が無かった。**
qsub argv (`:211`) にも cwd を固定する指定は無い。

`PBS_O_WORKDIR` が投入時の cwd になることは、本 wave で新たに測ったのではなく既存の実測記録による。
`output/insights/2026-09-07/a1-pilot-attempt-0002/README.md:144` に、job `981331.nqsv` の
`pbs_o_workdir` が投入元の専用 worktree `submit-tree` の絶対 path だったと記録されている。

## 2. 既存の防御はどこまで効いていたか (主張の限定)

job 側には部分的な防御がある。自分の木の下に submit receipt が現れるのを 60 秒待ち (`:207-216`)、
自分の木の HEAD と clean を検査し (`:221-225`)、receipt の `source_commit`・job script hash・
request ID・project・queue・nodes・walltime・ratio・protocol・非 dry-run を照合する (`:240-259`)。
多くの食い違いはここで fail-closed になる。

**したがって「木が食い違えば certified 成果物が偽になる」とは書けない。** 本 wave の段 3 が
親のこの断定を real 所見として退けた。`pinned_clean` は `certify_calibration.sh:823-825` で
CCBench の属性として書かれる field であり、全入力の checkout path 一致を表さない。
job は third-party source を `:598-630` で pinned-pristine 検証し、CCBench の HEAD と clean を
`:632-636` で確認する。

**成立するのはここまで:** submit 側の検査が job の実行木に掛からない。submit が検査した
third-party staging (`output/` 配下 = clean 検査の除外対象) と job が実際に使う staging の
同一性は誰も検査しない。照合を通せる入力は存在する (submit script の所在木・`--repo-root`・
投入元 cwd を別々に指定し、commit と script hash を揃えた場合)。

## 3. 直した内容

1. qsub 実行を `( cd -- "$REPO_ROOT" && "${qsub_cmd[@]}" ) >… 2>…` の subshell にした。
   **リダイレクトは括弧の外**に置く。cd より前に投入元 cwd で開かれるため、相対 `--attempts-root` の
   保存先は変わらない。`set +e` 配下なので `&&` が必要で、cd 失敗時は qsub を起動せず cd の rc が返る。
2. 相対 `--job-script` を argv 構築の直前に**投入元 cwd 基準**で絶対化した。存在確認 (`:67`) と
   sha256 (`:117`) が解決した先と同じ基準であり、submit が検査した file がそのまま qsub へ渡る。
   既定値は `:13,15` により既に絶対なので、既定入力の argv は 1 bit も変わらない。
3. 絶対化では `CALLER_CWD=$(pwd -P && printf '.')` / `CALLER_CWD=${CALLER_CWD%$'\n.'}` として
   **directory 名末尾の改行を保持**する。素朴な `$(pwd -P)` は command substitution の仕様で
   末尾改行をすべて落とすため、cwd 名が改行で終わる場合に検査した file と別の file を投入しうる。

qsub の option 構成、`-v` export spec、`pegasus-pre-submit/v1` と `pegasus-submit-receipt/v1` の
schema は変えていない。絶対化は `job_script_path` の生成 (`:159,182,195`) より**後**なので、
receipt の記録値も既定・絶対・相対のいずれでも変わらない。

## 4. 不変条件を 1 つ緩めた

親 brief は当初「qsub argv を 1 bit も変えない」を不変条件に置いた。段 2 と段 3 がこれと
「相対 `--job-script` の参照先を保つ」が両立しないことを示したため、段 4 で次へ置き換えた。

> qsub の option 構成・export spec・両 schema は変えない。**既定入力および絶対 `--job-script` 入力では
> argv を 1 bit も変えない。** 相対 `--job-script` 入力に限り、submit が検査・hash した file を
> 指し続けるために path 表現を絶対化する。

byte 単位の不変を優先すると「submit が検査した bytes と qsub が読む bytes が別」という経路を
新設することになる。検査を素通りする経路を増やす向きなので、不変条件の方を譲った。

## 5. 実測値

- 焦点走 (`test_pegasus_calibration_workload.py` + `test_pegasus_tools.py`):
  実装後 **143 passed / 赤 0**、fix 後 **144 passed / 赤 0**。
- 変更した test file の単独走: **74 passed / 赤 0**。
- 所要台帳の被覆率 (`test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`):
  **1 passed**。追加ケースが台帳に無くても 90% を割らないことを実測し、台帳更新は不要と確定した。
- 全史 provenance 監査: **10270 件・新規違反なし**。
- 変異 matrix: `mutation/` に spec と report を凍結。baseline **PASSED**、
  **KILLED 6/6・SURVIVED 0・MISMATCH 0・PARSE_ERROR 0・期待 node 完全一致**。

変異の観測 node (probe で実測し、本走の期待値に採った完全集合):

| 変異 | 内容 | 殺した node 数 |
|---|---|---|
| M1 | `cd -- "$REPO_ROOT" &&` を削除 | 6 |
| M2 | `cd -- "$REPO_ROOT"` を `cd -- "$PWD"` へ | 6 |
| M3 | 相対 job-script の絶対化ブロックを削除 | 3 |
| M4 | 絶対化の基準を `REPO_ROOT` へ変更 | 3 |
| M5 | リダイレクトを subshell の内側へ移す | 1 |
| M6 | 改行保持の sentinel を外す | 1 |

**M3 / M4 / M6 は厳密な単一理由性を満たさない。** 同じ不正状態を同一 node 内の後続 assertion も
検出する (焦点再レビューが `T:1792,1800,1863-1865` で特定)。因果は「異なる script の選択」に
絞れるが、冗長 gate であることを明記して単独変異の証拠としては最初の殺傷点だけを根拠にする。

初回 probe は全件 SURVIVED 登録で観測 node を集めたため MISMATCH 6 件になった。これは設計どおりで、
`mutation/mutation-report-probe.json` に残してある。

## 6. 主張しないこと

- 本修正を通した実 scheduler の観測は行っていない。fake qsub で確かめたのは
  **submit が起動するプロセスの実 cwd** までである。`PBS_O_WORKDIR` の値そのものは §1 の既存実測を根拠とする。
- 既存 certify receipt の値が偽であったとは主張しない (§2)。
- 「木が食い違う入力はもう無い」とは言えない。相対 PATH 要素と検査後の差し替え (TOCTOU) は残る (§7)。

## 7. scope 外へ送った real 所見 (実装していない)

ユーザー裁定が「本題の修正だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」と
定めたため、次は直していない。

1. **相対 PATH 要素。** `PATH=bin:/usr/bin:/bin` のように相対要素があると、cd 後は
   `REPO_ROOT/bin/qsub` を探索する。既定・絶対 `--job-script` でも起こる。qsub を事前解決する案は
   `test_pegasus_tools.py:1669-1731` の「dry-run で cluster command を要求しない」既存契約と衝突する。
2. **CDPATH と相対 `--repo-root`。** `:30` の `$(cd "${2:?}" && pwd -P)` は `CDPATH` が設定されていると
   cd の出力と pwd が連結される。`--repo-root -P` はオプションとして解釈される。既存欠陥である。
   同型は `:13,14` にもある (本 wave が新規に足した `cd -- "$REPO_ROOT"` は絶対・物理 path を受けるので
   この問題を持たない)。
3. **job 側 hash 照合の射程。** job が hash するのは `$TOOLS/certify_calibration.sh` (`:227`) であって
   実行中の spool script ではない。script 取り違えをこの照合が必ず捕捉するわけではない。
4. **任意 `--attempts-root` の job 側配送。** submit (`:31,125-128`) と job (`:50,208`) の非対称は残る。
   異なる保存先を指定すると job は receipt を見つけられず待機検査で止まる。

## 8. 運用事故 1 件

変異 probe の初回投入が `orphan-hold` で起動前に中止した (rc=2、`phase: collection`、
`source_state: unchanged`、`dirty_paths: []`)。原因は親が**同じ worktree から 2 種類の dispatch を
並行させた**ことである — 全史 provenance 監査 (計算ノードへ dispatch される) の走行中に変異 probe を
投入した。`DW-O26` の「同一 worktree からの dispatch は全種を直列にする」に反する。

復旧は hold 自身が指示する順序で行った。`qstat` で対象 job (999882 / 999897) の終端を確認 →
dirty path なしを確認 → clean/HEAD を確認 → sidecar
(`probe-report.json.orphan-stop.json`) を手動削除 → 新しい `--out` / `--attempt-out` /
`--wrapper-attempt` で再投入。**手動 `qdel` は F47 のラッチを武装させるため使っていない。**
変異は 1 つも注入されておらず、木は clean のままだった。

## 9. 一次資料

- 段 1 brief / 段 2 plan / 段 3 敵対相談 2 本 / 段 4 裁定 / 段 5 実装 / 段 6 レビュー 2 本・fix・
  焦点再レビュー: `verbatim/`
- 変異 spec と report (probe と本走): `mutation/`
