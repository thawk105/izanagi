## 裁定の射程

**1. 親の旧 P1 の根拠は逐語に反する。〔real／scope 内／must-fix〕**

[D1936 項38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2563-walltime-refreeze/docs/decisions.md:58398) は確かに「必要分だけ要求時間を増やす」と定める。しかし後続の [D1971](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2563-walltime-refreeze/docs/decisions.md:59442) は明記している。

> 要求時間・timeout・標本数は本waveで変更しない。

> 要求時間増加へ戻さず、時間式再凍結を完了扱いにしない。

「既定解としない」という見出しだけを根拠に、短縮策撤回後の増枠を許可したとは読めない。一方、plan を「恒久禁止と読んだ」とする追補も強すぎる。plan の結論は「現裁定のまま実装へ渡せない」であり、将来の変更まで永久に禁じるとは述べていない。

**成果物影響:** 旧 P1 では新規 receipt の要求枠・式・値が変わり、未解決の最大経路包含を解決済みとして材料レポートへ載せることになる。

**2. D1986 は P1′ の意味変更を授権していない。〔real／scope 内／must-fix〕**

全文を活動名・成果物名でも検索し、末尾 D2019 まで確認した。T-2563 の要求時間を変更する、D1971 より新しい裁定は見つからなかった。D1986 は新しいが、項3・9・10 の対象はそれぞれ T-1912・T-2469・T-2485。前文も「各実装は名指しの変更に限定」とする。

限界を明記する説明方針の参考にはなるが、`required_s` を「既存逐次処理の上限」から「CLI と後処理の配分」へ変更する権限にはならない。

**成果物影響:** P1′ は新規 receipt の `required_s` を 6610→5590 に変更し、同じ欄が表す保証の意味と成果物の digest を変える。

## 活動を止める裁定の探索

**3. 認定較正全体・当該 script の一律凍結は確認できない。〔refuted／scope 内／nit〕**

個別時間値に限定せず、較正・認定・calibration・`certify_calibration` と停止・凍結・保留・再開を、決定の節単位で照合した。

- D155 決定5には「この wave」は較正の再取得・凍結 bytes・pin を更新しないという制限がある。一律の恒久停止ではない。後続 D547 は D143 の択一を終端し、D1936 項7も rr95/rr5 の取得認可を確認している。
- D1936 項39 は **Cicada** を Silo 合成再開後に置く順序制約。
- D1971 は当該短縮実装の撤回と時間式再凍結の未完了を定める。これを認定較正そのものの停止へ広げる根拠はない。

**成果物影響:** 一律凍結を理由に成果物を変更すべき根拠は確認できないため、must-fix とはしない。

## 親の実測の一般化

**4. `b3c62ee7f` の変更は確認できるが、「現在2通り」は限定が必要。〔real／scope 内／nit〕**

`git show` で専用 `condition_gate(300)` の撤去と、冒頭コメントの 6910→6610 を確認した。現行コメント・数値代入・receipt 文字列は 6610 で一致する。

ただし、この確認から歴史資料を含めた異なる式の総数が「2」とは導けない。確実に言えるのは「コメントと receipt の食い違いは消えたが、実処理との不整合は残る」まで。

**成果物影響:** 「2通り」という数自体から選択値・受理集合・参照の変更は示せないため nit。

**5. 3250 は timeout 設定値の部分和であり、job の実時間上限ではない。〔real／scope 内／must-fix〕**

訂正の算術は正しい。

```text
30 + 120 + 180 + 360 + 360 + 120 + 1800 + 60 + 60 + 120 + 40
= 3250
```

perf は第1候補の smoke 失敗後、第2候補の version・smoke へ進めるため最大配分40秒。3230 は20秒不足していた。

しかし、[script](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2563-walltime-refreeze/tools/pegasus/certify_calibration.sh:626) には timeout のない `git worktree add`、複数の `git status`、interpreter 起動・版数確認・後処理がある。submit receipt 待ちの最大60回の sleep も含まれない。

したがって 8840 も**選んだ予約項の和**であり、「真の最大所要時間」ではない。追補の「3250は下限」も、実所要の下限という意味なら誤り。省略項のある配分集計、と呼ぶべきである。また `remaining` は perf 前に計算されるので、後処理600秒の確保保証にもならない。

**成果物影響:** 部分和を最大経路保証として凍結すると、receipt と材料レポートが実装の保証範囲を過大表示する。

**6. 「rc≠0なら accepted 成果物は一つも残らない」は反証される。〔real／scope 内／must-fix〕**

[CLI の書込み順](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2563-walltime-refreeze/orchestrator/calibrator/cli.py:1017) は次のとおり。

1. 計測・事後観測・品質判定後に `status="accepted"` を決める。
2. accepted 内容の `attempts/<id>/candidate.json` を書く。
3. `calibration.md` に `quality: accepted` を書く。
4. `registered/calibration-<digest>.json` を公開する。
5. 公開後自己比較、attempt 内 rename、`publish.json` の書込みを行い、最後に `return 0`。

**2以降から終了までに outer timeout が発火する経路がある。** TERM を例外化する処理は確認できず、`except (Exception, SystemExit)` は TERM 時の清掃を保証しない。shell は非ゼロ終了を記録するだけで、CLI 側の accepted ファイルや registered target を撤去しない。

下流も完全には閉じていない。

- [calibration admission](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2563-walltime-refreeze/orchestrator/campaign/calibration_verify.py:83) は渡された path・SHA・schema・環境値を検証する。shell の `job-result.json`、`failure.json`、`publish.json` は照合しない。**完全に書けた candidate／registered artifact を明示参照する経路**を、job 失敗だけでは拒否できない。
- `collect_receipt.py:142` は `calibrate_rc` の整数型を要求するが、ゼロは要求しない。失敗結果と残存成果物を同じ収集 receipt に束ね得る。

ただし、**計測途中で殺された新規 attempt が不完全標本を accepted にする経路は確認していない**。accepted 決定は計測終了後である。既存参照が残存ファイルへ自動更新される経路も確認していない。

**成果物影響:** 失敗 job に accepted 材料レポート・較正 JSON が残り、明示参照された完全な JSON は後段の較正材料として受理され得る。

**7. 5590への変更による「小さい qsub 要求の通過」は現行 wrapper 経路では反証される。〔refuted／scope 内／nit〕**

CLI 単体の不等式では、他条件を満たす `5590 ≤ Q < 6610` の入力は差を生む。しかし [script:233](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2563-walltime-refreeze/tools/pegasus/certify_calibration.sh:233) は submit receipt の要求秒数を policy の `REQUESTED_S=7200` と**実行時に一致検査**する。根拠は B4/B5 の静的テストだけではない。

P1′ が変更するのは producer の値で、CLI の受理述語そのものではない。現行 policy・wrapper のまま小さい要求を通す具体的経路は確認できない。したがって、この理由だけで受理集合拡大を must-fix とするのは不適切。ただし、所見2の意味変更は別問題として残る。

**成果物影響:** 正規 wrapper 経路で小さい要求により新たに受理される成果物は示せないため nit。

**8. 186秒・35〜39秒・長時間要求の前例は保証へ一般化できない。〔real／scope 内／nit〕**

一次資料の35〜39秒は `Started→pre observed` の区間であり、**その後の perf 選定等まで含む計測前全体ではない**。35秒側は撤回した並行化候補の別ノード1標本で、現行逐次構成の反復実測でもない。

長い PBS directive の存在は、この時点の gen_S・SFC・当該利用者の要求が受理される証拠ではない。必要なのは当該時点のキュー上限・資源制限・予算条件、または当該要求に対応する scheduler の受理記録。前例だけでは待ち時間や費用も確定しない。

**成果物影響:** この観測だけでは選択値・受理集合の変化を示せないため nit。ただし「7200で足りる」という材料レポートの保証根拠には使えない。

## scope の切り方

**9. 別 script の同一欠陥は、調べた箇所では確認できない。〔refuted／scope 外／nit〕**

`silo_ladder_rung1.sh` と `ss2pl_lock_study.sh` の依存構築は、各 command に同じ上限を繰り返し与える方式ではなく、**共有 deadline から残時間を差し引く方式**だった。`floor_campaign.sh` も driver envelope と prologue 見積りを分け、残余を「保証値・実測値ではない」と明記している。

これで他 script 全体の正しさを証明したわけではない。同型欠陥が別 script に見つかった場合も、対象 script を明示した局所完了なら成立し得る。「Pegasus job 全体の予約保証を再凍結した」とは呼べない。

**成果物影響:** 他 script の変更で改善する具体的な成果物値は確認できず、scope 拡張は推奨しない。

**10. P1′ を T-2563「再凍結完了」と呼ぶことはできない。〔real／scope 内／must-fix〕**

予約値の再定義と限界説明は、D1936 の最大経路を収容する欠陥修正を達成しない。D1971 も完了扱いを明示的に退けている。

**成果物影響:** 完了表記により、未解決の予約保証を proof chain 付き材料レポートの解決済み前提へ昇格してしまう。

## 総括

**第3案「T-2563の予約式不整合と保証限界の追補」を選ぶ。**

- 7200秒・各 timeout・標本数・`frozen_required_s=6610` と既存 receipt を維持する。
- 予定済み insight・説明文で、3250／8840の限定された意味と、所見6の公開・終了順序を記す。
- 「誤認定は生じない」「accepted は一つも残らない」という包括保証を撤回する。
- 完了対象は**現物照合と保証説明の訂正**。T-2563の時間式再凍結は未解決として残す。

これは D1971 の現状維持を採用し、D1986 を他案件の数値変更権限へ一般化しない選択である。追加の関門・台帳・並行化は不要。

静的照合のみ実施し、編集・テスト・計測・commit・push は行っていない。探索中の `orchestrator/env_attestation*` は存在せず、実在する `orchestrator/campaign/env_attestation.py` と admission leaf を特定して検査を継続した。