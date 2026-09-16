## 並行時の実態

**所見**：異なる key の初回要求は proto 構築まで直列化され、その後のコピー・finish は並行する。
**分類**：nit
**根拠**：`orchestrator/tests/test_s8b_oracle_driver.py:923`「`fcntl.flock(lock, fcntl.LOCK_EX)`」、`:952`「`proto_root, info = self._get_proto()`」、`:954`「`shutil.copytree(proto_root, root, symlinks=True)`」。コピーは proto lock 解放後。
**影響**：5 key 同時開始では実 repo 取得が5回から1回になる一方、全 key が最初の取得完了を待ち、各 key に約3秒の派生コピーが加わる。
**推奨**：実 repo 複製を R、proto 側 Git を Gp、finish 側 Git を Gf とすると、発行あり key の旧経路は `Rk+Gp+Gf+53秒`、新経路は `Rproto+Gp+3+Gf+53秒`。R=38〜53秒、Gp+Gf≈9.5秒を機械的に当てると旧100.5〜115.5秒、新103.5〜118.5秒。その他処理・競合を除くモデルであり、wall 改善を保証しない。コピー部分の延べ処理量削減は `ΣRk−Rproto−15秒`、同じRなら137〜197秒だが、待機込み worker durations の削減とは異なる。

**所見**：同一 key の待機は finish 完了まで続くが、別 key の finish を塞がず、確認した取得順序に循環はない。
**分類**：refuted
**根拠**：`orchestrator/tests/test_s8b_oracle_driver.py:944` の key lock 内で proto を取得し、`:955` の finish、`:964` の「`pending.replace(marker)`」まで保持する。`:919` の `_get_proto` は key lock を取得しない。
**影響**：default key の6 node は1本の構築完了を待つが、他 key は proto 公開後に独立してコピー・発行できる。
**推奨**：変更不要。48 worker が参加しても、実際の構築本数は要求された key 数に依存する。完成済み同一 key の取得も短時間だけ key lock を通り、その後の各 test 用コピーは並行する。

**所見**：通常の xdist 待機や `-p no:cacheprovider` が、この flock 待ちを timeout にする根拠はない。
**分類**：refuted
**根拠**：`orchestrator/tests/test_s8b_oracle_driver.py:923` は期限なし flock。インストール済み `xdist/dsession.py:154` の「`queue.get(timeout=2.0)`」は `:156`「`except Empty: continue`」で再待機する。共有 marker は pytest cache を使用しない。
**影響**：長い proto 構築は待機 node の所要を増やすが、確認した xdist 自体は無通信2秒を worker 障害と扱わない。
**推奨**：変更不要。外側のジョブ期限は別物として扱う。今回の環境では `pytest_timeout` は見つからず、pytest.ini に timeout 設定もない。

## 失敗と cleanup

**所見**：「proto 構築失敗で待機 worker 全員が同じ例外により赤になる」は現物と異なる。
**分類**：refuted
**根拠**：`orchestrator/tests/test_s8b_oracle_driver.py:924`「`if not marker.is_file():`」から残骸削除・再構築し、`:928` の builder 成功後だけ marker を公開する。`:1900` の負例も失敗後の再要求成功を検査する。
**影響**：最初に失敗した consumer node は元の例外で FAILED となり、次の待機 node は再構築する。一過性障害なら後続は通り、持続障害なら要求ごとの再試行が proto lock 上で直列化され、旧方式より失敗完了 wall が延びうる。
**推奨**：説明を訂正する。これは裁定の「marker 不在→再構築」に一致するため変更不要。例外は失敗箇所に応じた `CalledProcessError`、`OSError`、`AssertionError` 等であり、共有の失敗例外ではない。公開済み JSON 破損は `JSONDecodeError`、root 欠損は `FileNotFoundError` が後続要求へ伝播する。

**所見**：通常終了・異常終了の cleanup 構造は旧方式のままで、追加 proto も session parent と一緒に削除される。
**分類**：refuted
**根拠**：`orchestrator/tests/test_s8b_oracle_driver.py:905` の `close()` は lifetime SH を解放し、EX|NB を取得できた退出者が `:915`「`_t080_remove_tree(self.parent)`」を実行する。`:981` は「`atexit.register(bases.close)`」。
**影響**：通常終了では最終退出者が proto を含めて削除する。SIGTERM 等で最後の所有 process が atexit を実行せず終了すると残骸が残り、その追加量は proto 1本分になる。
**推奨**：変更不要。atexit は逆登録順だが、proto 専用 callback は追加されていない。異常終了 worker の fd が閉じても、後に正常退出する参加者がいれば削除可能。全員異常終了・最後の参加者の異常終了による残留は既存経路と同じ。

**所見**：単独走の cleanup 登録は wrapper 化後も維持されている。
**分類**：refuted
**根拠**：`orchestrator/tests/test_s8b_oracle_driver.py:1017`「`atexit.register(_t080_remove_tree, base_parent)`」は builder 呼出し前に実行され、`:1413` の wrapper は同じ parent に proto を直組みする。
**影響**：単独走では独立した共有 proto を追加せず、構築途中の失敗も従来の base_parent 削除対象になる。
**推奨**：変更不要。

## 容量

**所見**：通常成功時の増分は session 当たり proto 1本であり、worker 数倍にはならない。
**分類**：nit
**根拠**：`orchestrator/tests/test_s8b_oracle_driver.py:920`「`self.parent / "proto"`」、`:954` の key 派生コピー。既存の key base と test 用コピーは引き続き存在する。
**影響**：提示値では約681 MB＋submodule checkout・Git store・その他 basis files、inode は約23k＋Git objects等が追加される。129 GB空きに対し既知部分だけなら約0.53%。
**推奨**：増分は「proto 1本」と記録する。proto は superproject の `git add -A` 前なので、発行済み base と同量の superproject objects が増えるわけではない。独立した実 builder 検査が同時に動けば、その private parent にも別の proto が存在するが、新規小型 test は実 corpus を複製しない。

## 新 test の実行費用

**所見**：追加数は `test_t080_proto_*` が5 function／8 node、finish 失敗検査を含め6 function／9 node。正常経路に長時間待機はない。
**分類**：nit
**根拠**：`orchestrator/tests/test_s8b_oracle_driver.py:1765`、`:1856`、`:1969` が各2値 parametrization。`:1891`、`:1951` の「`receive.poll(30)`」は到着時に戻る上限であり、30秒の固定待機ではない。
**影響**：実 Git を多く起動する同値性2 node が追加費用の中心で、他7 node は小型コピー・fork/Pipe・例外検査。静的には222秒級の node を追加する処理構造は見当たらないが、134秒の全体報告から個別所要や5分以内を証明できない。
**推奨**：正常時の粗い見積りは同値性が各数秒級、残りは各1秒未満〜数秒級。ただし実行環境依存であり実測値ではない。親の既定 post 実走で9 node の durations と終了時刻を確認すればよく、追加 gate は不要。

**所見**：所要台帳の未登録は許容され、shard 配置と shard 内実行順では既定値が異なる。
**分類**：refuted
**根拠**：`tools/acceptance_shards.py:404`「`1.0 if duration is None`」。一方 `orchestrator/tests/conftest.py:1756` は既知 work unit の上位96番目相当を unknown cost に使う。台帳に今回の新規 node はない。
**影響**：shard 配置上は計9秒の重みが加算されるが、実行順で各 node が必ず「1秒扱い・末尾配置」になるわけではない。
**推奨**：登録は実行・collection の必須条件ではなく、今回の must-fix としない。個別実測なしに134秒を配賦した値を登録しない。

## 受入 shard 割当てと collection

**所見**：file 単位の閉包は変わらないが、全体の shard 割当てまで完全不変とは言えない。
**分類**：nit
**根拠**：`tools/acceptance_shards.py:339`「`union.find(f"f:{record.file}")`」、`:483` の file-shard 一意性検査。`:442` 以降は load 最小の bin へ残り成分を配る。
**影響**：新9 node は既存 oracle-driver file と同じ shard に入り、既存 group 接続は増えない。ただしその bin の重みが9秒増えるため、他 file の後続LPT配置が変わる可能性がある。
**推奨**：既存の配置成果物で pre/post の component 配置も比較する。「同じ file に追加したので全 shard 配置不変」とは記録しない。

**所見**：新 test の private bases と module 直下の共有 parent は lifetime lock を共有しない。AST consumer 検査にも追加されない。
**分類**：refuted
**根拠**：`orchestrator/tests/test_s8b_oracle_driver.py:901`「`self.parent / "workers.lock"`」、`:979` の session 固有 parent、`:1814` の「`_T080SharedBases(tmp_path / "bases")`」。AST は `:1369` で関数名 `_t080_stub_free_e2e_repo` の直接呼出しだけを照合する。
**影響**：private `bases.close()` はその parent だけを削除し、module 共有 parent の最終退出者判定を変更しない。新 test の `bases.get()`・proto builder 呼出しは既存6 function／11 node の集合に入らない。
**推奨**：変更不要。collection 時には既存どおり lifetime 参加だけが起き、proto 構築は最初の `get()` まで遅延する。新 test に real-repo access map の追加もない。

## probe の運用

**所見**：指定された独立 CLI 実行では、fixture の書込み先は一時 tree に閉じる。ただし結果 JSON の出力先は別途指定に依存する。
**分類**：nit
**根拠**：`tools/t080_proto_equivalence_probe.py:109`、`:130` は「`_assert_t080_temp_root_outside_real_output`」を通す。`orchestrator/tests/test_s8b_oracle_driver.py:59` は import 時に ambient temp を検査する。一方 probe `:195` は「`args.output.write_text(...)`」で、`:165` は絶対パスだけを要求する。
**影響**：builder は実 repo の output を生成先にしないが、誤って `--output` に実 output 配下を指定した場合の報告書書込みまでは防いでいない。
**推奨**：予定どおり repo 外の job artifact を `--output` に指定する。今回の限定運用ではコード変更不要。

**所見**：pytest collection 内の monkeypatch は復元されないが、独立 process・collect-only という予定運用では後続 test 本体へ残らない。
**分類**：refuted
**根拠**：`tools/t080_proto_equivalence_probe.py:86` の環境変数削除、`:98` の Git metadata 固定、`:188`「`--collect-only`」、`:189` の単一軽量 node 選択、`:200` の process 終了。
**影響**：この process 内の module/env は変わるが、別 process の受入には伝播しない。通常の test 本体は走らず、TemporaryDirectory は終了時に削除される。
**推奨**：独立 CLI として1回実行し、既存 pytest process に `run()` を組み込まない。副作用ゼロという一般保証ではなく、指定運用で隔離されると記録する。

**所見**：probe は旧2 build＋新2派生に加え、共通 proto を1回構築する。
**分類**：nit
**根拠**：`tools/t080_proto_equivalence_probe.py:116` の proto 構築は loop 外、`:126` の旧 build と `:132`〜`:133` のコピー・finish は2 key分。`:135`〜`:136` で全 working tree を読む。
**影響**：概算は `3R＋2D＋4×発行53秒＋Git処理`、提示値なら約342〜415秒に snapshot 比較・cleanup・collection を加えた時間になる。
**推奨**：おおむね6〜7分＋比較等の余裕を見込む。`new_seconds` は共通 proto 時間を含まないので、旧新の単純比較に使わない。この一回限り probe の時間を受入5分の permanent test 費用へ加算しない。

## 計測設計への注意

**所見**：node duration、shard span、全受入 wall は別の指標であり、proto 化で費用の帰属も移る。
**分類**：nit
**根拠**：`orchestrator/tests/test_s8b_oracle_driver.py:1007` の同期 `get()` が test 呼出し内にあり、`:1027` の test 用コピーもその後に行われる。`s4-ruling.md:135`〜`:137` は焦点走と最遅 shard wall 中央値を区別する。
**影響**：最初の node には proto 構築、同時要求 node には lock 待ちが乗るため、durations の合計や特定 node の短縮だけから実作業削減・受入改善を判断すると誤る。
**推奨**：親の既定計測で、①各走の最初の要求 node、②同一 key 待ちと別 key 待ち、③node の開始・終了位置、④新9 node と shard 配置変化、⑤session 最終退出時の追加削除費用を併読する。e2e 11 node の `-n 48` は48本の e2e 同時実行ではなく、全受入の競合を再現しない。発行なし key には53秒モデルを適用せず、OS cache・他 session の負荷差も proto 効果に帰属させない。

## 裁定パッケージ候補

**所見**：取得回数削減だけを理由とする採用、第2 proto、異常終了時の残骸対策は今回の実装修正とは分ける。
**分類**：nit
**根拠**：`s4-ruling.md:137`「10% 未満・符号不明 → fixture 変更は land しない」、`:142`〜`:145` は共有資源削減の例外採用・第2 proto 等を scope 外とする。
**影響**：資源削減と受入 wall 改善を同一視すると、確定した採否条件を満たさない変更を採用することになる。
**推奨**：新しい gate・台帳・cleanup 機構は提案しない。10%未達なら今回の計測値を既存裁定候補へ添える。再試行や異常終了対策は、実際に運用上の問題が観測された場合だけ別件にする。

## 総括

静的レビューで **must-fix は確認しなかった**。ロック順序、成功後公開、private parent の隔離、単独走 cleanup は裁定と整合する。

訂正すべき説明は、**構築失敗後は後続 worker が再試行すること、新規追加が計9 nodeであること、未登録所要の扱いが配置と実行順で異なること**。性能改善と5分上限は静的検査では確定せず、予定された親の実走結果で判断する。こちらではファイル変更・pytest 実行を行っていない。