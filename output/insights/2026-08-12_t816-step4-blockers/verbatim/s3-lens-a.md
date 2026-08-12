## 総括

**現プランのまま段 4 へ進めるのは不可**です。偽の certified を作れる未検査境界が 1 件、既存の検証・再現経路を確実に壊す scope 漏れが複数あります。

特に重大なのは次です。

- 負の `txid` を持つ v2 trace が `missing_txids=0 / framing_violations=0` のまま **certified になり得る**。
- tracked の保存済み raw trace 4 本が v1 で、現行 ladder はそれを current verifier で再検証する。機械移行すると凍結証拠の hash chain を破壊し、据置なら strict parser が拒否する。
- `s2_verify_calibration.py` は歴史 pin `dff0f1e` の trace を current CLI へ渡す生きた再現経路であり、「verify 経路は 2 箇所だけ」は反証された。
- 親 brief の「framing 違反なら indeterminate」と、プランの「cycle があれば non-serializable を優先」が矛盾している。

以下は read-only の静的検証結果です。テストは実走していません。

## 1. blocker: 負の txid で false-green certified

**[静的再現]**

(a) `txid=-1` の v2 frame が密連番違反として検出されず、正常な空更新 trx として certified になります。

(b) 再現入力は次です。

```text
C -1 0 2 1 0 0
E -1
```

プランは read/write 件数だけを非負検査し、txid 密連番検査は変更しません（[s2-plan.md:89](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t816-step4/s2-plan.md:89)、[s2-plan.md:103](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t816-step4/s2-plan.md:103)）。現行検査は `expected=max(txid)+1; missing=expected-len(txns)` なので、`{-1}` では `missing=-1` となり違反を立てません（[parse.py:213](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4/orchestrator/verifier/parse.py:213)）。commit `(2,1)` は genesis 違反でもありません。

(c) 想定成果物は `n_txns=1`, `missing_txids=0`, `framing_violations=0`, `serializable=True`, `verdict="serializable"`, `certified=True`。pipeline は `vr.certified` で通すため、variant 選択・fitness・台帳 commit まで進み得ます（[pipeline.py:1051](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4/orchestrator/campaign/pipeline.py:1051)）。

`txid >= 0` を構文検査し、少なくとも `min(txids)==0` と負値不在を固定する負例が必要です。`{-1,1}` のように負値が欠番を相殺するケースもテスト対象にすべきです。

## 2. blocker: tracked の凍結 raw trace 4 本が v1

**[実測]**

(a) プランの移行対象 16 fixture とは別に、tracked の ladder raw bundle に v1 trace が 4 本あります。全ファイルの先頭 C は 5 token です（例: [trace_0.log:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4/output/env/pegasus/silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/correctness/traces/trace_0.log:1)）。これらは raw manifest に SHA-256 付きで固定されています（[raw-manifest.json:1628](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4/output/env/pegasus/silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/raw-manifest.json:1628)）。

(b) `validate_raw_bundle()` はこの保存 trace を current `verify_trace_dir()` で読み直し、保存済み verifier JSON と exact 比較します（[silo_ladder_rung1.py:2849](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4/orchestrator/campaign/silo_ladder_rung1.py:2849)、[silo_ladder_rung1.py:2862](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4/orchestrator/campaign/silo_ladder_rung1.py:2862)）。strict v2 化後は最初の C で `ParseError` です。

さらに保存 JSON の integrity schema には新 field がありません（[silo_ladder_rung1.json:507](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4/output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json:507)）。現行 validator を新 key 必須にすると、その前段でも schema reject になります。

(c) 結果は以下の二択です。

- 据置: `verify-result` が旧 certified artifact を再検証できなくなる。
- v2 へ書換え: trace SHA、raw manifest、verifier JSON、上位 evidence identity が全変更され、歴史的な `all_pass=true` の証拠を別物へ改竄する。

加えて evidence test は `verifier/report.py` を現行 bytes と一致させています（[test_silo_ladder_rung1_evidence.py:1243](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1243)）。プランどおり `report.py`、ledger、current pin を変えると、[同:1254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1254) と [同:1267](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1267) も赤になります。

これは機械移行対象ではありません。旧 artifact を歴史 verifier で隔離再生するか、current eligibility を失った歴史証拠として固定するか、人間裁定が必要です。

## 3. 親の「verify 経路は 2 箇所だけ」は反証された

**[実測]**

(a) 直接の `verify_trace_dir` caller 以外に、公開 CLI と複数の subprocess caller があります。例:

- 公開 wrapper: [orchestrator/verify.py:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4/orchestrator/verify.py:5)
- S2 calibration: [s2_verify_calibration.py:152](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4/orchestrator/campaign/s2_verify_calibration.py:152)
- lock coverage: [s3_lock_coverage.py:110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4/orchestrator/campaign/s3_lock_coverage.py:110)
- permutation coverage: [s5_permutation_coverage.py:106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4/orchestrator/campaign/s5_permutation_coverage.py:106)
- trigger coverage: [s8a_trigger_coverage.py:202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4/orchestrator/campaign/s8a_trigger_coverage.py:202)
- write-intent coverage: [t152_write_intent_coverage.py:444](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4/orchestrator/campaign/t152_write_intent_coverage.py:444)

(b) とりわけ S2 calibration は、brief が据置を命じる歴史 pin `dff0f1e` を固定し（[s2_verify_calibration.py:62](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4/orchestrator/campaign/s2_verify_calibration.py:62)）、そこから `ycsb_silo.exe` を build/run して current CLI に渡します（[同:260](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4/orchestrator/campaign/s2_verify_calibration.py:260)、[同:281](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4/orchestrator/campaign/s2_verify_calibration.py:281)）。v2 導入 commit より古いので出力は v1です。

(c) strict parser 後は CLI rc=2、stdout に JSON が無いため `_verifier_run()` が `RuntimeError` となり、S2 calibration の `all_pass` JSON/Markdownを再現できません。これは certified 選択を誤って通す問題ではありませんが、現行 phase が正本として指す再現経路の破壊です（[phase3.md:282](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4/docs/phase3.md:282)）。

SI については、**現在の自動 campaign caller** は見つけられませんでした（負の探索なので未確認）。しかし公開 CLI は protocol を識別せず任意 trace dir を受けます（[cli.py:42](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4/orchestrator/verifier/cli.py:42)）。repo は SI trace-hook と実 SI 検証実績を現役文書に残しています（[patches/README.md:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4/patches/README.md:9)、[phase1.md:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4/docs/phase1.md:97)）。したがって「自動選択経路は Silo のみ」は成立し得ても、「生きた verify 経路は 2 本だけ、受理集合の実損ゼロ」は成立しません。

## 4. brief と verdict precedence が矛盾している

**[実測＋静的再現]**

(a) brief は件数不一致・E 欠落・重複を `indeterminate` に倒すとしています（[s1-brief.md:12](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t816-step4/s1-brief.md:12)）。一方プランは、cycle と framing 違反が共存すれば `non-serializable` を維持します（[s2-plan.md:113](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t816-step4/s2-plan.md:113)）。

(b) r1 write-skew を v2 化し、片方の宣言 read count だけ誤らせれば、DSG cycle と `framing_violations=1` が共存します。現行分岐は cycle を integrity より先に返します（[model.py:205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4/orchestrator/verifier/model.py:205)）。

(c) `certified=False` は共通なので偽の選択は起きませんが、verdict/WAL reason は `non-serializable` になります。critic はこの枝では `integrity.clean=False` とだけ出し、framing counter・notes を表示しません（[digest.py:647](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4/orchestrator/critic/digest.py:647)）。報告上は「cycle と trace 破損の共存理由」が落ちます。

推奨は「実証済み cycle を `non-serializable` とする」現行順を維持しつつ、brief を修正し、critic に framing の kind/count を併記することです。逆に brief 文言を絶対視するなら verdict precedence の変更が必要です。裁定なしに両方を満たしたことにはできません。

## 5. X/I を件数から除外する保証が、テストでは発火しない

**[静的検証]**

(a) X/I を誤って observed read/write に数えても、既存 X/I テストは元から integrity 不良を期待するため、`indeterminate / certified=False` の assertion がそのまま通ります。

(b) 例は X の [test_verifier.py:296](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4/orchestrator/tests/test_verifier.py:296)、I の [同:369](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4/orchestrator/tests/test_verifier.py:369) です。プランは I を W と E の間に置きますが、「この trace の framing violation は 0」とは固定していません（[s2-plan.md:207](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t816-step4/s2-plan.md:207)）。

(c) selection は元から赤ですが、レポートに架空の `count-mismatch` が追加され、X/I という variant 機構違反と trace framing 破損が混同されます。

少なくとも X と I の各1例で `framing_violations == 0`、内部 `ParseIssues` に `count-mismatch` が無いことを固定し、「X/I を R/W に数える変異」を追加すべきです。P/A と abort 非対称について、プランどおり P/A を件数対象外にし abort が C/E を持たない扱い自体には破れを見つけませんでした。

## 6. E 検査は拒否側だが、duplicate の構造化契約を満たし切らない

**[静的再現]**

(a) EOF の open frame、次 C が来た場合、直後の重複 E はプランで捕まります。一方、記憶するのが「直前 close txid」だけなので、古い txid の重複 E は `duplicate-end` ではなく orphan/mismatch `ParseError` になります。

(b) 例:

```text
C 0 0 2 1 0 0
E 0
C 1 0 2 2 0 0
E 1
E 0
```

最後の `E 0` は `last_closed=1` のため、プランの分岐では orphan E です（[s2-plan.md:92](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t816-step4/s2-plan.md:92)）。別 txn が open 中に紛れた古い E も mismatch ParseError です。

(c) certified 選択は拒否されるので安全側ですが、`framing_violations=1 / kind=duplicate-end` の VerifyResult は作られず、pipeline 台帳は `reason="trace-parse-error"` になります（[pipeline.py:1028](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4/orchestrator/campaign/pipeline.py:1028)）。これはプラン自身の「E 重複を ParseErrorだけにするのは brief 違反」という基準とも衝突します（[s2-plan.md:224](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t816-step4/s2-plan.md:224)）。

全 duplicate を structured integrity にするなら、`last_closed` ではなく file-local の `closed_txids` 集合が必要です。即時重複だけを対象にするなら、brief を狭める裁定が必要です。

## 7. FN-2 テスト反転は本物だが、kind の保証が弱い

**[静的検証]**

(a) 計画入力では txid 1 が `read=1, write=1` を宣言し、実際は `0,0`、かつ E 欠落です。

(b) EOF で次が立つ設計です。

- `count-mismatch` 1件
- `missing-end` 1件
- `missing_txids=0`
- DSG は acyclic
- `framing_violations=2`
- `verdict="indeterminate"`
- `certified=False`

これは [s2-plan.md:190](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t816-step4/s2-plan.md:190) に明示され、単なる `not certified` assertion ではありません。FN-2 の反転自体は実効的です。

(c) ただし report に出すのは aggregate `framing_violations=2` と文字列 notes だけです（[s2-plan.md:118](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t816-step4/s2-plan.md:118)）。テストも aggregate 2 しか固定しないため、別種の違反を誤って2件作る実装でも通り得ます。

`ParseIssues` を直接検査し、kind がちょうど `{"count-mismatch","missing-end"}`、txid=1、expected=`1/1`、observed=`0/0` であることまで固定すべきです。宣言値と `len(current.reads/writes)` を直接比較する実装なら恒真比較ではありませんが、その式はプラン本文より明示的に固定すべきです。

## 8. fixture の anomaly は保存可能だが、framing 移行ミスが緑で残る

**[実測＋静的検証]**

(a) 読んだ代表2件は、metadata だけを足せば元 anomaly を保存できます。

- `integrity_orphan`: `read=1, write=0, E 0` とすれば orphan read は残る（[trace_0.log:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4/orchestrator/tests/fixtures/integrity_orphan/trace_0.log:1)）。
- `m2_version_dup`: 両 trx を `read=0, write=1` として各 E を足せば、同一 key/version の重複は残る（[trace_0.log:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4/orchestrator/tests/fixtures/m2_version_dup/trace_0.log:1)）。

(b) しかし green fixture テストは `serializable` と anomaly の有無しか見ません（[test_verifier.py:36](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4/orchestrator/tests/test_verifier.py:36)）。r1/r3 は cycle、integrity fixtures は既存の unclean 理由だけを確認します。誤った宣言件数で framing が増えても、多くのテストがそのまま通ります。

(c) g2/g3/g4 は `serializable=True` のまま `certified=False` になり得ます。r1/r3 の anomaly、orphan、version dup も保存されるため、fixture 移行が不正でもテスト全体が見かけ上緑になり得ます。

16 fixture 全てに対し `framing_violations == 0` を固定する永続テストが必要です。一時 converter の逆射影 assertion は有効ですが、削除後の回帰防壁にはなりません。

## 9. v1・空 trace の抜け道

**[実測＋静的検証]**

(a) 5-token C を含む通常の v1 trace が「空」として解釈される経路は見つかりません。計画どおり exact 7-field にすれば最初の C で ParseError です。

(b) `parse_trace_dir()` が `no trace_*.log` 以外で空リストを返す経路はあります。

- 一つ以上の空ファイル
- 空行だけのファイル
- A 行だけのファイル
- P 行だけのファイル

これは [parse.py:205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4/orchestrator/verifier/parse.py:205)〜226 の制御から確定します。

(c) `verify_trace_dir()` 経由では `n_txns==0` が `indeterminate`、`certified=False` になるので偽の certified にはなりません（[model.py:199](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4/orchestrator/verifier/model.py:199)、[model.py:212](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4/orchestrator/verifier/model.py:212)）。repo 内で `parse_trace_dir()` の空リストを直接 green 判定する consumer も見つかりませんでした。

## 10. 追加の scope 漏れ

**[実測]**

(a) プランの trace literal 地図に ladder driver test がありません。同 test は v1 C/W を生成して `validate_raw_bundle()` へ渡します（[test_silo_ladder_rung1_driver.py:1496](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4/orchestrator/tests/test_silo_ladder_rung1_driver.py:1496)）。

(b) trace 形式を記載する正本候補 `patches/README.md` も依然 v1 C/R/W のみです（[patches/README.md:356](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4/patches/README.md:356)）。ここは Silo/si 両方の入力契約だと明記されています。

(c) 前者は ladder raw-bundle テストを赤にし、後者は operator が v1 形式を正しいものとして生成・解釈する文書 drift を残します。`test_silo_ladder_rung1_driver.py:1501` の v2 化と、`patches/README.md` の「Silo=v2、SI=v1のためcurrent verifier拒否」という移行状態の明記が必要です。

## 段 4 へ返す裁定パッケージ候補

推奨は次です。

1. current verifier は v2-only のまま維持し、`txid >= 0` 検査を追加する。
2. 凍結 raw trace は書き換えない。旧 artifact は、その artifact が pin した歴史 verifierでのみ再生する隔離経路を設けるか、current eligibility を失った歴史証拠として明示する。
3. `s2_verify_calibration.py` を「歴史再現 driver」として legacy verifierへ束縛するか、再実行不能として退役させる。current verifierに v1 compatibility を戻してはいけない。
4. cycle＋framing の verdict precedence を裁定し、選んだ意味を brief・critic・共存テストへ反映する。
5. X/I 非算入変異、全 fixture framing-clean、負 txid、非直後 duplicate E、FN-2 kind/value のテストを追加する。
6. ladder synthetic trace、凍結 evidence test、`patches/README.md` を scope に含める。