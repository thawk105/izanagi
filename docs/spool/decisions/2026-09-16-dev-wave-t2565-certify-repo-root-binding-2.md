---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-16
wave: dev-wave-t2565-certify-repo-root-binding
seq: 2
---

## {{D:certify-submit-job-tree-binding}}. 認定投入は qsub の cwd で検査木と実行木を束縛し、相対 job script の参照先維持のために argv の byte 不変を譲る

**決定:** `tools/pegasus/submit_certify.sh` は qsub を `REPO_ROOT` を cwd とする subshell
(`( cd -- "$REPO_ROOT" && "${qsub_cmd[@]}" )`) で起動し、リダイレクトは subshell の**外**に置く。
相対 `--job-script` は argv 構築の直前に**投入元 cwd 基準**で絶対化する。絶対化では
`$(pwd -P && printf '.')` と `${…%$'\n.'}` によって directory 名末尾の改行を保持する。

不変条件は次のとおりとする。qsub の option 構成・`-v` export spec・`pegasus-pre-submit/v1` と
`pegasus-submit-receipt/v1` の schema は変えない。**既定入力および絶対 `--job-script` 入力では
argv を 1 bit も変えない。** 相対 `--job-script` 入力に限り、submit が存在確認と sha256 を行った
file を指し続けるために path 表現を絶対化する。

`certify_calibration.sh` 側には検査を足さない。

**理由:**

- submit 側の検査 (clean・HEAD・policy・third-party staging の構造) は `--repo-root` の木に掛かるが、
  job 側は `PBS_O_WORKDIR` から木を導出しており、両者を結ぶ機構が無かった。`PBS_O_WORKDIR` が
  qsub 実行時の cwd になることは既存の job 実測で裏付けられる。cwd を合わせれば、argv も receipt も
  変えずに束縛が成立する。
- リダイレクトを subshell の外に置くのが要である。中に入れると相対 `--attempts-root` の保存先が
  実行木側へ移る。外に置けば cd より前に投入元 cwd で開かれるため、既存の相対 attempts 入力の
  意味が保たれる。
- **byte 単位の argv 不変と、相対 job script の参照先維持は両立しない。** cwd を変えれば同じ相対 argv は
  実行木側の file を指し、元の file を指し続けるには argv の値を変えるしかない。前者を選ぶと
  「submit が存在確認と hash を行った bytes と、qsub が実際に読む bytes が別」という経路を新設する。
  検査を素通りする経路を増やす向きなので、不変条件の方を譲る。既定入力では既定値が絶対 path なので
  argv は変わらず、既存の受理集合も狭めない。
- 絶対化で末尾改行を保持するのは、素朴な command substitution が directory 名自身の末尾改行まで
  落とし、検査した file と別の file を投入しうるためである。本決定が閉じようとしている食い違いの
  再発型なので、実装の一部として扱う。
- job 側に検査を足さない。job には既に receipt 待ち・自木の clean 検査・複合照合があり、
  submit 側で cwd を合わせれば本件は閉じる。投入側の欠陥を受け側の検査で代替しない。

**却下した選択肢:**

- job 側で `PBS_O_WORKDIR` と repository の一致を検査する — 先行例 `paper_story_a1_paired.sh` が
  この形を持つが、比較対象の両辺がどちらも `PBS_O_WORKDIR` 由来であり、正規化済み絶対 path なら
  恒真になる。独立した束縛ではない。
- 供給や repo root を `qsub -v` で job へ渡す — export spec と receipt の形が変わる。
  既に別決定が同じ理由でこの案を却下している。
- 相対 `--job-script` を拒否する — 既存の公開入力であり、受理集合を狭める。
- 相対 `--attempts-root` も絶対化する — 外側リダイレクトで投入元基準に保たれるため不要で、
  むしろ既存の保存先を動かす。
- `CDPATH` / 相対 PATH 要素 / 検査後の差し替えへの対処を同時に入れる — いずれも本件とは別の層の
  既存欠陥であり、本決定の射程外とする。別項目として次の一手へ送る。
