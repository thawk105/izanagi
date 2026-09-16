## 現状の把握

必読6ファイルとA群の実物を確認した。対象2ファイルは、親 brief の基準 `9d52ef1459fdae5bc97050155b28fce0601d259f` との差分がない。行番号は編集前を示す。

**A1・A6だけを編集する。** checker 全体の保証範囲をA1で定義し、計測への入口であるA6にも明記する。A2は保証名の凍結値、A3は失敗理由、A4・A5は限定例外の説明として維持する。

D297の保証、完全除去に対する必要条件、検査失敗時の実行禁止は別の主張である。必要条件と明記しても、失敗時の禁止を緩めてよいことにはならない。

## 編集プラン (file:line + 逐語案)

**A1 — `tools/check_trace0_preprocess_identity.py:3`**

既存の1行docstring全体を次に置換する。

```python
"""選定した macro context における TRACE=0 正規化 preprocess 出力の同一性、および include 活性の同一性を検査する。

この検査は D297 の保証を証明するものであり、計測ビルドからの trace 完全除去に対しては必要条件の一つである。
この検査だけで trace の完全除去を証明したと解釈してはならない。
"""
```

既存の日本語と保証名を維持する。D780決定1の統一文言を逐語で採り、次行で禁止される解釈も明示する。最初の文がD297の保証内容を具体化するため、「D297」という参照だけに説明を委ねない。

**A6 — `tools/pegasus/mocc_trace_pilot.sh:1742–1743`**

既存2行を維持し、その直後、`build_mode 0` より前に2行追加する。完成形は次のとおり。

```bash
  # D297 checker is deliberately a hard gate.  Its nonzero result means that
  # TRACE=0 execution is skipped; no fallback or relaxed branch is permitted.
  # This check proves the D297 guarantee and is one necessary condition for
  # complete trace removal from the measurement build; it does not prove that removal.
```

周辺の英語コメントに合わせ、D780決定1を英語で言い換える。`proves` の対象は **D297 guarantee** に限定し、完全除去については **one necessary condition** と **does not prove that removal** を併記する。完全除去を証明したという読みを明示的に排除し、既存の失敗時制御の説明も保持する。

追加の実装、定数変更、テスト変更は行わない。

## 触らないアンカーとその根拠

| アンカー | 非編集の根拠 |
|---|---|
| A2 — checker `:38–41` | `GUARANTEE` はD297が指定する限定された保証名そのもの。完全除去、全TU、実ビルドの同一性を主張していない。値変更はreportとconsumerの凍結契約に触れるため禁止。 |
| A3 — checker `:62–63` | `CheckError` は限定された同一性を「確認できない」という失敗の説明。成功時の完全除去を約束する文ではない。ここに「この検査は…証明する」を繰り返すと、例外自体が証明を与えるような文脈上の混乱も生む。既存の日本語を維持する。 |
| A4 — checker `:419–426`、特に `:421–424` | helperの局所契約であり、許可する挿入位置と、それ以外のinclude・markerの一致を説明している。`Return ... insertion index` という役割を超えて完全除去を保証していない。checker全体の射程はA1が定義する。既存の英語と限定条件を維持する。 |
| A5 — checker `:539–541` | 「D297 の保証」を括弧内で具体的に限定し、特別扱いが任意のinclude追加許可でないことを説明する。完全除去への拡張はない。A1の射程注記を同一ファイル内で反復する必要はなく、既存の日本語を維持する。 |

「注記がない」ことと「完全除去を証明したと読める主張がある」ことを同一視しない。A3〜A5は局所説明として既に限定されており、全体の射程をA1で明示すれば足りる。

## 規律 2 非緩和の確認手順

以下は**後段で実施する手順**であり、この段では変更・テスト実行とも行っていない。新しいgateや検査ファイルは追加しない。

1. **差分の位置・種類を限定する。**

   ```bash
   git diff --no-ext-diff --check
   git diff --no-ext-diff --unified=5 9d52ef1459fdae5bc97050155b28fce0601d259f -- tools/check_trace0_preprocess_identity.py tools/pegasus/mocc_trace_pilot.sh
   ```

   production差分がA1のdocstring置換とA6のコメント追加だけであることを確認する。記録用fragment・insightは別に確認する。

2. **逐語置換以外のbytesが不変であることを機械的に確認する。**

   一回限りの `python3 -B -` に標準ライブラリだけを使う。基準内容は `subprocess.check_output(["git", "show", BASE + ":" + path])`、編集後は `Path(path).read_bytes()` で取得する。

   - checkerは基準の3行目にある旧docstring bytesが1回だけ存在することをassertし、上記の新docstring bytesで1回置換する。
   - pilotは基準の既存2行コメントが1回だけ存在することをassertし、上記の完成形4行で1回置換する。
   - **その置換結果と編集後ファイル全体のbytesが一致することをassertする。**

   これにより、想定外の空白変更、実行文変更、追加コメント、heredoc内の変更も検出できる。シェル全体から `#` 行を一律除去する比較は使わない。

3. **Pythonの実行構造を確認する。**

   同じ一回限りの確認で基準・編集後を `ast.parse` し、両方のmodule先頭が文字列docstringであることを確認する。**module先頭のdocstringだけ**を除き、`ast.dump(..., include_attributes=False)` の一致をassertする。他の文字列や関数docstringは除外しない。

   これにより、`GUARANTEE`、`SCHEMA`、受理・拒否条件、report生成、JSON出力処理を含む残りのASTが不変であることを示す。

4. **出力への影響を静的に確認し、既存テストで裏付ける。**

   現物ではreport生成は checker `:703–720`、JSON出力は `:748–749`、CLI説明は `:724` の `GUARANTEE` 参照である。module docstringの参照や自己ソースの読み込みは見当たらない。したがって、同じ入力・依存・実行環境に対するcheckerの受理集合と出力JSON bytesを維持する根拠になる。有限個のテスト成功だけで全入力の不変を証明したとは扱わない。

なお、checkerの**ソースbytesとそのSHAは変わる**。pilot `:1751` がソースSHAを採取するため、将来のreceipt全体まで旧bytesと同一になるとは主張しない。これはchecker reportの出力不変とは区別する。

## 主張の強さの変化表

親の「A6だけが弱まる」という判定には同意しない。明示的な保証内容と、読み手が補ってしまう推論を分けて評価する。

| アンカー | 編集前 | 編集後 | 強さの判定 |
|---|---|---|---|
| A1 | 選定macro contextでの同一性検査を説明。完全除去との関係は未記載 | D297の保証内容を維持し、完全除去には必要条件の一つと明記 | 保証対象の拡大なし。完全除去への過大な推論を抑える方向 |
| A6 | 非ゼロなら実行を止め、fallbackを許さない | その禁止を維持し、成功しても完全除去の証明ではないと明記 | 拒否時の強制力は不変。成功時の過大な推論を抑える方向 |
| A2〜A5 | 限定保証名、失敗理由、局所例外の説明 | 非編集 | 不変 |

A1には「検査する」から「D297の保証を証明する」という語の追加がある。ただし対象は既存の同一性に限定され、D780が直接指定する表現であり、新しい保証対象は加えない。

A6の `hard gate` 自体は「通れば完全除去済み」を意味しない。したがって、A6の既存の明示的保証だけが実質的に弱まる、とは評価しない。**保証対象や受理範囲を上げる変更はない。**

## 受入 test の列挙

参照検索は次で行った。台帳のtest名から推測していない。

```bash
rg -n 'trace0_preprocess_identity|mocc_trace_pilot' orchestrator/tests --glob '*.py'
```

焦点走の対象は次の4ファイルとする。

| test file（`orchestrator/tests/` 配下） | 確認した参照関係 |
|---|---|
| `test_check_trace0_preprocess_identity.py` | `:19` でchecker実体を指定、`:179–190` でCLI実行、`:211–216` でmodule読込み。`:219` のtestがJSONの再現性、schema、保証名を検査する。 |
| `test_mocc_trace_job_contract.py` | `:27–28` で両production fileを指定。`:76` でpilot構文、`:874` で実ソースのgate順序、`:4212` でreport読込み、`:4908` でcheckerの実ASTとfixture契約を検査する。 |
| `test_mocc_trace_pair.py` | `:400–406` にcheckerのpath/SHAを含むreceipt fixture、`:474,498` にreport binding、`:749–757` などに改変検査がある。実checkerの直接実行ではなく、成果物consumerとして含める。 |
| `test_hooks.py` | `:3048,3199` にpilotの登録期待値、`:4392–4418` で `tools/pegasus` の実ファイルを読むinventory検査がある。計測処理のテストではなく、実行入口の参照consumerとして含める。 |

checkerの受理・拒否については、同ファイル内のinclude活性、例外挿入、空context、context件数不一致、preprocess失敗、`:1275` の `test_unresolved_indirect_cmake_value_is_not_a_rejection_reason` もファイル全体の実行で含める。

後段の焦点走：

```bash
python3 tools/dev_wave_wait.py acceptance -- python3 tools/run_tests.py \
  orchestrator/tests/test_check_trace0_preprocess_identity.py \
  orchestrator/tests/test_mocc_trace_job_contract.py \
  orchestrator/tests/test_mocc_trace_pair.py \
  orchestrator/tests/test_hooks.py
```

親briefが要求する受入全走：

```bash
python3 tools/dev_wave_wait.py acceptance -- python3 tools/run_tests.py
```

本段での実行結果はない。TRACE=0の再計測も要求しない。

## (P1) への意見

**(P1-a)：同意。** 今回の編集対象をproducerのliveな射程説明と、以後の材料レポートが転記する元に置くことは妥当。A1・A6に統一文言を置き、新規insightにもA1の統一文言を使用する。過去記録は遡及改変しない。ただし「成果物側」がコードコメントだけで永久に完結するという解釈にはしない。以後の材料レポートも同じ射程で記述する必要がある。

**(P1-b)：同意。** D780の「文言を…統一する」は新fieldを要求していない。既存 `guarantee` はD297の正しい限定保証名であり、その維持と射程注記は両立する。report schema、field集合、定数値、consumerの期待値は変更しない。

**(P1-c)：同意。** 役割の異なる2箇所、checker全体の説明と計測入口に注記する。局所例外や失敗理由へ同文を反復せず、既に限定されている説明を維持する。行数や編集アンカー数を成果量にしない。

## 裁定候補 (scope 外だが real と考えるもの)

新規の裁定候補はない。

実compile command・全TU・link object・trace symbol/data・build receiptを結合していない限界は実在するが、D780決定2でT-1644と同じ閉包へ既に割り当てられている。本プランでは設計を始めない。D774の間接値に関する限界と扱いも据え置く。

## 総括

実装案は**2ファイル・2アンカー、docstring置換とコメント追加のみ**。A2〜A5は限定された既存説明として維持する。後段では逐語置換による全bytes比較、module docstringだけを除いたAST比較、既存consumerの焦点走と受入全走で非緩和を確認する。本段ではファイル変更・テスト実行・commitを行っていない。