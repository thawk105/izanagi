## 判定と確認範囲

**NO-GO：A1 は closed ですが、指定された M1 の anchor と期待6件が不整合です。** 修正が必要なのは親の変異登録です。製品コードの安全性に関する新たな must-fix はありません。

必読資料はすべて読めました。ファイル変更・pytest・テスト関数の直接実行はしていません。anchor は現物の文字列計数、分類はコードと component 列の検算で確認しました。

親の `focus-impl-2.log` は **152 passed in 14.12s、rc=0**。ログ自身が明記するように、受入全走・変異実走・段9の成功証拠ではありません。

以下、`tool`＝[tools/dev_wave_cleanup.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2777-cleanup-hardlink-fix/tools/dev_wave_cleanup.py:758)、`test`＝[orchestrator/tests/test_dev_wave_cleanup.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2777-cleanup-hardlink-fix/orchestrator/tests/test_dev_wave_cleanup.py:1136)。`H38` は38桁の小文字hexです。

## A1 — ref／reflog の誤分類は closed

**判定：real／修正済み。** `tool:763` の除外節で、次の中間 component が検査されます。

| admin 相対パス | `parts[1:-3]` | 結果 |
|---|---|---|
| `modules/sub/refs/heads/objects/ab/H38` | `['sub','refs','heads']` | False |
| `modules/sub/logs/refs/heads/objects/ab/H38` | `['sub','logs','refs','heads']` | False |
| `modules/sub/refs/objects/ab/H38` | `['sub','refs']` | False |
| `modules/sub/worktrees/wt/refs/heads/objects/ab/H38` | `['sub','worktrees','wt','refs','heads']` | False |
| `modules/sub/worktrees/wt/logs/refs/heads/objects/ab/H38` | `['sub','worktrees','wt','logs','refs','heads']` | False |
| `modules/sub/modules/nested/refs/heads/objects/ab/H38` | `['sub','modules','nested','refs','heads']` | False |
| `modules/sub/objects/ab/H38` | `['sub']` | True |
| `modules/sub/modules/nested/objects/cd/H38` | `['sub','modules','nested']` | True |
| `modules/objects/objects/ab/H38` | `['objects']` | True |

入れ子 submodule の reflog も同じ列に `logs`／`refs` が入り False。admin root 直下の `refs/...`、`logs/...`、`worktrees/...` は、先頭が `modules` でないため `tool:760` で False です。

新規2件は `test:1158,1162` にあり、共通 assertion `test:1183` 以下で rc=20、木・branch・alias bytes・nlink の不変を要求しています。

**段9への影響：** A1 の同形 registry hardlink を共有 object として撤去継続する経路は閉じています。

## 安全側の限界と他 subtree

**判定：real／既裁定の制限。** `modules/refs/x/objects/ab/H38` の中間列は `['refs','x']`、`modules/logs/x/objects/ab/H38` は `['logs','x']`。真の store でも False です（`tool:763`）。

これらが **nlink>1 の regular file** なら、通常 preflight で `tool:773` の厳格条件により rc=20。False だけで、nlink=1 のファイルまで拒否されるわけではありません。

fix 前の述語を P とすると、fix 後は `P ∧ 中間列にrefs/logsがない`。受理集合は縮小するだけで、規律2を緩めません。

他 subtree は、標準配置と任意に置いたファイルを区別する必要があります。以下の False 判定は `tool:760,765` からの推論です。

| subtree | user 名の階層／同形パスの可能性 |
|---|---|
| `branches/` | 旧式の user 指定名を持つ URL shorthand。手動で `branches/objects/ab/H38` を置けば述語は True になり得るが、Git が ref 名から自動生成する階層ではありません。 |
| `rr-cache/` | 標準は conflict hash と `preimage`／`postimage` 等。user のパス階層を再現せず、指定 object 名前形にはなりません。 |
| `lfs/` | 標準は `lfs/objects/<2hex>/<2hex>/<64hex>`。末尾から3番目が `objects` でなく、ファイル名長も38／62桁でないため False。 |
| `worktrees/` | user の checkout 名に由来する ID を持ちます。配下の ref／reflog は今回の除外対象、通常の `HEAD`／`gitdir` 等は名前形で False。 |
| `hooks/` | Git の標準 hook は固定名。独自補助ファイルとして同形階層を手動配置することは可能ですが、標準生成形ではありません。 |
| `info/` | 標準の `refs`／`exclude`／`attributes` 等は固定名で False。任意の独自階層まで禁止する述語ではありません。 |
| `remotes/` | `branches/` と同様、旧式 shorthand の user 指定名を持ちます。手動配置した同形階層への一般的な拒否保証はありません。 |

配置の根拠：[Git repository layout](https://git-scm.com/docs/gitrepository-layout)、[Git rerere 実装](https://raw.githubusercontent.com/git/git/master/rerere.c)、[Git LFS 仕様](https://raw.githubusercontent.com/git-lfs/git-lfs/main/docs/spec.md)。

**判定：refuted — この述語が任意の subtree に置かれた非objectをすべて識別する、という一般化。** 名前形による分類という限界は残ります。上記の手動配置を理由に除外集合の拡大を must-fix にはしません。

**段9への影響：** `refs`／`logs` を含む真の共有 store では rc=20 が残ります。他 subtree の仮想配置から、この wave の失敗や新たな gate の必要性は導けません。

## 既存所見の退行検査

fix 1 は、定数・述語の変更と負例2 case の追加だけです。test の既存 parameter 行は6件へ書き換わっていますが、旧4 id は維持。**既存 assertion の削除は、初回 patch・fix 1 patch とも0行**です。

| 所見 | 判定・現物の根拠 | 放置時の段9への影響 |
|---|---|---|
| 入口条件 | **refuted／退行なし**。regular 判定、nlink=0 拒否、allow=False の nlink=1 条件は不変（`tool:773`）。 | 新たな特殊 file／0-link 受理はありません。 |
| `stable()` | **refuted／退行なし**。object の5要素、registry の7要素比較は不変（`tool:779`）。 | registry race 拒否を維持。object の ctime 履歴検出低下は既裁定の nit のままです。 |
| 既定6呼出し | **refuted／退行なし**。`tool:631,854,855,903,1038,1059` は keyword なし。 | resolver・binding・journal の拒否を維持します。 |
| semantic／marker | **refuted／退行なし**。root の4パス完全一致、分類前の marker 拒否、symlink／特殊 file 拒否を維持（`tool:803,822,825`）。 | 拒否迂回や semantic 範囲の拡大はありません。 |
| prefix／recovery | **refuted／退行なし**。再帰の prefix と root 空文字は不変（`tool:816,989,1052`）。 | HEAD／config 消失後も分類が変わらず、部分撤去後の再入を維持します。 |
| race fixture | **refuted／退行なし**。保存 fstat、実 link 注入、直接読取範囲の patch は不変（`test:1200`）。 | registry の nlink 変化による拒否を引き続き検査します。 |
| A5／環境変数 | **refuted／退行なし**。`GIT_OPTIONAL_LOCKS=0` と木全体の比較は維持（`test:1147,1185`）。 | index の任意更新を抑え、hardlink 拒否自体は緩めません。 |
| A6／既存 assertion | **refuted／退行なし**。既存正例・race・recovery assertion は削除なし（`test:1122,1191,1227,1378`）。 | synthetic の保証は維持。ただし live 成功は引き続き未確認です。 |

## 変異 anchor と M1 の不整合

**anchor 重複の懸念は refuted。指定文字列はすべて各1回です。**

| anchor | 開始行 | 出現回数 |
|---|---:|---:|
| M0 最終 return 2行 | `tool:765` | 1 |
| M1 同上 | `tool:765` | 1 |
| M2 同上 | `tool:765` | 1 |
| M3 撤去側読取2行 | `tool:994` | 1 |
| M4 stable 分岐2行 | `tool:779` | 1 |
| M5 registry 除外2行 | `tool:763` | 1 |

**新規所見 F1：real／must-fix（変異登録）。** M1 で `tool:765` の2行だけを `return True` に置換しても、次が残ります。

- `gitdir`、`submodule-config`、`ref-named-objects`、`submodule-named-objects` は `tool:760` で False。
- `ref-shaped-object`、`reflog-shaped-object` は `tool:763` で False。

したがって、**指定 M1 は負例6件のどれも KILL しません。** fix 前は単一 return が述語全体でしたが、fix 後の最終 return は末尾名前形だけです。

node はすべて `orchestrator/tests/test_dev_wave_cleanup.py::` 配下。以下は静的予測であり、変異 pytest 実測ではありません。

| 変異 | 期待失敗 node の完全集合 |
|---|---|
| M0 | `[]`、SURVIVED |
| **指定 M1：末尾だけ `return True`** | **`[]`、SURVIVED の予測。指定の6件と不一致** |
| M2 | `test_admin_shared_objects_are_removed`、`test_unpublished_admin_journal_reenters[linked]`、`test_cleanup_partial_admin_removal_reenters[None-gitdir]` |
| M3 | M2 と同じ3件 |
| M4 | `test_admin_read_link_race[registry]` |
| M5 | `test_admin_nonobject_hardlink_is_rejected[ref-shaped-object]`、`test_admin_nonobject_hardlink_is_rejected[reflog-shaped-object]` |

M2 は共有 object の preflight rc=20、M3 は撤去再読の rc=30／`phase=admin-remove`。M3 の recovery 2件は再入成功 assertion で赤になります。M4 は registry race の `DID NOT RAISE` です。

M5 では既存 `ref-named-objects` は `parts[-3]=='refs'` なので、除外節に関係なく False のままです。他の旧負例も構造条件で拒否、真の正例は変更前から除外節を通過し、race は述語を直接使いません。**M5 の追加赤化は新規2件だけ**という予測に整合します。

**修正指示：** M1 の `old` を `tool:759` からの述語本体全体へ広げ、`new` を `    return True` にしてください。製品コード・既存テスト期待値は変更不要です。この M1 なら負例6件を KILL する予測が成立します。anchor 一意性を再確認し、親 probe で完全集合を確定してください。

**段9への影響：** 現登録のままでは変異検証が期待不一致となり、registry 拒否の変異被覆を成立済みとして段9へ進めません。製品コードの撤去挙動への直接影響はありません。

## author 報告との一致

| 報告項目 | 判定 |
|---|---|
| (c) M5 で新規2件だけ赤化 | **一致。** `tool:763`、`test:1158,1162,1183` と静的に整合します。author の直接呼出し実測は本レビューでは再実行していません。 |
| (d) anchor 6件各1回 | **一致。** 独立した文字列計数でも各1回。ただし、一意性は M1 の意味・到達性を保証しません。 |
| (e) 縮小方向のみ | **一致。** `tool:760` は旧構造条件と同値、`tool:763` が追加制限、末尾 regex は不変です。 |

**判定：refuted — (c)〜(e) の報告が patch と食い違う。** F1 は、author が実走未確認と明記した M0〜M4 のうち、親指定 M1 の置換範囲に関する問題です。

**段9への影響：** 報告の訂正を実装修正の代わりに求める必要はありませんが、anchor 各1回を M1 の被覆成立と読み替えてはいけません。

## 総括

**(a) NO-GO。A1 の実装修正は妥当。残る阻害要因は M1 登録の置換範囲です。**

**(b) 所見ごとの状態**

| 所見 | closed／partial／regressed | real／refuted と理由 |
|---|---|---|
| A1 | **closed** | real の誤分類を修正。同形 ref／reflog を拒否し、指定の真の store を維持。 |
| A2 nit | **partial** | real の受理範囲制限は残存。既裁定どおりで退行なし、拡張不要。 |
| A5 | **closed** | 先行拒否・環境変数による迂回の懸念は refuted。旧4件と assertion を維持。 |
| A6 | **partial** | assertion 削除は refuted。real の live 未確認は段9まで残る。 |
| B nit | **regressed** | real。`return True` でも末尾だけの置換では恒真にならず、期待6件と再び不整合。 |

**(c) 残る must-fix：F1 の1件。** `tools/dev_wave_cleanup.py:759` の述語本体全体を対象に、親の M1 登録を修正してください。現指定の `:765` 2行だけでは不足します。既存テストの期待値変更・緩和は不要です。

**(d) nit：** 補助 store file と `refs`／`logs` を含む submodule 名の共有 file は rc=20 が残ること、object の ctime 履歴検出の限界、synthetic／焦点走と live／受入全走の区別を維持してください。

**(e) 裁定パッケージ候補：** 「A1 closed、製品コードは維持、M1 のみ述語全体の恒真化へ登録修正、M0／M2〜M5 は維持、親 probe 後に再判定」。追加 gate・除外集合の一般化・scope 外課題は提案しません。