## 現行挙動

以下の行番号は現行ファイル基準。検査対象の木を **R**、投入元 cwd を物理パスにした木を **C** とする。

**submit は R を検査するが、job は C を使う。親の見立ては、追加条件付きで支持する。**

| 処理 | submit 側 | job 側 |
|---|---|---|
| 木の決定 | `tools/pegasus/submit_certify.sh:13-14,30` で R を決定 | `tools/pegasus/certify_calibration.sh:46` で `PBS_O_WORKDIR` から C を決定 |
| policy | submit `:72-93` で R の policy を読む | job `:47-49,119-147` で C の policy を読む |
| staging | submit `:52-65` で R の構造を検査 | job `:186-201` で C の構造を検査 |
| source | submit `:105-112` で R の HEAD と clean を検査 | job `:221-225` で C の HEAD と clean を検査 |
| receipt | submit `:125-133,248-278` で指定の attempts 配下へ保存 | job `:50,208-216` で C の固定 attempts 配下を探索 |
| qsub | submit `:211` で argv を構築、`:223` で cwd を変えず実行 | その投入元 cwd を使う |

経路ごとの結果は次のとおり。

1. **C が通常の repo 外ディレクトリ**
   - submit の R が正常なら投入まで進める。
   - job は C 配下へ出力ディレクトリを作ろうとする（`:50-57`）。作成失敗、policy 不在（`:119-125`）、staging 不在（`:186-201`）などで停止する。
   - policy 不在なら receipt 待ちより前に rc=2。常に「60 秒後に失敗」ではない。

2. **C が別の有効な checkout、attempts は既定値**
   - submit は R の attempts へ receipt を書く。
   - job は C の attempts を探すため、共有・別途配置がなければ `:207-216` で最大 60 回待って rc=2。
   - この経路は fail-closed。

3. **receipt は C から見えるが、source 等が不一致**
   - C が dirty なら job `:223-225` で rc=2。
   - commit、job script hash、request ID、project、queue、nodes、walltime、ratio、protocol、dry-run 状態の不一致は `:240-259` で停止する。
   - Python の照合失敗は rc=2 固定ではなく、通常 rc=1 を ERR trap（`:91-98`）が記録する。

4. **別 checkout で照合を通る経路**
   - `--attempts-root C/output/env/pegasus/calibration/attempts` を指定する。
   - R と C が同じ commit で、両方とも source 面が clean。
   - submit がハッシュした `JOB_SCRIPT`（submit `:117`）と C の `tools/pegasus/certify_calibration.sh`（job `:227`）が同じ bytes。
   - 両側の policy 等が照合条件を満たし、receipt が待機時間内に現れる。

   この場合、job `:240-257` に **R と C のパス同一性の検査はなく、照合を通る**。親の「同じ commit・clean」は通常の同一 checkout 内容なら成立するが、それだけを十分条件とするのは不正確。

両側の clean 検査は `output` を除外する。したがって、この照合の通過は R と C の third-party staging 内容の一致を証明しない。後続の認定処理まで必ず成功する、という意味でもない。

## 先例の評価

`tools/pegasus/paper_story_a1_paired.sh` の値の流れは次のとおり。

```text
:127       PBS_O_WORKDIR → cd + pwd -P → REPO_ROOT
:588       REPO_ROOT を Python に渡す
:591       PBS_O_WORKDIR の元文字列も渡す
:601-606   repo_raw → Path(...).resolve(strict=True) → repo
:747-748   pbs_o_workdir と str(repo) を比較
```

**独立した submit 側の期待パスとの比較ではない。**

厳密には恒真ではない。symlink 経由、末尾 `/` など、元文字列と正規化後のパスが違えば拒否する。しかし、`PBS_O_WORKDIR` が正規化済み絶対パスなら同一性条件は恒真となり、別 checkout を指していてもこの比較自体は通る。

よって、この形を本 wave の束縛策として採用しない。なお、先例の receipt 内 argv 照合（`:723-732`）は別の検査であり、その効力まで否定するものではない。

## 修正プラン

**P1 の「qsub の実 cwd を R にする」という方向は妥当。ただし、相対 `--job-script` の意味維持と「argv を 1 bit も変えない」は、一般には両立しない。現条件で全面採用可能な完成案とは判定できない。**

### 1. cwd を変更する箇所

`tools/pegasus/submit_certify.sh:223` の実行部分を、次の形にするのが最小の変更単位となる。

```bash
  (
    cd -- "$REPO_ROOT" &&
      "${qsub_cmd[@]}"
  ) >"$SUBMISSION_DIR/qsub.stdout" 2>"$SUBMISSION_DIR/qsub.stderr"
```

- `cd` が失敗した場合は qsub を実行しない。`:222` の `set +e` 配下なので、`&&` が必要。
- subshell の rc は既存の `:224-229` で保存・伝播する。
- `:211` の argv 構築、`:205-208` の export spec、両 schema は変更しない。
- 親 shell の cwd を維持し、preflight と receipt 書込みの解決先を維持する。

これは **既定または絶対パスの `JOB_SCRIPT` について成立する変更形**である。

### 2. 相対 `--attempts-root`

この subshell 方式なら絶対化は不要。

`:223` のリダイレクトを括弧の外に置けば、相対 `SUBMISSION_DIR` は投入元 cwd で解決される。前後の `:128-198,226,231,248-280` も親 shell の元の cwd で動く。未作成の相対 attempts ディレクトリも、既存の `mkdir -p` のまま扱える。

したがって、`:31,125-133` は変更しない。親 brief の「両引数とも cd 前の絶対化が要る」は、attempts については必須ではない。

### 3. 相対 `--job-script` に残る制約衝突

現行では次のすべてが投入元 cwd 基準である。

- `:67` の存在確認
- `:117` のハッシュ
- `:223` の qsub による script 読込み

例えば C の `jobs/custom.sh` を渡すと、cwd 変更後は qsub が R の `jobs/custom.sh` を読む。同名ファイルがなければ失敗し、別内容なら検査済み bytes と異なる script を投入しかねない。

これを元のファイルへ固定する絶対化は、`:211` の最終 argv 要素を変更する。**argv の式を変更しなくても、実際に渡る値は変更される。** brief `:12-13` の「1 bit も変えない」に反するため、今回の採用案には含められない。

相対引数の一律拒否や、R 配下への代替ファイル作成も採用しない。したがって、上記 subshell 変更だけを全入力対応の実装として author に渡すことはできない。

## テストプラン

対象は `orchestrator/tests/test_pegasus_calibration_workload.py`。**dry-run の argv 表示だけでは cwd 修正を検証できないため、fake qsub を使って非 dry-run 経路を実行する。**

### fixture の利用

- `:1501-1526` の clean Git fixture と staging 作成を共通 helper に切り出す。
- 既存 `_run_submit_dry_run_in_clean_fixture`（`:1492`）の既定動作、返却値、既存テストの期待値を維持する。
- 新規テスト専用に、`:435-448` と同様の一時 `fake-bin` を用意する。
- `qstat`、`pegasusinfo`、`rbudgetcheck`、`check_quota` は成功する stub とする。
- fake qsub は絶対パスの観測ファイルへ実 cwd、argv、script の bytes/hash を保存し、`Request 12345.server submitted` を返す。
- `PATH` の fake-bin は絶対パスで設定する。実 qsub、計算ノード、認定本走を使わない。

### 追加するケース

| ケース | 検査内容 |
|---|---|
| 正例：cwd=R、既定 script | submit 成功、qsub cwd=R、receipt の request ID と観測 argv が一致 |
| 回帰例：repo 外 C から `--repo-root R` | submit 成功、**観測 cwd=R かつ C ではない**。現行 `:223` なら赤になる |
| 別 checkout C、同じ commit・clean | receipt 配置を C の固定 attempts に向けても、qsub cwd は R。commit 一致で木の違いを見逃す回帰を捕捉 |
| 相対 attempts | C 基準の未作成・空白入り相対パスへ指定。全 capture、rc、両 JSON が C 側の指定先に残る |
| qsub 失敗 | stub が例えば rc=7。submit rc=7、`qsub.rc` と stderr 保存、submit receipt 不在を確認 |

別 checkout は同じ fixture commit から作り、staging は各木の `output` 配下へ作成する。これにより、木の同一性を commit の違いで代用しない。

相対 `--job-script` については、次の**仕様衝突を表すケース**も必要になる。

- C と R に同じ相対名で異なる内容の script を置く。
- 要求する観測値は「cwd=R」「argv の script 文字列は元の相対値」「読んだ bytes は C 側」。
- 単純な cwd 変更は bytes の条件を破り、絶対化は argv 条件を破る。

このケースを黙って除外して全面対応を報告しない。

実装後は既存テストを含む対象ファイルを `tools/run_tests.py` 経由で実行する。本段では編集・テスト実行は行っていない。

## 受理集合の変化

**既定・絶対 `JOB_SCRIPT` の成立範囲では、新しい入力拒否条件を設ける必要はない。** 相対 attempts、repo 外 cwd、別木を指定する `--repo-root` を引き続き受理できる。

相対 `JOB_SCRIPT=j` に単純な cwd 変更だけを適用すると、従来 C/j を読めた入力のうち、R/j を qsub が読めない入力が新たに失敗する。R/j が読めても別内容なら、拒否されずに投入対象が変わる。このため、その案を受理集合維持とは扱えない。

また、submit の受理と job の完遂は区別する必要がある。`--attempts-root` を C の固定 attempts に向ける入力は修正後も submit が受理できるが、job は R を使うため、R から receipt が見えなければ既存の待機検査で停止する。これは意図する木の束縛による変化であり、新しい submit gate ではない。

全入力について拒否を増やさず意味も維持する案は、厳密な argv 不変条件の下では成立していない。

## 残る不確実性

- **仕様上の未解決点:** P1 が要求する相対 script の絶対化と、brief の byte 単位の argv 不変条件が衝突している。「オプション構成だけ不変」と読み替える根拠はない。
- **実測範囲:** fake qsub は submit が設定する実 cwd を検証できる。実 scheduler が生成する `PBS_O_WORKDIR` 自体は本テストでは実測しない。
- **保証の範囲:** cwd 束縛は検査木と実行木の選択を一致させる修正であり、投入後のファイル変更を防ぐ保証ではない。

## 総括

親の不具合認識と P2 は、script hash 等の一致条件を補えば正しい。先例の cwd 比較は独立した束縛ではなく、採用しない。

最小修正の核は `submit_certify.sh:223` の subshell 内 `cd`。相対 attempts は外側リダイレクトで維持できる。ただし、**相対 `--job-script` の意味維持と argv の byte 単位不変は両立せず、現条件のまま全面対応プランを確定することはできない。**