静的敵対レビューのみ。必読入力はすべて読了した。Pegasus login node・read-only 条件のため pytest/build は実走しておらず、緑の主張はしない。

### A-1 — P1「同じ値」は materializer の字下げで崩れる

- 対象: [s1-brief.md:27](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s1-brief.md:27)、[s2-plan.md:57](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:57)、[s2-plan.md:136](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:136)
- 攻撃シナリオ: `implementation = "izanagi_gate_pass=true;" + " " * 4073` は raw 4096 bytes で前段 checker を通る。しかし [render_hole()](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/p3_s4_loop.py:161) が骨格の2空白を前置し、実 source hole は4098 bytesになる。「hole行をそのまま」再検査すれば後段だけ `RESOURCE_LIMIT` になる。
- 成果物影響: 同一候補の受否段階と reason_code が materializer により変わり、試行台帳の reject 段・候補成功率・receipt hash が分岐する。
- 提案: **must-fix / 境界テスト / 変異登録**。唯一の権威入力を「render 後の exact hole bytes」にする。raw 4094/4095/4096 bytesと実 source 4096/4097境界を別々に固定する。

### A-2 — `parse_template_file()` が CR を消し、文法外の実 bytes に receipt を出せる

- 対象: [s2-plan.md:57](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:57)、[s2-plan.md:142](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:142)
- 攻撃シナリオ: hole の物理 bytes を `b"  izanagi_gate_pass=true;\r\n"` にする。現行 [parse_template_file()](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/diff_quarantine.py:538) は text mode・universal newline で読み、`\r\n` を `\n` に正規化する。checker には CR を除いた正例が渡り、凍結文法が禁止する CR を含む実 source に receipt が発行される。
- 成果物影響: certified 受理集合へ DSL 外の source bytes が入り、receipt の implementation hash がコンパイラ入力の raw bytesを表さなくなる。
- 提案: **must-fix / 境界テスト / 変異登録**。source gate は binary readまたは `newline=""` で抽出し、CR/LF/NUL/非ASCIIを保存したまま拒否する。CRLF・CR-only・複数行を proposal 経由でなく実 source へ直接置く負例が必要。

### A-3 — 資源上限と A2-5 の reason_code が実装可能な粒度まで固定されていない

- 対象: [s2-plan.md:35](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:35)、[s2-plan.md:270](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:270)、[s1-brief.md:8](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s1-brief.md:8)
- 攻撃シナリオ:
  - `"é" * 2049` は `len()==2049` だが UTF-8 は4098 bytes。`len`、ASCII encode、UTF-8 encodeで `INVALID_CHARACTER` / `RESOURCE_LIMIT` / 例外に分岐する。
  - `"\ud800" * 4097` は通常のUTF-8 encode自体が例外になり、判定順と非リークを破る。
  - `":" + " true" * 512` は許可文字内・513 lexical unitsだが、先頭で即 `INVALID_TOKEN` にするか、token上限を先に適用して `RESOURCE_LIMIT` にするか未定義。
  - A2-5も期待値が未記載。scanner案からは `: :→INVALID_TOKEN`、`= =→INVALID_GRAMMAR`、`! =→INVALID_TOKEN`、`& &→INVALID_TOKEN`、`&&&→INVALID_TOKEN`、`===→INVALID_GRAMMAR`、`|| |→INVALID_TOKEN` となるが、planだけでは一意に決まらない。
- 成果物影響: 同じ入力の台帳 reason_code・レポート集計・再現判定が実装依存になる。surrogateでは安全な結果型を返さず例外停止し得る。
- 提案: **must-fix / 境界テスト**。raw-size の全域で定義された算法、invalid-tokenとtoken-countの優先順、A2-5の完全入力とexact codeをplan v2へ逐語固定する。

### A-4 — Python evaluator の自己一致は C++ コンパイル可能性・意味一致の oracle ではない

- 対象: [s2-plan.md:268](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:268)、[s2-plan.md:278](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:278)
- 攻撃シナリオ: 128式と正例9件は実質 `==` の `||` 列挙で、`&&`、`!=`、括弧、混合優先順位を覆わない。例えば `kUnset || kLockConflict && kUpdateAbsent` 型の式を parser が左結合で誤実装すると、private evaluator は同じ誤ASTへ自己一致し得る。
- 成果物影響: C++では sentinel=true の式を recognizer が拒否、または逆に意味の異なる式を受理し、certified 候補集合が変わる。
- 提案: **must-fix / 境界テスト**。全productionを含む bounded AST corpusを実C++小型 harnessで compileし、8 enum値の結果を独立truth tableと比較する。純Python evaluatorだけを証拠にしない。

### A-5 — `_SEAL + _issued + exact type` は発行関数限定を証明しない

- 対象: [s2-plan.md:63](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:63)、[s2-plan.md:107](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:107)、[s1-brief.md:49](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s1-brief.md:49)
- 攻撃シナリオ: `object.__new__(TriggerGateReceipt)` と `object.__setattr__` で exact type の `_body_json` / `_issued=True` を作れる。既存様式なら module の `_SEAL` も import可能である。現行 [build_admission.py:4](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/build_admission.py:4) 自身が「in-process callerへのsecurity boundaryではない」と明記している。`frozen=True` はこの迂回を防がない。
- 成果物影響: WAL/cache の `"issued": true` と「発行関数を通った」というreceipt provenanceが偽になり、少なくともcompiler到達権と台帳値が変わる。
- 提案: **must-fix / 境界テスト**。receiptをcapabilityとして信用せず、build境界自身がimmutable source snapshotを再認識してreceiptを出力する形に反転する。`object.__new__`、公開 `_SEAL`、発行後 `object.__setattr__`、`issued=1`、duplicate JSON keyを負例にする。認証を主張するなら別processの署名が必要。

### A-6 — pre/post 再読は ABA 差し替えを捕れない

- 対象: [s2-plan.md:107](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:107)、[s2-plan.md:143](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:143)、[s2-plan.md:146](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:146)
- 攻撃シナリオ: valid sourceでevidence/receiptを発行後、configure/build中だけ hole を `izanagi_gate_pass = true; pro_set_.pop_back();` へ替え、post-build再検査前にvalid bytesへ戻す。pre/post SourceEvidenceは一致するがbinaryは差し替え中の内容を持つ。既存build admissionのdocstringもABA windowを既知未閉鎖としている。
- 成果物影響: valid receipt/cache preimageに文法外binaryが束縛され、そのfitnessがcertified選択・材料レポートへ入る。
- 提案: **must-fix / 境界テスト / 変異登録**。receipt発行後のbuild専有snapshotからのみcompileし、source rootのwriter lock・snapshot identity・compiler入力を同一preimageへ束縛する。barrier付きfake compilerで swap→compile→restore を再現する。

### A-7 — receipt前 reject と WAL の「build_start 3 field必須」が自己矛盾する

- 対象: [s2-plan.md:148](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:148)、[s2-plan.md:173](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:173)
- 攻撃シナリオ: checkerが不合格を返すとreceiptは発行できない。現行pipelineはreceiptless `build_start → abort` を記録し、[wal.py:671](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/wal.py:671) も「receiptlessはbuild_done/commit不可、abort可」とする。一方planはgrammar lock下の `build_start` に3 fieldを必須化しており、最初の正当なgate rejectだけでWAL replay全体が赤になる。
- 成果物影響: 不合格候補1件がcampaign resume・レポート・試行台帳の読出しを不能にする。
- 提案: **must-fix / 境界テスト**。`pre-admission-reject` を独立eventにするか、receiptless startは閉じたprebuild reasonのattempt-bound abortだけ許す topology にする。receiptless `build_done/commit` 負例と正当reject正例を対にする。

### A-8 — cache/WAL の追加fieldと変異候補が既存 admission 束縛にmaskされる

- 対象: [s2-plan.md:120](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:120)、[s2-plan.md:331](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:331)
- 攻撃シナリオ:
  - raw cache keyは既に `adm=<BuildAdmission receipt SHA>`、v2 preimageはadmission body全体を含む。nested trigger receiptにversion/hashがあるため、明示 `trigger_gate_language` / `trigger_gate_receipt_sha256` だけ落としてもkeyは分離されたまま。
  - WALも既存 `build_admission` bodyと `build_admission_receipt_sha256` を全terminalへ伝播する。trigger専用SHAだけ落としてもreceiptless terminalにはならない。
  - `_issued` と exact-type の同時削除は二防壁を一変異に束ね、単一理由性を満たさない。
- 成果物影響: certified受理集合は変わらないのに、変異台帳だけがKILLEDを過大計上し、防壁の検出力を誤記する。
- 提案: **refuted候補 / 変異再登録**。cache/WALは唯一のauthoritative bindingを決め、補助fieldは正しさcreditに数えない。plan 333・335は現状のまま登録不可、332は二変異へ分割する。

### A-9 — P3 の「source_rootが無ければrecipe再構成」は現物fieldから実行不能

- 対象: [s2-plan.md:130](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:130)、[s2-plan.md:154](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:154)、[s1-brief.md:14](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s1-brief.md:14)
- 攻撃シナリオ: legacy cacheのSourceEvidenceが指す一時worktreeを通常cleanupする。cache/receiptはimplementation本文を保存せず、現行SourceEvidenceもdigest・pathだけ、GeneratorReceiptもinput hashだけである。hashからsourceやmaterialization recipeは復元できない。
- 成果物影響: 既存cache/WALの一部は再検査でなく実質cold invalidateとなり、旧certified結果の再利用・レポート参照・台帳継続性が失われる。
- 提案: **must-fix / 親実測**。実在旧artifactを「source root存続・権威recipeで再構成可能・不可」に全数分類し、recipeの所在とhash束縛を定義する。不可分は正直にinvalidateし、brief P3の一般化を訂正する。

### A-10 — 旧terminalを「標準attempt records」として再発行すると新実測を捏造する

- 対象: [s2-plan.md:182](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:182)、[s2-plan.md:184](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:184)
- 攻撃シナリオ: 旧commitをsource再検査だけで新WALの `build_start/build_done/commit` に写す。`reinspection_of` は追加fieldに過ぎず、現行 [重複解決](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/p3_s4_loop.py:629) はcommitの存在だけでsuccess扱いする。新policy下でbuild/verify/benchした標準attemptと区別できない。
- 成果物影響: 旧fitnessが新campaignのcertified選択として数えられ、レポートと台帳のattempt参照・実測時代が偽になる。
- 提案: **must-fix / [捏造・幻覚] 再発検査**。import/reinspection専用state・schemaを作り、全consumerが imported evidence と表示・集計する。標準commitへ昇格するならcurrent build/verifyを実走する。

### A-11 — 非リーク検査がproposal入口だけで、source抽出例外・WAL・notesを覆わない

- 対象: [s2-plan.md:41](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:41)、[s2-plan.md:148](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:148)、[s2-plan.md:284](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:284)
- 攻撃シナリオ: holeにinvalid UTF-8を置くとcheckerへ届く前に `UnicodeDecodeError` が文字位置・byte値を持つ。現行 [pipeline._prebuild_abort()](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/pipeline.py:554) は例外文字列をWAL、log、`result.notes`へ複製する。計画テストの「ログ非リーク」はdriver proposal経路しか指定していない。
- 成果物影響: WAL/試行台帳・log・レポートnotesへ入力byteや位置が流れ、リーク規律を破る。
- 提案: **must-fix / 境界テスト**。`SECRET_CANARY`、invalid UTF-8、lone surrogateを actual-source / cache-hit / WAL migration / S8B resumeへ投入し、return・例外・stdout/stderr・log callback・WAL・notes全てから本文/token/offsetが消えることを検査する。

### A-12 — generic quarantine と S8A の検査は前後層にmaskされる [恒真ゲート] [テスト代表性]

- 対象: [s2-plan.md:137](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:137)、[s2-plan.md:284](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:284)、[s2-plan.md:287](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:287)
- 攻撃シナリオ: generic `p3_s4_loop.quarantine()` の新checkerだけ常時passへ変異する。driverは前段checker、calibration/direct comparisonも各局所checker、pipeline/buildcacheは後段actual-source checkerが拒否する。S8A testは正例だけなので全て緑のままになり得る。
- 成果物影響: generic中央gateが未配線でも検査済みと記録され、実際には文法外sourceがwrite・preview・auditor到達してreject段と台帳reasonが変わる。
- 提案: **must-fix / 境界テスト / 変異登録**。実template上でpublic `quarantine(..., invalid, write=True)` を直接呼び、file不変・auditor/build未到達を検査する。他層を通さないこのnodeへgeneric-gate変異を単独帰属させる。

### A-13 — 「pinは3本だけ」はqualification trust rootを見落としている

- 対象: [s1-brief.md:19](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s1-brief.md:19)、[s1-brief.md:23](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s1-brief.md:23)、[s2-plan.md:47](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:47)
- 攻撃シナリオ: planは `pipeline.py`、`buildcache.py`、`build_admission.py`、`source_digest.py` を変更するが、4本とも [REQUIRED_CODE_IDENTITY_PATHS](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/qualification/contract.py:38) に含まれ、qualification seriesがexact hashを束縛する。既存qualification receiptを再利用すれば、正しく拒否して本番が止まるか、照合漏れなら旧code証拠を新codeへ誤帰属する。
- 成果物影響: certified選択・材料レポートが参照するqualification evidenceが現行gate bytesを証明しなくなる。
- 提案: **must-fix / 親実測**。DW-O09のpin閉包へqualification series/receiptを追加し、再qualificationとconsumer照合を同waveの受入条件にする。

### 攻撃したが構成できなかった面

- 凍結BNF自体は、単独 `!` 削除後、scanner/parserが忠実なら「受理するがC++でcompile不能・意味不一致」の具体式を構成できなかった。A-4は実装誤りを捕るoracle不足の所見である。
- `implementation` / `gate_predicate` の意味的な別検査分岐は、A-1のrender変換以外には構成できなかった。
- 新規S8B bindingがversion/hashをexact検証し、legacy branchを全 `_load_resume_manifest` 経路とoracle再materializeへ置く前提では、別のreceiptless resumeを構成できなかった。
- exact型検査、duplicate-key拒否、`allow_nan=False`、self-hashの除外fieldが全readerで統一される前提では、canonical JSON単独の別表現迂回は構成できなかった。
- normal new-pathでSourceEvidence v2・BuildAdmission v2・trigger campaign identityを全て要求する前提では、grammar version欠落による独立downgradeは構成できなかった。

## 総括

- must-fix は **12件**。最重要は **A-6 ABA差し替え**で、valid receiptと別sourceのbinaryを結べる。
- 次点は **A-2 actual bytesのCR消失**、**A-7 receipt前rejectでWAL自己破壊**、**A-13 qualification pin見落とし**。
- 親は旧cache/WAL/S8Bのsource root存続率・権威recipe保有率を全数実測し、P3の回収可能範囲を確定すべき。
- render前後のbyte境界、CRLF、surrogate、A2-5 exact code、C++ differential oracleを計算ノードで実測すべき。
- qualification再発行要否と、旧terminal移行がreport/duplicate consumerで「新attempt」に見えないことを実測すべき。