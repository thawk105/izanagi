## plan — 1. 修理の hunk

F `25898d00b9a6bbf09329ff8e8318c77d4f08b46e` から `izanagi-mocc-validation-fix` を切り、1 commit で `cc/mocc/transaction.cc` の validation だけを直す。[F の該当箇所](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/verbatim/ccbench-F/cc/mocc/transaction.cc:1031)では、V1 の版 load・比較が 1032〜1043 行、lock 検査が 1045〜1059 行、`max_rset_` が 1061 行にある。

採るのは案 A。1059 行の `#endif // RWLOCK` の後、1061 行の前へ次を挿入し、1061 行の右辺を `check` に替える。既存の版不一致と同じ `failed_verification_`、`status_`、`ADD_ANALYSIS` の by_tid 計上を使う。lock 不一致の by_writelock 経路はそのままにする。

```cpp
    Tidword check_after_counter;
    check_after_counter.obj_ =
        __atomic_load_n(&((*itr).rcdptr_->tidword_.obj_), __ATOMIC_ACQUIRE);
    if (check_after_counter.epoch != check.epoch ||
        check_after_counter.tid != check.tid) {
      (*itr).failed_verification_ = true;
      this->status_ = TransactionStatus::aborted;
#if ADD_ANALYSIS
      ++result_->local_validation_failure_by_tid_;
#endif
      return false;
    }

    this->max_rset_ = max(this->max_rset_, check);
```

V1=`check`、L=既存の lock load、V2=`check_after_counter` とする。案 A は元の **V1 一致かつ L 通過**に **V2 一致**を加えるので、同じ実行で元が拒否した取引を新たに受理しない。publish は writer lock 保持中の release store（1306 行）、解錠はその後（1320 行）。L が解錠を acquire で観測したなら、その後の V2 は先行する publish を見落とせない。V1=V2 で版の ABA がなければ、L 時点にも V1 の版が存在し、Silo の単一 word 検査（`cc/silo/transaction.cc` 453〜478 行）の「同じ版かつ他者の writer lock なし」に対応する。L 後に施錠された writer の publish を V2 が見て abort する余分な拒否はあり得るため、ここでいう同値は**通過時に成立した検査条件**であり、全並行スケジュールの受理件数一致ではない。

案 B の「L → 版を一度だけ load・比較」も、L 時点で単一 word を検査する Silo の考え方に対応する。しかし L を元より前へ移すと、L では未施錠、その直後に他者が施錠し、版はまだ V1 のまま、という実行を通し得る。同じ実行で元の後段の L が施錠を見れば元は拒否する。したがって依頼の「受理集合を縮める方向だけ」には案 A が適する。

ABA 不在の根拠と限界は明記する。`writePhase` 1141〜1155 行は read/write set の最大版と当該 worker の前回版をそれぞれ `tid++` した候補、および現在 epoch の候補から commit 版を選ぶ。`Tidword` は `absent:1, tid:31, epoch:32` で、`obj_` 順に比較する（[tuple.hh](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/verbatim/ccbench-F/cc/mocc/include/tuple.hh:14)）。通常の同一 record の連続 publish では版が前進する。ただし有限幅の `tid`・`epoch` の周回や record 再初期化まで含めた**無条件の ABA 不在は、このコードからは証明できない**。論証の適用範囲をそのように記し、絶対保証と書かない。

node set 検査（1064〜1071 行）、自己 write の `searchWriteSet` 例外、hot record の read lock と read phase、DELETE/absent の扱いは変更しない。自己 write と read lock 保持中の item にも版の再確認は掛かるが、他者がその間に正当に publish できなければ追加 abort は起きない。DELETE/absent の経路へ、今回の read-heavy witness の論証を広げない。

## plan — 2. `#line`

既存の `#line` 値は動かさない。挿入分だけ validation から次の `#line 1158` までの論理行番号が進むのは、実際に有効な C++ 文を足すことに対応する。1225 行の `#line 1158` 以降は従来の論理行番号へ戻る。`ERR` は挿入箇所より前の 521 行と、後段の `#line 1187` に続く 1289 行にあり、どちらの `__LINE__` も変える必要がない。

後続の `#line` を挿入行数だけ増やすと、修理と無関係な後段の `__LINE__` を変え、D297 の差分も広がる。既存値を保てば差分は修理の hunk に収まり、`#line` を context に持つ既存 patch と上流での読みやすさにも有利である。ただし patch の適用可否は §7 で実測する。

## plan — 3. 整形と commit message

上の代入・条件式の改行は F の 2 space、80 列の `.clang-format` に合わせる。実装後は対象 file を clang-format 14 で整え、§4 の全 file dry-run で確定する。commit は F の直接の子、変更 file は `cc/mocc/transaction.cc` だけと照合する。

親が trailer を付ける前の本文案：

```text
fix(mocc): close the validation version and lock gap

Recheck each read-set record's version after inspecting its writer lock.
Abort on a changed epoch or tid, and use the validated version when
computing the commit tid. This prevents a writer from publishing and
unlocking between the original version check and lock check while the
reader commits with the stale version.

Keep the existing lock-failure path and the rest of validation unchanged.
```

上流への短い説明案は「MOCC validates a read-set version and writer lock with separate loads. A concurrent writer can publish and unlock between them. This change rechecks the version after the lock load and aborts on a change.」とする。push・PR・追加報告は人間の手番に残す。

## plan — 4. CI 2 本

- **format:** 修理 tip の clean checkout で、[format.yml](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/verbatim/ccbench-F/.github/workflows/format.yml) の `git ls-files -- cc include common | grep -E '\.(cc|hh|cpp)$' | xargs clang-format --dry-run --Werror` をそのまま回す。先例の `format-ci-F.sh` と `scripts/check_format_ci.sh` を、F 固定の OID・bundle・出力名を修理 tip 用へ替えて再利用する。login の 14.0.0 と、取得済み CI `:latest` image の 14.0.6 の双方で全追跡対象（F の先例では 213 file）を確認し、版、file 数、rc、ログを残す。
- **build:** [run_ci_build.sh](/work/SFC/tanab/tmp/t2854-ccbench-format-ci-20260929/build/run_ci_build.sh) を複製して、`parent_oid=40a7…` の固定検査を **F の full SHA** に替え、修理 tip の immutable bundle を渡す。計算ノードで CI `:ci` image を `apptainer --userns` で起動し、[build.yml](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/verbatim/ccbench-F/.github/workflows/build.yml) の Release・sanitizer OFF・ccache launcher・全 protocol build を用いる。offline 供給用の `FETCHCONTENT_FULLY_DISCONNECTED` と三依存の source dir という先例の追加 4 引数、clean clone、依存 pin 照合、configure/build の rc とログを流用する。`run-build.sh` の job path・bundle・OID・出力先も替える。結果は「CI image と CI 手順による手元通過」と記し、GitHub Actions の緑とは区別する。

## plan — 5. D297

修理 tip の full SHA を `X` として、先例の判定 jobを F→X 用へ改作する。`run_judge.sh` の旧 C 固定、親 C2′ 固定、三つの変更 path 固定、rc=0 のみ成功とする末尾を替える。GCC 11.4 と 12.3 それぞれで、検査器の argv は次の形にする。

```text
python3 -B tools/check_trace0_preprocess_identity.py
  --repo <FとXを含むclean clone>
  --old 25898d00b9a6bbf09329ff8e8318c77d4f08b46e --new <Xのfull SHA>
  --cxx /usr/bin/g++-11 [次は g++-12]
  --header-cc /usr/bin/gcc-11 [次は gcc-12]
  --third-party-cache /work/1/SFC/tanab/izanagi-thirdparty-cache
  --dependency-prefix /work/1/SFC/tanab/izanagi-a2-deps
  --scratch-root /scr
  --expect-paths cc/mocc/transaction.cc
```

期待する rc は両方 **1**。TRACE=0 の有効な修理文を足すので、検査器は正規化 preprocess 出力の不一致で止まる。これは D297 の pass ではない。差分が修理だけであることは、`git diff F X` が当該 hunk のみであることと、同じ compiler・macro context で取った F/X の TRACE=0 `-E -P` 出力を比較し、追加が再 load・比較・abort と `max_rset_` の `check` 化だけであることを示す。`git diff-tree --raw -r F X` の変更 path が `.cc` 一つで header が 0 であることを記録する。検査器は preprocess 不一致で先に止まるため、**header 分岐が不発火**とは言えても、include 活性まで pass したとは言わない。

別の gitlink 前進 wave には、C→修理込み tip の D297 をそのまま pass と扱えない点を起票する。選択肢は、意図した修理差分を別途審査して D297 の不一致を明示的に受け入れるか、pin 前進用の受理手順をその wave で裁定するか。本 wave では決めない。

## plan — 6. 計器と runner

[旧 probe patch](/work/1/SFC/tanab/tmp/t2872-mocc-g2-split-20260929/probe/mocc-g2-probe.patch) は F に厳密適用できず、template 適用後の F にも 1156 行の hunk で失敗する。F 用と X 用の二本を、**各 commit に template を適用した source**から作り直す。既存の hit 保留、abort 時破棄、commit 時確定、固定長配列、終了時 TSV 出力を維持する。

Vmid は両方とも最初の版比較通過直後・lock load の前に置く。lock の既存 load を local に受ける。F 用 V3 は従来どおり lock 検査と元の `max_rset_` の後、X 用 V3 は**修理の再読・比較を通過した後**に置く。X では修理用 V2 と診断用 V3 を混同しない。class A は commit した取引で L が未施錠かつ Vmid≠V1、class B は Vmid=V1 かつ V3≠V1 とする。X の class B は修理の V2 後に publish された可能性があり、0 を要求しない。

[runner](/work/1/SFC/tanab/tmp/t2872-mocc-g2-split-20260929/probe/t2872_probe.py) と [arm 定義](/work/1/SFC/tanab/tmp/t2872-mocc-g2-split-20260929/probe/arms-t2872.json) は六本へ改作する：`T_F/T_X` は TRACE=1＋対応 probe＋verifier、`N_F/N_X` は TRACE=0＋対応 probe、`P_F/P_X` は TRACE=0 素。arm に source full SHA を持たせ、runner の pin C 固定（21・498〜500 行）、単一 probe path（495・520〜525 行）、三 arm 固定（437〜452 行）、build と集計（550〜645 行）を六 arm 化する。全 source は clean checkout から clone し、template、対応 probe の順に各々 `git apply --check`→`git apply` する。F に template が当たる親の実測を起点とし、X でも厳密適用を確認する。macro off の前処理一致は **F の P_F source 対 F の N_F source、X の P_X 対 X の N_X** で、同じ commit 内だけを比べる。F 対 X の一致を要求してはならない。

既存の workload、R0、verifier argv、witness 突き合わせ、集計を流用し、同じ job 内で F/X の順を batch ごとに交替させる。1 batch は各系統で T 4・N 4・P 2、計 20 benchmark とし、benchmark が終わってからその batch の T 8 件を verify する。2 job × 14 batch なら T_F/T_X/N_F/N_X が各 112 走、P_F/P_X が各 56 走となる。事前登録は **T_X 112 走固定・延長なし、R0 なし、G2 0/112、T_X＋N_X の commit 側 class A 合計 0**。同時刻対照は T_F・N_F の class A と T_F の G2 件数。G2 が F 側で 0 の可能性もそのまま報告する。P の commit 数は trace 無し・probe 無しの観測値に限り、性能の headline に使わない。

改作後に一 batch の smoke を計算ノードで取り、**その Elapse に 28 batch を掛け、六 build と verifier の固定費も足して**総 node 時間を見積もる。旧 3 arm の完走 smoke は 267 秒、本走は 1.86 node 時間だった。六 arm は単純には倍程度で 2 node 時間を超え得るため、見積りが線以上なら本走投入前にユーザー確認を求める。

## plan — 7. patch 棚卸し

修理 tip の複製木へ [patch_inventory.py](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/scripts/patch_inventory.py) を `X <full SHA>` で適用し、`cc/mocc/transaction.cc` を触る同じ 10 本それぞれの SHA、`git apply --check` rc、最初の stderr を F の [result.tsv](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/inventory/F/result.tsv) と突き合わせる。F では 5 本が rc=0、early-unlock・hot-update-unlock・lock-coverage 計器三本の計 5 本が既に rc=1。したがって「修理で新たに外れた」は **F=0→X≠0** だけとし、F から失敗していたものを修理のせいにしない。

rc=0 の patch も hunk の意味を読む。とくに `broken-mocc-lockskip-validation.patch` は名称と違い、[現物](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-mocc-validation-fix/patches/broken-mocc-lockskip-validation.patch:4)では validation の **write set の writer lock 取得**（F 1016 行）を飛ばす。read set の 1047 行の lock 検査を削る patch ではない。X 上でも適用後に取得を飛ばし、修理の再読が取得を代替しないことを確認して「壊しとして成立／意味変化あり／適用不可」を判定する。`#line` context を持つ patch は、その行が変わらなくても前後の hunk context と改作順で判定する。patches 自体はこの wave で変更しない。

## plan — 8. 記録

`output/insights/2026-09-29/mocc-validation-fix/README.md` は、結論と適用範囲、F→X の逐語 diff・版順序の論証、CI 二本の argv/rc、生出力、D297 の意図した不一致と header path 0、probe の source SHA・macro off 照合、事前登録と smoke 見積り、本走の R0/六 arm 集計・witness、patch 10 本の F/X 表と裁定、push 依頼と上流説明案、という節で構成する。trace build と TRACE=0 の commit 数は別 build・別集計で記す。

spool worklog fragment は二件。T-2872 の MOCC read-heavy G2 item には、欠陥修理 commit・CI 相当・112 走の事実と旧 pin の測定を無効化しないことを書き、**gitlink 前進までは完了にしない**。新規の gitlink 前進 wave には、F の main 着地、人間による X branch push、GitHub CI 緑、X の取得を前提条件として記し、D297 の C→修理込み tip の扱い、patch 適用、Silo 修理と同時なら両方を積んだ tip の可能性を引き継ぐ。

## (P1)〜(P5) への意見

- **P1 採用。ただし限定付き。** 案 A と `max_rset_=…check` を採る。Silo 同値は検査時点の条件について成立する。Tidword の有限幅から無条件の ABA 不在とは書かない。
- **P2 採用。** 後段の `#line` は据え置く。
- **P3 採用。** F/X それぞれの macro off 照合、同一 job の交互実行、112 走固定を明示する。X の class B=0 は要求しない。
- **P4 採用。ただし表現を限定。** D297 は想定 rc=1。header path 0 は示せるが、先行する不一致で止まる検査器の header/include 活性 pass は主張しない。
- **P5 採用。** F の子の一 commit、変更は MOCC の一 file。trailer は親が付ける。

## 総括

実装順は、F の子 branchで修理一 commit → format・CI image build → F→X の D297 差分記録 → 二本の probe と六 arm runner の smoke・費用判断・固定反復 → patch 棚卸し → insight と worklog、である。完了時は branch 名・commit SHA・CI 相当結果を添えて人間に push を依頼し、gitlink は動かさない。この段では指定どおり、ファイル変更も build・テスト・benchmark も行っていない。