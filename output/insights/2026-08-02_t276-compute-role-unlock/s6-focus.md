結論は **NO-GO**。親実測 request `877327` の **179 passed** は事実として受領したが、こちらでは pytest・変異本走を行っていない。以下は staged source の静的再レビューである。

## revC 対応表

| 所見 | 判定 | 独立根拠・残存 |
|---|---|---|
| C1 従量 5 key deny | `closed` | 5 key の存在拒否は [claude_transport.py:50](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_transport.py:50)、実 gate は同 :182。M16/P3 も登録済み。 |
| C2 policy I/O より前の env preflight | `partial` | PBS/TLS/未受理 proxy/従量 key は :169–184 へ移った。一方、lowercase proxy pair の欠落・型不正は policy read :340 より後の :241 に残る。壊れた policy と欠落 `http_proxy` が共存すると依然 policy 側理由が先になる。**fix.md の closed と不一致。** |
| C3 成功 consumer と report↔attempt 正例 | `partial` | `_invoke()` 成功は検査するが、provider と run-level に同じ receipt dict を渡す [test_claude_transport.py:1215](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_claude_transport.py:1215)。さらに report 部は `_run_workload` を手渡し event で置換する同 :1241。実 consumer [p3_autonomous_workload_trial.py:1064](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:1064) を迂回している。**fix.md の closed と不一致。** |
| C4 P1 / real subprocess shim | `partial` | real subprocess は production provider を通るよう改善された [test_claude_transport.py:1110](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_claude_transport.py:1110)。しかし P1 は provider 単体だけで、flag 省略 `run_trial`、resolver 0 回、journal/report 不変を実行しない。同 :1141、:1667 は後者が AST-only。**fix.md の closed と不一致。** |
| C5 M5/M10/M12 の照準 | `partial` | M5 と M12 の分割は有効。M10 は「provider ごとの再解決」ではなく、provider 作成前に同じ admission を4回解決して最後を共有する変異 [mutations.json:83](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/mutations.json:83)。テストも production provider を FakeProvider に置換する [test_claude_transport.py:909](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_claude_transport.py:909)。元の provider-local 再評価穴は残る。**fix.md の closed と不一致。** |
| C6 terminal/fatal/cleanup closure | `partial` | supervisor error、両 wall-budget、run-finish は receipt 付きになった [p3_autonomous_workload_trial.py:878](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:878)。cleanup failure は report 確定後の close に残る同 :1365。artifact 診断も OSError は閉じたが、check→FIFO swap の blocking read は残る。fix.md の partial と一致。 |
| C7 診断・単一理由性 | `partial` | M11/M12/M13 の node 分割自体は改善。ただし M13 2件を通常の KILL として扱う spec のまま [mutations.json:123](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/mutations.json:123)。DW-M03/DW-M08 上は diagnostic sensitivity pin である。**fix.md の closed と不一致。** |

## revD 対応表

| 所見 | 判定 | 独立根拠・残存 |
|---|---|---|
| D1 従量 5 key deny | `closed` | C1 と同じ。値が空でも key presence で拒否する。 |
| D2 PATH/HOME・実行体 trust root | `partial` | PATH/HOME と executable digest 承認は未束縛のまま。T-242 残余という fix.md の申告と一致。 |
| D3 PBS witness の偽装 | `partial` | syntax gate は追加されたが scheduler attestation はない。さらに regex `[A-Za-z0-9._:-]{1,64}` は `":"` や `"."` も通し、repo の qsub authority grammar [qsub_binding.py:14](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/qualification/qsub_binding.py:14) と不一致。「exact syntax」という自己申告は過大。 |
| D4 receipt 平文 sink | `partial` | URI path 禁止は追加されたが、endpoint と生 PBS_JOBID は receipt のまま [claude_transport.py:84](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_transport.py:84)。fix.md と一致。 |
| D5 opt-out forged receipt bypass | `closed` | receipt key が存在する場合だけ拒否する [p3_autonomous_workload_trial.py:718](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:718)。receipt 無しの正当な provenance はこの条件で過剰拒否されない。 |
| D6 診断例外による attempt 消失 | `partial` | OSError は無視して元 invalid を残す同 :731–755。ただし `is_file/is_symlink` 後に FIFO 等へ差し替える race は `read_bytes()` で停止でき、invalid append へ到達しない。**fix.md の closed と不一致。** |
| D7 opt-out 不変性 | `partial` | provider object には今も `transport_receipt=None` が追加される [claude_projected_provider.py:186](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_projected_provider.py:186)。異常分類と完全 byte parity も未固定。fix.md の partial と一致。 |

対応表上の `regressed` は 0 件。ただし、fix で新設された mutation 成果物には以下の新規欠陥がある。

## 新規所見

| # | 深刻度 | 根拠 file:line | 成果物影響 | 推奨対応 |
|---|---|---|---|---|
| N1 | **BLOCKER** | harness は timeout を無条件に `TIMEOUT` とし [mutate.py:178](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/mutate.py:178)、正例を含め成功集合へ入れる同 :284。さらに login では `tools/run_tests.py` が PBS dispatch する [run_tests.py:939](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/tools/run_tests.py:939) が、timeout 時の request cancel／生存照合がない。 | P1〜P3 の timeout すら harness rc=0 になり得る。残存 compute job が復元後または次 mutant の source を読むと、mutation matrix の KILL/SURVIVE 帰属が壊れる。 | `expect_timeout` を明示した hang mutant だけ timeout を受理する。正例・通常負例の timeout は abort。login dispatch の request ID を捕捉して cancel＋terminal 照合するか、harness 全体を専有 compute allocation 内で走らせ process group を確実に終了する。 |
| N2 | **MAJOR** | M10 は4回読んでも最後の admission を全 provider が共有する [mutations.json:83](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/mutations.json:83)。M13 2件は診断文字列だけ [mutations.json:123](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/mutations.json:123)。harness はどちらも通常 `KILLED` にする [mutate.py:216](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/mutate.py:216)。 | matrix が受理集合・fail-closed 検出力を過大計上する。元の provider-local snapshot drift は未検出のまま「M10 kill」と記録される。 | M10 は各 real provider が別 resolver 結果を受ける変異へ再照準する。M13 は `diagnostic-pin` kind として KILL 総数から除外する。 |
| N3 | **MAJOR** | 成功 test は同じ receipt object を provider と expected に共用し [test_claude_transport.py:1215](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_claude_transport.py:1215)、report には同じ event を monkeypatch で直送する同 :1241。 | `_run_workload` が journal event の receipt/provenance を report cell へ写さない regression が生存する。journal と root receipt はあるのに cell 帰属だけ欠けた report を許す。 | provider receipt と run-level receipt を独立 deep copy で作る。production `_run_workload` を通し、journal bytes から読んだ event と report cell を独立比較する。`generation_record` で receipt を落とす変異も追加する。 |
| N4 | **MAJOR** | 事前登録 P1 は provider 単体 [mutations.json:187](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/mutations.json:187)、P2 は pure evaluator 単体 [mutations.json:195](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/mutations.json:195)。親定義の P1/P2 はそれぞれ flag 省略 run と compute+flag admission [adjudication.md:103](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/adjudication.md:103)。 | default run の余計な site/policy I/O、journal/report drift、wrapper の reject-all が正例 matrix を通過し得る。 | P1 を `run_trial` の flag-off E2E＋resolver 0 回＋固定 clock の HEAD byte比較へ、P2を wrapper/flag-on E2Eへ拡張する。P3 の leaf 正例は現状の射程でよい。 |
| N5 | **MAJOR** | 新 regex は producer [claude_transport.py:57](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_transport.py:57) と consumer [p3_autonomous_workload_trial.py:100](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:100) で独自複製され、既存 authority [collector.py:48](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/qualification/collector.py:48) より緩い。 | `":"` 等を job witness として受理し、journal/report に偽の allocation identityを残せる。 | qsub authority の単一 grammar/validator を再利用し、transport 独自 regex を廃止する。attestation 未実装である旨は残余として維持する。 |
| N6 | **MAJOR** | pure preflight [claude_transport.py:169](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_transport.py:169) に admitted pair の存在・型検査がなく、policy read :340 後の :241 に残る。追加 test も未受理名までしか複合条件に入れていない [test_claude_transport.py:387](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_claude_transport.py:387)。 | missing/non-string lowercase proxy と壊れた policy の併存時、恒久 env 違反が policy failure に隠れ、不要な I/O が戻る。選択は止まるが台帳理由が誤る。 | pair の presence/type を pure preflight へ移し、値一致だけを policy read 後に残す。broken reader 0 回 testへ両 key の missing/type を追加する。 |

### 指定された回帰レンズ

| レンズ | 静的判定 |
|---|---|
| pure preflight 順序で以前の拒否入力を受理するか | 通常の固定 dict について受理集合の拡大は見つからない。各 gate は後段も含め残っている。ただし C2/N6 の理由優先・I/O残存がある。 |
| opt-out forged 拒否が正当 run を過剰拒否するか | 実装条件は receipt key の存在だけなので、receipt 無し provenance は通る。新 test の正例配置は弱いが、コード上の reject-all はない。 |
| best-effort 診断が fail-open か | OSError を捨てても元 role は `invalid` のままで、certified 側 fail-open はない。ただし FIFO race による hang／attempt 消失は残る。 |
| terminal receipt が opt-out bytes を変えるか | helper は receipt `None` なら元 event の copyだけ [p3_autonomous_workload_trial.py:665](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:665)。内部 wall event も opt-in 時だけ :1025。transport field による deterministic payload 差はない。ただし test は field 不在しか見ず、固定 clock を用いた byte比較はない。 |

## 変異 spec の entry 別静的検証

独立走査では negative 23 entry の anchor はすべて最終ソース上 `count=1`、全26 entry の指定 node 関数は実在した。以下の「検出予測」は実走結果ではない。

| Entry | anchor | DW-M03 上の意味 | 指定 node の静的予測 |
|---|---:|---|---|
| M1 | CT:203 ×1 | leaf の非compute受理拡大。wrapperでは冗長 | 検出予測 |
| M2 | CT:178 ×1 | TLS override 受理拡大 | 検出予測 |
| M3 | CT:180 ×1 | 未受理 proxy 名の受理拡大 | 検出予測 |
| M4 | CT:244 ×1 | endpoint drift 受理拡大 | 検出予測 |
| M5-leaf | CT:265 ×1 | admission env/receipt binding破壊 | 検出予測 |
| M5-provider | Provider:199 ×1 | child HTTPS route の誤配線 | real shim が検出予測 |
| M6 | CT:139 ×1 | canonical receipt identity の fail-closed 破壊 | 検出予測 |
| M7 | CT:173 ×1 | PBS 欠落・型不正の受理拡大 | 検出予測 |
| M8 | Trial:1396 ×1 | default 境界変更・過剰 opt-in | AST node が検出予測 |
| M9 | Trial:838 ×1 | 正当 opt-in の過剰拒否 | AST node が検出予測 |
| M10 | Trial:1279 ×1 | **不適格**。安定入力では同じ最後の admission を共有し、危険な per-role drift を作らない | counter は非0予測だが KILL と数えてはならない |
| M11-invalid | Trial:740 ×1 | invalid event の fail-closed receipt closure破壊 | 検出予測 |
| M11-init | Trial:688 ×1 | init event の receipt closure破壊 | 検出予測 |
| M12-pre-open | CT:290 ×1 | symlink surface を open 層へ進める | no-open assert が検出予測 |
| M12-post-open | CT:311 ×1 | swapped regular file の受理拡大 | controlled swap が検出予測 |
| M13-leaf | CT:245 ×1 | **診断文字列だけ** | 非0予測だが diagnostic pin |
| M13-trial | Trial:660 ×1 | **診断文字列だけ** | 非0予測だが diagnostic pin |
| M14-exact | Trial:724 ×1 | malformed receipt の受理拡大 | 検出予測 |
| M14-success-reject | Trial:723 ×1 | valid receipt の過剰拒否 | 成功正例が検出予測 |
| M14-success-drop | Trial:723 ×1 | valid event を receipt 無しで受理 | `_invoke` 部分は検出予測 |
| M14-opt-out | Trial:718 ×1 | forged receipt の受理拡大 | 検出予測 |
| M15 | Registry:7 ×1 | policy registry の閉集合破壊 | literal registry node が検出予測 |
| M16 | CT:182 ×1 | 従量 env の受理拡大 | 検出予測 |
| P1 | — | 正例だが provider 単体へ縮退 | 現 node の射程内では受理予測、親定義P1は未充足 |
| P2 | — | 正例だが pure evaluator 単体 | leaf受理予測、wrapper/flag正例は未充足 |
| P3 | — | 従量5 key不在の独立正例 | 扱いは妥当 |

登録された exact `old→new` で rc=0 の **SURVIVE 予測はない**。ただし root-cause 等価な次の変異は生存すると考える。

- provider 内で site/policy を再解決する M10′：M10 test は FakeProvider へ置換するため非到達。
- `_run_workload` の `generation_record["roles"][role]` から receipt/provenance を落とす M14-report-drop：成功 test は `_run_workload` を置換するため非到達。
- alias/helper 経由で flag-off 時に transport I/O を追加する P1′：P1 は provider 単体、別 test は特定 call 名だけの AST 検査なので非検出。

### Harness 契約

| 契約 | 判定 |
|---|---|
| DW-M04 単一置換・注入実在 | 現 spec では充足。anchor 1件、`replace(..., 1)`、diff stat と対象名を確認する。 |
| DW-M05 内容比較復元・flock | 直接要件は充足。`finally` 復元後の内容比較と nonblocking flock がある。 |
| DW-M06 timeout 隔離 | **不充足**。正例を含む全 timeout を成功扱いし、dispatch job／孫 process の取消し・生存照合がない。 |
| DW-M08 node 記録・rc≠0/0件停止 | 通常 rc 経路は充足。failed node を記録し、0件なら abort。ただし timeout はこの照合を迂回して成功集合へ入る。 |

### 恒真性の再点検

- 成功 consumer 正例：`_invoke` 部分は有効だが、同一 receipt object と手渡し report event により report consumer 部分が実質的に恒真。
- real subprocess shim：production provider と既定 `subprocess.run` を実際に通すため、旧 shim の恒真性は解消。ただし P1 全体の run-level 境界は証明しない。
- M10 counter：期待値を production 定数から作っておらず恒真ではない。しかし検査対象の mutant が元 root cause を表していない。
- opt-out terminal：transport field 不在は見るが、journal/report の HEAD byte parity は検査していない。

## 総括

**NO-GO**

最重要理由は次の3件。

1. mutation harness が正例 timeout まで成功扱いし、Pegasus dispatch の残存 job を隔離できない。
2. M10/M13 を KILL と数える意味論が DW-M03 に違反し、root-cause 等価 mutant が生存する。
3. 成功 consumer/report、P1/P2 が production の全経路を拘束せず、fix.md の複数の `closed` 自己申告が成立しない。

再投入前に、timeout/cancel 契約、M10/M13 の再分類・再照準、独立 receipt を使う production E2E、P1/P2 の本来の正例、lowercase pair preflight、PBS grammar 共通化を直す必要がある。