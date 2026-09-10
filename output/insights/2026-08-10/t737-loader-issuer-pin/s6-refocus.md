以下は静的再レビューです。pytest・mutation harness はともに未実走であり、緑は主張しません。

## 所見対応表

### C-01 / D-01 — closed

file:line: [test_env_contract_activation.py:1719](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/tests/test_env_contract_activation.py:1719)、[test_env_contract_activation.py:1745](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/tests/test_env_contract_activation.py:1745)、[env_contract_activation.py:275](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/campaign/env_contract_activation.py:275)、[env_contract.py:535](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/campaign/env_contract.py:535)

fix は production-loader node を semantic kill に見せ続けず、leaf 2 nodeへ実効 kill を移した。loader node 自体は従来どおり calibration mask による diagnostic sensitivity であり、この限定を維持する限り root cause は閉じている。

放置時の成果物影響: loader の raw failure を semantic KILL と誤計上し、変異台帳と certified report が transition gate の受理集合を過大保証する。

修正案: 追加コード修正は不要。台帳では production-loader node を diagnostic と明記し、loader 自体の semantic kill が必要なら calibration-valid fixture を別途作る。

### C-02 — closed

file:line: [test_env_contract_activation.py:2414](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/tests/test_env_contract_activation.py:2414)、[test_env_contract_activation.py:2466](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/tests/test_env_contract_activation.py:2466)、[issue_env_contract_activation.py:143](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/tools/issue_env_contract_activation.py:143)

`issuer.__file__` が tmp repo 内になったため、縮退後は publish 後の `relative_to()` も成功する。`main()` は 0 を返し、node は「SystemExit が起きない」で赤になる。以前の downstream `ValueError` mask は消えている。

放置時の成果物影響: mutation ledger が handoff の `ValueError` を KILL 理由にし、「publish を防いだ」という未評価 postcondition を参照する。

修正案: 必須修正なし。publish 到達そのものも直接証拠化するなら、writer spyと `finally` 内の対象 path/postconditionを追加する。

### C-03 — partial

file:line: [test_env_contract_activation.py:249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/tests/test_env_contract_activation.py:249)、[test_env_contract_activation.py:2423](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/tests/test_env_contract_activation.py:2423)

`{name: sha256}` は同名 bytes 改変を閉じたが、file type、no-follow、別 authorityへの書込先、authority親の staging residueは依然見ない。例えば regular file が同一 bytes を指す symlinkへ変わっても比較は一致する。現 writerで成立する exploit は見つからないが、fix報告の `closed` は過大。

放置時の成果物影響: import/write経路がdriftした場合、production loaderのregular-only受理集合や別checkoutのactivation head参照が変わってもguardが不変と判定し得る。

修正案: `{name: (lstat type, no-follow sha256)}` を比較し、writer wrapperで書込先をtmp authorityへexact固定、親directoryのstagingも前後比較する。

### S-01 — 新規

file:line: [mutation-spec-C.json:6](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t737-loader-issuer-pin/mutation-spec-C.json:6)

`OVERREJECT` は正例を拒否へ反転させる変異なのに、`category` が `"negative"`。expected nodeは正しいが分類値が誤っている。

放置時の成果物影響: mutation ledgerが過剰拒否のpositive evidenceをnegativeへ分類し、受理集合の反転方向を誤記する。

修正案: `category` だけを `"positive"` に訂正し、expected node 2本は維持する。

### N-01 — 新規（fixによる回帰ではなく既存欠落）

file:line: [test_env_contract_activation.py:2223](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/tests/test_env_contract_activation.py:2223)、[test_env_contract_activation.py:2287](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/tests/test_env_contract_activation.py:2287)、[test_env_contract_activation.py:2337](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/tests/test_env_contract_activation.py:2337)、[test_env_contract_activation.py:2381](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/tests/test_env_contract_activation.py:2381)

fix対象3 nodeは `sys.path` を復元するが、既存issuer 4 nodeも `issuer.__file__` をtmpへpatchして `main()` を呼び、`sys.path` を復元しない。`monkeypatch` は `main()` によるlist直接変更をundoしない。

放置時の成果物影響: worker内にstale tmp import pathが蓄積し、後続nodeのmodule参照が実行順依存になり得る。

修正案: 全issuer nodeを共通contextで囲み、`issuer.main()` の全終了経路で `sys.path[:]` を復元する。

## 回帰と semantic kill

fix差分はテストファイルだけで、production bytesは不変。したがってproduction受理集合へのfix由来の変更はない。`_entry_names(directory)` の署名・本体も [同ファイル:245](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/tests/test_env_contract_activation.py:245) に維持されている。変更3 nodeの `sys.path` と全 `monkeypatch.setattr` に復元漏れは見つからない。既存83 nodeの実行結果は本レビューでは未実走。

新leafの静的制御フローは次のとおり。

- G `[:N]`: `pin-env-064` が走査外になり、先頭N件の正常な+1で `changed` は非空。predicateも成功し、登録済みg3・head hashも通って、serial 2・末尾g3の `ActivationState` を返す。
- P `[:N]`: Gは65件全部を`changed`へ入れるが、Pは末尾のFalse predicateを走査しない。serial 2・全件g2の `ActivationState` を返す。

どちらもleafでは後続calibrationがなく、例外拒否からstate受理へ反転する。一方production loaderは直後に存在しないsynthetic calibrationで再拒否されるため、semantic killではない。

## 変異spec照合

略号は `iG/iP`=issuer負例、`lG/lP`=leaf負例、`pG/pP`=production-loader負例、`i+/l+`=issuer/leaf正例。

| spec / id | 静的に赤くなるnode | 判定 |
|---|---|---|
| A G-N1 | iG, iP, lG, lP, pG, pP | 一致 |
| A G-N4 | iG, iP, lG, lP, pG, pP | 一致 |
| A G-N8 | iG, iP, lG, lP, pG, pP | 一致 |
| A G-N64 | iG, iP, lG, lP, pG, pP | 一致 |
| A P-N1 | iP, lP, pP | 一致 |
| A P-N4 | iP, lP, pP | 一致 |
| A P-N8 | iP, lP, pP | 一致 |
| A P-N64 | iP, lP, pP | 一致 |
| B G-N4 | なし、SURVIVED | 妥当 |
| B G-N64 | なし、SURVIVED | 妥当 |
| B P-N4 | なし、SURVIVED | 妥当 |
| B P-N64 | なし、SURVIVED | 妥当 |
| C OVERREJECT | i+, l+ | nodeは一致、categoryは誤り |

Aの `pG/pP` はraw failureとしてexpected nodeに必要だがdiagnostic-only。Bは変更前HEADの最大fixtureが4 envなので、`[:4]`/`[:64]` は恒等になる。以上はすべて未実走。

## 残る限定

- 「production loader層は到達性pinであってsemantic killではない」は正確。
- 「`ident`経路は未被覆」は、65-env G/P量化pinについて正確。[ident.py:217](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/campaign/ident.py:217) と [ident.py:292](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/campaign/ident.py:292) への新nodeはない。
- 「正例はleaf止まり」は無限定では誤り。正しくは「production-loader層のM=65正例はleaf止まり」。issuer正例は [test_env_contract_activation.py:2491](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/tests/test_env_contract_activation.py:2491) でpublishまで到達する。
- D-02の限定も残る。実走後も「実測N={4,8,64}」と「M=65 fixture上の静的envelope 4≤N≤64」を分離すべき。

## 総括

(a) 対応表は C-01/D-01=`closed`、C-02=`closed`、C-03=`partial`。fix報告のC-03=`closed`は訂正が必要。

(b) **NO-GO（現状のspecのままでは）**。コード上のmust-fixは閉じたが、spec Cの分類訂正後に変異本走へ進むべきであり、本レビューは緑・land可を主張しない。

(c) spec訂正は必要。expected nodeはA/B/Cすべて一致するが、spec C `OVERREJECT.category` を `negative` から `positive` へ直す。