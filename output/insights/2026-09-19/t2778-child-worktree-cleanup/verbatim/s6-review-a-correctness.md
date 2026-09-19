## 総括

**NO-GO。must-fix は所見 1〜5 の閉集合です。**

静的レビューと読み取り専用の Git 確認を行いました。pytest・撤去・変異は実行していません。`author.patch` は `git diff 2ba400087 HEAD` と byte 単位で一致しました。

唯一の実走証拠である `focus-1.log:101` は **293 passed / 1 failed、skip の記載なし**です。author.md の「直接呼出し183ケース PASS」は、正式 pytest の成功証拠としては扱えません。

以下、実装・テストの行番号は author 子木、`docs.patch` 等は指定された親 job dir を指します。

### 1 / must-fix / status に出ない生 bytes が失われる

**根拠:** `tools/dev_wave_cleanup.py:1527`、`:1608`、`:1613`、`:1655`。

**具体的な失敗入力:** tracked file に clean filter を設定し、たとえば `secret=` 行を除去して Git blob にする。子の作業木だけに `secret=child-only` 行を残す。filter 後の内容が index と一致すれば status と両 patch は空になり、その path は `dirty.tar.gz` にも入らない。index flag の拒否では検出できず、再計算も同じ空 payload なので通過する。

残した branch が保持するのは filter 後の blob であり、撤去後に元の生 bytes を復元できない。これは ruling A2 が解決対象に挙げた clean filter 問題の残存です。

**最小修正:** status の一覧だけに依存せず、tracked file の生 bytes も退避対象にする。退避を限定するなら、生 bytes と保存可能な blob の一致を独立に確認し、不一致で未退避の path は backup 前に rc20 とする。filter で status が空になる実 Git 負例を追加する。

### 2 / must-fix / submodule の到達性は、削除後の object 保存を証明しない

**根拠:** `tools/dev_wave_cleanup.py:1553`、`:1558`、`:1613`、`:1766`、`:1770`。正例は `orchestrator/tests/test_dev_wave_cleanup.py:363`。

**具体的な失敗入力:** 初期化済み submodule 内で未 push の commit X を作り、superproject の gitlink も X に更新して commit する。所有集合は main と一致する別 file にする。

この状態では以下がすべて成立します。

- submodule の HEAD は pin X と一致し、作業木は clean。
- HEAD reflog の全 commit は X の祖先。
- superproject は所有 path 一致の B で通過。

しかし X の object が子 admin の `modules/.../objects` にしかなければ、admin 撤去で消失します。superproject の branch に残る gitlink OID は、submodule の object を保存しません。現在の clean 正例は元 repo に object が残る構成なので、この問題を検出しません。

**最小修正:** 削除範囲内の submodule object store について、必要 object の削除範囲外での保存を証明できなければ rc20。救出を作らない今回の方針なら、そのケースを拒否するのが最小です。pin 一致・clean・履歴到達可能だが唯一の store が削除対象、という負例が必要です。

これは A3 の三条件には沿っていても、内容喪失を防ぐ不変条件には不足する、仕様条件自体の穴です。

### 3 / must-fix / 占有テストが実走で赤く、終了処理が不十分

**根拠:** `orchestrator/tests/test_dev_wave_cleanup.py:224`〜`:231`、`focus-1.log:30`、`:101`。

**具体的な失敗入力:** 親が実走した dispatch 環境そのもの。`process.terminate()` 後の `wait(timeout=10)` が `TimeoutExpired` になっています。

ログに現れた失敗箇所はテストのプロセス終了処理であり、cleanup 実装の占有判定失敗ではありません。ただし、終了しなかった原因をログだけで「環境問題」と確定することもできません。

**最小修正:** TERM 後に期限付き wait、期限超過時に KILL と回収を行う終了処理にする。必要なら子の準備完了を同期する。rc21・phase・非変更 assertion は維持し、同じ dispatch 経路で再走する。

### 4 / must-fix / DW-O28 の実行例は必須引数を欠き、必ず rc2 になる

**根拠:** `docs.patch:15`、`tools/dev_wave_cleanup.py:1398`〜`:1407`、`tools/check_docs.py:631`。

**具体的な失敗入力:** 新 DW-O28 の子撤去コマンドをそのまま実行する。`--main-worktree` がなく、3 option-value pairs しかないため、必要な4組を要求する parser が拒否します。wave 撤去の記述からも同じ必須 option が消えています。main への `cd` は option の代替になりません。

**最小修正:** 両コマンドに `--main-worktree <MAIN>` を明記する。1000 bytes 制限を満たすよう本文を調整し、両 literal と派生 byte assertion を同時更新する。

### 5 / must-fix / m6・m7 の現行 node は指定された単独変異を殺せない

**根拠:** `ruling.md:101`〜`:102`、`tools/dev_wave_cleanup.py:190`、`:201`〜`:205`、`:976`〜`:985`、`orchestrator/tests/test_dev_wave_cleanup.py:289`〜`:323`。

**具体的な失敗入力・変異:**

- **m6:** realpath 比較だけを文字列比較へ落としても、テストの symlink は先行する `:190` の検査で拒否されます。期待する rc・phase は変わりません。
- **m7:** `:978` の `admin.bindings` 比較だけを除去しても、現在のテストは rmtree 後に inode を交換するため、`:976` の snapshot 全体比較で同じ rc30 / admin-recheck になります。

したがって、author の「メモリ上で全件赤化」は、逐語 anchor がない現状では登録変異の証明になりません。

**最小修正・再照準案:**

- m6 は manifest 側の `_manifest_path` にある正規化 helper 呼出しを `Path(raw)` に置換する変異へ具体化する。既存の `[manifest]` は header の alias を使うため、後段の child identity 検査による重複拒否を避けられます。
- m7 は同内容・別 inode の binding 交換を、detach 後かつ `:1764` の snapshot 更新前に注入する。これなら snapshot 比較は通り、preflight 時の binding 比較だけが拒否理由になります。
- anchor と replacement を逐語固定し、指定 harness で確認する。m5 は所見3を直してから測定する。

### 6 / should / receipt は原子的に公開されない

**根拠:** `tools/dev_wave_cleanup.py:1625`〜`:1631`、`:1779`。

**具体的な失敗入力:** `removed.json` を `open("xb")` で作成した後、全 bytes の書込み前に中断する。撤去済みでも不完全な receipt が残り、次回は JSON 読込み失敗で rc20 になります。

偽の成功にはならず fail-closed ですが、原子的な成功記録ではありません。

**最小修正:** 同一 directory の一時 file に書いて fsync し、上書き禁止の原子的公開を行った後、directory を fsync する。既存 receipt を置換しない性質は維持する。

### 7 / should / 所有集合の安全条件が運用文書に落ちていない

**根拠:** `docs.patch:32`、`decision-fragment.md:17`〜`:22`、`tools/dev_wave_cleanup.py:1511`〜`:1515`。ruling A5 は rename 両端の文書化を採用しています。

**具体的な失敗入力:** 子で `old.py → new.py` と rename し、manifest は `old.py` だけ。main が旧 path の削除だけを取り込むと、双方不存在の比較で B が成立します。新 file は残した branch には保持されますが、main への採用を証明していません。

**最小修正:** 永続的な登録手順に schema の参照先と、rename の旧新両端を所有集合へ含める規則を記載する。現 docs は manifest への登録指示と相互参照だけで、必要 field・所有集合の規則が不足しています。採用済みの世代識別の残余 risk も decision に明記する。

### 8 / should / 正例は実 Git・scanner を通るが CLI の rc・出力を検査していない

**根拠:** `orchestrator/tests/test_dev_wave_cleanup.py:191`、`tools/dev_wave_cleanup.py:1837`。

**具体的な失敗入力:** `main()` の exit code や出力処理だけを壊しても、正例は `cleanup.run()` の結果を直接見るため通ります。subprocess で起動する CLI も `main(argv)` も通していません。

**最小修正:** 少なくとも主正例を CLI entry の `main(argv)` 経由にし、rc0・出力も確認する。現在の復元検査と実 scanner は維持する。

### 確認できた点と限界

- **tree entry:** 読み取り専用で `git ls-tree -z HEAD -- ':(literal)orchestrator/tests/test_dev_wave_cleanup.py'` を確認し、正しい file entry が返りました。直接指定 path に対する再帰不足の懸念は棄却します。raw entry 比較は mode/type/OID を含み、双方不存在を一致、空 owned_paths を B 不成立とする実装は ruling どおりです。
- **履歴:** HEAD reflog の old/new 両 OID を読む実装です。A と追加の B3 検査も存在します。
- **退避:** rename の2 path、`!!`、directory 再帰、symlink 本体、symlink 親拒否、列挙された special file の拒否を確認しました。両 patch は binary・full-index・no-renames。空 directory 非保存は `:1635` に明記されています。ただし、列挙されない bytes は所見1の対象です。
- **fail-closed:** manifest の exact key・重複 key・型・path 検査、実 branch、common、identity、cwd、fold、操作 marker の検査があります。occupancy helper の再試行契約はそのまま継承されています。
- **receipt:** 通常の残存 path・record・記録された admin は成功判定を阻止します。一方、receipt の手製 JSON と digest は真正性を証明しません。admin の backpointer と receipt の admin 名を共に改変すれば残骸の帰属を失わせられます。同一 principal の信頼境界外への耐改竄保証として扱うべきではありません。
- **partial:** backup 以後は `BaseException` を rc30 に包み、再検査時の占有エラーも partial になります。backup 前は `CleanupFailure` の rc を維持しています。SIGKILL 等まで捕捉するものではありません。
- **既存 wave:** `child_proof is None` の分岐は従来と同じ reflog 到達性検査です。追加 allowlist と既存禁止 verb の衝突は見当たりません。削除行を全確認し、cleanup 既存テストの期待値変更はありません。docs の byte assertion 2件の変更は ruling が許可した範囲です。
- **その他の変異:** m1・m2・m3・m4 は対応 node が期待差を検出する構造です。m5 は実 scanner を通りますが現在赤。m0 を含む正式 harness の結果は提示されていません。

### 裁定パッケージ候補

最後の内容・占有検査と `rmtree` の間には、再起動する producer を排他する仕組みがありません（`tools/dev_wave_cleanup.py:1758`〜`:1766`）。これは今回の「producer 終端・再投入禁止」という明示前提で扱われており、一般的な lease 導入は既裁定どおり scope 外です。

**最終判定: NO-GO。解除条件は所見1〜5の修正・必要な回帰検査・実走証拠の更新です。**