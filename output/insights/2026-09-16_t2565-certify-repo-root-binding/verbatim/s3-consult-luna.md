## shell の細部

以下、`submit` は `tools/pegasus/submit_certify.sh`、`test` は `orchestrator/tests/test_pegasus_calibration_workload.py`、brief・plan・rulings は指定された各 Markdown を指す。判定は静的検査による。

- **refuted — subshell 化で rc が失われる懸念。** plan:70–74 の `cd … && qsub` は、cd 失敗時には qsub を起動せず cd の rc、成功時には qsub の rc を返す。`set +e` が subshell にも効き、直後の `$?` 保存、`set -e` 復帰、記録、同じ rc での終了まで整合する。submit は ERR trap を定義しておらず、`-E` 自体は trap を作らない。`-u`・`pipefail` とも衝突しない。根拠: `submit:3`, `submit:222–229`, `plan:70–77`。

- **refuted — 相対 SUBMISSION_DIR の保存先が R に移る懸念。** 括弧の外側のリダイレクトは、subshell 本体の cd より前に C 基準で開かれる。例えば `C=/tmp/caller`、`--attempts-root 'new attempts'` なら、qsub の stdout/stderr は `/tmp/caller/new attempts/submissions/<nonce>/` に残る。親の cwd も変わらず、rc・JSON の後続保存も同じ場所になる。親 brief の「attempts も絶対化が必要」は過剰。根拠: `submit:128–140`, `submit:226`, `submit:248`, `plan:73`, `brief:21`。

- **real — 相対 PATH 要素も cwd 変更の影響を受ける。** `C=/tmp/caller`、`R=/tmp/repo`、`PATH=bin:/usr/bin:/bin`、qsub が C の `bin/qsub` にだけ存在する入力では、変更後は R の `bin/qsub` を探索する。別 executable の実行または command-not-found になる。既定・絶対 JOB_SCRIPT でも起こるため、plan の成立範囲にはこの留保が欠ける。絶対 fake-bin だけのテストは検出しない。これは具体的な互換性差分であり、一般的な PATH 防御の新設を求める所見ではない。根拠: `submit:211–223`, `plan:81`, `plan:116`, `plan:142`。

- **real（既存欠陥）／refuted（今回の新規 cd の欠陥）— CDPATH と引数解釈。** `--repo-root repo`、`CDPATH=/tmp`、`/tmp/repo` が存在すると、既存の `$(cd "${2:?}" && pwd -P)` は cd が出すパスと pwd のパスを改行で連結して受け取る。その結果 staging 検査で失敗する。`--repo-root -P` も既存 cd がオプション解釈する。一方、新規 `cd -- "$REPO_ROOT"` は、通常経路では既に絶対・物理パスであり、CDPATH 探索や symlink の論理名に依存しない。既存問題を今回の subshell 回帰と混同しないこと。根拠: `submit:13–14`, `submit:30`, `submit:52–57`, `plan:71`。

## テストの代表性

- **refuted — 既存 fixture では非 dry-run テストを構築できない、という懸念。** tools 一式をコピーして commit し、その後 output 配下に staging の３ディレクトリを作るため、submit の構造検査と clean 検査を通せる。submit は preflight の内容を解釈せず rc を使うので、４コマンドの成功 stub で十分。chmod と PATH 差し替えの先例も存在する。根拠: `test:1501–1526`, `test:435–448`, `test:455–473`, `submit:52–65`, `submit:110`, `submit:153–156`, `submit:200–203`。

- **real — helper はそのままでは使えない。** 現 helper は `--dry-run` 固定、`cwd`・`env` 指定なし、attempts も固定である。fixture 作成を切り出し、新しい実行経路に cwd・env・attempts・job-script を渡す必要がある。既存 wrapper の引数・返却値・既定動作を保てば、既存 argv 完全一致テストの期待値を変えず追加できる。根拠: `test:1492–1499`, `test:1528–1546`, `test:1577–1583`, `test:1628–1636`, `plan:111–112`。

- **real — 親 brief の実測表現が強すぎる。** fake qsub が証明するのは「submit が起動したプロセスの実 cwd」。scheduler が生成する `PBS_O_WORKDIR` や job の完遂は実測しない。plan はこの限界を明記しているが、brief の完了判定は job 側まで実走証明すると読める。完了記述を観測範囲に合わせるべきで、実 scheduler 投入の追加は不要。根拠: `brief:6`, `brief:29–32`, `plan:115`, `plan:153`, `tools/pegasus/certify_calibration.sh:46`。

- **real — テスト設計上の二つの落とし穴。**
  1. receipt には argv がない。「receipt の request ID と観測 argv が一致」は、request ID の照合と、表示 argv／fake 観測 argv の照合に分ける必要がある。
  2. 相対 script 衝突用の異なるファイルを commit 後の R の通常ディレクトリに作ると、clean 検査で止まり qsub に届かない。例えば両木の `output/custom.sh` を使えば、同 commit・clean を保ちながら bytes 差を作れる。

  根拠: `plan:122`, `plan:128–134`, `submit:110`, `submit:255–274`。

## consumer 波及

- **refuted — registry／runbook の連動変更が必要、という懸念。** registry は path・class・evidence を保持し、docs checker はその投影を比較する。今回の内部 cwd 変更は `local-ok`／`legacy-admitted (未実測)` を変更する根拠にならない。hooks の該当テストもコマンド表記と分類を扱う。根拠: `tools/pegasus/admission_registry.json:334–338`, `tools/check_docs.py:4431–4463`, `tools/check_docs.py:4831–4849`, `orchestrator/tests/test_check_docs.py:291–310`, `orchestrator/tests/test_hooks.py:3598–3603`, `orchestrator/tests/test_hooks.py:3978`, `docs/pegasus-runbook.md:558`。

- **real — 提示された consumer 一覧には追加の直接参照がある。** `test_pegasus_tools.py` には構文・symlink 検査だけでなく、module 関連文字列の禁止、clean fixture での submit dry-run と旧引数拒否の実行テストがある。特に qsub の事前解決を追加する案なら、dry-run で cluster command を要求しない既存契約を守る必要がある。根拠: `orchestrator/tests/test_pegasus_tools.py:125–131`, `:177–184`, `:734–742`, `:1669–1731`。

- **refuted — その他の参照にも一律修正が必要、という懸念。** `tools/pegasus/README.md` の実行例と分類表、同 README を検査するテストは、この変更で期待値を変える必要がない。`submit_floor.sh` の参照は commit 付き移植元コメントであり、動的な呼出しではない。他 submit への変更伝播は不要。根拠: `tools/pegasus/README.md:34`, `:125–129`, `:157`, `test:1703–1713`, `tools/pegasus/submit_floor.sh:561`。

## scope の漏れと過剰

- **refuted — plan が新 gate・台帳・一般化を持ち込んでいる懸念。** subshell 化、局所的な fixture 共通化、実際の回帰を捕捉する fake テストは既存経路の修正に収まる。相対 attempts の絶対化は不要なので省く判断が妥当。根拠: `rulings:7–10`, `plan:65–89`, `plan:109–126`。

- **real — 「argv 不変」を優先して相対 job-script を落とすと本題が未完になる。** 相対 script は既存の公開入力であり、cwd 修正が直接その意味を変える。維持のための局所修正は仮想リスク向け一般化ではない。plan 自身が「現状のまま author に渡せない」とした点は妥当。根拠: `submit:7–8`, `submit:32`, `submit:67`, `submit:117`, `plan:99–103`, `rulings:7–10`。

- **refuted — 任意 attempts を job に伝える新機構まで今回必要、という懸念。** job は R の固定 attempts を読む。C 側 attempts を指定したケースは、修正後に submit が成功しても job は receipt を発見できない場合がある。plan はこれを明記しており、このテストを job 成功の証明に使わなければ取り残しではない。任意 attempts 配送の新設は本題を超える。根拠: `plan:146`, `tools/pegasus/certify_calibration.sh:50`, `:207–216`。

## 不変条件の整合

- **real — 親 brief 内の条件が衝突している。** C の `jobs/custom.sh` を検査したまま qsub の cwd を R に変えれば、同じ相対 argv は R のファイルを指す。C のファイルへ絶対化すれば argv の値は変わる。「相対 script の意味維持」と「argv を１ bit も変えない」は提案方式では両立しない。根拠: `brief:12–13`, `brief:19–21`, `submit:67`, `submit:117`, `submit:211`, `plan:99–103`。

- **real — 緩めるべきなのは親が置いた byte 単位の argv 不変条件。** 提案は「qsub オプション構成・export spec・両 schema は維持し、相対 job-script の参照先維持に必要なパス表現変更を許容する」。既定・既存絶対パスの argv 期待値は維持できる。schema 変更や新 export は不要。相対 PATH 問題も対応するなら、executable 解決の変更範囲を別途明示し、同じ条件に隠さないこと。裁定は親に委ねる。根拠: `rulings:7–10`, `brief:12–13`, `submit:182–183`, `submit:205–211`, `test:1628–1636`。

## 総括

**real — 現プランは、そのまま全面対応として実装へ渡せない。** 主因は相対 job-script と argv 不変条件の衝突。追加の具体的な見落としは相対 PATH による qsub 選択の変化である。根拠: `plan:160`, `submit:211–223`。

**refuted — subshell・外側リダイレクト・既存 rc 処理そのものが修正を妨げる懸念。** この核は維持できる。親 brief の不変条件と実測表現を修正し、fixture の不足を補えば、registry・job 側の新検査・他 submit への一般化なしで進められる。根拠: `plan:70–89`, `plan:111–116`, `plan:153`, `brief:8–14`。

編集・commit・pytest 実行は行っていない。