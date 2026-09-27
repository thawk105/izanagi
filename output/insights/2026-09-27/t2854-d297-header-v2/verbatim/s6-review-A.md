## 親の事前所見 P-1〜P-5 の判定

| 所見 | 判定 | 根拠と直し方 |
|---|---|---|
| P-1 予定集合照合が恒真 | **real / must-fix** | [検査器:1004](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:1004) の `done` は比較前の `planned` 走査中に積まれる。比較を最後の１件だけ省く V9 でも、[テスト:121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/orchestrator/tests/test_check_trace0_header_rule.py:121) は同じ数を照合して緑になる。比較結果から実行済み `(configure, entry)` を復元し、予定集合と照合する。 |
| P-2 discovery が全 entry を列挙 | **real / should** | [検査器:980](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:980) は `dependencies()` を呼び、同関数は全 entry を走査する。S4(b) は discovery 中の *その protocol の production target entry* に限定する。実 CCBench では未選定 tictoc・cicada の 48 genome について余分な依存列挙が生じ、判定 job の時間・費用が増える。discovery に対象 target を渡して対象 entry だけを列挙する。選定後の configure は全 entry のままにする。 |
| P-3 既存拒否順序の移動 | **real、影響は限定的 / should** | 親 commit では macro 検査が ancestry・diff 検証の前、現 commit では [検査器:1066](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:1066) 以降の後に移った。例えば不正な diff と macro 検査違反が共存すると拒否理由が変わる。ただし有効な `.cc` 単独差分の受理・拒否が変わる経路は、この移動だけからは確認できない。既存順序を維持しつつ header 単独時だけ必要な分岐を設ける。 |
| P-4 `-Werror` で builtin probe が失敗 | **real / must-fix** | [検査器:830](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:830) が `__DATE__` 等を `-U`・`-D` で再定義する。実 CCBench の consumer argv は `-Werror` を含み、親の GCC 11.4 実測では `-Werror=builtin-macro-redefined` で rc=1。正しい C→C2′ が拒否され、判定 job は正例完了に届かない。[テスト fixture:70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/orchestrator/tests/test_check_trace0_header_rule.py:70) に `-Werror` がない。probe に限定して当該診断を無効化し、`-Werror` を持つ正例を追加する。 |
| P-5 V2 が偽緑まで届かない | **real / should** | [検査器:796](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:796) は `-E -dM -MD` の１回で依存と macro を取る。生成 build を飛ばした V2 は未生成 header で拒否に止まり、想定した pass 変異にならない。登録した V2 の不成立を記録し、`-M -MG` で依存だけを取る等、偽緑に到達する変異へ事前登録し直してから評価する。 |

## 所見

1. **must-fix — 比較の実行済み集合を証明できない。** [検査器:1018](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:1018) で集約先へ configure を加えた時点で `done` を積み、[検査器:1026](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:1026) の比較結果とは結び付けていない。具体入力は複数 consumer を持つ正例 fixture に V9「最後の比較を省く」を加えたもの。未比較 entry があっても pass と `executed_count == planned_count` が出せ、S7 の厳密一致を満たさない。集約した各比較の成功結果から所属 configure を展開して実行済み集合を作る。

2. **must-fix — 実 CCBench の正例を `-Werror` probe が拒否する。** P-4 の通り。[検査器:834](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:834) の probe 呼び出しで rc=1 となるため、GCC 11.4 側の C→C2′ 判定記録は pass にならない。`-Werror`、`-include`、生成 dir、production target、TRACE token のない entry を組み合わせた代表 fixture を追加する。現 fixture は `-include` と生成 dir を個別には扱うが、`-Werror` と TRACE token なしの実構成を写していない。

3. **must-fix — `_h_norm` が path の境界を見ず、展開結果の任意の bytes まで置換する。** [検査器:740](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:740)、[検査器:846](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:846)。例えば root `/scratch/src-old` に対する `/scratch/src-old-extra` と、新側の `/scratch/src-new-extra` はともに `<SOURCE>-extra` になる。configure がこの外部 path を文字列定数や define に渡す入力では、実際の TRACE=0 完全展開が違っても正規化後に一致し、pass し得る。S6 の argv 照合にも同じ衝突が及ぶ。root 置換は構文上の path 値と境界を確認して行い、通常の展開本文にある文字列定数を無差別に書き換えない。衝突例を test に固定する。

4. **should — S4(b) の discovery 範囲が広い。** P-2 の通り。未選定 genome の第三者 TU にだけ依存列挙失敗がある入力は、裁定が求める production target 調査なら選定判定を終えられるのに、現実装では拒否される。実 CCBench でも余分な全件走査により判定 job の 90 分制限に近づく。discovery の依存列挙を target entry に限定する。

5. **should — 判定 job は「裁定済み C2′」を固定値と照合していない。** [run_judge.sh:42](/work/1/SFC/tanab/tmp/t2854-d297-header-v2-20260927/judge/run_judge.sh:42) は OID の形式を、[run_judge.sh:46](/work/1/SFC/tanab/tmp/t2854-d297-header-v2-20260927/judge/run_judge.sh:46) は bundle head と引数 `NEW_OID` の一致だけを調べる。別の有効な OID とその bundle を渡しても「C2′ 判定」の成果物名で走れる。C `68106660…` と C2′ `40a7f4ac…` の完全 OID を job の入力契約に固定して照合する。並行起動、各 rc の保存、正例２件の rc 確認、負例の rc・不一致理由・TPC-C entry 確認、scratch clone の EXIT cleanup には、静的確認上の誤りを見つけなかった。

6. **should — 変異の単一理由性が揃っていない。** [テスト:113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/orchestrator/tests/test_check_trace0_header_rule.py:113) の V3・V4 は生成物と TRACE=1 consumer の別々の assert で識別できるが、V9 は恒真の件数 assert で殺せない。V2 は P-5 の理由で期待した偽緑に到達しない。V1、V5〜V8、V10〜V12 は fixture の狙いと期待例外を静的に照合した範囲では対応する単一理由を持つ。ただし変異実行はしていないため、kill の実測とは扱えない。V2・V9 を直し、各変異で期待する pass／拒否の変化を個別に記録する。

S1 の４引数条件、S2 の共通 diff 拒否、S3 の configure 供給 seam、S5 の両 TRACE 状態と実効値確認、S6 の多重集合照合、S8 の regular file 集合・blob 照合、S9 の生成 target build、S10 の header 限定 report 追加、S11 の timeout、S12 の一意 scratch と cleanup は、上記を除き明白な逸脱を見つけなかった。`.cc` 単独では `header_rule` を加えず、report 構築値も従来形なので、bytes 変更の経路は確認できない。

## scope 外候補

D780 項２の実 compile command・全 TU・link object・trace symbol/data・build receipt を結ぶ別防壁、および選定外 genome・opt-in target への拡張は、この wave の修正条件へ加えない。

## 判定 (GO / NO-GO)

**NO-GO。** S7 の予定集合証明が成立せず、root 正規化には偽緑経路がある。加えて実 CCBench の正例は `-Werror` probe で拒否される見込みで、判定 job の C2′ 固定確認も不足する。

## 総括

静的レビューのみを行い、ファイル変更・テスト実行・判定 job 実行はしていない。まず予定集合照合、root 正規化、`-Werror` probe、discovery 範囲、job の OID 固定を直し、V2・V9 と実構成代表 fixture を再確認する必要がある。