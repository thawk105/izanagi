## 受理集合と I1

以下、`T` は `orchestrator/tests/test_s8b_oracle_driver.py`、`P` は `tools/t080_proto_equivalence_probe.py`。変異の判定は静的予測であり、実測 KILLED ではない。

**所見**：分割・順序交換による、裁定済み snapshot 固定以外の受理集合変更は見つからない。
**分類**：refuted
**根拠**：T:1422、1487、1504、1512 の各区間を旧版 `08d56628e` と文字列比較し、準備部分・submodule 部分・descriptor 追記・`add -A` から発行後 return までの一致を確認した。追加は `info` の受渡しと `tmp_path = root.parent`。
**影響**：同一 snapshot・key・Git 設定・commit metadata の条件では、tree／receipt を変える処理差は認められない。
**推奨**：修正不要。実 corpus の I1 実証は親の probe 結果で確定する。

**所見**：派生コピーが Git の初期状態を失う懸念、および単独走・既存境界負例が別経路になる懸念は棄却する。
**分類**：refuted
**根拠**：T:954 は `shutil.copytree(proto_root, root, symlinks=True)`。proto は submodule add 済みの index、未誕生の親 HEAD、submodule store を保持する。T:1018 は wrapper 呼出し、T:1413 は proto 直組み、T:2094 は従来名での境界検査。
**影響**：descriptor 更新後の `add -A` は旧 build と同じ staged `.gitmodules`／gitlink を出発点とし、単独走も key memo を維持する。
**推奨**：修正不要。index の stat 情報の違いは裁定 §3 の除外内。

## 新 test の実効性

**所見**：小型同値性 test は独立 reference と実 Git を用い、派生機構を実行している。
**分類**：refuted
**根拠**：T:1775–1812 は reference を直接構築し、対象の proto／finish／output copier を呼ばない。T:1817 は実 `bases.get`、T:1822–1843 は独立 descriptor bytes、output 集合、snapshot、write-tree、HEAD、相対 pointer、双方向変更独立性、proto 削除後の Git 動作を検査する。
**影響**：対象実装と reference の共通 stub による偽の同値判定はなく、裁定 §4-2(a) の比較項目を満たす。
**推奨**：修正不要。発行なしの test なので receipt 同値性の証明には数えない。

**所見**：小型 source は指定された主要枝を通すが、copier の全分岐を網羅するわけではない。
**分類**：nit
**根拠**：T:1730–1742 に tracked regular／実行 bit／深い path／tracked-but-ignored／tracked symlink／untracked regular／ignored／receipt がある。一方、untracked symlink、draft 除外、tracked regular の欠損・symlink への置換、未知 mode・不正列挙出力は作っていない。
**影響**：この test 単独では列挙・拒否処理の全分岐の退化を検出できないが、今回追加された派生コピーの同値性は検査できる。
**推奨**：「全枝網羅」とは記載しない。untracked symlink・draft・tracked 欠損は既存 T:2004 の visibility test が補うため、今回の追加は必須ではない。

**所見**：未完成公開・proto lock・公開後破損・finish 失敗の検査は、裁定された境界を観測している。
**分類**：refuted
**根拠**：T:1869–1899 は正常 return 前の Pipe 停止中と失敗後に marker 不在を親が確認する。T:1928 は `Path(fd.name) == proto_lock` と EX を識別する。T:1980 は破損例外、T:1994 は key marker 不在、T:1998–1999 は finish 再実行／proto 再利用を確認する。
**影響**：key lock 通知との混同、未完成 proto の公開、公開済み破損の黙殺、失敗した key の cache hit を許さない。
**推奨**：修正不要。finish 失敗は実 finish 内部の障害注入ではなく、copy 後の呼出し境界での例外注入であり、M7 の管理層検査として有効。

**所見**：小型 cache fixture の proto／finish 両層 stub 化で、従来の cache 検査が弱まった形跡はない。
**分類**：refuted
**根拠**：T:1112–1118 は分割後の二関数を stub 化するが、旧 fixture も build 全体を stub 化していた。独立性・marker・lock・key 分離・cleanup は実 `_T080SharedBases` を通り、実 builder の wraps test は別に残る。
**影響**：小型 test が保証する cache 管理の範囲は維持され、proto のコピー独立性・構築回数の検査が追加される。
**推奨**：修正不要。小型 cache test を production 発行の検証として扱わない。

## 変異帰属

実行順序による「最初の失敗 node」は静的には確定できない。以下は名指し killer と、その内部で先に失敗し得る箇所の判定。

**所見**：M1 は固定 path の選び方を確定する必要がある。
**分類**：nit
**根拠**：T:1783 の `expected_output` と T:1826 の完全一致は `output/tracked.txt` の欠落を捕捉する。一方、KNOWN_AXES／HOLDOUT は T:1453、1485–1486 の operational コピーで再配置される。
**影響**：後段で復元される path を落とす M1 は成果物を変えず SURVIVED となり、検出力不足との誤帰属を招く。
**推奨**：M1 を proto の output コピー直後の `output/tracked.txt` 欠落に固定する。この場合の killer は `test_t080_proto_derivation_matches_direct_small_source[False/True]`。復元対象を選ぶ変異は登録から外す。

**所見**：M2 は名指しの distinct case が捕捉する。
**分類**：refuted
**根拠**：T:1803 は入力 descriptor に固定 suffix を加えて期待 bytes を独立導出し、T:1822 で実体を比較する。対象追記は T:1504–1510。
**影響**：追記削除による distinct basis の消失を、既存 e2e の自己整合的期待値に依存せず検出する。
**推奨**：`test_t080_proto_derivation_matches_direct_small_source[True]` を killer とする。旧 T:1735 相当は数えない。

**所見**：M3 は名指しの小型同値性 test が捕捉する。
**分類**：refuted
**根拠**：T:954 の `.git` コピー除外は、finish の T:1512 の Git 操作で先に失敗し得る。そこを通っても T:1820 の `.git` directory と T:1821 の `--show-toplevel` が拒否する。
**影響**：独立 repo でない派生物が tree 比較だけを通過することはない。
**推奨**：同値性 test の両 parameter を killer とする。失敗位置が finish 内でも同 node の捕捉として記録する。

**所見**：M4 は絶対化する pointer の種類にかかわらず検出可能。
**分類**：refuted
**根拠**：T:1833 は `.git` の `gitdir:`、T:1835 は `core.worktree` の絶対 path を拒否し、T:1840–1842 は proto 削除後の動作を確認する。`.git` bytes の変更は T:1827 の snapshot が先に捕捉し得る。
**影響**：派生側が proto の Git store／working tree を参照し続ける退化を拒否する。
**推奨**：同値性 test を killer とする。pointer assertion 到達前の snapshot 失敗も区別して記録する。

**所見**：M5 は proto lock を識別した専用 test が捕捉する。
**分類**：refuted
**根拠**：T:1928–1932 は proto.lock に対する EX の非阻塞試行が失敗した場合だけ通知し、T:1952 は `"blocked-on-proto-lock"` を要求する。
**影響**：EX 削除時は必要な通知がなく、別 key の proto 構築を無保護にする退化が赤になる。
**推奨**：`test_t080_proto_waits_for_identified_lock_across_keys` を killer とする。

**所見**：M6 は正常 return 前の公開を親の観測で捕捉する。
**分類**：refuted
**根拠**：T:1870 で builder が Pipe 待ちしている間に T:1893 が `assert not marker.exists()` を実行する。
**影響**：管理層が builder 呼出し前・完了前に marker を公開する退化を、後続成功によって隠せない。
**推奨**：`test_t080_proto_incomplete_build_is_rebuilt[False]` を killer とする。`[True]` は pending-only 再構築の別検査。

**所見**：M7 は copy 後の finish 例外でも key marker を公開する退化を捕捉する。
**分類**：refuted
**根拠**：T:1991 で finish を例外化し、T:1994 で `*/complete.json` 不在、T:1995 で proto marker 存在を要求する。
**影響**：発行未完了の key を完成品として再利用する退化が赤になる。
**推奨**：`test_t080_shared_base_finish_failure_has_no_marker` を killer とする。

**所見**：M8 は非 output 部の実 symlink により捕捉する。
**分類**：refuted
**根拠**：T:1716 の submodule 内 `link` は実 Git に commit され、T:954 の `symlinks=True` 削除で regular file 化すると T:1827 の種類・mode 比較が不一致になる。
**影響**：output 列挙で除外される symlink だけを配置して変異が生き残る問題はない。
**推奨**：同値性 test を killer とする。小型 cache 独立性 test の T:1140 も補助 killer となる。

**所見**：M9 は distinct identity の欠落を捕捉する。
**分類**：refuted
**根拠**：T:1230 の distinct key に対し T:1238 は返却引数の完全一致、T:1239 は finish 5 回を要求する。identity は T:1006、942。
**影響**：default の document／base を distinct 要求へ返す cache 衝突が赤になる。
**推奨**：`test_t080_shared_base_keeps_all_four_key_fields_separate` を killer とする。

**所見**：M10 は最初の close による共有木削除を捕捉する。
**分類**：refuted
**根拠**：T:1250–1253 は first.close 後の parent と proto payload の存在、および rmtree 未呼出しを要求する。
**影響**：参加者が残る session の proto／base を消す退化が赤になる。
**推奨**：`test_t080_shared_base_only_last_participant_removes_tree` を killer とする。

**所見**：M11 は新 proto 入口を直接呼ぶ専用 test が捕捉する。
**分類**：refuted
**根拠**：T:1851–1853 は `_build_t080_e2e_proto(forbidden)` に対して `"temp root"` の AssertionError を要求する。T:1422 削除時は、未存在 parent 配下の mkdir で FileNotFoundError となり、この期待を満たさない。
**影響**：境界検査削除は赤になる。ただしこの node の変異時失敗は、実 output への書込み発生そのものの観測ではない。
**推奨**：`test_t080_proto_boundary_rejects_before_write` を killer とする。既存実 output 境界 test は追加 killer だが、変異実走では専用 node を優先する。

## wraps test の仕様相違

**所見**：wrapper 回数から finish／proto 回数への変更は、分割後の実経路に対応した変更である。
**分類**：refuted
**根拠**：T:1081、1084 は両方とも `wraps`、T:1096 は `((1, 1), (0, 0))`。同一 key の再構築・二重 finish・毎要求の proto 構築は回数差になる。
**影響**：同一 key の共有について、実 builder を余分に呼ぶ退化の検出力は維持される。
**推奨**：変更を認めてよい。ただし「異なる key ごとに proto 再構築」はこの単一 key test だけでは検出せず、T:1240 と T:1956 の専用検査が担う。

## probe の健全性

**所見**：旧 builder は旧 bytes で動き、現行 production import の共有は比較目的に合致する。
**分類**：refuted
**根拠**：P:90 は `git show <base>:<relative>`、P:97 は独立 module 辞書への `exec`、P:126 はその旧 builder 呼出し。P:95 の `__file__` により ROOT は同じ checkout を指す。
**影響**：同一現行 corpus／production 世代を入力として旧 fixture と新 fixture を比較でき、旧環境全体との差を混入させない。
**推奨**：修正不要。「旧 fixture の比較」であり「旧 production checkout の再現」ではないと記録する。

**所見**：basis metadata 固定と活性化 commit OID 除外の扱いは I1 と整合する。
**分類**：refuted
**根拠**：P:28–33 は両者の author／committer 名前・mail・日時を固定する。T:1539 の子側 sanitizer はそれを除去するが、receipt は T:1636 で確定し、活性化 commit は T:1657。P:44 は HEAD commit OID ではなく tree を比較する。
**影響**：basis OID は固定され、活性化時刻の差で正しい同値結果を誤って拒否しない。
**推奨**：修正不要。

**所見**：比較器単体は `None == None`／`{} == {}` を許すが、現行の通常実走で発行なし同士の偽 equal になる経路はない。
**分類**：refuted
**根拠**：P:119 は通常実走で `issue_receipt=True`。T:1645 の receipt add、T:1666 の active-valid assert、T:1689 の子成功確認を経由する。旧経路もこの区間と逐語一致する。
**影響**：receipt 未生成なら比較成功まで進めず、selftest の発行なし結果が通常実走の receipt 証明に混ざらない。
**推奨**：修正不要。将来の防御として通常実走時の receipt 存在・document 必須 field を明示 assert してもよいが、現状の must-fix ではない。

**所見**：selftest の 1 byte 負例は working-tree 比較の検出力を示す。
**分類**：refuted
**根拠**：P:143 は先頭 byte を XOR で必ず変更し、P:144 で snapshot を取り直して P:146 で比較器の `rc == 1` を要求する。
**影響**：working-tree bytes を無視する比較器は selftest を通過できない。
**推奨**：修正不要。ただし receipt bytes／document／OID 各比較欄の個別変異検証まで証明したとは扱わない。

## 既存 e2e の期待値

**所見**：既存 e2e 6 関数／11 node の本文と fixture 返却契約は維持されている。
**分類**：refuted
**根拠**：旧版との文字列比較で対象 6 関数すべての本文一致を確認した。T:1027 は従来どおり `root, root / migration.RECEIPT_REL, copy.deepcopy(document)`、T:1522 は未発行時 `{}`、T:1691 は発行時 document を返す。
**影響**：assert の文字列・件数の緩和や、receipt path／document の意味変更によって受理集合を広げていない。
**推奨**：修正不要。親が実走中の結果は本静的レビューの成功根拠には含めていない。

## 禁止事項

**所見**：指定差分と作業ツリーの変更範囲に、禁止された実装変更は認められない。
**分類**：refuted
**根拠**：差分は T と P のみ。read-only の Git 列挙でも tracked 変更は T、untracked は P、staged 変更は空。T:954 は通常 copytree、T:1527 は key ごとの runtime コピー、T:919–939 の EX lock は返却時に閉じる。
**影響**：production／conftest／docs の変更、whitelist 化、alternates／hardlink 導入、process proto memo、runtime snapshot、copy 中 shared lock、並列 copytree による新たな参照共有はない。
**推奨**：修正不要。probe は裁定どおり commit 対象から除外する。本レビューでは編集・git 状態変更・pytest 実行を行っていない。

## 総括

**must-fix は 0 件。** 静的点検では裁定 §3／§4 に反する成果物・受理集合・参照の変化を確認しなかった。

M1 は `output/tracked.txt` の欠落に固定すれば名指し killer が成立する。後段で再コピーされる operational path の欠落は、無効な変異として登録から外すべきである。M2〜M11 は上記の名指し node で赤になる見込み。

実 corpus の I1、変異の実測帰属、性能採否は親の実行結果で確定する。