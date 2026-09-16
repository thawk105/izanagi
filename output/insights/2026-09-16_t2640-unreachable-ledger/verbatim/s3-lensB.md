## 総括

全件救出案は静的検査上成立する。救出 ref は監査の到達不能集合から対象を除き、plan の直接 ref 作成・到達性再検査は台帳契約を満たす。  
ただし、親 brief の「rc=0・通知なし」だけでは、30 件の記帳も救出 ref の存在も証明できない。plan の件数確認・個別 ref 証拠を受理条件に残す必要がある。  
再集計は **30 commit・53 組、内容一致37組、全報告 path 一致16 commit／不一致を含む14 commit**。この数値区分を逆転させる証拠はないが、「未保全」「旧版」「喪失受容可能」への意味づけには飛躍がある。  
親の16件 `accepted-loss` 案は採用せず、plan の30件 `rescued` を支持する。契約・検査機構の新設は不要。静的検査のみで、救出・pytest は実行していない。

## 所見

- [B-1] 重さ(blocker) | 親の「内容一致16件なら人間の喪失受容を授権済み」という解釈は、確定裁定から導けない。
  - 根拠: `docs/unreachable-object-ledger.md:53` は「人間が喪失を明示的に受容した場合」。`ruling-d2044-item7.txt:7` の決定は具体的判断を求めるが、16 OID の喪失受容を記していない。理由文も類型による代替を否定する。
  - 成果物影響: 親案では16行が根拠不足の `accepted-loss` となり、その後の再報告まで通知対象から外れる。
  - 是正: `s2-plan.md:201` の全件救出を採用する。これは親案への blocker であり、全件救出 plan を止める所見ではない。

- [B-2] 重さ(must-fix) | 親の完了判定は必要な記帳・救出を単独では検証できない。
  - 根拠: `tools/check_branch_rescue.py:1752` は台帳不在でも空集合・issuesなしを返す。`:1732` の `rescued` 検証は解決 field の形式だけで、ref を引かない。`:1860` の stale 判定も audit 再報告を条件とする。候補なしでは `:2100` で実 root snapshot を省略する。
  - 成果物影響: 先にrefだけ作って記帳を忘れても、auditがゼロならrc=0・通知なしになり得る。逆に救出refが失われても、対象がauditに出なければ検知されない。
  - 是正: plan の既存手順どおり、対象OID集合一致、30行、全件解決、各 `rescue_ref` の直接OID・到達性証拠と最終ledger-checkを一組として受理する。新しいcheckerは作らない。

- [B-3] 重さ(must-fix) | 「30件を解決すれば通知が止まる」は、通知経路と実行時点を限定して記述すべきである。
  - 根拠: `tools/check_branch_rescue.py:1853`、`:1860`、`:1874`、`:2141`。
  - 成果物影響: status変更だけで通知解消済みと誤記したり、技術的不完全な結果を成功扱いする。
  - 是正: 最終証拠の説明には次の逐語上の条件を明記する。
    - `unledgered-audit-finding`: auditの報告OIDが有効なentry集合にない場合。新規OIDや不正entryの脱落でも残る。
    - `stale-ledger-resolution`: audit再報告かつstatusが `rescued`／`reachable-again`／`object-missing`。ref名の存在そのものは調べない。`accepted-loss` は除外。
    - `pending-ledger-entry`: auditの報告有無によらず、下界≦現在なら `deadline-passed`、現在＜下界≦現在＋7日なら `urgent`。全30件が有効な解決済みentryなら、この30件には発火しない。
    - rcは `technical_incomplete` が優先して2、完全かつ通知ありなら3、それ以外0。通知falseでもaudit timeout・parse不良などがあれば成功ではない。
  
  救出refによる除外自体は成立する。`tools/audit_dangling_commits.py:288` は対象OIDを限定せず `git fsck --unreachable --no-reflogs --no-progress --connectivity-only` を実行し、その結果だけを `:1382` から後段へ渡す。通常refから到達可能になれば対象から外れる。後段のlocal branch tip収集は `:443` の `refs/heads/` 限定だが、ここに救出refが入らないことは反証にならない。なお、`accepted-loss` を選んだOIDは到達不能のままなので、**独立したdangling auditの報告・rc=1は残り得る**。

- [B-4] 重さ(must-fix) | 14／16は内容一致の観測区分であり、情報喪失や改版関係の確定区分ではない。
  - 根拠: `content-match.json` 全53レコードの再集計。`findings.json` と `(oid,path)` 集合も一致。`tools/audit_dangling_commits.py:1413` は除外prefixやmain・branch tipのpath存在で絞っており、commit全差分の内容同値検証ではない。
  - 成果物影響: `resolution_note` に「commit全体が保全済み」「必要情報が喪失」「旧版だから不要」と過剰な結論が入る。
  - 是正: 数値区分は維持し、以下を個別判断の根拠として記す。
    - **handoff 5件**: `5b3ff770`／`c7a57d64` はblob `64281f…`、`8c2e4e3f`／`cb0d9305` は `a83bfd…`、`c0439777` は `8c44a8…`。5件は3種類の内容である（`content-match.json:3812`、`:4242`、`:4923`、`:6275`、`:6284`）。`docs/handoff/README.md:16` は正常終了時の吸収・削除を定めるため、mainで同一blobがないことだけでは情報喪失を示さない。「吸収確認なしの履歴保存」として救出する。working treeへ戻さなければ、稼働中handoffを復活させる副作用はない。
    - **T812の2件**: `1aa5ae77` のblob `442348…` と `c3e2218c` の `3e43c3…` は互いにも異なり、同名 `.gz` とも不一致（`:207`、`:4928`）。同題main commitの存在は改版の傍証だが、指定資料には本文差分がなく、旧版として置換済みか別内容かは確定できない。
    - **`75d55ccd`**: `verbatim/analyze.py` と `orchestrator/calibrator/analyze.py` は同名候補でしかなく、内容一致はない（`:4227`）。保全済みへ移さない。
  
  **親と異なる数値区分になるOIDはない。異議は区分の意味である。** 指定資料だけで「mainのどこにもない」という探索の網羅性までは再証明できないため、noteは「提供された照合で一致を確認できない」に留める。

- [B-5] 重さ(must-fix) | 親の「全件期限超過」と「26 packed」の断定は、台帳の観測値へ転記できない。
  - 根拠: `s1-brief.md:25`、`:37`。`evidence.json` のloose 4件のmtimeは9月9日で、2週間後は9月23日。`tools/check_branch_rescue.py:1377` はpack membershipを含めてstorageを分類し、`:1424` と `:1434` はpure looseとpacked等を別扱いする。
  - 成果物影響: `storage_kind`、`loss_possible_not_before`、`lower_bound_basis` が誤る。
  - 是正: planの再観測・算術訂正を維持する。9月16日06:35:04Zという既存ledger-check時刻では、4件の9月23日04時台の下界は7日以内なので、pure looseでも `pending` は **期限超過ではなくurgent** になり得る。

- [B-6] 重さ(nit) | 30本の救出refはscope内だが、成果物を「docs-only」だけで表すと共有Git状態の変更が抜ける。
  - 根拠: `s2-plan.md:151`、`:162`。`tools/check_branch_rescue.py:916` は通常refを恒久rootにする。`.claude/commands/cleanup-branches.md:29`、`:46` の棚卸し・削除対象はbranchである。
  - 成果物影響: 台帳をmergeしただけの別cloneでも救出済みと誤認したり、保持量を30commitだけと誤記する。
  - 是正: 「tracked実装差分ゼロ、共有common directoryに30ref追加」と記録する。commit・祖先・tree・blobの閉包を保持し、gcの回収対象や `rev-list --all` の集合を変える。fsckの到達不能集合も縮む。一方、branchやworktreeを作らないため `git branch -a`／`git worktree list` の項目数は増えない。保持閉包の容量・処理時間は未測定とする。

- [B-7] 重さ(nit) | 完了commandは一回で新しいref状態を反映するが、planは高価な監査を二回要求している。
  - 根拠: `tools/check_branch_rescue.py:1796` は毎回audit subprocessを起動する。既存実測は `audit-plain.txt:112` が85.194秒、`ledger-check3.json:1` が149.927041秒。既定timeoutは `tools/check_branch_rescue.py:33` の300秒。planは `s2-plan.md:182` と `:197` で再実行する。
  - 成果物影響: 完了までの所要と最終証拠の時点が曖昧になる。
  - 是正: ref作成前の結果は流用せず、完成した台帳・refに対する最終一回を証拠にする。キャッシュ更新のための二回実行は不要。途中確認を残すなら最終確認とは区別する。既存所要は約1.4分／2.5分であり、救出後の所要保証ではない。

## 親 brief への直接の異議

- **P1は撤回する。** 内容一致は喪失受容ではなく、しかも対象はaudit報告pathに限られる。30件救出なら追加裁定待ちを作らず進められる。
- **P2の14件という保存対象の限定は不要。** 30件救出は依頼された30件の具体的判断に収まり、新たな一般化ではない。
- **「必ずindeterminate」は4件の観測から一般化できない。** `s1-brief.md:26` と `:53` は、planどおり各OIDの実測値を使う。判定器の修正は不要。
- **通知解消の射程を限定する。** 本waveが閉じるのは既知30件。将来の未記帳発生や独立auditの報告停止を保証しない。
- **P3は支持する。** 一回限りの収集と既存validatorの利用、証拠保存は本題を実施する手順である。新規gate・checker・一般化されたtoolの追加はplanに見当たらない。

## scope 外だが real な所見 (裁定パッケージ候補)

- **記帳を迂回する面は残る。** `docs/unreachable-object-ledger.md:110` の手動 `git branch -d`、`:111` の `DW-O28` 自動撤去、`:112` のD978未施行部分は今回も覆わない。そこで別commitが到達不能になりauditのpath条件を満たせば、同じ `unledgered-audit-finding` が再発する。救出refの撤去・変更なら、既知OIDに `stale-ledger-resolution` が再発し得る。今回の30件へ便乗して閉じる層ではない。
- **救出ref喪失の検知には限界がある。** stale判定はaudit報告依存なので、別branchに同じpathがある、除外prefixに入るなどで対象が報告されなければ通知されない。これは現行実装の実在する制約であり、本waveで契約やcheckerを変更しない。
- **他機構との全面的な非衝突は未検証。** 指定されたcleanup commandとの名前空間分離は確認できるが、`dev_wave_cleanup.py`、land、provenance監査の実装は射影外である。`HEAD`起点の履歴集合は救出ref追加だけでは変わらず、`--all`起点なら変わる。どちらを使うかを確認せず「影響なし」「監査対象が増える」と断定しない。
- **timeout・cleanup速度・T-2688のrc解釈は実装対象外。** 提供された所要と親のtimeout観測は裁定材料にできるが、今回それらを修正・検証したとは扱わない。