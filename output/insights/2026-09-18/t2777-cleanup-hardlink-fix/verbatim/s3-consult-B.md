## 判定と読解範囲

指定資料はすべて読めた。静的検査のみで、編集・pytest・変異実行は行っていない。以下、`plan` は `codex/s2-plan.md`、`brief` は `s1-brief.md`、`tool` は `tools/dev_wave_cleanup.py`、`test` は `orchestrator/tests/test_dev_wave_cleanup.py` を指す。

レンズ B の範囲では、**提案された実装経路に must-fix の欠陥は確認できない**。M1/M3/M4 の到達性は成立する。ただし、部分撤去 recovery の被覆、`stable()` の保証説明、harness 契約には以下の留保がある。

## 1. stable() の除外と残る保証

**判定：refuted — hardlink 追加を許容するための nlink/ctime 除外自体は妥当。**

POSIX の hardlink 追加は同一 inode の link count と ctime を更新する。bytes が変わらなくても現行の比較は拒否する（`tool:755–766`）。plan の object 限定除外は、この偽拒否を除く設計になっている。

ただし、「同一 inode なので同 size・同 mtime の bytes 差し替えは不可能」は誤りである。inode を維持した上書きは可能で、mtime も復元できる。除外後に見逃し得るものは次のとおり。

- link/unlink による nlink/ctime だけの変化。最終 nlink が元に戻る場合も含む。
- 同 size の上書きと mtime 復元。読取中に起きれば、ctime による検出を失う。
- mode を変更して元に戻すなど、比較時には元の値に戻り、ctime だけに履歴が残る操作。
- bytes を変更して戻す一時的な書換え。読取結果が一時状態や混合状態になる可能性は、inode の一致だけでは排除できない。

継続して残る bytes 差は、snapshot と再読の length/sha256 比較で通常は拒否される（`tool:772–775,913–920,971–973`）。しかし、この比較は読取区間の原子性や、読取後から unlink まで不変だったことを証明しない。`plan:106` の「既存の同一性モデルを維持するには十分」は、**ctime による変更履歴の検出能力は弱まる**ことを明記すべきである。

**段9への影響：** 純粋な共有 link 操作による rc=20/30 を回避する一方、上記の一時書換えでは従来の拒否が通過に変わり得る。ただし unlink 対象は自 wave の entry のままで、他 alias の bytes を cleanup が書き換える経路は増えない（`tool:973`、D2119 項8）。

**判定：nit — mtime 維持の説明不足。**

mtime は通常の bytes 更新の検出に役立つため、残す理由は成立する。一方、「Git object は作成後に mtime が変わらない」という前提は採れない。今回の射影資料から Git の全 object 処理を確認できず、実際の更新経路・発生頻度は**不確実・未実測**である。

**段9への影響：** 読取中に mtime が変われば、bytes 不変でも引き続き rc=20/30 になり得る。今回の修正が除くのは全 metadata race ではない。

## 2. prefix と部分撤去 recovery

**判定：refuted — root entry が欠けることで prefix がずれる経路はない。**

`_admin_snapshot` は `prefix + name + "/"` で再帰する（`tool:795`）。plan の撤去再帰も同じ規約で、root 呼出しは空文字である（`plan:66–83`）。

recovery では journal の階層を保持した snapshot を受け取り（`tool:837,855–856`）、現在の階層との部分集合照合を行う（`tool:931,941–942`）。`_recheck_admin` が返すのは保存済み全体ではなく **current**（`tool:953`）であり、これを撤去へ渡す（`tool:1299–1301`）。兄弟 entry の欠落は残存 entry の相対パスを変えない。

`tool:931` と `tool:951` はともに `_admin_snapshot(admin.admin_fd)`。同じ空 prefix から `795` の再帰と、変更後の `798` の述語を通る。`1025` の残存再検査も同様である。

**段9への影響：** 提案どおりなら、部分撤去後も残った object の共有許容が維持され、prefix 起因の rc=20/30 は生じないという静的判断。未実測。

**判定：real、ただし nit — linked fixture は部分撤去後の再入を被覆しない。**

`plan:203–211` が拡張する `linked` は、journal 公開の temporary unlink で中断する（`test:1249–1253`）。これは `tool:1011` 内であり、admin entry 撤去の `1027` より前である。したがって recovery 分岐は被覆するが、**root entry が既に消えた状態との組合せ**は被覆しない。

既存の `test_cleanup_partial_admin_removal_reenters` は実 unlink 後に中断する（`test:1095–1151`）。必要なら既存の `removed="gitdir", tamper=None` ケースだけへ shared-object helper と alias 確認を加えれば、node・repo 数を増やさず補える。

**段9への影響：** 現案の誤動作は示せないため nit。ただし、この組合せの回帰による再入 rc=20/30 を `linked` の緑だけでは否定できない。

## 3. M1 の到達性

**判定：refuted — plan の到達性修正は正しい。brief P6 の元の説明は不正確。**

通常 preflight は resolver を `tool:1183` で呼び、`1185` の `_bind_admin` より先に `631` の既定拒否で `gitdir` hardlink を拒否する。M1 は path 述語だけを恒真にするため、**負例 A の CLI だけでは殺せない**。

plan の snapshot 直接 assertion は成立する。通常 fixture の root `gitdir` が nlink=2 でも、M1 なら `allow_shared_object=True` となり、`_admin_snapshot` は当該理由で例外を出さない。`pytest.raises` が `DID NOT RAISE` で赤になる（`plan:177–193,283`）。

負例 B の `modules/sub/config` は resolver の読取対象ではない。M1 で snapshot と撤去再読の両方が許容され、他条件が fixture どおりなら CLI は rc=0 となり、期待20と不一致になる。occupancy stub の指定もある。

**段9への影響：** M1 相当の誤実装は modules 非 object の hardlink を受理して撤去する。plan の A直接検証＋B CLI はその退行を検出できる設計。未実測。

## 4. M3 の rc・部分撤去・赤理由

**判定：refuted — rc=30、phase=admin-remove の推論は正しい。**

M3 では snapshot が通り、撤去側の再読だけが `tool:756–757` で拒否する。呼出しは `1300–1301` の `phase="admin-remove"` 内で、`1322–1323` から `_partial`（`126–127`、rc=30）に変換される。

その時点では次の状態になる。

- wave directory は既に撤去済み（`tool:1289–1294`）。
- journal は公開・確認済み（`1011–1014`）。
- snapshot は名前順（`781`）。通常 fixture では `HEAD`、`commondir`、`gitdir` 等が `modules` より先に削除され、admin は部分撤去状態になる（`957–974`）。
- branch 削除の `1313` には到達しない。
- object の外部 alias は残る。

正例の rc==0 確認だけでも KILL になる。通常正例と recovery 再入の共通原因は「撤去側が共有 object の再読を拒否」であり、DW-M01 の単一理由性に沿う設計である。ただし、rc assertion だけでは phase と原因までは証明しないため、親の変異実測で stderr を確認する必要がある（`plan:321`）。

**段9への影響：** M3 なら rc=30、journal と部分 admin と branch が残る。他 wave の admin や外部 alias は撤去されない。未実測。

## 5. M4 と fstat wrapper

**判定：refuted — fixture は成立する設計。ただし wrapper の具体化が必要。**

`tool:11` は `import os` なので、`monkeypatch.setattr(cleanup.os, "fstat", wrapper)` は test 側の `os.fstat` にも作用する。安全な形は次である。

1. patch 前に元の `fstat` と対象の `(st_dev, st_ino)` を保存する。
2. wrapper は必ず保存した関数から stat を取得する。
3. inode pair が一致し、未注入の場合だけ、フラグを先に立てて `os.link` する。
4. link 前に取得した stat を返す。後続は保存した関数の実値を返す。
5. patch の有効範囲を直接読取呼出しに限定する。

`os.fstat` を wrapper 内から名前で再呼出しすると無限再帰になる。inode 番号だけの照合より dev/ino pair が適切である。

初回 `tool:755` には nlink=1 が返り、入口を通る。その後 `764` には nlink=2 が返るため、registry は `admin entry changed while reading` になる。M4 の `if True:` では nlink/ctime を比較せず、bytes・size・mtime が不変なら例外が消え、`pytest.raises` が赤になる。object 正例は元から通る。

`_read_admin_file` は今回の編集対象なので、この直接試験を「no-touch 関数を monkeypatch している」とする指摘は refuted。DW-O14 の逐語自体は射影にないため、規則全体の適合までは断定しない。

**段9への影響：** M4 相当なら registry の読取中 hardlink 化を見逃す。この test はその拒否保証の退行を単独で検出する設計。未実測。

## 6. M0・anchor・harness

**判定：refuted — M0 は意味上の等価変異。**

外側の括弧追加は演算順序・受理集合を変えず、通常の Python コンパイルでは実行命令も変えない。ただし位置情報まで含めた code object 全体の同一性を意味するものではない（`plan:254–264`）。

**判定：nit、未確認 — expected_nodes=[] の harness 適合。**

plan は `tools/mutation_harness.py:544–577` を根拠とするが、この file は本段の指定読解対象に含まれない。したがって、SURVIVED と空配列の組合せが実際の schema・判定処理に適合するかは独立確認できていない。

**段9への影響：** M0 自体に挙動変化はない。契約不適合なら変異検証が成立しないが、撤去結果への直接影響はない。

**判定：refuted — 提示 diff 上では anchor は各1箇所になる設計。**

- M0/M1/M2：新 helper の return 文1箇所。
- M3：`raw = _read_admin_file(` を含む2行。snapshot 側は `_admin_content(...)` 内なので一致しない。
- M4：`def stable(st):` と直後の条件の2行で1箇所。

根拠は `plan:17–23,55–60,72–77,259–329`。ただし実装後 source は未作成なので、最終出現数は未確認。

**段9への影響：** anchor 不一致は変異適用の失敗であり、撤去コードの退行検出が未成立になる。直接の撤去影響はない。

## 7. 所要と親 brief の食い違い

**判定：nit — 時間は概算のみ。**

`_make_repo` の標準呼出しは Git subprocess 10回（`test:66–84`）。3 repo 追加で setup は30回増え、別途 CLI 3回と結果確認が増える。race 2件は Git 不要。node 数は提示 baseline 143から148になる。

13秒÷143の平均を単純適用すると、repo 使用3件で約0.27秒だが、各 node の重さが不均一なので予測精度は低い。計画上は**約0.3〜2秒増、合計13〜15秒程度**を粗い目安とし、親の計時で置き換えるのが妥当。保証値ではなく未実測。

**段9への影響：** 時間見積自体は rc・撤去範囲を変えない。実測を省く根拠にはできない。

**親 brief の判定：**

- **P2：real、nit。** 「5箇所」は誤り。`tool:631,831,832,880,1013,1034` の6呼出しで、plan が正しい。列挙対象は一致するため直接の挙動差はない。
- **P6：real、plan で解消。** A の CLI だけでは M1 を殺せない。snapshot 直接 assertion を残すこと。放置すると root registry の述語退行をその負例では検出できない。
- **P3：real、説明上の不足。** `brief:9,13` は静的受理形と読取中の変化を分ける必要がある。`plan:374` は改善だが、ctime 除外は「link 操作に伴う変化」だけを識別して許すわけではない。段9への影響は節1のとおり。
- **DW-O13：real、nit。** `brief:10` の115/31件、nlink各値は本 wave の観測として扱う。同一 inode の時系列、全 registry、全入れ子 submoduleへの一般化は導けない。`plan:94` の「共有と変動を裏付ける」は「共有を裏付ける」に修正する。
- **全数 rc=20：real、plan で解消。** `brief:5` は F1026・insight §1.3 の条件付き説明と食い違う。「hardlink が残り、通常 snapshot に到達する場合」に限定する。段9の各実行結果は DW-O28 に従って個別記録する。

## 総括

**(a) must-fix（real）一覧**

レンズ B で、提案実装を止める must-fix は確認できない。実装・変異・撤去成功はいずれも未実測。部分撤去 recovery の被覆不足と保証説明の過大さは、現案の誤撤去を示せないため nit とした。

**(b) refuted の一覧と理由**

- prefix が部分撤去でずれる：残存階層から再構成するため成立しない。
- M1 が殺せない：A の snapshot 直接検証と B の CLI で到達する。
- M3 が rc=20になる：撤去再読の例外なので rc=30、`phase=admin-remove`。
- M4 の race が入口拒否になる：保存した初回 stat は nlink=1なので入口を通る。
- M0 が受理集合を変える：括弧追加のみで意味は不変。
- 提示 anchor が重複する：計画どおりの source では各1箇所になる設計。

**(c) 裁定パッケージ候補**

なし。任意の同時書換えに対する完全な原子性や、全 Git object 処理の mtime 挙動を保証する仕組みは本題外であり、追加 gate・検査は提案しない。

**(d) plan v2 への具体的な修正指示**

- `plan:94,106,374`：nlink の時系列は未確認とし、ctime 除外で失う変更履歴検出と、残る hash 照合を分けて書く。mtime 不変は保証しない。
- `plan:203–211`：`linked` は「admin 削除前の recovery」と明記。部分撤去も検証するなら `test:1097` の既存 `removed="gitdir", tamper=None` だけに helper を追加する。
- `plan:222–228`：保存した fstat、dev/ino 照合、先行フラグ設定、patch 範囲を明記する。
- `plan:321`：M3 の実測では rc=30 と `phase=admin-remove`、単一原因の stderr を確認する。
- `plan:238–264`：harness の空 `expected_nodes` 契約と、実装後 anchor の各1回出現は親の確認事項として残す。
- `brief:5,10,12,16`：条件付き rc、観測範囲、6呼出し、M1 の直接 assertion を plan と揃える。