## 判定と確認範囲

**GO。レンズ B の範囲で must-fix はありません。** 親の修正版 M0〜M4 の期待 node 集合は静的検証と一致します。

指定資料を読み、patch と統合後の実装を照合しました。ファイル変更・pytest・変異実行はしていません。以下、`tool` は `tools/dev_wave_cleanup.py`、`test` は `orchestrator/tests/test_dev_wave_cleanup.py`、報告資料は指定 job directory 内を指します。変異結果の完全集合は静的予測であり、親の probe による実測確定は未確認です。

## prefix と recovery

**自己判定：refuted — 部分撤去後に prefix がずれ、共有 object を拒否する懸念。**

snapshot の再帰は `prefix + name + "/"`（`tool:809`）、撤去側も同じ規約（`tool:982`）、root 呼出しは `prefix=""`（`tool:1045`）です。兄弟 entry の欠落は残存 entry の相対パスに影響しません。

recovery は `_load_admin_recovery` → `_bind_admin(..., recovery)` で保存 snapshot を取得し（`tool:909,853`）、現在の木を `_assert_snapshot_subset` で照合します（`tool:947,958`）。`_recheck_admin` が返す **current**（`tool:969`）を `_mutate` が撤去へ渡すため（`tool:1317,1319`）、既に消えた entry を削除し直しません。

`tool:947,967,1037,1043` の snapshot はすべて空 prefix から同じ `tool:814` の述語を通ります。submodule の `HEAD`・`config` が先に消えても、分類は sibling の存在に依存しません。

**段9への影響：** prefix 起因で再入が rc=20/30 に戻る経路は認めません。撤去は束縛済みの自 wave admin 内に限定されます（`tool:979,991,1048`、D2119 項8）。

## race test の成立性

**自己判定：refuted — wrapper の再帰、入口での先行拒否、DW-O14 違反という懸念。**

`test:1190` で保存した `original` を `test:1195` で呼び、dev/ino 一致・未注入の場合だけ先にフラグを立て、実 file に実 hardlink を作り、link 前の stat を返しています（`test:1196`）。patch 範囲は直接読取だけです（`test:1203`）。

`cleanup.os` と test の `os` は同じ module ですが、wrapper が保存関数へ委譲するため再帰しません。実際の順序は次のとおりです。

1. 初回 `fstat` は保存済み nlink=1 を返し、入口を通過（`tool:765`）。
2. 実 bytes を読む（`tool:770`）。
3. 2回目の `fstat` は nlink=2。
4. registry は nlink 比較で不一致となり、`admin entry changed while reading`（`tool:775,778,780`）。
5. object は nlink/ctime を比較しないため bytes を返す（`tool:773`）。

M4 は入口条件を変えず、この4番の拒否だけを消します。ctime の時計精度に依存せず、nlink の差で検出できます。`_read_admin_file` は patch の編集対象であり、この実物へ委譲する観測 wrapper を DW-O14 違反とする根拠はありません。

**段9への影響：** 本実装は object の共有操作による偽拒否を除き、registry の読取中 hardlink 化の拒否を維持します。M4 相当では後者の受理集合が広がります。

## recovery 拡張の被覆

**自己判定：refuted — 拡張が意図した中断点を通らない、または既存 assertion を弱める懸念。**

- `None-gitdir` だけに helper を追加しています（`test:1222`）。snapshot は名前順（`tool:795`）なので、root は `HEAD` → `commondir` → `gitdir` → `index` → `logs` → `modules`。実 `gitdir` unlink 後の中断（`test:1236`）は `modules` 撤去前です。初回 alias nlink=2（`test:1254`）、再入成功後の bytes 不変・nlink=1（`test:1279`）が対応します。
- `linked` だけに helper を追加しています（`test:1372`）。temporary unlink の**実行前**に中断し（`test:1379`）、final journal と temporary が同じ inode のまま残ります。admin 撤去前の recovery を被覆します。再入は `tool:889` で該当 temporary を除去して journal を既定の厳格読取へ渡します。
- patch は既存 parameter・assertion を削除していません。foreign admin 不変、branch 保持、中断 phase、再入成功の検査も残っています（`test:1250,1269,1274,1409,1422`）。

**段9への影響：** admin 撤去前と root 部分撤去後の両方で、共有 object を残した再入成功を検証します。他 admin の inode・bytes 不変も引き続き検査します。

## M0〜M4 の完全集合と単一理由性

以下の node はすべて `orchestrator/tests/test_dev_wave_cleanup.py::` 配下です。

| 変異 | 静的な期待結果・完全集合 | KILL の理由 |
|---|---|---|
| M0 | SURVIVED、`[]` | return 式の外側括弧は等価 |
| M1 `return True` | KILLED、`test_admin_nonobject_hardlink_is_rejected[gitdir]`、`[submodule-config]`、`[ref-named-objects]`、`[submodule-named-objects]` | 非 object の snapshot／撤去読取を許容 |
| M2 `return False` | KILLED、`test_admin_shared_objects_are_removed`、`test_unpublished_admin_journal_reenters[linked]`、`test_cleanup_partial_admin_removal_reenters[None-gitdir]` | 初回 preflight の共有 object 読取が rc=20 |
| M3 撤去側 keyword 除去 | KILLED、M2 と同じ3 node | 撤去側の共有 object 再読が rc=30、`phase=admin-remove` |
| M4 stable 条件を `if True` | KILLED、`test_admin_read_link_race[registry]` | 読取中 nlink 変化を見逃し `DID NOT RAISE` |

**自己判定：refuted — 親案以外の既存 node も決定的に赤になる懸念。**

追加の赤 node は静的には認めません。特に次を確認しました。

- journal hardlink 負例（`test:1432`）は既定呼出し `tool:896` の入口で拒否されます。M1 はこの呼出しを変えず、M4 も入口検査を変えません。
- index-change 6 case（`test:1335`）は読取前に bytes を追記、または inode を交換します。snapshot の length/sha256・inode 比較が残るため、M1/M4 でも期待した拒否を維持します（`tool:820,952`）。
- registry 再検査の11 case（`test:1283`）も marker、bytes、binding、inode、symlink、wave 再出現で拒否されます。nlink/ctime のみの変化を検査する既存 case ではありません。
- recovery の他 parameter は helper を追加しておらず、M2/M3 による共有 object 拒否を踏みません（`test:1222,1372`）。
- `submodule-config` 負例は共有 object も持ちますが、`config` が先に読まれて拒否されるため、M2 でも緑です（`test:1150`、`tool:795`）。
- race 2件は述語を呼ばず、keyword を直接指定するため M1〜M3 の影響を受けません（`test:1206,1209`）。

M3 の recovery 2件は、初回の意図的中断では赤になりません。**再入の成功 assertion**（`test:1274,1422`）が、撤去再読による rc=30 で赤になります。通常正例と同じ原因であり、DW-M01 の単一理由性に整合します。

anchor は読み取り専用の文字列計数で、M0/M1/M2 の return 行（`tool:759`）、M3 の2行（`tool:987`）、M4 の2行（`tool:772`）とも各1回でした。

**段9への影響：** M2 は共有 object が残る対象を rc=20 で停止させ、M3 は部分 admin・journal・branch を残して rc=30。M1/M4 は registry の拒否を弱めます。M0 は挙動を変えません。DW-M08 の実測上の完全集合は親 probe で確定する必要があります。

## M1 の到達性と author 報告

**自己判定：refuted — M1 の4 case が別 gate で止まり KILL できない懸念。**

`gitdir` は CLI 前の直接 snapshot assertion が `DID NOT RAISE` になります（`test:1168`）。CLI だけなら resolver の既定拒否が残るため、直接 assertion は必要です（`tool:631`）。

他3 case は root binding を変更せず、tracked tree にも変更を加えません。fixture は landed・unlocked（`test:61,63,84`）、occupancy は通過（`test:1143`）。`_assert_clean_and_head` が読む checkout の dirty 条件も作っていません（`tool:1195`）。M1 なら snapshot と撤去再読が通り、CLI rc=0 により `test:1173` が赤になる推論は成立します。

**段9への影響：** M1 相当なら該当 modules 内 registry hardlink を受理して撤去します。4 case は snapshot 境界と CLI 撤去の退行を検出します。

**自己判定：real／nit — 段4文書の旧 M1 と期待4 case の不整合。ただし今回の親案で解消済み。**

`return parts[0] == "modules"` は root `gitdir` に False を返すため、その node を殺しません。author の指摘（`s5-author-unit1.md:52`）は正しく、今回指定の `return True` なら4 case と一致します。

author 報告の(b)の反実仮想は実装と整合しますが、直接呼出し実測自体を本レビューで再現したわけではありません。(c)の anchor 各1回は独立確認しました。(d)の既定呼出し6件も `tool:631,847,848,896,1031,1052` に一致します。node 名 pin は `test_pytest_collection_config.py:370,390,488` に残っています。

**段9への影響：** 旧 M1 の記述を登録へ戻すと root registry の変異被覆を誤報します。製品コードの撤去挙動には直接影響しません。

## 所要と保証の限界

**自己判定：real／nit — 焦点走から受入全走5分以内までは確定できません。**

新規は正例1・負例4・race2の計7 node。recovery 拡張は node 数不変で、143 → 150 と一致します（`test:1122,1136,1181,1217,1368`）。親ログは計算ノード `gen_S`、**150 passed in 4.39s** を記録しています（`focus-impl-1.log:2,18`）。

login baseline 13.2秒との差は実行環境が異なる比較であり、node 数や本修正による高速化には帰属できません。焦点走に大幅な所要悪化の兆候はありませんが、ログ自身が受入全走ではないと明記しています（同`:1`）。5分上限への適合は受入全走で確認する事項です。

**段9への影響：** 所要の留保は rc・撤去範囲を変えません。性能問題を理由に追加 gate やテスト緩和を求める根拠もありません。

object の ctime による変更履歴検出が弱まる点は既裁定どおりで、author も明記済みです（`tool:773`、`s5-author-unit1.md:43`）。新たな must-fix ではありません。

## 総括

- **(a) GO / NO-GO：GO（レンズ B）。** 変異の完全集合は静的予測であり、親 probe・受入全走・段9の実測完了を意味しません。
- **(b) must-fix（real）：なし。** 実装への修正指示はありません。
- **(c) should / nit：** 段4の旧 M1 記述を最終登録へ持ち込まず、今回指定の `return True` と4 caseを対応させること。author の指摘は正しいです（`s5-author-unit1.md:52`）。焦点走4.39秒を受入全走5分以内の証拠にしないこと（`focus-impl-1.log:1,18`）。
- **(d) refuted：** prefix のずれ、race wrapper の再帰・入口先行拒否、recovery 被覆不成立、既存 assertion の緩和、M1 の到達不能、M3 が preflight rc=20になるという推論、追加の既存 KILL node、anchor 重複。理由と行番号は各節のとおりです。
- **(e) 裁定パッケージ候補：なし。** 本レンズから scope 外の gate・検査・一般化は提案しません。