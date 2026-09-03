## 総括

must-fix は 7 件です。特に C1 走は正しい入力を process 間で渡しておらず、raw 候補の増分 KILL を人工的に作っています。既知の `BASE_COMMIT` 起因 `contract-loader-drift` は再提出していません。pytest は実行していません。

## must-fix

- MF-1 — `orchestrator/tests/test_p3_b4_producer_auth_experiment.py:240-289,292-321,477-555`: C1 の発行 process は publication と空の result directory しか作らず、attempt artifact を生成しないため、後段 assembly は `incomplete_set` で拒否されますが、`_assembly_probe` は認証不一致以外をすべて `False` に潰し、lines 543-545 は raw R 以外の既存拒否を無条件で否定しています。  
  影響: raw C1 の baseline 既存拒否が受理扱いとなり、prototype の認証拒否 3 件が偽の増分 KILL になり、frozen C1 は guard 前の早期 return で走行不能になるため、比較値と decision は無効です。

- MF-2 — `orchestrator/tests/test_p3_b4_producer_auth_experiment.py:990-1004,1048-1063` / `orchestrator/campaign/p3_b4_producer_auth_experiment.py:927-1057`: 「承認済み prereg」は実在せず、走行直前に executable registry 自身から `canonical_preregistration_bytes()` を生成して同じ registry と比較しているため、D1531 の独立した内容凍結になっていません。  
  影響: mutation、投入位置、期待 matrix、decision input をコード側で同時変更すると検査を通過し、受理集合と勝者を事後変更できます。

- MF-3 — `orchestrator/tests/test_p3_b4_producer_auth_experiment.py:499-507,529-537`: issuer の R/D と raw の D は rogue artifact を別 directory に書くだけで、その bytes を続く issuer/assembly routeへ渡しておらず、正常 publication に対する guard probe を結果として採用しています。  
  影響: issuer の decision-input R 3 件と D control 6 件は実変異への SURVIVED ではなく no-op の値となり、候補の受理集合と D 系非保証の根拠が失われます。

- MF-4 — `orchestrator/campaign/p3_b4_producer_auth_experiment.py:621-648,664-725`: `decide_candidate()` は 39 組の完全性、重複、`ABORTED`、期待不一致、非後退結果を検査せず、欠損や中断をゼロ KILL としてそのまま leader を選びます。  
  影響: cleanup failure や欠損 case が候補の点数を下げて別候補を勝者にでき、既存受理集合を壊す候補も decision から排除されません。

- MF-5 — `orchestrator/tests/test_p3_b4_producer_auth_experiment.py:1076-1133` / `orchestrator/campaign/p3_b4_producer_auth_experiment.py:664-725`: 29-node 非後退走は独立した pytest assertion に留まり、結果や候補別 eligibility が comparison report に入力されません。  
  影響: candidate-specific な既存テスト回帰が report に現れず、matrix 上の leader と実際に維持される受理集合が食い違います。

- MF-6 — `orchestrator/tests/test_p3_b4_producer_auth_experiment.py:1043-1047,1076-1083`: scratch が書けない場合、78 走と候補別 29-node 検査を `pytest.skip` するため、24 meta node だけで pytest の終了値が成功になり得ます。  
  影響:比較値も非後退証拠も無い状態が成功扱いされ、未測定候補について decision を進める余地が残ります。

- MF-7 — `orchestrator/campaign/p3_b4_producer_auth_experiment.py:873-906`: case 単位で `ABORTED` に変換するのは `ScratchTreeError` だけで、subprocess failure、route assertion、artifact I/O などは全走を例外終了させ、該当 case の中断記録を残しません。  
  影響:異常 case が比較表から消え、比較値と decision を再現できない全体失敗になります。

## 主 worktree と凍結境界

新設コードから主 worktree の tracked file を直接書き換える経路は確認できませんでした。prototype patch、C0/C1 source mutation、artifact 出力は `ScratchTree` 配下です。

5-file pin の拡張も `orchestrator/campaign/p3_b4_producer_auth_experiment.py:433-476` の scratch 用 exact patch に閉じています。恒久的な `_SOURCE_CLOSURE_PATHS` / `_CLOSURE_PATHS` 変更はありません。

frozen は `orchestrator/campaign/p3_b4_producer_auth_experiment.py:462-475` で receipt 作成後、`evaluate_b4_artifacts` 前に独立した `ProducerAuthRejection` を発生させており、凍結 reason enum への写像はありません。

`ScratchTree.__exit__` の通常の破棄失敗は `orchestrator/campaign/p3_b4_producer_auth_experiment.py:826-839,889-905` で `ABORTED` になります。ただし失敗した directory は scratch root に残り、SIGKILL では case tree と一時 prereg file が残ります。主 worktree の tracked bytes は残留物に含まれません。

## 正しさゲートの弱体化

MF-1、MF-4、MF-5、MF-6 が該当します。

既存 producer test の期待値変更、削除、恒久 skip はありません。指定 command は `test_p3_b4_raw_record_producer.py` 全体を選択しており、静的には既存 29 node を指しています。ただし、候補別結果を report/decision に束縛していない点と、外側 gate 自体が skip 可能な点は解消が必要です。

fixture への現行 working-tree hash 差し込みは確認できませんでした。

## scope 逸脱

所見はゼロです。汎用 gate、新台帳、族一般化、公開 dataclass 拡張、本番認証層の恒久採用は確認できず、変更は新設 experiment/test 3 file と scratch patch 定義に閉じています。

## 書かれていない非保証

- `orchestrator/campaign/p3_b4_producer_auth_experiment.py:716-724`: 項目 1 は対象集合を列挙するだけで、「他の判断値」「任意のコード変異」「coordinated rewrite」「path race」へ一般化できないことを名指ししていません。  
  影響:測定外の攻撃まで拒否できると解釈され、候補の保証範囲と採用 decision が過大評価されます。

- `orchestrator/campaign/p3_b4_producer_auth_experiment.py:719`: 項目 3 は temporary prototype とだけ書き、値が「追加 gate を伴う 6-member closure」のものだという条件、現行 5-file consumer の拒否能力ではないこと、本採用可否を示さないことを明示していません。  
  影響:frozen の counterfactual 値が現行 consumer の性質として扱われ、受理集合と採用可否を誤判定します。

残る 5 項目は短い識別子形式ながら内容を表しています。

## nit

- `orchestrator/campaign/p3_b4_producer_auth_experiment.py:744-758` / `orchestrator/tests/test_p3_b4_producer_auth_experiment.py:907-921`: 主 worktree 不変検査は porcelain status の一致だけなので、開始時から dirty な tracked path の bytes が別内容へ変わっても status が同じなら検出できません。現実装内にその書込経路は見つからないため nit とします。