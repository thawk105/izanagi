## 変異 anchor 表

全 6 件の `old` は、現行 `orchestrator/campaign/s1_direct_comparison.py` 内で**一致数 1**を静的に確認した。M4 は復活させない。ファイル変更・git 操作・テスト実行は行っていない。

表の `old` / `new` は、空白・改行を正確に保存するため **JSON 文字列**で記載する。JSON decode 後の文字列を置換に使う。末尾の `\n` も置換対象に含む。M7 の `...` は実ソースに存在する文字列であり、省略表記ではない。

| # | file | line | old（完全な JSON 文字列） | new（完全な JSON 文字列） | 期待 kill node | 単一理由性 |
|---|---|---:|---|---|---|---|
| M1 | `orchestrator/campaign/s1_direct_comparison.py` | 341 | `"        for record in (*supply_records, *meaning_records):\n"` | `"        for record in ():\n"` | 下記 M1 の 7 件 | admission と reason 集約は不変。detail ループを通らず、本文保持と例外注入テストが失敗する。manifest hash 検査は対象から外す。 |
| M2 | `orchestrator/campaign/s1_direct_comparison.py` | 341 | `"        for record in (*supply_records, *meaning_records):\n"` | `"        for record in tuple(\n            record for record in (*supply_records, *meaning_records)\n            if record.terminal_status != \"green\"\n        )[:1]:\n"` | 下記 M2 の 3 件 | non-green を選別してから 1 件に限定する。先頭 green による別理由の欠落を避ける。RuntimeError テストも 2 件分の fallback を要求するため失敗する。 |
| M3 | `orchestrator/campaign/s1_direct_comparison.py` | 352 | `"            except Exception:\n                rejection += \"\\n<condition detail unavailable>\"\n"` | `"            except ():\n                rejection += \"\\n<condition detail unavailable>\"\n"` | 下記 M3 の 1 件 | 外側の例外捕捉だけを無効化する。内側の `:294` に捕捉層があるが、対象テストは helper 自体を差し替えるため通らない。 |
| M5 | `orchestrator/campaign/s1_direct_comparison.py` | 291 | `"        tail = encoded[-tail_bytes:].decode(\"utf-8\", errors=\"ignore\")\n"` | `"        tail = \"\"\n"` | 下記 M5 の 2 件 | `omitted` は変更後の保持量から再計算されるため、末尾保持だけを破る。予算・digest は維持する。 |
| M6 | `orchestrator/campaign/s1_direct_comparison.py` | 290 | `"        head = encoded[:head_bytes].decode(\"utf-8\", errors=\"ignore\")\n"` | `"        head = \"\"\n"` | 下記 M6 の 2 件 | M5 と対称。先頭保持だけを破り、`omitted` は整合する。 |
| M7 | `orchestrator/campaign/s1_direct_comparison.py` | 283 | `"                f\"sha256={digest}>...\"\n"` | `"                \">...\"\n"` | 下記 M7 の 4 件 | 全文 sha256 の印だけを削除する。ただし omitted テストの正規表現も sha256 を要求するため、同じ削除で 2 種の検査が失敗する。両方を期待集合へ登録する。 |

以下は**静的予測の完全集合**であり、実測結果ではない。日本語 param は pytest の既定 escaping を仮定している。設定・collection hook は射影外なので、最終表記は probe で確定する。

**M1：7 件**

```text
orchestrator/tests/test_s1_direct_comparison.py::test_condition_rejection_preserves_every_real_red_detail[first source]
orchestrator/tests/test_s1_direct_comparison.py::test_condition_rejection_preserves_every_real_red_detail[changed volatile source]
orchestrator/tests/test_s1_direct_comparison.py::test_condition_detail_formatter_failure_preserves_rejection[RuntimeError]
orchestrator/tests/test_s1_direct_comparison.py::test_condition_detail_formatter_failure_preserves_rejection[KeyboardInterrupt]
orchestrator/tests/test_s1_direct_comparison.py::test_condition_detail_formatter_failure_preserves_rejection[SystemExit]
orchestrator/tests/test_s1_direct_comparison.py::test_condition_detail_formatter_failure_preserves_rejection[GeneratorExit]
orchestrator/tests/test_s1_direct_comparison.py::test_condition_real_process_detail_within_diagnostic_budget_is_complete
```

**M2：3 件**

```text
orchestrator/tests/test_s1_direct_comparison.py::test_condition_rejection_preserves_every_real_red_detail[first source]
orchestrator/tests/test_s1_direct_comparison.py::test_condition_rejection_preserves_every_real_red_detail[changed volatile source]
orchestrator/tests/test_s1_direct_comparison.py::test_condition_detail_formatter_failure_preserves_rejection[RuntimeError]
```

**M3：1 件**

```text
orchestrator/tests/test_s1_direct_comparison.py::test_condition_detail_formatter_failure_preserves_rejection[RuntimeError]
```

**M5：2 件**

```text
orchestrator/tests/test_s1_direct_comparison.py::test_condition_long_record_detail_keeps_both_ends_and_omission_evidence[common.hh-tail]
orchestrator/tests/test_s1_direct_comparison.py::test_condition_long_record_detail_keeps_both_ends_and_omission_evidence[\u5171\u901a.hh-tail]
```

**M6：2 件**

```text
orchestrator/tests/test_s1_direct_comparison.py::test_condition_long_record_detail_keeps_both_ends_and_omission_evidence[common.hh-head]
orchestrator/tests/test_s1_direct_comparison.py::test_condition_long_record_detail_keeps_both_ends_and_omission_evidence[\u5171\u901a.hh-head]
```

**M7：4 件**

```text
orchestrator/tests/test_s1_direct_comparison.py::test_condition_long_record_detail_keeps_both_ends_and_omission_evidence[common.hh-omitted]
orchestrator/tests/test_s1_direct_comparison.py::test_condition_long_record_detail_keeps_both_ends_and_omission_evidence[common.hh-sha256]
orchestrator/tests/test_s1_direct_comparison.py::test_condition_long_record_detail_keeps_both_ends_and_omission_evidence[\u5171\u901a.hh-omitted]
orchestrator/tests/test_s1_direct_comparison.py::test_condition_long_record_detail_keeps_both_ends_and_omission_evidence[\u5171\u901a.hh-sha256]
```

## masking 層

**P1 の固定 hash を除外する理由は、射影された現行テストの構成と整合する。**

| 根拠 | 確認内容 |
|---|---|
| `orchestrator/tests/test_s8b_oracle_manifest.py:88–89` | materializer path と SHA-256 `c7364f2da5decbd6b4d44041385edc60feaf9c83638b73f178cfe4c9adff1bbe` を RAW に固定している。 |
| 同 `:219–224` | 検証用 source の供給元に live `_ROOT` を指定している。 |
| 同 `:266–270` | 固定 `PIN_GATE_SPEC_RAW` を検証用 spec として書く。 |
| 同 `:1081–1096` | live source の設置後、固定 pin で `load_approved_spec(root)` を呼び、RAW と hash の一致を要求する。 |

したがって、このテストの赤は「診断保持が壊れた」証拠には使えない。ただし、呼び先の source コピー実装・loader 本体は射影外であり、内部の比較行や実際の失敗 node 集合まで今回独立確認したわけではない。

`test_s1_direct_comparison.py` 内には次の source 依存検査があるが、今回の 6 置換を一律に赤にする内容ではない。

- `:138–143`：実関数の source に 4 API 名があることを確認する。全置換で保持される。
- `:1112–1123`：AST の import と禁止文字列を確認する。全置換で条件は変わらない。
- `:63–65`：live driver を複製するが、固定 hash との比較ではない。
- `:1565–1579`：bytes 比較対象は fixture の transaction source であり、driver 自身ではない。

**他の `orchestrator/tests/` ファイルにある masking 層の網羅探索は未実施。**「次の絶対パスだけを読む」という射影制限のためである。brief `:39–40` は report / driver テストが動的 hash で自己整合すると報告しているが、今回はその現物を検証していない。

単独 runner にした際の検出漏れは次のように評価する。

- `test_s1_direct_comparison.py:130–135` の autouse fixture は通常の condition 実行を置換する。しかし `:53` に保存された実関数を診断テストが直接呼ぶため、M1–M3 はこの stub に隠れない。
- M5–M7 は `:291` で実 helper を直接呼ぶので、admission の拒否や compiler 環境に隠れない。
- 今回登録する 6 置換にはそれぞれ検出候補がある。一方、長文を拒否本文へ接続する統合経路、全体サイズ、helper 内側の BaseException が外側も越える経路を、この集合だけで網羅したとはいえない。
- 除外した manifest 検査は受入検査へ残す。変異の検出理由から外すことと、通常の整合性検査を省くことは別である。

## 攻撃面の地図

以下で driver は `orchestrator/campaign/s1_direct_comparison.py`、test は `orchestrator/tests/test_s1_direct_comparison.py` を指す。

| 攻撃面 | file:line | 確認する理由 |
|---|---|---|
| byte 予算と境界 | driver `:54–55, :275–289` | 固定予算は 4228 bytes。marker は ASCII なので `len(marker)` を bytes と扱える。通常の入力長では `available` が負になるとは考えにくいが、定数変更時の負値・ゼロ、とくに `[-0:]` が全文になる条件を切り分ける。 |
| 予算ちょうどの入力 | driver `:275–276`、test `:235–260, :312–317` | `<=` 境界を通ると切り詰めない。既存テストは短文・予算内・長文を扱うが、4228 bytes ちょうどと直後の境界は明示していない。 |
| UTF-8 切断と omitted | driver `:290–293`、test `:296–305` | `errors="ignore"` で落ちた不完全文字も、再 encode 後の保持長から省略数に含まれる設計。head / tail 双方の境界、重複のない分割を確認する。 |
| digest の対象 | driver `:273–277` | digest は raw `detail` ではなく、`shlex.join([detail])` を UTF-8 `backslashreplace` した bytes に対するもの。元の stderr bytes と同一とは限らない。 |
| 証拠の復元可能性 | driver `:279–293`、test `:306–307` | digest は別途得た全文候補を照合できるが、省略した中央本文を復元できない。切断後の shell quote を完全な shell token として扱えるかも別問題。 |
| surrogate の扱い | driver `:274–276` | 長さ判定には置換済み bytes を使う一方、短文では元の `rendered` を返す。孤立 surrogate の表示・保存時にも同じ byte 予算を保証できるか。 |
| 内外の例外境界 | driver `:272–295, :344–353`、test `:200–232, :320–342` | 両境界は `Exception` を捕捉し BaseException を捕捉しない。helper の失敗と `record.evidence.get` の失敗で経路が異なる。 |
| 整形前の拒否確定 | driver `:331–340` | admission と reasons は整形前に確定する。ただし reason 属性取得・join は整形側の try の外であり、実 gate の発行型契約が前提になる。 |
| 拒否本文全体の上限 | driver `:335–353` | 4228 bytes は 1 detail の予算。全体は reasons 行、各 record の prefix、改行を加えた総和となり、全体共通の上限はここにない。request 数の実効上限と区別する。 |
| 改行と機械 consumer | driver `:349, :1305–1306, :1321–1323, :1414`、test `:189–197, :224–229` | driver は例外型で伝播し CLI は本文を表示する。テストには行数・全文一致の consumer が存在する。detail 自身の改行で「1 record＝1行」とは限らない。 |
| green 経路 | driver `:334, :355`、test `:345–361` | admitted の場合は整形せず発行 record を返す。既存正例は同一性と canonical bytes を検査している。 |

repo 全域の production consumer の有無は、射影制限により未確認。改行追加に依存する外部 parser が「ない」とは結論しない。

## 本走の手順

**probe と本走の 2 段構成を推奨する。**

anchor は一意に確定したが、node 集合は静的予測である。特に M1 は割込み param まで失敗し、M7 は sha256 削除が omitted 検査にも波及する。さらに pytest の日本語 ID 表記を決める設定が射影外にある。完全一致が条件の `DW-M08`（`docs/dev-wave/mutation.md:56–60`）に従い、初回 probe で確認する理由がある。

1. **最終 commit を確定し、anchor を再照合する。**  
   fix があれば上表をそのまま使わず、最終状態で再計数する（DW-M07 `:44`）。brief `:61–62` に従い、統合 commit 後・porcelain 空の状態で始める。この plan 子は実施しない。

2. **外側の時間予算と単独実行を確認する。**  
   6 変異それぞれの dispatch・runner・復元時間と余裕を見積もる。変異中は親の編集と書込み可能な子を止める（DW-M05 `:30–35`）。brief の過去所要は見積り材料であり、今回の実測値にはしない。

3. **全件 SURVIVED 登録で probe を行う。**  
   上表の 6 置換を `tools/mutation_harness.py` に渡し、rc・観測失敗 node・注入実在を保存する。未知の失敗は期待値へ機械的に追随させず、環境失敗・mask・意図した検出を区別する。

4. **erratum を残し、最終 spec を登録して再走する。**  
   probe の初回結果を残す。観測 node の理由を説明したうえで期待完全集合を確定し、本走では正規化した集合の完全一致を要求する。rc≠0 かつ抽出 node 0 件は成功扱いしない（DW-M08 `:56–60`）。

runner argv の構成は以下とする。これは**引数構成の模式図**であり、射影外の CLI parser を確認済みとするコピー実行用 command ではない。

```text
python3 tools/mutation_harness.py
  ［spec 指定］
  --runner-mode dispatch
  --out OUT
  --attempt-out ATTEMPT_OUT
  --wrapper-attempt INTEGER
  --scratch-root SCRATCH_ROOT
  --
  python3 tools/run_tests.py
  --force-dispatch
  --detached
  ［同 runner が受け取る形式で pytest に渡す引数:
    -q -rf orchestrator/tests/test_s1_direct_comparison.py］
```

`--` の後には test runner argv を渡す。直接 pytest を起動せず、`tools/run_tests.py` を通す。正確な spec 指定法と pytest 引数の渡し方は、親が射影外の CLI 契約を確認して具体化する。

配置と再投入の制約は次のとおり。

| 項目 | 制約 |
|---|---|
| `--out` | checkout 外。`--scratch-root` と同一 device。 |
| `--attempt-out` | checkout 外。`--wrapper-attempt` と同時指定。 |
| `--scratch-root` | 本走主体が書込み可能な scratch。`--out` と同一 device を実際に確認する。文書は scratch 自体の checkout 外必須までは明記していない。 |
| 再投入 | attempt-out の path と wrapper-attempt の整数を両方変更する。 |
| `--resume` | 前回 sidecar を新 path へ複写して渡す。空 file は不可。 |
| insight 配下の成果物 | brief `:73–74` の出力名を、checkout 内の live `--out` に使わない。終了・復元後に外部出力を収録する。 |

**結果の分類には契約上の論点がある。** DW-M03 `:18–20` は診断文字列だけの赤を kill に数えず、DW-M08 `:61–62` は diagnostic sensitivity pin を別枠としている。M5–M7 と M2 の失敗は主として診断保持の検出であり、harness が `KILLED` と出力しても受理集合・fail-closed 挙動の検出力を証明したことにはならない。M3 は RuntimeError の外部伝播という例外境界の変化を検出する。段 4 では、brief の「全件 KILLED」とこの契約の関係を明示して裁定する必要がある。

## 読めなかった射影 file

なし。

射影外のテスト・consumer・harness / runner 本体は、読取り対象外として扱った。

## 総括

6 変異の一意な anchor と静的な期待 node 集合を提示した。P1 の runner 限定は妥当だが、repo 全域の masking 不在までは確認できていない。probe 後に期待集合を確定し、harness の判定と diagnostic sensitivity の証拠分類を分けて記録する。実走結果は未取得である。