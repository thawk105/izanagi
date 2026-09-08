## B-01 — 実装形と性能予測が一致していない

- **severity:** blocker
- **自己判定:** **real**。plan は `<commit>:<path>` を直接 `cat-file --batch -z` へ送る形だが、親の 12〜15 秒予測は `ls-tree + oid batch` の値を使っている。
- **根拠:** `parent-measurements.md:9-12,19-21` では前者が 0.618〜1.566 秒、後者が 0.071〜0.091 秒。plan は前者を明記している (`plan.md:45-59,197-205`)。
- **静的見積り:** 現行 704 Git 回は、1 binding 操作あたり `root確認 + commit確認 + 62 blob = 64` 回なので 11 組に相当する。10 回の公開検査に加え、共有 lock helper の 64 回で説明できる (`campaign_lock_test_support.py:12-19`)。変更後の Git 時間は概算で `11 × (0.618〜1.566 + 0.072〜0.094)` = **7.6〜18.3 秒**。非 Git 部分 11.1 秒を足すと、47.5 秒から **18.7〜29.4 秒**であり、12〜15 秒ではない。
- **修正案:** `<commit>:<path>` batch の実測値で計画を引き直すか、brief の scope を裁定し直して `ls-tree + oid batch` を採る。両者を同じ最適化として扱わない。

## B-02 — 48 worker 時の別律速は未排除だが、index lock 仮説は弱い

- **severity:** should-fix
- **自己判定:** **real**なのは「計算ノードで未測定」という不確実性。`.git/index.lock` が主要因という仮説は **refuted 寄り**。
- **根拠:** 親自身が 48 worker 条件を未測定としている (`brief.md:20,63`, `parent-measurements.md:20-21`)。対象 argv は `rev-parse`、`cat-file` で、index を更新しない (`contract_loader_binding.py:318-345`)。さらに `GIT_OPTIONAL_LOCKS=0` が設定済み (`contract_loader_binding.py:280-285`)。
- **推測:** あり得る別律速は、Git process と動的 loader の同時起動、Lustre 上の executable・refs・loose object metadata、pack index/page cache の競合、CPU run queue、各 `commit:path` が繰り返す tree traversal である。親実測も tree traversal が path batch の遅さだと示している (`parent-measurements.md:10`)。
- **修正案:** 48 worker A/B で wall だけでなく batch latency 分布、timeout 件数、process 数、object DB が loose/packed のどちらかを記録する。10 秒 timeout 維持 (`plan.md:26`) も同条件で検証する。

## B-03 — 親の時系列と集計値だけでは因果を帰属できない

- **severity:** blocker
- **自己判定:** **real**。09-03 の module commit と、依頼に示された 09-05 20:48 の悪化開始との間が説明されていないうえ、計測値には正規化不明または内部不整合がある。
- **根拠:**
  - 同一 node の W は 17,091 から 24,247 秒 (`brief.md:6-11`)。これが単一の 48-worker run なら、最遅 shard は少なくとも `24,247 / 48 = 505` 秒でなければならず、報告された 286〜350 秒と両立しない (`brief.md:5`)。K=3 合算なら説明できるが、W の正規化が明記されていない。
  - `_run_git` 704 回に対して列挙された公開操作は 10 回、すなわち 640 回。共有 helper の追加 64 回で説明できるが、親はそれを内訳として示していない。
  - capture 18.9 秒、committed 14.9 秒、live 4.9 秒の合計は 38.7 秒で、同じ箇所の総計 36.4 秒を上回る (`parent-measurements.md:16-18`)。別 run ならその旨が必要。
- **別原因の具体候補:** module が既に存在していても、09-05 に caller・fixture の呼出し頻度が変わった、最初に当該 commit を含む canonical run が09-05だった、repo の pack/loose 状態や page cache が変わった、shard 配置や compute node が変わった可能性がある。また TMPDIR 撤去は login で 5.6 倍差を生むと記録されている (`conftest.py:3-22`)。計算ノードの local `/tmp` では差が小さいため、これは候補であって受入悪化の実証ではない。
- **修正案:** receipt 単位で K、worker 数、W が一走か合算か、実効 TMPDIR、対象 commit、caller commit、最初に新 module を含んだ走を表にする。これなしに +42% を本 module へ一般化しない。

## B-04 — 残り 11.1 秒はこの plan ではほぼ減らない

- **severity:** should-fix
- **自己判定:** **real**。
- **根拠:** `_read_regular_file_no_follow` 4.3 秒、うち `posix.open` 3.6 秒、さらに fsync 2.4 秒が報告されている (`parent-measurements.md:16-20`)。plan は clean input でも全 disk read を維持すると明記する (`plan.md:99-114`)。fsync の変更も scope にない。
- **修正案:** 11.1 秒を下限として性能予測へ明記する。Git batch 化によって減る Git 内部の open と、維持される Python の no-follow disk read を混同しない。

## B-05 — `_run_git` fake の追随が少なくとも一件欠けている

- **severity:** blocker
- **自己判定:** **real**。
- **根拠:** plan は `redirected_git_view` だけを更新対象にしている (`plan.md:128-140`; `test_artifact_admission.py:2329-2337`)。しかし射影対象への `rg` で、同じファイルの `test_v2_loader_validation_rejects_missing_blob` にも `real_run_git`、`missing_blob(root, *args)`、monkeypatch が存在した (`test_artifact_admission.py:2377-2397`)。この fake は `input_bytes=` を受け取れず、旧 `cat-file blob` 前提も再検査が必要である。
- **網羅判定:**
  - `campaign_lock_test_support.py:12-19` の `_blob` 直接呼出しは plan が追随済み。
  - spawn site 台帳は source 上の `subprocess.run` 箇所を数えるため、wrapper 内一箇所のままなら値 1 でよい (`test_ccbench_spawn_sites.py:79-82,111`; `plan.md:21-24`)。
  - `test_t671_source_binding.py` は所有 test として扱われている。
  - `test_layer3_report.py`、`test_mocc_trace_pair.py`、`test_s8c_preregistration_predicates.py`、`test_t139_blobref_digest_binding.py` は射影外のため未読であり、無影響とは断定できない。plan に repo-wide 検索結果もない。
- **修正案:** `_run_git` の monkeypatch、保存した callable、`_blob`、共有 lock helper の全ヒットを列挙し、missing fake は batch stdin/output を理解する fake へ直す。単なる `**kwargs` 追加だけで旧 missing 注入が機能するとは限らない。

## B-06 — 変異 matrix に冗長 gate と別理由 kill が混在する

- **severity:** blocker
- **自己判定:** **real**。D1712 の所有 test 制限は守る方向だが、現行表の全候補が DW-M01 の単一理由証拠になるわけではない (`rulings.md:1-18`; `plan.md:209-227`)。

| 変異 | 静的判定 |
|---|---|
| `input=input_bytes` 削除 | subprocess wrapper が stdin 値を直接検査すれば有効。空出力を parser が拒否しただけなら下流 kill |
| `-z` 削除かつ LF join | 二変更を含む複合変異。binary test と process-count test の exact argv も重複 |
| query reverse/sort | binary 正例と process-count の二重 gate |
| `_blob` を旧実装へ戻す | compatibility test が直接 kill。良い候補 |
| missing を空 blob 扱い | disk file が残る構成では後段 drift が赤にする。missing parser の単独証拠にならない |
| `type == blob` 削除 | parser 直接 test なら単独証拠 |
| size不足検査削除 | record LF 検査でも赤になり得る |
| protocol LF検査削除 | exact EOF または次 header の検査でも赤になり得る |
| exact EOF検査削除 | extra-output test が直接 kill。良い候補 |
| digest比較削除 | direct verifier と admission 層が冗長 |
| live/capture disk比較削除 | 二分岐を同時に変えると二 test が重複 |

単独証拠として残せる候補は、runner を変異ごとの exact nodeid へ狭める前提で少なくとも次の 7 件である。

1. `_run_git` の subprocess stdin plumbing 削除
2. batch input の NUL delimiter を LF に変更
3. `_blob` compatibility wrapper の逐次版への後退
4. blob type 検査削除
5. response 全消費後の exact EOF 検査削除
6. committed verifier の digest 比較削除
7. live verifier の disk 比較削除

- **修正案:** `-z` と delimiter を別変異にし、capture/live 分岐も分ける。missing、size不足、record LF は parser を直接呼ぶ test にして、drift・EOF・次 record parser が先に赤を出さないことを固定する。

## B-07 — gate・cache・互換層による scope 膨張という批判は概ね当たらない

- **severity:** nit
- **自己判定:** **refuted**。
- **根拠:** plan は production caller、closure、schema、cache を変更しない (`plan.md:3-5,110-114,234-238`)。parser の type・size・delimiter・EOF 検査は P1 の fail-closed 維持に必要 (`brief.md:26-30,57-58`)。`_blob` wrapper は既存 test API を維持し、共有 helper の追加 64 Git process を一括化するための最小互換面 (`plan.md:116-126`)。spawn site gate も新設せず既存値を維持する。
- **修正案:** scope 膨張として削る必要はない。ただし B-11 の NUL例外正規化は別途明示裁定が必要。

## B-08 — acceptance duration ledger の更新義務を plan が扱っていない

- **severity:** blocker
- **自己判定:** **real**なのは plan の欠落。ledger 更新が実際に強制されるかは、射影不足のため未確定。
- **根拠:** plan は新規 test を少なくとも 13 node 増やす構成である。内訳は通常 node 8件に加え、ambiguous/non-blob 2件、size/LF corruption 3件 (`plan.md:146-183`)。静的確認一覧には ledger や `nodeid_count` がない (`plan.md:243-247`)。
- **制約:** `acceptance_duration_ledger.json` 本体は必読射影に含まれず未読。指定された `conftest.py:1-120` にも ledger 処理は現れない。そのため「更新不要」とは判定できない。
- **修正案:** author 前に ledger 本体と実際の conftest hook 範囲を射影し、exact node count や digest を固定しているなら同 commit で更新する。更新しない場合は不要である静的根拠を plan に追加する。

## B-09 — P2/P3 を外したまま 5 分へ届く保証はない

- **severity:** should-fix
- **自己判定:** **real**。
- **根拠:** 現在の p75 は 350 秒で、上限まで 50 秒の削減が必要 (`brief.md:5,41`)。B-01 の見積りでは profiled node 一件あたりの削減は約 18〜29 秒なので、critical shard に同程度の hit が一件だけなら **321〜332 秒**で上限を超える。二件なら約 292〜314 秒となり、分布次第で割れる。
- **P2推定:** capture 直後の live verify 一回を除けるなら、path batch 0.618〜1.566 秒、rev-parse 約0.072〜0.094秒、disk scan 約0.7秒、合計 **約1.4〜2.4秒/呼出し**。該当する呼出し数は profile から一回しか確定できない (`ident.py:280-285`; `parent-measurements.md:17-20`)。
- **P3推定:** 同一 root/commit の残り10回の batchを再利用できれば、profile 一件で **約5.6〜15.7秒**追加削減し、全体を概算 **12.5〜13.7秒**へ近づけられる。ただし cache 寿命・root identity・例外再現は未設計である。
- **次 wave 裁定パッケージ候補:**
  1. `commit:path batch` から `ls-tree + oid batch` へ切り替える裁定。期待差 0.62〜1.57秒から0.07〜0.09秒/組。
  2. P2 の二重 live verify 除去。受理集合同値の証明、caller 回数、期待1.4〜2.4秒/回を添付。
  3. P3 の process 内 memo。root/commit identity、寿命、memory上限、例外非cache方針、期待5.6〜15.7秒/profileを添付。

## B-10 — commit 後に焦点走する順序は brief にはあるが plan にはない

- **severity:** should-fix
- **自己判定:** **全体としては refuted、plan 単体の欠落は real**。
- **根拠:** brief は対象 file が closure の一員であり、未 commit なら drift になるため「焦点走・受入は commit 後」と明記する (`brief.md:48-53`)。一方、plan の author 確認節は diff と test を述べるだけで、commit を焦点走の前提として再掲していない (`plan.md:243-247`)。変異節の drift 注意 (`plan.md:227`) は通常焦点走の順序説明ではない。
- **修正案:** author 手順に `実装とtestをcommit → 所有test焦点走 → A/B → acceptance` を明記する。未 commit 自走結果を回帰証拠に数えない。

## B-11 — upfront path 検査と NUL 正規化は「挙動不変」と両立しない

- **severity:** blocker
- **自己判定:** **real**。
- **根拠:**
  - 現行は loop 内で `_blob` を呼ぶたびに path を検査する (`contract_loader_binding.py:343-345,353-360,396-420`)。plan は全 path を subprocess 前に検査する (`plan.md:41`)。先頭 path に digest mismatch、後方 path に escape がある場合、現行は先頭 mismatch、新実装は後方 escape を先に返す。fail-closed 集合は同じでも、plan が主張する拒否順維持 (`plan.md:36-39`) は成立しない。
  - 現行 `_relative_parts` は NUL を拒否しない (`contract_loader_binding.py:133-145`)。NULを argvへ渡した際の `ValueError` は `_run_git` の捕捉対象 `OSError` / `SubprocessError` に含まれない (`contract_loader_binding.py:301-308`)。plan はこれを `ContractLoaderBindingError("contract-loader-git-error: ...")` へ変えるとしており (`plan.md:61`)、brief の例外種類不変 (`brief.md:28-29`) と矛盾する。
- **修正案:** 受理集合だけ不変でエラー優先順位は変更可能、と契約を狭める。また NUL の例外正規化は安全側の変更だが、scope 内の互換維持ではないため、明示的に裁定して専用 test を置く。

## 総括

blocker **6件**、should-fix **4件**、nit **1件**。pytest・性能測定は未実施で、緑は主張しない。  
最重要1: 実装する path batch と 12〜15秒予測が別方式で、実見積りは約18.7〜29.4秒。  
最重要2: 二つ目の `_run_git` fake と duration ledger が plan から漏れている。  
最重要3: 計測集計の不整合と変異の別理由 kill を解消しない限り、+42%の帰属と単一理由性を証明できない。