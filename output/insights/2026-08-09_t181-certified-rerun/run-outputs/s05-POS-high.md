結論は **NO-GO** です。指定9資料を全文読了し、編集・pytest・runner実行はしていません。前回所見10件のうち7件は closed、3件は partial。加えて pre-policy の rc=2 regression を確認しました。

### 前回所見対応表

| ID | fix後 | 根拠と結論 |
|---|---|---|
| A-1 | **partial** | parser出力はLF byteだけで分割され、CR/VT/FF/NEL/LS/PSの偽key化は閉鎖：[実装](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/tools/check_ai_provenance.py:94)、[テスト](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/orchestrator/tests/test_check_ai_provenance.py:403)、[D98](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/docs/decisions.md:4350)。ただしCLI入力取得がbare CRをLFへ変換する残存問題あり。 |
| A-2 | **closed** | fresh temporary ceiling配下にnested cwdを作り、subprocess終了後にcleanup：[実装](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/tools/check_ai_provenance.py:80)、[hostile ancestor/cleanupテスト](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/orchestrator/tests/test_check_ai_provenance.py:323)、[D98](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/docs/decisions.md:4352)。subprocessは`with`内で完了するためcleanup後cwd参照・並行削除raceは見当たらない。 |
| A-3 | **partial** | AI-Agent/scope/Codex-authorは旧repo-cwd・divider parserへ分離済み：[実装](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/tools/check_ai_provenance.py:140)、[境界テスト](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/orchestrator/tests/test_check_ai_provenance.py:276)、[D98](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/docs/decisions.md:4354)。しかしCAB parser自体はpre-policyにも実行される。 |
| A-4 | **closed** | `--full-history --no-renames`はD98と一致：[実装](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/tools/check_ai_provenance.py:243)、[rename](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/orchestrator/tests/test_check_ai_provenance.py:665)、[merge](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/orchestrator/tests/test_check_ai_provenance.py:707)、[D98](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/docs/decisions.md:4358)。rename-in/out、merge retain/drop、0→2→1を固定している。 |
| B-1 | **partial** | `--no-divider`による既存AI判定の変更自体は解消。ただしA-3と同じpre-policy parser failureが残る：[validate](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/tools/check_ai_provenance.py:165)。 |
| B-2 | **closed** | M1は旧AI parserの結果を固定したままCAB findingだけを変える：[テスト](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/orchestrator/tests/test_check_ai_provenance.py:291)。診断文言だけでなく`cab=[]`対非空の受理集合controlになっている。 |
| B-3 | **partial** | local ancestor/ceilingはCAB受理集合controlだが、system/global/env fixtureは3 alias同時注入：[テスト](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/orchestrator/tests/test_check_ai_provenance.py:323)、[ambient fixture](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/orchestrator/tests/test_check_ai_provenance.py:365)。隔離除去時も`raw=1, parsed=3`で拒否が残り、exact診断差だけで赤になり得る。 |
| B-4 | **closed** | test側の独立literal、production定数、実policy exact 1件を照合：[literal](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/orchestrator/tests/test_check_ai_provenance.py:16)、[exact照合](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/orchestrator/tests/test_check_ai_provenance.py:539)、[policy](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/docs/ai-provenance.md:18)。 |
| B-5 | **closed** | policy導入commit自身をsplit CABにし、そのcommit単独rangeを拒否：[fixture](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/orchestrator/tests/test_check_ai_provenance.py:64)、[境界node](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/orchestrator/tests/test_check_ai_provenance.py:583)。 |
| B-6 | **closed** | backtick/tilde fenceの列頭CABをCAB finding単独で拒否：[テスト](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/orchestrator/tests/test_check_ai_provenance.py:202)、[D98 grammar](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/docs/decisions.md:4344)。 |

### 残存finding

1. **HIGH / real / regressed — pre-policyでもcanonical CAB parser failureがrc=2になる**

   [main loop](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/tools/check_ai_provenance.py:372) は、[validate_message](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/tools/check_ai_provenance.py:165)でCAB parserを実行した後に、[policy適用判定](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/tools/check_ai_provenance.py:377)を行っています。findingを捨てても、temporary-dir作成失敗、Git parser error、decode errorは先に例外となり[rc=2](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/tools/check_ai_provenance.py:391)です。

   - 成果物影響: D98が従来受理するとしたpre-policy履歴が、CABとは無関係な一時領域・parser障害で実行不能へ変わる。
   - 最小fix: commitごとにpolicy適用を先に決め、pre-policyではCAB parserを呼ばない。parserを例外化したpre-policy単独rangeがrc=0、post-policyがrc=2になる相補テストを追加する。

2. **MEDIUM / real / A-1 partial — LF-byte契約がmessage取得層まで通っていない**

   CAB parser内部はbytesですが、履歴messageは[`_git(..., text=True)`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/tools/check_ai_provenance.py:65)、message fileは[`Path.read_text()`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/tools/check_ai_provenance.py:340)を通ります。read-only probeでは両text-mode経路がbare CRをLFへ正規化しました。Unicode LS/PS等は保持されるため、現行単体テストはその部分には有効です。

   - 成果物影響: bare CR直後のCAB-looking文字列を「LF物理行でない」として受理すべきmessageが、履歴・file指定CLIでraw候補へ変換され過剰拒否され得る。
   - 最小fix: message fileを`read_bytes().decode("utf-8")`、履歴messageをbytes subprocess出力のstrict UTF-8 decodeで取得する。bare CRを含む境界をhelper直呼びだけでなくmessage-file/history CLIまで通す。

3. **HIGH / real / B-3 partial — M2 ambient fixtureが受理集合の単一理由controlでない**

   [ambient test](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/orchestrator/tests/test_check_ai_provenance.py:365)はsystem/global/envの3 aliasを同時に有効化します。隔離を一括で外す変異ではparsed CABが0→3となり、`raw=1`との差が残ります。テストはexact診断の変化で赤になりますが、CAB拒否集合は変わりません。これはDW-M03のkill条件に反します。

   - 成果物影響: ambient aliasでsplit CABを誤受理する実装を、診断差だけのM2 killとして承認し得るため、commit provenance受理集合の防護証拠が不足する。
   - 最小fix: system/global/envを各1 aliasの独立fixtureへ分け、隔離除去時に必ず`raw=1, parsed=1`、すなわちCAB finding非空→空になるcontrolにする。local cwd/ceilingも、定数・kwargs欠落による例外ではなくCAB受理変化を期待nodeにする。

### budget・D96 closure

policy実体は **8,832 bytes / 9,000 bytes**。独立registryは[check_docs.py:162](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/tools/check_docs.py:162)、全budget consumerへの合流は[同:1466](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/tools/check_docs.py:1466)、dispatch allowlist非拡張は[同:231](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/tools/check_docs.py:231)、9,000/9,001境界は[テスト](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/orchestrator/tests/test_check_docs.py:417)で静的に成立しています。

[D96](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/docs/decisions.md:4269)が要求する新D・実装・境界テストは現在同じ未commit差分集合にありますが、まだcommitではありません。したがって「同一変更closure」は構造上は準備済み、履歴上は未成立です。段7ではD98、policy、両checker、両テストを分割せず同一commitへ含める必要があります。

## 総括

**NO-GO。残must-fixは3件です。** A-2、A-4、B-2、B-4、B-5、B-6はfix後コードと境界テストによりclosedです。A-3/B-1の中心だった既存AI-Agent parserの無裁定変更も解消しています。しかし、履歴mainはpolicy適用判定より前にCAB parserを呼ぶため、pre-policy commitの受理がtemporary-dir・parser障害によってrc=2へ変わります。これはD98の非遡及宣言に直接反する最重要blockerです。またLF-byte修正はparser出力内部に留まり、履歴取得とmessage-file読取のtext modeがbare CRをLFへ変換するため、D98が定めた物理LF境界の受理集合を端から端まで保存していません。さらにM2は複数aliasによる過剰決定fixtureで、CABの受理・拒否ではなく診断値の差だけをkillとして数えられる状態です。budgetは8,832/9,000、独立registry、全consumer合流、dispatch allowlist非拡張を静的に支持しますが、D96 closureはまだ未commitです。以上3点を閉じ、同一変更としてcommitされるまでは段7へ送れません。pytest緑およびrunner緑は主張しません。