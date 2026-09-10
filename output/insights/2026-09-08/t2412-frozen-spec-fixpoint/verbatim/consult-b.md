## 所見

1. **主張:** plan の二段 commit 方式自体は実行可能だが、提案された実 Git 正例は「commit だけから再構成した checkout でも load できる」ことを証明しない。  
   **自己判定:** real（条件付きの残存欠陥）。  
   **根拠となる file:line:** `test_floor_pair_driver.py:152-160` は空の `out/` を作るが、plan は calibration・receipt・binary だけを親 commit に入れるとしている (`plan.md:72-77`)。Git は空 directory を記録しない。一方 loader は全 output の親 directory が存在することを要求する (`floor_pair_driver.py:517-526`, `1222-1227`)。したがって同じ `tmp_path` では通っても、その二 commit を fresh checkout すると `out/` が消えて load が落ちる。  
   **これが real なら成果物がどう変わるか:** 発行 commit は作れるが、別 worktree・clone では window/summary の出力予約前に load が失敗し、`candidate_floor` は生成されない。  
   **提案する対処:** 実 Git fixture の親 commit に `out/.gitkeep` 等を含め、commit 後に clean checkout 相当へ戻してから load する。実運用手順にも「output parent は親 commit から再構成可能、または load 前に明示作成」を入れる。

2. **主張:** `run_window` の判定を二者一致へ変えても、plan は例外 status `source_commit_mismatch` を残すため、名前と実際の判定がずれる。  
   **自己判定:** real。  
   **根拠となる file:line:** 現在の三者判定と status は `floor_pair_driver.py:2175-2183`。plan は比較を `runtime_head == spec.loaded_head` のみにしつつ「既存 status は維持」とする (`plan.md:54-56`)。対応 test も現在 `source_commit_mismatch` を pin している (`test_floor_pair_driver.py:2003-2015`)。変更後は `source_commit` を一切比較していない。  
   **これが real なら成果物がどう変わるか:** 拒否は出力確保前なので成果物は作られないが、失敗記録・呼び出し側には「親 source commit の不一致」と誤読できる理由が返る。  
   **提案する対処:** status と test を `loaded_head_mismatch` 等へ更新する。互換性上 status を維持する必要があるなら、少なくとも message と test 名で「歴史的名称」と明記する。

3. **主張:** 新 helper の負例を模擬 Git だけで試す計画では、実 Git の byte-level 出力 parser が正しい証拠にならない。  
   **自己判定:** real（テスト証拠の不足）。  
   **根拠となる file:line:** 現在の `_install_git` は実 repository を持たず、HEAD を定数、blob を working-tree bytes として返す (`test_floor_pair_driver.py:301-331`)。plan は親・changed-path override を追加する (`plan.md:79-84`) が、実 Git 正例は単一親・spec 追加の一形だけ (`plan.md:68-77`)。merge・追加 path の負例は模擬のみ (`plan.md:86-91`)。実出力は親が `b"<oid>\\n"` または複数 OID の空白区切り、差分 path が `b"path\\0"` であり、parsed tuple を直接注入すると改行・終端 NUL・空出力の処理を迂回する。  
   **これが real なら成果物がどう変わるか:** parser の実装を誤っても模擬負例は緑になり得る。実 repository では正しい spec-only commit が load 不能になるか、逆に追加 path を含む commit が受理され、その commit の成果物が権威出力になり得る。  
   **提案する対処:** override は parsed tuple ではなく実 Git同形の raw stdout を返す。加えて実 Git fixture で少なくとも「spec＋別 path」を commit した負例を一本置く。

4. **主張:** calibration・build receipt を親 commit に入れれば `_bind_checkout_inputs` と spec-only diff 条件は両立する。ここに別の不動点はない。  
   **自己判定:** refuted（親 brief への攻撃は成立しない）。  
   **根拠となる file:line:** calibration と receipt は working-tree SHA と HEAD blob の一致を要求する (`floor_pair_driver.py:581-597`, `1083-1107`)。親 commit `C` にそれらを入れ、子 `H` では spec だけを追加すれば、`C` の blob は `H` にそのまま継承される。plan の手順もこの順序を明示している (`plan.md:72-77`)。binary は regular-file SHA で束縛されるが HEAD blob は要求されない (`floor_pair_driver.py:1093-1100`)。  
   **これが real なら成果物がどう変わるか:** この攻撃は成果物を変えない。正しい順序なら loader は通る。逆に calibration/receipt を spec と同じ子 commit に初めて追加すると、binding 自体は通っても changed-path exact 判定で拒否される。  
   **提案する対処:** plan の順序を維持し、「最後の calibration/receipt commit を `source_commit` とし、その次を spec-only child にする」と author 向けに明記する。

5. **主張:** plan 指定どおり既存 test を更新すれば、既知の負例が気づかれず恒真になる箇所はない。  
   **自己判定:** refuted。  
   **根拠となる file:line:** 現在は `SOURCE_COMMIT == HEAD` (`test_floor_pair_driver.py:25-27`)。plan は `PARENT != HEAD` へ分離し (`plan.md:79-83`)、旧 source mismatch test (`test_floor_pair_driver.py:996-1010`) を「唯一の親でない」負例へ置換すると明記する (`plan.md:86-89`)。runtime 負例の `"a"*40` は新設計では親値になるが、期待される runtime は子 HEAD なので引き続き真正な負例である (`test_floor_pair_driver.py:2003-2015`)。header の `"a"*40` 改変も同様に親を runtime/loaded と偽る有効な負例になる (`2272-2312`)。  
   **これが real なら成果物がどう変わるか:** 該当なし。正常系全体が `source_commit != loaded_head` で走るため、三者同値を誤って復活させると広範囲に赤くなる。  
   **提案する対処:** plan どおり mutation 19 を「source が親 tuple と一致しない値」に変える。旧名称・旧期待文言だけを残さない。

6. **主張:** 親 brief の変更面表に追加の file 漏れはないが、同一 file 内の proof-limit 文言二箇所がアンカーから漏れている。plan はこれを補っている。  
   **自己判定:** file 漏れは refuted、アンカー漏れは real。  
   **根拠となる file:line:** brief の表は `brief.md:53-61`。意味変更後に不正確になる文言は `floor_pair_driver.py:22,86` で、plan が明示的に変更対象へ追加している (`plan.md:36-38`)。その他の実変更 file は driver、driver test、spawn inventory の三つで brief の scope (`brief.md:5-7`) に収まる。  
   **これが real なら成果物がどう変わるか:** 実行結果は変わらないが、未修正なら summary の `proof_limitations` に旧「同一 revision」説明が入り (`floor_pair_driver.py:3027-3030`)、成果物の説明と実装が矛盾する。  
   **提案する対処:** plan item 1 を維持し、brief の変更面にも `floor_pair_driver.py:22,86` を加える。

## 発行手順の書き下し

1. **binary、calibration、build receipt を先に生成する。**  
   binary の SHA を確定し、それを参照する strict build receipt を作る。calibration は spec の environment/cell と一致する accepted record にする。  
   落ちる条件: binary が regular file でない・symlink component がある・SHA 不一致 (`floor_pair_driver.py:505-514`, `1093-1100`)、receipt が strict validation 不合格、binary SHA または `trace=false` と不一致 (`1052-1080`)、calibration が不合格・null・env/threads/clocks/workload/records 不一致 (`1108-1149`)。

2. **全ての固定入力を commit し、その commit を `C` とする。**  
   少なくとも calibration と全 build receipt は tracked blob として `C` に入れる。binary も親へ commit してよい。output parent を fresh checkout でも存在させるなら tracked sentinel もこの commit に入れる。`C = git rev-parse HEAD` を取得する。  
   落ちる条件: calibration/receipt が未追跡または後で working-tree 編集されると `_git_show_head`/byte 比較で拒否 (`581-597`)。空 output directory だけでは checkout 後に消え、`517-526` で拒否される。SHA-256 object-format repositoryなら現行 40 桁 OID制約 (`627-629`, `576-577`) 自体に合わない。

3. **`provenance.source_commit = C` として spec を生成する。**  
   spec 内には固定入力の path/SHA、environment、cells、pairs、windows、outputs を完全に記載し、最終 bytes の SHA-256 `S` を計算する。  
   落ちる条件: JSON duplicate/non-finite、unknown/missing key、非 canonical path、schema/version/type/value域違反 (`floor_pair_driver.py:460-467`, `621-1049`, `1193-1221`)。output path 重複または親 directory 不在でも落ちる (`1222-1227`)。

4. **spec path だけを commit して子 commit `H` を作る。**  
   `git add -- <spec-relpath>` と限定して commit する。calibration、receipt、binary、submodule pointer、mode を同じ commit で変更しない。  
   落ちる条件:

   - `H` が root commitなら親 tuple が空で拒否。`C` 自体が root commitなのは問題なく、その子 `H` は通る。
   - merge commit は親が複数なので拒否。
   - `C..H` が空、または spec 以外の追加・削除・mode変更・submodule pointer変更を含むと拒否。
   - rename は `--no-renames` により旧 path と新 path の二件になり拒否。
   - spec pathだけの追加・内容変更・mode変更は一 pathとして現れ、この path 条件上は受理される。
   - shallow checkout等で `C` objectを読めない、Git起動・timeout・非zero、親OIDまたはNUL出力が不正なら helper で拒否される。

5. **`H` を checkout した状態で spec bytes と SHA を確認する。**  
   working-tree spec が `git show H:<spec-relpath>` と byte一致することを確認し、`S` を `--expected-sha256` に渡す。  
   落ちる条件: spec が未追跡、事後編集、regular fileでない、symlink、repo外、SHA不一致 (`floor_pair_driver.py:1152-1192`)。

6. **`load_frozen_spec(spec, S, repo_root=...)` を呼ぶ。**  
   plan 実装後は `loaded_head = H`、親 tuple `(C,)`、changed paths `(spec-relpath,)` が成立し、返値は `source_commit=C`, `loaded_head=H` となる。  
   落ちる条件: 手順1〜5のどれか、HEAD が `H` でない、親/diff query の実出力を誤って parseする場合。calibration/receipt を `H` で同時に追加した場合は `_bind_checkout_inputs` を通り得るが、最終 changed-path 判定で必ず落ちる。

7. **実行・再検証時も HEAD を `H` に保つ。**  
   `run_window` は runtime HEAD `H` を header の `loaded_head`/`runtime_head` に記録し、finalizer は両方に `H` を期待する。別 CLI invocation の finalize も最初に loader を再実行する。  
   落ちる条件: 後続 commitへ移動、別 checkout、既存 output leaf、live environment不一致。これらは load 後または再load時に成果物発行を止める。

## plan で足りている点

- 唯一の親 `(source_commit,)` と spec-only tree diff の組合せは、不動点を解消しつつ source と実行 tree の差を spec path に限定できる。
- `load_frozen_spec` の `loaded_head=H`、`run_window` の runtime `H`、window header と finalizer の期待 `H`、summary の `loaded_head=H` は、plan の三箇所を同時に変更すれば整合する (`floor_pair_driver.py:1235-1255`, `2175-2197`, `2643-2651`, `3004-3010`)。
- `git diff-tree` は spec 以外の追加・削除・mode変更・submodule pointer変更も pathとして列挙する。`--no-renames` も rename を二 pathへ展開するため、目的に合う。
- spawn inventory は新 helper 各一箇所の `subprocess.run` を追加する設計と一致し、plan の `test_ccbench_spawn_sites.py:113-117` 更新で exact inventory (`2600-2607`) と噛み合う。
- 行番号は現在の現物と一致している。既知のずれである `_install_git` の開始行 `305` も plan は正しく訂正している。
- schema を維持しても、指定範囲内の全 consumer は spec SHA と `loaded_head` で再束縛されるため、内部整合の破れは見つからなかった。

## 総括

親子二 commit方式は、固定入力を親へ先に commit すれば実際に spec を作って load できる。  
主要な意味連鎖も、runtime/finalizer を `loaded_head` に統一すれば閉じる。  
残る具体的問題は、空 output directory に依存する実 Git正例、旧 status 名、模擬 Git が raw 出力 parser を証明しない点である。  
brief に追加 file の漏れはないが、proof-limit の二アンカーは plan による補完が必要である。