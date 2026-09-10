結論として、現行 call count と `cxx` 配線、mocc fixture には直接の不整合を認めません。一方、DW-G05を閉じるには実測証拠とAST meta testに補強が必要です。追加のpytest実行はしていません。

略記: `plan` = `stage4-plan-v2.md`、`author` = `stage5-author-output.md`、`campaign/direct/meta/receipt` = 各stage6射影。

| ID | severity | 判定 | DW-G05影響 | 所見と根拠 file:line | 最小fix |
|---|---|---|---|---|---|
| F1 | high | real | block | receiptは対象9 nodeとmeta 6 nodeについて `13 passed, 2 skipped` を記録する一方、自身で「受入形でない走行」と明記している。さらにplanが要求する選択compilerのrealpath/versionが成果物にない。`plan:5-6,26`、`receipt:52-70,88,94` | 同一node集合を受入用入口から再実行し、選択compilerの名前、`which`、realpath、versionをreceiptへ保存する。現receiptはfocused evidenceとして保持する。 |
| F2 | medium | real | weaken | AST matcherはcalleeの末尾名だけを数え、`ast.walk()`でnested functionやlambda内も走査する。従って、未実行nested scopeに `source_digest.resolve(..., cxx=cxx)` を置き、実呼出しをalias経由のdefault compilerへ戻す迂回が可能。順序検査もline番号だけで支配関係を証明しない。`meta:119-147,170-196,229-251`。特に該当conditional 2 nodeはreceipt上skipで実経路未確認。`receipt:94` | dotted calleeを `source_digest.*`、`buildcache.cache_key`、`S.source_digest.resolve` に限定し、nested scopeを除外するwalkerへ変更する。conditional call、selection、consumerの最上位祖先statement順も検査し、nested decoyとalias迂回の反例を追加する。 |
| F3 | medium | real。実signature不一致自体はunclear | weaken | `_CONSUMER_CXX_POSITION`のうち、対象nodeで実際に位置引数として使われるのは `_cpp_normalize:2`だけ。他は全て先に `cxx=` keywordが見つかるためindex表を参照しない。誤ったindexでもmetaとfocused実測は通りうる。`meta:72-80,140-147`、`campaign:10903,10926,11423-11450,11462-11488,12190-12230`、`direct:800-815`。現呼出しとのcount不一致はないが、特に`src_token:3`は射影内で独立検証されていない。 | `inspect.signature()`を使う追加assertで各indexのparameter名が実際に`cxx`であることを固定し、`cache_key`はkeyword-onlyであることを確認する。既存binding検査は維持する。 |
| F4 | medium | unclear | weaken | missing-defineは完全define positiveを先に通すため、旧「任意RuntimeError」より明確に強化されている。ただしmarkerの `"undef"` は、例外文字列にcompiler argvの `-Werror=undef` が含まれる実装なら自己充足しうる。該当nodeはreceiptでconditional skipされ、実診断は得られていない。`campaign:10952-10967`、`receipt:94` | `BACKOFF_FIXED`と`not defined`、`undefined`、`undef`が同じ診断行にあることを検査する。positive controlはそのまま維持する。 |
| F5 | low | real | limited | `test_site_compiler_helpers_choose_first_available...`という名前に対し、実行例はg++-12だけ存在する場合と全滅だけ。g++-13だけ、g++だけの場合に誤った固定文字列を返す変異は通りうる。`meta:199-226` | 両helperについて、g++-13のみ、g++-12のみ、g++のみ、全滅の4ケースを表駆動で追加し、戻り値と探索順を固定する。 |
| F6 | low | real | none | helper docstringの日本語文言を完全な部分文字列として固定している。保証境界ではなく表現変更まで失敗させる過剰固定。`meta:211-212`、`campaign:10851-10860`、`direct:229-237` | `scope=single-selected-compiler`、`cross-version-guarantee=false`のような機械可読markerへ置換し、旧版横断保証の不在検査を加える。helperの挙動assertは維持する。 |
| F7 | low | real、scope外 | none | 旧meta node名はREADMEとarchive worklogに残るとのauthor報告がある。collection consumerは見つからず、meta node数6も維持されている。`author:26-29,49-50`。READMEはactive T-1593所有なので、このcommitで直さなかった判断は正しい。`plan:15,19` | 親がT-1593のland状態を確認し、land済みならmain同期後にREADMEを更新、未landならscope外handoffへ明記する。現commitへREADME変更を混ぜない。 |
| F8 | info | refuted | none | 現行の9 node censusと実call site数は一致し、全対象呼出しが選択した`cxx`を受け取っている。`meta:37-80,229-251`、`campaign:10903-10984,11423-11488,12190-12230`、`direct:800-815`。exact countはM4の呼出し消失を捕らえる独立literalで、恒真ではない。 | なし。ただしF2/F3の証明穴は補強する。 |
| F9 | info | refuted | none | mocc fixtureはowner CMakeと条件なしの最小sourceだけを追加し、両方をinitial commit前にstageしている。余分なOPTIONSやproduction bytesはない。`direct:69-74,240-262,273-278`。direct nodeもfocused receiptの実行集合に含まれる。`receipt:60,94` | なし。fixtureの追加・削減は不要。 |

Scope外はREADME/archive同期、production変更、shared resolver、`prepare_toolchain`、compiler portability一般化です。`author:45-50`と`plan:27`の境界に反する変更は確認していません。

## 総括

コード本体の現在のconsumer配線とmocc fixtureは妥当です。ただし、F1のreceipt不足はDW-G05 closureを止めます。加えてF2、F3は「metaが通った」ことをconsumer順序と実signatureの十分な証明にしていません。最低限、受入形receiptの再取得、callee/scope-aware AST検査、実signature照合をmust-fixとします。