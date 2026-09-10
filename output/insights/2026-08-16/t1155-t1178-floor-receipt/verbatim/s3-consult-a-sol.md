判定は NO-GO。以下は静的検査結果であり、pytest・実測は未実行である。

1. SWO receipt は oracle 実行証明になっていない

[severity: must-fix]

[攻撃シナリオ] 攻撃者 X が oracle を呼ばず、公開定数と任意の 64 hex、任意の compiler path/version から exact 7-key attempt と 12-key raw receipt を手書きし、その raw bytes の SHA-256 も自分で計算する。提案 validator は内部一致・定数・型だけを見るため、`classification="pass"` の偽 receipt が通る。さらに portable receipt は cell、freeze entry、binary identity を持たず、別 comparator の PASS receipt の移植も検出できない。

[根拠 file:line] `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1155-t1178-floor-receipt/plan.md:32-56` は portable 側で raw receipt を保持せず、`receipt_sha256` は型検査だけとしている。実 receipt の全 field は公開・再現可能な値で、署名や秘密値はない (`orchestrator/campaign/sort_swo_oracle.py:187-216,1368-1385`)。PASS 表示も通常の dict 射影にすぎない (`sort_swo_oracle.py:1681-1707`)。既存の freeze entry 束縛は binary binding にしか届かない (`s8b_ratified_freeze.py:1709-1732`)。

[提案] 最低限、receipt に `cell_id`、freeze `entry_sha256`、独立再計算した comparator/proposal SHA、binary SHA を束縛し、receipt 移植を拒否する。ただし「oracle を一度走らせた」の証明には hash だけでは足りない。検証時の oracle 再実行、または artifact author と分離された署名付き・追記専用 oracle authority が必要。positive control は「oracle 関数を呼ぶと即失敗する設定で手書き PASS receipt を投入」「異なる comparator 間で receipt を交換」「private raw file を欠落」の 3 本を要求する。

2. `result.json` 単体 verifier は台帳削除を検出できない

[severity: must-fix]

[攻撃シナリオ] 攻撃者 Y が result 発行後に admission root を削除し、下流が `expected_holdout_admission=result["holdout_admission"]` として pure verifier を呼ぶ。artifact と expected は同じ自己申告値なので完全一致し、削除を検出しない。live inspector が先に成功した直後、pure verifier 呼出し前に台帳を削除する TOCTOU でも、その検証呼出しは cached receipt で完走できる。

[根拠 file:line] 提案 API は provenance を表せない通常の `Mapping` を期待値にする (`plan.md:315-329`)。しかも pure verifier は root に触れないと明記されている (`plan.md:334`)。現行 verifier 自身も standalone 層が journal 等の真正性を保証しないと明記する (`orchestrator/campaign/s8b_floor_stats.py:593-606`)。report は ratified reverify を毎回呼ぶので、削除が inspector より前なら report は拒否できる (`s8b_oracle_report.py:1820-1847`)。

[提案] 「pure projection verifier」と「live admission を含む公開 verifier」を別 API にする。公開 API は `repo_root` から inspector を自身で呼び、artifact receipt を期待値として渡せない形にする。可能なら inspector が発行する exact opaque witness または lock/dir-fd を検証完了まで保持する context を使う。positive control は、artifact field の自己投入、root 削除、inspector 後の削除 race を各 public consumer で拒否させる。`result.json` 単体では事後削除を検出不能であることも保証範囲へ明記する。

3. claim digest と ledger digest は再構成攻撃に耐えない

[severity: must-fix]

[攻撃シナリオ] 攻撃者 Z が admission root を削除し、manifest、freeze、journal、result から claim、main row、attempt row、consumed marker を同じ canonical bytes で作り直す。claim digest も ledger digest も同じになり、inspector は復元物を正本として受理する。削除中に別測定を行ってから旧 bytes を戻す履歴も、現在状態だけを見る検査では判別できない。

[根拠 file:line] `_claim_digest` の入力は freeze SHA、holdout、configuration、ccbench pin、env tag、role だけで、すべて公開かつ決定的である (`s8b_holdout_admission.py:406-428`)。attempt ID も cell と schedule から決定的に作られる (`:637-645`)。claim 本文の HEAD、protocol、campaign、run path、attempt IDs も既存成果物から再導出できる (`:780-811`)。`O_EXCL` は file が存在する間だけ効き、unlink 後の再作成は防がない (`:813-830,435-438`)。attempt marker も公開値だけで構成される (`:1333-1363`)。

[提案] exact 再構成を検出するには repo 所有者が消せない外部履歴が必要である。WORM/append-only service、別権限の署名付き monotonic registry、または人間管理の不変 ledger へ one-shot key を先行記録する。unkeyed digest の追加では解決しない。positive control は「全 root を削除し、保存済みまたは再導出した同一 JSONL/claim/marker を再作成して inspector を呼ぶ」。現 scope で外部 authority を導入しないなら、再構成耐性を明示的に保証外として裁定へ返すべきである。

4. `.py` の generator source pin を見落としている

[severity: must-fix]

[攻撃シナリオ] 計画どおり `s8b_holdout_freeze.py` を変更する。現在は freeze verification hold により generator bytes 検査が保留されるため赤にならないが、hold 解除時には active v1 freeze の記録 SHA と現行 source bytes が不一致になり拒否される。「pin による阻害なし」という前提で land すると、保留解除後の proof chain を壊す。

[根拠 file:line] frozen holdout は generator として `s8b_holdout_freeze.py` の SHA を直接記録する (`output/s8b-freeze/holdout_freeze.json:13-15`)。consumer は current worktree bytes を再 hash して完全一致を要求する (`orchestrator/campaign/s8b_holdout_freeze.py:870-891,947-951`)。現在は `HELD=True` かつ当該 check ID が登録されている (`freeze_verification_hold.py:14-25`)。計画はこの pinned file の編集を明示する (`plan.md:355-363`)。静的実測では現行 SHA `6ba57a5a…`、記録 SHA `1910fff3…` で、既に hold 下の不一致である。

[提案] `FROZEN_MANIFEST` の `.py` 件数だけで pin 閉包を判断しない。本 file の変更を generator transition／versioned consumer として扱うか、hold と世代移行をユーザー裁定へ送る。hold 中であることを「検査緑」と扱わず、変更 path が held source pin と交差したことを検出する静的 positive control を追加する。

5. 「実 floor 成果物 0 件」は探索範囲により覆る

[severity: should-fix]

[攻撃シナリオ] 現 worktree の `output/` だけを探索して schema 移行不要と判断するが、別 worktree を退避した `/work` 上の bundle に実 compute-node pilot result が残っている。新 schema はそれらを拒否する。

[根拠 file:line] 実物は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t748-pilot-path/w2-evidence/bundle/output/env/pegasus/calibration/s8b-floor-pilot/20260812T072101Z-261cec1c/result.json:3269-3275` にあり、mode=pilot、schema=`s8b-floor-result/v2`、120 sessions、12 binaries を持つ。対応 journal は compute node `bnode049` の execution receipt を持ち、terminal completed で閉じている (`同 run/journal.jsonl:2,259`)。別 run `20260812T072934Z-261cec1c/result.json:3269-3275` も存在する。driver の既定出力は checkout ごとの `output/` なので、現在地だけの `find output` は他 checkout を数えない (`orchestrator/campaign/layout.py:40-46`, `s8b_floor_campaign.py:5822-5826`)。

[提案] main、全既知 worktree、job bundle、保存済み submission evidence の既知 floor layoutを棚卸しし、mode/schema/再検証可能性を記録する。この 2 件は既に現行 v3 から見ても legacy なので v4 が新たに壊すとは断定しないが、「0 件ゆえ移行不要」という根拠は使えない。`/scr` に durable result がある証拠は得られず、production CLI は checkout output を使うため、そこまで一般化もしない。

6. standalone verifier は重複 binary cell を余分と認識しない

[severity: should-fix]

[攻撃シナリオ] expected が stock と sort_best の 2 組のとき、同じ `(holdout_id, configuration_id)` を持つ 3 件目を別 `cell_id` で追加し、自己 hash 型 receipt を再計算する。`got_key_set` では重複 pair が潰れ、`expected_binaries=None` なら cell ID 集合の比較もないため、余分な binary が通りうる。

[根拠 file:line] verifier は期待値と実値を pair の `set` に落とす (`s8b_floor_stats.py:906-945`)。cell ID 比較は `expected_binaries` がある場合だけで、しかも missing 側のみである (`:946-949`)。計画はこの set 差分をそのまま維持する (`plan.md:330-332`)。producer と ratified manifest は別途 exact cell set を見るが、standalone verifier には届かない。

[提案] external expected cells から canonical cell ID 集合を作り、`set(binaries)` と完全一致させ、件数も一致させる。positive control は「既存 pair の重複 binary」「未知 cell ID」「同じ cell ID に別 pair」をそれぞれ投入し、`expected_binaries=None` でも拒否させる。

7. 空集合分岐の計画は正しいが positive control が不足する

[severity: should-fix]

[攻撃シナリオ] `ledger.jsonl` は存在するが 0 byte、または他 campaign の行しかない状態にする。実装者が「file exists」を確認するだけで selected-row coverage を落としても、事前登録済み mutation は「file 自体が欠落」の一種しか試さず、生存しうる。同様に `claims/` が空、inspector へ `cells=[]`、attempt 消費期待 1 件で zero-byte attempt ledger の枝が独立に固定されていない。

[根拠 file:line] 現 `_read_ledger` は file 欠落と既存 zero-byte fileをともに `[]` として返す (`s8b_holdout_admission.py:476-498`)。計画本文は selected rows と expected cells の比較を要求している (`plan.md:404-413`) が、列挙テストは main ledger 欠落と claim 改竄のみ (`:430`)、mutation も missing file のみ (`:473-477`)。

[提案] 次を別 nodeid にする。

- root 不在
- `claims/` 空
- main ledger 不在
- main ledger zero byte
- foreign campaign 行だけ
- `cells=[]`
- attempt ledger zero byteかつ消費期待 1 件
- 全 pre-probe competing で attempt 0 行を許す唯一の正例

8. conditional exact-key の central gate を直接固定するテストがない

[severity: should-fix]

[攻撃シナリオ] helper の common/sort 集合は正しく実装するが、`validate_portable_binary_record` 冒頭で exact 集合を呼び忘れる。sort receipt の必須・禁止テストは通っても、任意の余分な key を持つ record が central validator を通り、呼出し側の一箇所でも exact 検査を忘れれば受理集合が広がる。

[根拠 file:line] 現 central validator は top-level record の exact key を検査せず、`admission_receipt` だけを取り出す (`s8b_binary_admission.py:232-254`)。既存 test は honest record の set を assert するだけで、余分 key を validator に渡さない (`test_s8b_binary_admission.py:118-121`)。計画は central exact gate を約束する (`plan.md:79-84`) が、テスト列挙は集合の meta assertion と SWO receipt 必須・禁止だけである (`:427`)。

[提案] sort/non-sort の双方で `record["unexpected"]=...` を加え、central validator 単体が拒否する positive control を追加する。さらに mutation として exact-set 呼出しだけを除去し、このテストが KILL することを固定する。未知 schema の素通り経路自体は見つからず、現行 ratified、holdout、resume は定数への不一致で拒否し、計画も pure verifier へ v4 exact 検査を追加する方向である。

9. 親 brief の grep 結果は逐語では再現しない

[severity: nit]

[攻撃シナリオ] 次の監査者が brief 記載の広い grep を再実行し、「hit は S-1 と test のみ」を証拠として利用するが、実際には別の token hit があり、実測記録が再現不能になる。

[根拠 file:line] `oracle_attempt` は `consume_oracle_attempt_ticket` にも hit する (`s8b_oracle_driver.py:1493-1498`, `s8b_holdout_admission.py:1203`)。`attempt-ledger.jsonl` は別用途だが `tools/codex_reasoning_ab.py:2452,2487-2489` にも hit する。一方、意図した意味では `PreparedCell.oracle_attempt` を floor campaign が読まず、prepared の束縛後に built recordへ載せていない (`s8b_floor_campaign.py:2445-2449,2578-2598`)。shared admission root を直接読む production module も現状は holdout admission moduleだけで、意味上の 2 主張は覆らない。

[提案] `PreparedCell.oracle_attempt` の属性参照と、`shared_admission_root()` から導出した exact path の consumer を別々に検索し、別名 ledger を除外した command を brief に記録する。

## 総括

最も危険な所見は、攻撃者 X が oracle を一度も実行せず、公開値だけで PASS receipt を合成できること。現案は「receipt field がある」ことを保証するだけで、oracle 実行を保証しない。

親 brief の実測で覆ったものは「実 floor 成果物 0 件」と「編集対象 `.py` に pin なし」。oracle field 非消費と shared admission ledger の直接 consumer 範囲は、表現上の grep 誤りはあるが意味上は維持された。

scope 外だが裁定パッケージへ送るべき所見は、削除後再構成に耐える外部 one-shot authority の要否、および `s8b_holdout_freeze.py` generator pin／freeze hold と本変更の世代移行である。