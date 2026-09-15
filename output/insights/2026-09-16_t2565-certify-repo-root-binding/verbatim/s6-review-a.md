## 絶対化の正しさ

**real — must-fix（P2）：投入元 cwd の末尾改行が失われる。**

[`submit_certify.sh:212`](tools/pegasus/submit_certify.sh#L212) の `$(pwd -P)` は、出力末尾の改行をすべて削除する。ディレクトリ名自身の末尾改行も対象となる。

具体例（`\n` は実際の改行）：

- 投入元 cwd：`/work/caller\n`
- `--repo-root /work/repo`
- `--attempts-root /work/repo/output/env/pegasus/calibration/attempts`
- `--job-script job.sh`
- `/work/caller\n/job.sh` は正規 certification script のコピー。
- `/work/caller/job.sh` は別内容の script。

存在確認 `submit_certify.sh:67` と hash `:117` は前者を読むが、`:212` は `/work/caller/job.sh` を生成し、`:214,226` は後者を投入する。script 引数自身には改行がないため、既存の hash 出力処理の問題を前提としない。

**成果物影響：成功した qsub の request ID に、実際に投入した script と異なる `job_script_sha256` を持つ submit receipt が結び付く（`:251-277`）。**

修正は、物理 cwd の取得で末尾改行を保持すること。例えば sentinel を付けて取得後に除去し、`pwd` の失敗も伝播させる。

**refuted — 通常のパスで途中の cwd 変更・変数再代入が別 file を指させる。**

`JOB_SCRIPT` の入力代入は `:32`、次の代入は `:212`。それまでの `cd` は command substitution 内（`:13,14,30`）で、`git -C` も親 shell の cwd を変えない。`:67` → `:117` → `:212` は同じ投入元 cwd を基準にする。

静止した filesystem では、symlink と `..` は文字列のまま維持され、物理 cwd の前置によって同じ対象へ解決される。空白、script 引数内の改行も引用と配列により保持される。ただし「任意の改行パスで安全」は上記反例で成立しない。

## subshell の rc と副作用

**refuted — subshell が rc を失う、または cd 失敗後に qsub を実行する。**

`submit_certify.sh:225-232` は正しい。

- `set +e` 配下なので失敗直後に親 shell が終了しない。
- `cd && qsub` により、cd 失敗時は qsub を起動しない。
- Bash の cd が存在しない・非 directory・検索権限不足で失敗すると rc は `1`。subshell も `1` を返す。
- 外側リダイレクトが成功し、保存先が書込可能なら `qsub.rc` に `1\n` を書き、submit も `1` で終了する。
- cd 成功時は qsub の rc をそのまま保存・伝播する。
- submit に ERR trap はなく、`-E` による追加副作用はない。ここに pipeline もない。

リダイレクトは cd 前に投入元 cwd で開かれるため、相対 attempts の保存先は変わらない。親 shell の cwd も不変。

なお、最初から不正な `--repo-root` は通常 `:30` で終了し、`qsub.rc` 自体を作らない。後段の cd 失敗は、途中で削除・権限変更された場合などに該当する。「読めない」が read 権限だけの欠如なら、検索権限があれば cd は成功し得る。

## receipt への波及

**refuted — 絶対化後の `JOB_SCRIPT` が `pre-submit.json` に渡る。**

実際の順序は以下である。

1. `submit_certify.sh:159` で Python に渡す。
2. `:182,195` で `job_script_path` を生成・保存する。
3. **その後** `:211-213` で絶対化する。

| 入力 | 今回の変更による `job_script_path` の変化 |
|---|---|
| 既定入力 | 変わらない |
| 絶対入力 | 変わらない |
| 相対入力 | 変わらない。元の相対文字列を従来どおり処理する |

`pegasus-pre-submit/v1`（`:180`）と `pegasus-submit-receipt/v1`（`:259`）の schema・field 構成も変更なし。最終 receipt は保存済み pre-submit から作り、絶対化後の変数を参照しない（`:251-277`）。

## 残る穴

**real — 上記の cwd 末尾改行による script 取り違えが残る。**

したがって、全入力について「穴は無い」とは判定できない。

**refuted — 通常の入力で、3 オプションの組合せだけから別の実行木へ逸れる。**

裁定済みの scheduler 対応と、静止した filesystem・正規 job script を前提にすると：

- repo-root は既定でも明示でも、検査に使った値へ qsub が cd する（submit `:52,72,105,110,226`）。
- job は `PBS_O_WORKDIR` から木を選ぶ（job `:46-51`）。
- job-script は既定・絶対入力を維持し、通常の相対入力は投入元の同じ file を渡す（submit `:211-214`）。
- attempts は実行木を選ぶ入力ではない。job の固定配送先と異なれば、通常は receipt 待ちで拒否される（job `:50,208-216`）。

明示した job-script が repo 外にあること自体は、正規 script の木選択を変えない。ただし任意内容の custom script に正規 job の規律まで保証する実装ではない。

## fail-closed への影響

**refuted — 正規 job の拒否条件が直接緩和された。**

変更は job 側に触れておらず、以下はそのまま有効：

- receipt 不在で終了：`certify_calibration.sh:207-216`
- dirty tree で終了：`:223-225`
- commit・script hash・request ID・資源条件・ratio・protocol・非 dry-run の全条件照合：`:240-259`

**real — script 取り違えを、この hash 照合が必ず捕捉するわけではない。**

job が hash する対象は実行中の spool script ではなく、`$TOOLS/certify_calibration.sh`（`:227`）。上記反例で、検査済みコピーと repo 内の正規 script が同じなら、取り違え先がこの照合処理を保持した別内容でも `:243` は一致し得る。

これは certified 成果物の不正受理を実証した主張ではない。しかし、今回の変更が作る script の不一致を既存 gate が必ず閉じる、という反論は成立しない。

## scope 外の real

以下は **real・backlog、must-fix には含めない**。

- **相対 PATH：** `PATH=bin:/usr/bin:/bin` では cd 後の `repo-root/bin/qsub` が解決対象になり得る（submit `:214,226`）。段 4 の既裁定どおり。
- **CDPATH／repo-root のオプション解釈：** `:30` の `cd` 出力混入や `--repo-root -P` は既存問題。
- **任意 attempts の配送：** submit `:31,125-128` と job `:50,208` の非対称性は残り、異なる保存先では receipt 不在で拒否され得る。
- **検査後の差し替え：** script の symlink や repo directory を検査後に交換する競合は、path の絶対化だけでは防がない（submit `:67,117,226`）。既存の時間差の問題として留保する。

## 総括

**静的レビュー結果：must-fix 1 件。**

`submit_certify.sh:212` の command substitution が投入元 cwd の末尾改行を削除し、検査済みとは別の script を投入し得る。段 4 が求める「同じ file を指し続ける」を満たす修正が必要。

通常入力の repo-root 束縛、subshell の rc 伝播、外側リダイレクト、receipt schema 維持は妥当。編集・commit・pytest・scheduler 実走は行っていない。