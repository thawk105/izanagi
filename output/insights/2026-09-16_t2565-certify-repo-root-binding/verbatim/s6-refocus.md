## 所見対応表

以下の略号は現行ファイルを指します。`closed` は静的に対応確認済み、`partial` は留保が残るものです。実走による閉鎖確認は含みません。

- S：`tools/pegasus/submit_certify.sh`
- T：`orchestrator/tests/test_pegasus_calibration_workload.py`
- J：`tools/pegasus/certify_calibration.sh`
- D：指定された `s4-adjudication.md`

| 出所 | 所見 | 判定 | 根拠・残件 |
|---|---|---|---|
| レビュー A | `$(pwd -P)` が投入元 cwd の末尾改行を削除する（must-fix） | **closed** | S:213–215 が改行を保持。T:1868–1891 が改行なし兄弟との取り違えを検出する |
| レビュー A | job 側 hash 照合は script 取り違えを必ず捕捉しない | **partial** | J:227,243 は引き続き repo 内 script を照合する。今回の取り違え原因は閉鎖したが、この照合の限界は残る。backlog |
| レビュー A | 通常パスでも途中の cwd／代入で別 file を指す疑い | **closed** | S:67,117,213–215 は同じ投入元基準。親 shell の cwd 変更はない |
| レビュー A・段3 luna | subshell の rc 喪失、cd 失敗後の qsub 起動 | **closed** | S:228–235 の `cd && qsub` と rc 保存・伝播 |
| レビュー A・段3 luna | 相対 attempts の保存先が repo 側へ移る疑い | **closed** | S:229 の外側リダイレクト。T:1823–1843 |
| レビュー A | 絶対化が pre-submit／receipt を変更する疑い | **closed** | S:159,182,195 の保存後に絶対化。receipt は S:254–279 で保存済み値を使用 |
| レビュー A・段3 sol | 正規 job の fail-closed を緩める疑い | **closed** | J:207–259 の receipt・clean・複合照合は維持 |
| 段3 sol・luna | 相対 script の bytes 分離、argv 不変条件の衝突 | **closed** | D:13–21 の訂正に S:211–217 が適合。絶対入力は変換しない |
| 段3 sol | P2 の十分条件、provenance 断定が過大 | **closed** | D:28–35,54–57 で訂正。J:240–256 も複合条件であることを確認 |
| 段3 sol・luna | scheduler 実測と fake qsub 観測の混同 | **closed** | D:41–45。T:1733–1737 が観測するのは qsub プロセスまで |
| 段3 sol | 束縛根拠なし、負例が恒真、既定 argv 維持不能 | **closed** | 根拠の扱いは D:41–45。負例は T:1807–1817、既定絶対値は S:13–15 |
| 段3 luna | fixture／helper をそのまま使えない | **closed** | T:1493–1521 で fixture を分離。既存 wrapper は T:1524–1591 |
| 段3 luna | receipt に argv がない | **closed** | T:1766–1783 の表示照合と T:1798 の request ID 照合に分離 |
| 段3 luna | 衝突 script が clean 検査に掛かる | **closed** | T:1856–1858,1872–1880 は `output/` 配下。S:110 は同領域を除外 |
| レビュー B | 変異 M1–M5 の殺傷経路 | **closed** | 静的経路を再確認。現在の最初の assertion は M1/M2=T:1815、M3/M4=T:1792、M5=T:1764 |
| レビュー B | M3/M4 の assertion 重複 | **partial** | T:1792,1800,1863–1865。厳密な単一理由性は満たさない。nit |
| レビュー B | stub が対象機構を置換する／揮発値を焼き込む疑い | **closed** | T:1747–1762 で実 submit を実行。T:1733–1737 は実 cwd・実 bytes を観測 |
| レビュー B | 既存テストの弱体化 | **closed** | 旧 blob `24ddc4ec2` と AST 比較し、旧42テスト関数の変更は0件 |
| レビュー B | 追加ケースの所要台帳未登録 | **partial** | 現在は追加 **5関数・7ケース**、台帳一致0件。被覆率判定は `test_acceptance_schedule_order.py:704–712`。backlog |
| 段3 | 第三案、registry／runbook／他 submit 連動、新 gate、任意 attempts 配送の新機構 | **closed** | D:95,106–111 の不採用裁定を維持。今回の fix に再導入なし |
| 段3・レビュー A/B | 相対 PATH、CDPATH 等の既裁定留保 | **partial** | D:72–82、S:13–14,30,229。scope 外として維持 |

## fix の検査

**末尾改行の must-fix は閉じています。**

S:213–214：

```bash
  CALLER_CWD=$(pwd -P && printf '.')
  CALLER_CWD=${CALLER_CWD%$'\n.'}
```

物理 cwd を `C` とすると、取得する出力は `C + 改行 + "."`。末尾が `.` なので command substitution は改行を削除しません。続く `%$'\n.'` が **pwd の出力改行と sentinel の一組だけ**を除去し、`C` 自身の末尾改行は複数でも保持します。

`pwd` が失敗すると `&&` により `printf` は実行されず、代入コマンドが非ゼロを返します。この代入は条件式内ではなく、S:3 の `set -e` が有効なので停止します。後段の `set +e`（S:228）には到達しません。

**成果物影響：cwd の末尾改行削除によって、投入 script と異なる hash を持つ submit receipt が生成される経路を閉じています。**

## 回帰の有無

**静的に回帰は見つかりませんでした。**

件数を原データから数え直すと、旧42テスト関数は AST 同一、現行47関数です。段5の追加は `2+1+2+1=6` ケース、fix の追加1ケースを合わせて **7ケース**です。

helper の契約は次のとおりです。

| 項目 | 確認結果 |
|---|---|
| 引数 | T:1712–1719。既存引数を維持し、keyword-only の `bash_quoted_display` を追加 |
| 既定値 | `False`。段5の呼び出しは省略するため、従来の `shlex.split` 照合を通る |
| 新しい分岐 | 改行ケースだけ `True`（T:1884）。Bash `%q` の表示を照合 |
| 返却値 | `(completed, observed, submission)` の3要素を維持（T:1804） |
| 共通検査 | 表示分岐後の hash・rc・receipt 検査は両分岐で実行（T:1784–1803） |

新分岐も観測 argv と表示の一致を検査します。正しい script の選択は別途 hash・payload で検査するため、表示オプション追加による期待値の緩和はありません。

## 変異 anchor と期待 node

以下は**静的な赤予測**です。node の共通接頭辞は：

```text
orchestrator/tests/test_pegasus_calibration_workload.py::
```

### M3：絶対化の削除

S:211–216 の **old 逐語**：

```bash
if [[ "$JOB_SCRIPT" != /* ]]; then
  # Keep directory-name newlines; remove only pwd's newline and the sentinel.
  CALLER_CWD=$(pwd -P && printf '.')
  CALLER_CWD=${CALLER_CWD%$'\n.'}
  JOB_SCRIPT="$CALLER_CWD/$JOB_SCRIPT"
fi
```

これを空文字へ置換します。

最初の期待 node：

```text
test_submitter_keeps_relative_job_script_bytes_from_caller[original]
```

最初の失敗は **T:1792**。repo 側の衝突 script が読まれ、投入前 hash と観測 hash が不一致になります。`[changed]` も同じ箇所で赤予測です。

### M4：絶対化の基準を REPO_ROOT に変更

**old は M3 と同じ S:211–216 の逐語ブロック**です。new：

```bash
if [[ "$JOB_SCRIPT" != /* ]]; then
  JOB_SCRIPT="$REPO_ROOT/$JOB_SCRIPT"
fi
```

最初の期待 node と assertion は M3 と同じ：

```text
test_submitter_keeps_relative_job_script_bytes_from_caller[original]
```

**T:1792** で repo 側 script との hash 不一致になります。

### M6：sentinel を外す

S:213 の **old 逐語**：

```bash
  CALLER_CWD=$(pwd -P && printf '.')
```

new：

```bash
  CALLER_CWD=$(pwd -P)
```

S:214 は残します。末尾改行が消えた値に `改行 + "."` は存在しないため、同じ値のままです。

最初の期待 node：

```text
test_submitter_keeps_relative_job_script_bytes_from_newline_caller
```

最初の失敗は **T:1792**。改行なし兄弟の script を読み、hash が不一致になります。

参考として、M1/M2 は `test_submitter_runs_qsub_in_repo_root[outside]` の **T:1815**、M5 は `test_submitter_keeps_relative_attempts_in_caller` の **T:1764** が最初の赤予測です。

## 単一理由性

| 変異 | 前段・内部の別拒否 | 後続の重複検出 | 厳密な判定 |
|---|---|---|---|
| M3 | 存在確認・hash・clean は通過。repo 側衝突 file も存在する | T:1800,1863–1865 | **満たさない** |
| M4 | M3 と同じ | T:1800,1863–1865 | **満たさない** |
| M6 | 改行付き caller 内の相対 `custom.sh` で前段検査を通過。誤選択先の兄弟 file も存在する | T:1800,1888–1891 | **満たさない** |

3変異とも、因果は「異なる script の選択」に絞れます。しかし、指定の厳密な条件である「同じ入力を拒否する層が後にもない」は成立しません。

したがって **M3/M4/M6 を厳密な単一理由性成立として登録しない**こと。最初の殺傷点は共通の **T:1792** であり、末尾の payload assertion ではありません。検出重複は受理集合を広げないため **nit** です。

## scope 外の real

新規所見はありません。既裁定の留保を再要求しません。

所要台帳の未登録は fix 後には7ケースです。他条件が同じなら、追加前の被覆率 `K/N` は `K/(N+7)` になります。未登録だけで失敗するわけではなく、全収集の90%条件を割るかは未確認です。台帳更新は **backlog／親の受入確認事項**です。

## 総括

**must-fix は閉鎖。新しい must-fix・回帰は静的検査では見つかりませんでした。**

親への引継ぎは、上記 anchor による変異実測、M3/M4/M6 の厳密な単一理由性不成立の明記、台帳被覆率の受入確認です。pytest・変異・scheduler の実走、編集、commit は行っていません。