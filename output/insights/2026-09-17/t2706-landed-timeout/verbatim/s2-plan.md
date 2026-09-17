## 変更面

行番号は現状のファイル基準。

| file:line | 変更内容・理由 |
|---|---|
| `tools/check_branch_landed.py:38` | 親の段4で選んだ値へ `COMMAND_TIMEOUT_SECONDS` を変更。直前に実測日・repo規模・選定根拠を1〜2行で記す。値は本planでは確定しない。 |
| `orchestrator/tests/test_check_branch_landed.py:3` | 新規テスト用に `inspect`、`shutil`、`shlex` を追加。時刻取得は `TOOL.time.monotonic()` を利用可能。 |
| 同`:1006` 直前 | 以下の正例1本・負例2本と偽git helperを追加。既存の全体timeoutテストに隣接させる。 |
| 新規 insight README`:1` | 操作別実測表、予算別完走率、候補比較、選定理由、残る制約を記録。配置先は親が既存規約に沿って確定する。 |
| 新規 worklog / decisions fragment`:1` | T-2706の結果とD2104項24に基づく値の選定を記録。既存裁定の受理条件は変更しない。ファイル名は親が確定する。 |

**定数への直接参照は完全列挙で2箇所**：

1. `tools/check_branch_landed.py:38` — 定義。
2. 同`:210` — `Git.run(command_timeout=COMMAND_TIMEOUT_SECONDS)` の既定引数。

間接的な利用は同`:225` の `min(command_timeout, remaining)`、同`:236` の `subprocess.run(timeout=timeout)`。対象ファイル内に別の `command_timeout` 指定箇所はない。

`:210` は関数定義時に束縛されるため、import後にmodule属性だけをmonkeypatchしても実効既定値は変わらない。テストでは明示引数を渡す。製品側の既定引数・`min`構造・判定経路は変更しない。

## 受理述語不変の根拠

**最優先の留保：観測層のtimeout後に、独立した決定的証拠によって `landed` / `not-landed` を返す経路は存在する。**
したがって「timeoutが一度でも発生したら必ず最終 `indeterminate`」とは書けない。一方、**決定的探索のtimeoutを肯定・否定の証拠へ変換する経路は見当たらない**。前者はD922項3の観測層分離と整合する。

`AssessmentError` の捕捉は、briefの8箇所ではなく**10箇所**。

| `tools/check_branch_landed.py` | 層 | 捕捉後の処理・verdictへの影響 |
|---|---|---|
| `:475` `_target_resolution_candidates` | 入力解決 | `branch-not-found` だけ吸収。timeoutを含む他の例外は`:477`で再送出し最上位へ。 |
| `:1310` `_verbatim_observation` | 観測 | `decisive=False` の outcome/reasonだけ返す。unit判定を変更しない。 |
| `:1403` `_proof_unit` | 決定的・spool整合性 | `indeterminate`、`incomplete=True`。receipt evidenceにも例外のoutcome/codeを記録。 |
| `:1425` `_proof_unit` | 決定的・spool exact探索 | 例外を `SearchResult(exc.outcome, exc.code, …)` に変換。`:1336`の不完全判定から `indeterminate`。 |
| `:1739` `assess` history scan | 決定的・負証拠 | `complete=False`。`:1753`以降で暫定 `not-landed` unitを `indeterminate` へ戻す。 |
| `:1773` ledger corpus | 観測 | 不完全な `CorpusResult` を記録。判定を変更しない。 |
| `:1788` ledger probe | 観測 | `decisive=False` の失敗情報を記録。判定を変更しない。 |
| `:1922` patch-id | 観測 | outcome/status/reasonのみ更新。判定を変更しない。 |
| `:1931` task index | 観測 | outcome/reason等のみ更新。判定を変更しない。 |
| `:1987` `assess` 最上位 | 全体 | active phaseのoutcomeとissueを記録し、`:2000`で必ず `indeterminate`。 |

追加の根拠：

- `:239`〜`:242`：実 `subprocess.TimeoutExpired` を `AssessmentError("assessment-timeout", …, outcome="truncated")` に変換する。
- `:214`〜`:215`：全体deadline切れも同じcode/outcome。
- `:1381`：通常ファイルのexact探索例外は局所捕捉されず最上位へ伝播する。
- `:1331`、`:1341`：exact探索の `matched` のみ肯定証拠。不完全探索は `indeterminate`。
- `:1351`〜`:1359`：通常ファイルの負例にはpure-add、同pathの候補ゼロ、any-path探索の不一致が必要。さらに上表の完全history scanを要求する。
- `:1322`：spoolの肯定はreceipt一致。receipt不在自体は負証拠にならない。
- `:1589`〜`:1606`：ref移動を拒否し、indeterminate unitを伝播。空closureの `landed` は証明義務が空の場合であり、timeoutによる空stdoutとは異なる。
- `:1596` のledger probe肯定分岐は `if False` で無効。観測timeout後も、終端ref確認が成功すれば既存の決定的証拠による確定判定は可能。

定数変更で変わるのは時間内に証拠収集できる範囲であり、証拠を受理する条件ではない。

## test 設計

挿入位置はいずれも `orchestrator/tests/test_check_branch_landed.py:1006` 直前。

### `test_command_timeout_default_is_bounded_and_bound`

```python
assert 0 < TOOL.COMMAND_TIMEOUT_SECONDS <= TOOL.DEFAULT_TIMEOUT_SECONDS
assert (
    inspect.signature(TOOL.Git.run)
    .parameters["command_timeout"].default
    == TOOL.COMMAND_TIMEOUT_SECONDS
)
```

ここでの「同一」は値の一致。floatのobject identityを `is` で検査しない。module属性へのmonkeypatchも行わない。

### `test_git_run_real_command_timeout_is_truncated`

fixture：`tmp_path`、`monkeypatch`。

- PATH変更前に `shutil.which("sleep")` で実体を確保。
- executableな `#!/bin/sh` 偽gitを作り、内容を `exec <絶対sleepパス> 2` とする。パスは `shlex.quote` で引用する。
- `monkeypatch.setenv("PATH", f"{fake_bin}{os.pathsep}{old_path}")`。
- `Git(tmp_path, TOOL.time.monotonic() + 60)` を作り、`run(["status"], command_timeout=0.05)`。
- `pytest.raises(TOOL.AssessmentError)` で次を検査：
  - `code == "assessment-timeout"`
  - `outcome == "truncated"`
  - `__cause__` が実 `subprocess.TimeoutExpired`
  - `command_count == 1`

`Git.run` は`:217`で毎回 `os.environ["PATH"]` を取り込むため、setenvが有効。`exec sleep` により、timeout時に残るsleep子プロセスを作らない。

### `test_assess_real_proof_log_timeout_is_indeterminate`

fixture：`tmp_path`、`monkeypatch`。既存 `_history_fixture`（`:1693`）を `"f"` で再利用する。

同helperはtopic状態をmain履歴に置いた後、main tipから削除するため、`:775`のtip一致で終了せず、`:777`のproof `log` に到達する。

1. PATH変更前にrepo fixtureを完成させ、本物のgit・sleepの絶対パスを取得する。
2. 偽gitは先頭の `-c VALUE` 群を解析してsubcommandを識別する。proof用の `log --full-history --format=%H … -- <path>` だけ `exec sleep 2`、他は**元の全引数を保持して** `exec <本物git> "$@"` へ委譲する。解析はsubshell内などで行い、委譲引数を壊さない。
3. 保存した `original = TOOL.Git.run` へ委譲する薄いwrapperを設け、対象logだけ `command_timeout=0.05` を明示する。他の呼出しは変更しない。
4. wrapperは対象到達回数と、捕捉した例外の `__cause__` が `TimeoutExpired` であることを記録して再送出する。例外自体は注入しない。
5. `TOOL.assess(repo, "topic")` の結果を検査：
   - decisionは `verdict="indeterminate"`、`reason="assessment-timeout"`、`landed=None`、`conclusive=False`
   - `phase_outcomes["preflight"] == "matched"`
   - `phase_outcomes["closure"] == "matched"`
   - `phase_outcomes["proof"] == "truncated"`
   - issueに `assessment-timeout`
   - 対象logへ1回到達し、実 `TimeoutExpired` を通過したこと

全体deadlineではなくcommand上限が効いたことも、wrapper内で残余予算が明示上限より十分大きいことを確認する。

既存テストとの差：

- `test_batch_failure_never_becomes_negative`（`:414`）は `AssessmentError` 注入、deadline操作、stdout破損を検査する。
- `test_global_timeout_is_indeterminate_json`（`:1006`）は全体予算 `1e-6` 秒のCLI経路を検査する。
- 新規2本はPATH経由で実プロセスを起動し、**実際の `TimeoutExpired` 変換とproof段からの伝播**を検査する。

## 変異候補

node名はすべて `orchestrator/tests/test_check_branch_landed.py::` 配下。

| id | 変異内容 | 期待killer / 扱い |
|---|---|---|
| a | `:239`のtimeoutを握り潰し、成功・空stdoutを返す | `test_git_run_real_command_timeout_is_truncated`。例外が出なくなり確実に赤。空stdoutは一般にlanded相当ではなく、未証明状態を正常結果へ偽装する変異と呼ぶ。 |
| b | `:241`の `outcome="truncated"` を `"error"` に変更 | 同上、および `test_assess_real_proof_log_timeout_is_indeterminate` のproof outcome検査。 |
| c | `:210`の既定値を定数からリテラルへ変更 | **同値リテラルなら検出不能として除外**。signatureの値比較では構文上の依存関係を証明できない。異なる旧値を固定した場合だけ正例がkillerとなるため、親が具体値を確定して別変異として登録する。 |
| d | 定数を `DEFAULT_TIMEOUT_SECONDS + 1` に変更 | `test_command_timeout_default_is_bounded_and_bound`。 |
| e | `:2000`を `_decision("landed", code)` に変更 | `test_assess_real_proof_log_timeout_is_indeterminate`。既存 `test_global_timeout_is_indeterminate_json` も検出見込み。 |
| f | 根拠コメントだけ変更 | 等価変異。`SURVIVED` 期待で、検出漏れ扱いにしない。 |

同値リテラルの構造依存まで守るならAST検査等が別途必要だが、今回の3本へ追加する必須要件にはしない。極小の正数への定数変更も、明示timeoutを使う負例と範囲検査では保証して検出できないため登録しない。

## 値の決め方

1. 親が30件の計測完了を確認し、JSONLの固定スナップショット・計測条件・refを記録する。途中のcommandだけのOIDを完了runとして数えない。
2. 操作は `op` 別に集計する。特にpath log、find-object log、batch-check、通常cat-fileを混ぜない。
3. 正常完了commandの時間を昇順 \(x_{(1)},…,x_{(n)}\) として、中央値、最大値、nearest-rank方式の \(p95=x_{(\lceil0.95n\rceil)}\) を算出する。timeout標本は完了時間不明の打切りとして別集計する。
4. 既存5秒を対照に、全操作最大値と余裕倍率等から複数候補 \(0<c\le60\) を作る。最大値×2〜3は候補生成則であり、自動的な採用根拠にはしない。
5. 予算 \(B\in\{8,60,300\}\) ごとに比較し、選定後は少なくとも新定数・60秒で30件を再実走する。

今回読んだ途中スナップショットは **419レコード、完了run 4件**。参考値は以下。残る途中OIDのcommandも含むため最終集計ではない。

| 操作 | n | 中央値秒 | p95秒 | 最大秒 |
|---|---:|---:|---:|---:|
| `log -- <path>` | 54 | 3.844 | 8.778 | 10.141 |
| `log --find-object` | 1 | 19.476 | 19.476 | 19.476 |
| `cherry` | 4 | 4.294 | 9.115 | 9.115 |
| `ls-tree` | 158 | 0.049 | 0.288 | 0.933 |

**途中データでもfind-objectが19.476秒あり、「重いのはpath logだけ」「最大10.1秒」という初期見積りは更新が必要。**

完走と確定判定は分けて集計する：

\[
R_{\mathrm{complete}}(c,B)
=\frac{\#\{\text{予算内に必要な探索と終端ref確認まで完了したrun}\}}{30}
\]

\[
R_{\mathrm{conclusive}}(c,B)
=\frac{\#\{\text{予算内のverdictがlandedまたはnot\text{-}landedのrun}\}}{30}
\]

timeoutによる早期JSON返却は完走に数えない。`refs-moved` や証拠不足は完走しても非確定になり得る。観測層のtimeoutは別列に記録する。

持上げ計測からの候補比較は、完了runの壁時計 \(W_i\) と最大command時間 \(M_i\) を使う：

\[
\widehat R_{\mathrm{trace}}(c,B)
=\frac1N\sum_{i=1}^{N}\mathbf1[M_i<c\land W_i<B]
\]

これは**記録された全commandを打ち切らず再現できる見積り**であり、実測完走率ではない。観測timeoutを許容する実経路、負荷・cache変動、プロセス起動等の時間を完全には再現できない。未完了runは成功とも失敗とも補完しない。

| 候補c秒 | 8秒予算：推計／実測完走 | 60秒予算：推計／実測完走 | 300秒予算：推計／実測完走 | 確定判定率 | timeout・ref移動等の内訳 |
|---|---|---|---|---|---|
| 5（対照） | … | … | … | … | … |
| 候補A | … | … | … | … | … |
| 候補B | … | … | … | … | … |

未実走欄は「未測定」と書く。8秒はrescueの内部assessment予算として比較し、rescue呼出し全体の完走率と混同しない。\(c\ge B\) では `min(c, remaining)` により全体予算が支配する。

## 裁定パッケージ候補

- **全体60秒／rescue 8秒予算の見直し**：途中runに96.698秒・83.203秒があり、command上限だけでは解消しない。30件の最終結果を根拠にcarryする。本waveでは変更しない。
- CLI追加、retry、timeout基盤、探索方式変更、gate追加は提案しない。
- 捕捉数、観測timeoutの意味、同値リテラル変異の扱いはplan・実測記録の訂正事項であり、製品仕様変更を要しない。

## 総括

決定的探索のtimeoutを確定判定へ変換する経路は見当たらない。
観測timeoutと確定判定の共存は可能であり、受理述語不変の説明にはこの区別が必要。
変更は定数・根拠コメント・3テスト・結果文書に限定する。
値は30件の最終実測で親が確定し、同値リテラル変異は検出可能と扱わない。
本段では静的確認のみ実施し、書込み・pytest実走は行っていない。