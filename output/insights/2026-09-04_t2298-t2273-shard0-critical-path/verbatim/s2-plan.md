## 単位 A の plan (file:line)

以下、`T` は [test_p3_b4_raw_record_producer.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1178)、`C` は [conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/conftest.py:928)、`I` は [pytest.ini](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/pytest.ini:1) とする。行番号は変更前の現在値である。

- `T:3-14` に lock 負例用の `errno`、writer 閉包検査用の `ast` を追加する。
- `T:1178-1243` の fixture 本体を、次の三層へ分ける。

  1. `_certified_evidence_lock_scope(shared, *, access_mode, seed)`  
     `fixture.lock` の open、seed 排他、test 本体用 lock、unlock、close だけを所有する内部 context manager。
  2. `_certified_evidence_fixture_scope(tmp_path_factory, *, access_mode)`  
     現在の seed 構築、metadata 復元、`mock.patch.object` 群、`yield evidence` を所有する共通実装。
  3. `certified_evidence` と `certified_evidence_writer`  
     前者は共通実装へ `"read"`、後者は `"write"` を渡す薄い pytest fixture。

lock 順序は次に固定する。

1. 現行 `T:1182-1186` と同じ方法で shared root と `fixture.lock` を決め、fd を一度 open する。
2. `metadata_path.exists()` が偽の場合だけ `LOCK_EX` を取得する。
3. `LOCK_EX` 取得後にもう一度 `metadata_path.exists()` を検査する。まだ無い場合だけ、現行 `T:1191-1209` と同じ `_evidence_scope` 引数、metadata field、JSON encoding で seed を作る。
4. seed 区間の `LOCK_EX` を明示的に `LOCK_UN` する。
5. 同じ fd に、reader は `LOCK_SH`、writer は `LOCK_EX` を改めて取得する。
6. lock 取得後に metadata を読み、現行 `T:1211-1239` と同じ `_Evidence` 復元と patch を行う。`ExitStack` の巻き戻しまで lock 内に置く。
7. `finally` で test 本体用 lock を解放し、その後 fd を close する。seed 生成例外でも fd が閉じるよう、保持状態を boolean で管理する。

`LOCK_EX` から `LOCK_SH` への直接変換は採らない。Linux `flock` の mode 変換は原子的な downgrade ではなく、旧 lock の解除と新 lock の取得の間に競合相手が入れる。明示的な `LOCK_UN` と再取得にして、その非原子区間をコード上でも明らかにする。区間中は metadata を読まず、patch も test 本体も開始しないため、別 writer が先に取っても、こちらは最終 mode の取得完了まで待ち、破損した途中状態を観測しない。

`_evidence_scope` (`T:313-495`) と 17 consumer の assertion、期待値、受理集合は変更しない。

## 単位 B の分類表と選択

B2 の別 fixture を選ぶ。writer 宣言が関数引数として静的に見え、marker の文字列照合より閉包検査が簡単になる。また `I:1-14` には `--strict-markers` も marker 登録もないが、外部 CLI の strict 指定までは否定できない。B1 なら marker 登録が必要で、`pytest.ini` の「キー追加はゲート再裁定を要する」というコメントにも触れる。B2 なら `pytest.ini` は変更不要である。

M17/M18 だけ fixture 引数とその参照を `certified_evidence_writer` に変更する。assertion 文は変更しない。

| consumer、現在行 | shared evidence / admission への直接操作 | 非共有の変更 | mode |
|---|---|---|---|
| M01 `T:1305-1321` | 読み取りのみ | `tmp_path` の publication artifact を改変 | read |
| M02 `T:1324-1334` | 読み取りのみ | publication は `tmp_path` | read |
| M03 `T:1337-1353` | 読み取りのみ | publication は `tmp_path` | read |
| M04 `T:1356-1376` | 読み取りのみ | publication artifact 改変、`P` の process-local monkeypatch | read |
| M05 `T:1379-1407` | 読み取りのみ | `P` の process-local monkeypatch と観測 list | read |
| M06 `T:1410-1417` | 読み取りのみ | publication は `tmp_path` | read |
| M07 `T:1420-1427` | 読み取りのみ | publication は `tmp_path` | read |
| M08 `T:1430-1444` | 読み取りのみ | 同一 test 専用 publication への二回 publish、process-local monkeypatch | read |
| M10 正例 `T:1455-1463` | 読み取りのみ | publication は `tmp_path` | read |
| M12 `T:1503-1536` | 読み取りのみ | `tmp_path` の二 publication、process-local patch | read |
| M13 `T:1539-1545` | 読み取りのみ | publication は `tmp_path` | read |
| M16 `T:1588-1602` | 読み取りのみ | field ごとの `tmp_path` publication | read |
| M17 `T:1605-1630` | `on_receipt.write_bytes` で一時上書きし `finally` で復元 | `P._snapshot_regular` の process-local monkeypatch | write |
| M18 `T:1633-1662` | admission `role_file` を rename、symlink 化、unlink、復元 | `tmp_path` に receipt 向け symlink を作成 | write |
| assembly 再導出 `T:1665-1697` | 読み取りのみ | 三つの `tmp_path` publication artifact を改変 | read |
| driver 不一致 `T:1781-1788` | 読み取りのみ | publication は `tmp_path` | read |
| non-guarantees `T:1791-1800` | 読み取りのみ | publication は `tmp_path` | read |

`_publication` (`T:111-132`) は planned result を `root/results`、publication root を `root/publication` に置く。上表の全呼び出しで `root` は当該 test の `tmp_path` またはその子である。`_request` (`T:776-783`) は shared path を文字列として渡すだけ、`_publish` (`T:786-799`) は publication と request を `P.publish_b4_attempt_result` へ渡すだけ、`_assert_write` (`T:817-820`) は publication artifact を読むだけである。

したがって、対象 test ファイル自身に現れる shared path の直接 writer は M17/M18 の二本で、親の数はこの範囲では正しい。

## 単位 C の正例・負例 (file:line と DW-G05 の 1 行)

現在の `T:1245`、二つの fixture wrapper の直後かつ現在の `_build_full_publication_evidence` (`T:1246`) の前へ、次の小さい検査を追加する。いずれも共通 lock helper を直接使い、17 consumer を増やさない。競合 fd は必ず同じ lock file を別 `os.open` で開き、別 open-file description にする。

| 検査 | 実装形 | DW-G05 |
|---|---|---|
| `test_certified_evidence_lock_allows_two_readers` | metadata を事前作成し、内部 helper を `"read"` で保持中に、別 fd の `LOCK_SH | LOCK_NB` が成功することを確認 | 無いと旧 `LOCK_EX` のままでも受入機能は緑になり、D1620 の最遅 shard wall だけが退行したまま残る。 |
| `test_certified_evidence_seeded_reader_never_requests_exclusive` | seed 済み shared root で `fcntl.flock` を wraps して operation を記録し、`LOCK_SH` と最後の `LOCK_UN` はあり、`LOCK_EX` は一度も無いと確認 | 無いと短時間の隠れた排他取得が混入し、consumer 増加時に受入 wall が再び直列鎖へ戻る。 |
| `test_certified_evidence_reader_blocks_nonblocking_writer` | helper の reader 保持中に別 fd の `LOCK_EX | LOCK_NB` を実行し、`OSError.errno == errno.EWOULDBLOCK` を確認 | 無いと reader が無 lock でも緑になり、M17/M18 の一時変異を reader が読み、certified 選択と受入結果が順序依存になる。 |
| `test_certified_evidence_writer_blocks_nonblocking_reader` | helper の writer 保持中に別 fd の `LOCK_SH | LOCK_NB` が `EWOULDBLOCK` になることを確認 | 無いと writer が `LOCK_SH` でも緑になり、一時的な壊れた receipt または role symlink を reader が観測できる。 |
| `test_certified_evidence_seed_double_check_observes_competing_seed` | 初回 exists は偽にし、`LOCK_EX` 取得を委譲した wrapper 内で競合者相当の metadata を作る。seed callback が呼ばれず、operation 列が `EX, UN, SH` で始まることを確認 | 無いと二 worker が seed を二重生成し、metadata と evidence/admission の対応が割れて certified 選択や受入の緑が非決定的になる。 |
| `test_certified_evidence_writer_fixture_closure_matches_shared_mutations` | `ast.parse(Path(__file__).read_text())` で fixture wrapper の mode、17 consumer の fixture 引数、shared-path mutator を検査 | 無いと M17/M18 の writer fixture を reader fixture へ戻しても単体では緑になり、受入全走だけが競合する。 |

閉包検査には次を含める。

- 期待 map は上表の 17 function 名と read/write mode を完全列挙する。
- `certified_evidence` と `certified_evidence_writer` の wrapper が、それぞれ共通実装へ `"read"` と `"write"` を渡すことを AST で固定する。
- fixture 引数が二種類のどちらかである test の集合と mode が期待 map に完全一致することを確認する。
- fixture 引数を起点に、属性参照、`Path(...)`、`with_name` で導出された path だけを taint する。`_publish` の返値は taint しない。
- tainted receiver に対する `write_bytes`、`write_text`、`rename`、`replace`、`unlink`、`symlink_to`、`hardlink_to`、`mkdir`、`rmdir`、`touch`、`chmod` を shared mutation と数え、その function 集合が M17/M18 と一致することを確認する。
- M18 の `tmp_path` 側 `link.symlink_to(shared_receipt)` は receiver が tainted でないため writer 判定理由にはしない。M18 は admission `role_file` の操作で writer になる。

これで M17/M18 から writer 宣言だけを外すと、宣言 map と taint 由来 writer 集合の不一致で必ず赤になる。任意 helper の内部に隠した将来の mutation まで完全に証明するものではないが、現在の二 writer の宣言抜けを殺す最小閉包は示せる。

## 単位 D の変異事前登録案

| 変異 | 変異位置 | 殺す検査 |
|---|---|---|
| (a) write mode を `LOCK_SH` にする | 新しい `_certified_evidence_lock_scope` の mode map、現在 `T:1178-1243` の置換部 | `test_certified_evidence_writer_blocks_nonblocking_reader` |
| (a-2) writer wrapper が `"read"` を渡す | 新しい `certified_evidence_writer` wrapper、現在 `T:1178-1243` の置換部 | writer 閉包検査の wrapper-mode assertion |
| (b) reader が test 本体 lock を取らない | 新しい helper の seed 後 `flock`、現在 `T:1188-1240` 相当 | `test_certified_evidence_reader_blocks_nonblocking_writer` |
| (c) M17 の writer fixture 宣言を外す | `T:1605-1630` | writer 閉包検査 |
| (c) M18 の writer fixture 宣言を外す | `T:1633-1662` | writer 閉包検査 |
| (d) EX 取得後の二度目の `metadata_path.exists()` を外す | 新しい seed 排他部、現在 `T:1189-1209` 相当 | `test_certified_evidence_seed_double_check_observes_competing_seed` |
| (e) reader を `LOCK_EX` のままにする | 新しい mode map、または seed EX を `yield` まで保持する箇所 | `test_certified_evidence_lock_allows_two_readers` と seeded-reader の no-EX 検査 |
| EX から SH へ直接変換して明示 unlock を消す | 新しい seed 後の遷移 | double-check 検査の `EX, UN, SH` operation 列 |

## 単位 E の P1 点検

(i) `real_repo_fixture_lock` を流用する利点は、期限付き retry、regular-file、owner、permission 検査、fork 後 fd reset、同一 process 内の mode refcount といった既存の防護を使えることだけである (`C:1110-1301`)。しかし lock identity 自体が b4 evidence に合わないため、現状の API をそのまま使う利点ではない。

(ii) 既存 resource は `("parent", "ccbench")` のみ (`C:923-929`) で、root は repository root または `external/ccbench` (`C:979-989`)、lock key は Git common-dir (`C:992-1075`) である。b4 evidence は pytest shared tmp の inode 資源であり、どちらでもない。

`parent` を代用すれば、b4 writer が全 real-repo parent reader/writer を止め、real-repo writer も全 b4 reader を止める。これは余計な直列化だけでなく、別資源を同一排他領域と誤表現する。`ccbench` 代用も同じ問題を持つ。親の provisional 裁定どおり、自前 `fixture.lock` を残すべきである。

(iii) 新しい resource 名の追加は一行では済まない。少なくとも次が変更対象になる。

- resource inventory `C:928`
- Git repository に固定された root 解決 `C:979-989`
- Git common-dir に固定された key 作成 `C:992-1075`
- `parent` / `ccbench` を直書きした取得順 `C:1347-1359`
- 二資源だけを受ける fixture context `C:1363-1375`
- これらへ access を供給する collection inventory 側

さらに `conftest.py` は T-2297 所有で、本依頼では変更禁止である。T-2298 で一般化する変更面ではない。

## 単位 F の競合点検

- `_publication` (`T:111-132`) の全出力は test 固有 `tmp_path` 配下である。`_publish` (`T:786-799`) と `_assert_write` (`T:817-820`) 自身には evidence path への書き込みがない。
- M01、M04、assembly test が改変する `write.artifact_path` も test 固有 publication 配下であり、shared seed ではない。
- M05、M08、M12、M17 の `mock.patch.object(P, ...)`、fixture の `mock.patch.object(C/L, ...)` (`T:1234-1239`) は worker process 内の Python object だけを変える。xdist worker 間では process を共有せず、同一 worker は test を同時実行しないため、別 worker の module state は変えない。
- M17 は shared `on_receipt` を変えるので write。M18 の `tmp_path` symlink は非共有だが、admission `role_file` の rename と symlink 化は shared なので write。
- writer の復元は両方 `finally` にある。ただし worker が SIGKILL された場合の復元不能は現行から残る既知限界で、read/write lock 化では解消しない。

重要な未証明点がある。射影には `p3_b4_raw_record_producer.py` 本体が含まれないため、`P.publish_b4_attempt_result` が request の campaign root 配下で WAL、receipt、execution lock file を作成または更新しないことは、この一次資料だけでは証明できない。特に非共有 test の `T:1558-1560` は `P._execution_lock_for_root` の存在を示しており、callee の open mode や `O_CREAT` は対象 test ファイルからは分からない。author は実装前に callee の exact write surface を確認すべきであり、書き込みがあれば次のどちらかが必要になる。

- 純粋な coordination lock file の初回作成だけなら seed EX 区間で事前作成し、reader 中の path/bytes 変更をなくす。
- WAL、receipt、その他意味データへの変更なら、その consumer も writer に再分類する。

session 間共有については、現行 `T:1182-1185` は xdist の `popen-gwN` だけを一段上げ、pytest session 固有 basetemp の外へは出ない。`I:1-14` に固定 `--basetemp` はないため、pytest の通常の別 session は別 root になる。ただし canonical CLI が同じ `--basetemp` を複数 shard へ明示するかは射影資料から確認できない。

K=3 の三 shard が同一ホストへ同居できるかも、この射影だけでは確定できない。同居しても basetemp が別なら共有しない。同じ basetemp を再利用する場合は shared reader が session をまたぐため危険が増えるが、writer は同じ `fixture.lock` の `LOCK_EX` で排他される。より重大なのは、一方の session が basetemp を清掃して lock file を再作成し、同じ path に別 inode の lock が生じる場合である。親の実測時に各 shard の `getbasetemp()` と `fixture.lock` の device/inode を記録すれば、この前提を確認できる。

## 親 brief への指摘

- 「consumer は `T:1300-1680`」という行範囲は不足している。17 本に数えるには `T:1781-1788` と `T:1791-1800` も含める必要がある。
- 親の「M17/M18 の二 writer」は、対象 test ファイルに直接書かれた path mutation の分類としては正しい。ただし `P.publish_b4_attempt_result` の callee-side write surface が射影されていないため、「全共有 mutation の閉包」としては未証明である。
- handoff の当日丸め値を17 consumerだけ合計すると約 84.5 秒で、「約82秒」は小さくずれている。設計判断には影響しない。
- P1 の元 carry にある `real_repo_fixture_lock` 流用は資源 identity が誤っている。親の provisional 裁定「fixture 自前 lock を維持」が妥当である。
- `fixture.lock` の mode 改訂だけでは、別 pytest session が同一 basetemp を共有しないという前提までは保証しない。canonical runner の basetemp 実値を親の実測証拠へ含めるべきである。

## 総括

実装は B2 とし、`T:1178-1243` を共通 lock helper、共通 evidence scope、reader/writer 二 fixture に分ける。seed は不在時だけ `LOCK_EX` と double-check、seed 後は明示 unlock/relock、test 本体中は reader `LOCK_SH`、M17/M18 だけ `LOCK_EX` とする。

正負例、double-check 競合、writer 閉包 AST により指定された五変異をすべて殺せる。`pytest.ini` と `conftest.py` は変更しない。read-only sandbox のため pytest は実走しておらず、緑は主張しない。唯一、producer 本体の共有 path 書き込み有無は資料不足で未証明なので、author の実装前確認事項として残る。