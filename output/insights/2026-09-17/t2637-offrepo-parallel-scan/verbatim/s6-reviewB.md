## 前提の検算

指定された射影資料、累積差分、適用後の現物を静的に確認した。ファイル変更、pytest、実根走査は行っていない。**レンズ B の実装レビューは GO。must-fix は確認しなかった。** 実根の逐語一致・性能受理は別途必要である。

以下、`A`＝[tools/audit_dangling_commits.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2637-offrepo-parallel-scan/tools/audit_dangling_commits.py)、`T`＝[orchestrator/tests/test_audit_dangling_commits.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2637-offrepo-parallel-scan/orchestrator/tests/test_audit_dangling_commits.py)、`C`＝`tools/check_branch_rescue.py` とする。資料名は指定された job directory 内を指す。

- **refuted / nit：旧部分木単位の設計をレビューする懸念。** `s6-fix-prompt.md:27`、A:977・1043 は directory ごとの最初の yield を処理する現行仕様で一致し、旧 tail の原因だった部分木単位の固定割当は残っていない。
- **unknown / nit：性能受理。** `s6-parent-measurement-v1.md:9` の旧版1366.379秒・段5版1043.369秒は現行 queue 版の成績ではない。`s4-adjudication.md:42`・43 の逐語一致と独立走最大300秒以下を、このレビューや155 passedで代替できない。

## thread 安全と終了判定

**refuted / nit：共有辞書・計数の競合と早期完了。** A:1127 で作った `by_basename` は走査中に変更されない。`local`、`found`、`found_keys` は worker 専有であり、公開計数だけを slot の lock 越しに読む（A:890・894・1030）。主 thread の root 処理は worker 起動前に完了し、結果の merge は join 後である（A:1167・1083・1086）。

正常経路の終了判定は次の不変条件で説明できる。

1. `pending` は未完了 task 数、すなわち queue 内と処理中の合計として初期化される（A:1017）。
2. `get()` は task を queue から処理中へ移すだけで、`pending` を減らさない。
3. 子の `put()` と `pending += len(children) - 1` は同じ lock 内にある（A:1047）。子を別 worker が先に取得しても、その worker の完了更新は同じ lock を待つ。
4. よって正常経路で `pending == 0` になった時点では、他 worker に未完了 task はない。別 worker が終了処理中である可能性はあるが、主 thread が join する。

**refuted / nit：sentinel 不足による通常終了時の停止不能。** A:1079 で停止を通知し、登録された全 thread 数だけ sentinel を投入する。worker は次の `get()` で sentinel または停止 flag を見て終了する（A:1040）。例外時は未処理 task 自体も終了のきっかけになるため、queue を空にする必要はない。

**refuted / nit：`Path.absolute()` による新しい cwd 競合。** 本番入口では root を先に `resolve()` しており（A:612）、その子 path も絶対 path になる。worker 内に cwd 変更はない。相対 root を内部関数へ直接渡し、別 thread が cwd を変更する条件まで保証する実装ではないが、本番経路の回帰は示せない。

## F627 / F628 型

**refuted / nit：報告間隔0による busy-spin。** A:1070 の待機は報告間隔と独立した1秒である。`done` が既に set なら即時復帰するが、同じ反復で break するため、完了 event を無進捗で再待機し続けない。

**refuted / nit：task 集合の反復走査による二次化。** queue の投入・取得は各 task ごとで、主 thread が毎回読むのは worker 数分の slot だけ（A:1018・1048・1071）。全未完了 task に対する `wait` や list membership は導入されていない。

**unknown / nit：queue と walk key の実根費用。** A:999 は子ごとに深さ分の key tuple を複製するため、総生成費用は概ね `O(Σ深さ)`。深さ20の25万 task が同時滞留する上側の仮定では、64-bit CPython の概算で key tuple 本体だけ約50MB、task の2要素 tuple が約14MBとなる。さらに `Path`、名前文字列、末尾の `(1, name)`、queue の参照、候補辞書が加わる。祖先の内側 tuple は参照共有され、25万 directory 全件が常に同時滞留するわけでもない。この数字は実測 RSS ではなく、実根での所要・メモリ適合性は未確認である。

A:1176 の sort は候補 group 数を `G`、深さを `h` として比較費用込みで概ね `O(G log G × h)`、再構築は `O(G)`。A:1098 の merge は dict lookup と既存 set の `update` であり、累積集合を毎回複製していない。

**unknown / nit：publish の定数費用。** A:1035 は256 fileごとの公開に加え、directory 終了時に必ず公開する（A:1046）。空 directory が続き file 数が256の倍数なら、directory 開始通知でも公開する。費用は概ね `O(D + F/256)` で、16 worker が同じ slot lock を奪い合う構造ではない。小 directory が多い実根での支配率は測定待ちである。

## 例外と資源

**refuted / nit：worker 例外の握りつぶし・型変更。** A:1054 は最初に lock 下で保存された例外を保持し、停止と完了を通知する。主 thread は join 後、同じ例外 object を再送出する（A:1085）。元の traceback は残り、再送出側の frame が加わる。任意例外を `RuntimeError` に包んでいない。

`main` の捕捉は従来の `OSError / RuntimeError / UnicodeError` のまま（A:2025）。`KeyboardInterrupt` は rc=2 へ変換されない。主 thread の待機中の割込みでも `finally` は通る。

**refuted / nit：通常の thread 生成失敗で既起動 thread を放置する懸念。** A:1067 の `start()` が資源不足の `RuntimeError` を投げた場合、その未起動 thread は登録されず、既起動分へ停止通知・sentinel・join を行って元の例外を伝播する。これは rc=2 になりうるため、「別環境では遅くなるだけ」とは言えない。

**real / nit：終了待ちに時間上限はない。** A:1083 の join は実行中 directory の処理終了を待つ。directory 内の大量 file 処理や filesystem I/O が停止すれば、異常検出後も監査の返却が遅れる。`daemon=False` なので終了時に処理を切り捨てない。これは裁定済みの制約であり、新たな must-fix とはしない。

**refuted / nit：設定検証と空候補時の副作用。** A:899 は列挙実行時に env を読み、空文字・非整数・0・負を拒否する。定数側の bool も明示的に拒否する。A:1124 の空候補 return は設定解決・filesystem・queue・thread 生成より前にある。

## heartbeat の同一性

**refuted / nit：flat fixture の破壊。** T:1049 の monotonic 3値は、初期化、root directory 通知、file 通知で消費される。子 directory がなければ A:1170 を通らず、追加 pulse は発生しない。期待する `directories=1 files=1` の1行を維持する。

**refuted / nit：総数の二重加算。** 並列待機中は、既処理 root 分の `counts` と当該 queue の worker 累積値を合計する（A:1073）。正常完了通知より前に各 task の計数公開が済み、merge 時に初めて `counts` へ加算する（A:1089）。加算後に同じ slot を重ねて pulse する処理はない。

文字列形式も逐次と同じである。ただし通常の報告間隔では、完了時の pulse が rate limiter に抑制される場合があるため、「最後に表示された heartbeat が必ず総数」とまでは保証しない。間隔0のテストは最終合計を検査している。

## consumer と scope

**real / nit：worker override は rescue 子 process に渡らない。** C:218 の allowlist に新 env はなく、C:1792 の監査 subprocess は既定16で走る。正常完走時の監査内容は維持される設計だが、thread 生成失敗による rc=2 や consumer の timeout 到達もありうるため、影響を所要だけとは限定できない。直接起動の `workers=1` を掃除全体の退避設定として案内しないこと。裁定どおり、本 wave で allowlist を変更する必要はない。

**refuted / nit：scope 逸脱・pin 更新漏れ。** 累積差分は tool と test の2 fileに限定され、境界 helper、alias 配布、rescue、CLI、報告行、docs を変更していない。`.claude/commands/cleanup-branches.md:37` の起動契約も変わらず、`tools/check_docs.py:6574` が検査するのは command 本文の hash なので pin 更新は不要である。

## test の実効性

- **refuted / nit：heartbeat test が timeout と呼出 thread を検査していない。** T:1551 は呼出 thread の有限 timeout を正値と assert し、T:1565 はその観測を必須にする。callback 自体も thread identity を検査する。待機中の複数回 pulse までは強制していない。
- **real / nit：例外 test の join 検証は弱い。** T:1537 は同一例外 object、T:1538 は active thread 数の復元を検査している。ただし全 worker が即時に例外を投げる fixture なので、join を除去しても自然終了が先行して通る余地がある。最小の補強は、別 worker がまだ処理中のケースで終了を待ってから再送出することを検査すること。
- **refuted / nit：設定・空候補 test の形骸化。** T:1585 は非空候補で既定16・env 1・4と実 thread 生成数を検査し、不正値も列挙入口から通す。T:1605 は指定された `walk / scandir / lstat / Thread / Queue / environ.get` の全6箇所を trap している。bool 定数の拒否は実装にあるが test case はない。
- **unknown / nit：規模 test による5分上限の証明。** T:1451 の深さ10・大部分木300・小部分木20は、worker 数を超えた深さと task の重複・欠落の検査には適切。25万 directory の所要やメモリの証拠にはならない。Barrier と順序逆転用 wait は10秒の上限付き（T:1319・1416）。
- **real / nit：同一 worker 内の複数 walk failure を強制していない。** T:1340 の deny1・deny2 は現行設計では別 task であり、同じ worker に割り当たる保証がない。合算6件は検査するが、裁定のその witness は弱まっている。必要なら既存 test 内で同一 worker の複数失敗を固定する。
- **real / nit：同値 walk key の OID 挿入順に残差がある。** A:1176 は同値 key の順序を辞書の挿入順に委ねる。例えば `a/x` が OID A・B の順で候補になり、その hardlink `b/y` が B だけの候補になる場合、B を先に merge すると、代表 key 更新後も B・A 順が残りうる。T:1394 の異なる OID は別 file にあるため、この同値ケースを検査しない。最小の是正は同一 file 内の候補順を tie-break に含めること。ただし後段は OID をソートする（A:1193）ため、監査報告・rc・掃除判断の差は示せず、must-fix とはしない。

変異 matrix は実走していない。`s6-fix.md:58` のとおり、現行設計では `followlinks=True` だけの M4 は再帰を起こさない。symlink 除外条件の除去と区別して扱う必要がある。

## 所見一覧 (real / refuted / unknown、must-fix / nit)

| ID | 判定 | 根拠と成果物への影響 |
|---|---|---|
| B1 | refuted / nit | A:1047：子投入と未完了数更新は同一 lock 内。正常経路の早期終了・候補欠落は確認しない。 |
| B2 | refuted / nit | A:1070：正の待機と完了時 break により F627 型の無進捗反復を回避。 |
| B3 | refuted / nit | A:1098・1176：merge は集合更新、整列は group 数の sort。F628 型の list 重複除去は導入していない。 |
| B4 | unknown / nit | A:999・1046：queue・key・公開計数の実根費用は未測定。300秒受理への影響は親の実測待ち。 |
| B5 | real / nit | A:1083：処理中 I/O が止まると例外・割込み後も返却が遅れる。裁定済み制約。 |
| B6 | refuted / nit | A:1067・2025：通常の thread 生成失敗は既起動分を終了させて rc=2へ伝播。成功結果として扱わない。 |
| B7 | refuted / nit | A:1073・1089、T:1049：heartbeat の二重加算・flat fixture破壊は確認しない。 |
| B8 | real / nit | C:218・1792：override 非継承により rescue は16 worker。資源不足では掃除判断が止まりうる既知の制約。 |
| B9 | real / nit | T:1528・1538：即時例外 fixture は join 除去の検出力が弱い。現実装の終了不良は確認しない。 |
| B10 | real / nit | T:1340：同一 worker の複数 walk failure を強制せず、その回帰の検出力が限定される。 |
| B11 | real / nit | A:1176・1193：同値 key の OID 挿入順が逐次と異なりうるが、後段 sort により報告差は示せない。 |
| B12 | refuted / nit | 差分、check_docs.py:6574：CLI・consumer・command 本文は不変で、pin 更新は不要。 |

## GO / NO-GO

**GO：レンズ B の静的実装レビュー。must-fix は0件。**

これは land の受理判定ではない。実根の逐語一致、現行 queue 版の prototype 倍率、D958 の独立走最大値は親の測定で判定する。155 passed は親・fix 子の報告として受け取り、本レビューでは再実行していない。

## 総括

thread の所有関係、queue の終了判定、例外伝播、heartbeat は現行仕様と整合している。残る所見は、既知の資源・終了待ち制約、テストの検出力、報告に波及しない OID 挿入順の nit。性能受理を妨げる実装上の欠陥は静的には確認しなかったが、実根での所要・メモリ適合性は未判定である。
