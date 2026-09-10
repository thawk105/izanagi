## 前提検証

- 親 brief の「compiler 不在 skip 7 件 + direct comparison 1 件」は、次の 8 node と解釈できる。

  - `test_campaign.py`: stock roundtrip、missing define、semantic change、builtin alias、include drift、TRACE 2 件
  - `test_s1_direct_comparison.py`: outer-whitespace identity 1 件

- `test_source_digest_fixed_variant_distinct` は別の条件付き未実走である。compiler 選択は `_any_cxx()` へ寄せても、`skip_conditional_unrun()` を先に評価する順序を維持し、通常受入で PASS に変えない。
- `source_digest.py:81-89,1490-1502,1588-1616` より、digest は canonical な 3 source tupleを同一 compiler で current/HEAD とも正規化する。direct fixture には `cc/mocc/transaction.cc` が欠けている。
- mocc source の追加だけでは足りない。`source_digest.py:1461-1486` が source owner の `cc/mocc/CMakeLists.txt` も読むため、最小 mocc CMake fixture も同時に必要である。
- compiler 版をまたぐ digest literal の一致は保証対象でない。D34 と `source_digest.py:1098-1111` は builtin を取り込むため値が compiler 依存と明記する。一方、同じ選択済み compiler 内の次の関係は維持できる。

  - clean current == HEAD → `STOCK`
  - コメントだけの変更 == 元 digest
  - 挙動変更 != 元 digest
  - 非 stock token → stock と別 cache identity
  - include drift、unknown macro、TRACE observer-effect → reject

- `submission.py:107-113` は qualification 用の exact `gcc-13/g++-13` acceptance、`submission.py:203-215` はその manifest を series identity へ織り込む。ユーザー裁定は `worklog-860.md:631-635` の「受入テストを `_any_cxx()` 系へ寄せる」であり、production qualification を広げる裁定ではない。したがって `prepare_toolchain()` を変更しない P1 は canonical 択 (a) と整合する。
- P2 は `test_campaign.py:11461-11469` の既存 `_any_cxx()` を最初の consumer より前へ移し、production resolver を新設せず、各 test module 内で明示的に選択値を渡す形で満たせる。

## file:line 実装手順

1. `orchestrator/tests/test_campaign.py:10851-10856,11461-11469`

   - 既存 `_any_cxx()` を `10851` より前へ移す。候補順は逐語的に `("g++-13", "g++-12", "g++")` のままにする。
   - `_require_g13()` は全 consumer 移行後に削除する。
   - 旧位置 `11461-11469` の定義を削除し、同一 module 内に resolver を重複させない。
   - helper の全候補不在だけが `skip()` になる契約は維持する。

2. `orchestrator/tests/test_campaign.py:10893-10903`

   - `test_source_digest_stock_roundtrip` の直接 `shutil.which("g++-13")` 判定を `cxx = _any_cxx()` に置換する。
   - `source_digest.src_token(g, head, cxx=cxx)` として、既定 `g++-13` へ落ちないよう明示配線する。

3. `orchestrator/tests/test_campaign.py:10906-10933`

   - `test_source_digest_fixed_variant_distinct` は `10912-10915` の `skip_conditional_unrun()` を一切変更せず、その後の `_require_g13()` だけを `cxx = _any_cxx()` にする。
   - 3 回の `src_token()` に同じ `cxx` を渡す。
   - `cache_key()` の比較は同一 toolchain 引数下で `src_token` の差だけを比較する現行形を維持する。compiler 名を片側だけ織り込まない。
   - この node は通常受入では引き続き条件付き未実走であり、8 skip 実走化の件数には加えない。

4. `orchestrator/tests/test_campaign.py:10936-10951`

   - `skip_conditional_unrun()` の判定を先に残す。
   - その後で `cxx = _any_cxx()` を選び、missing define 負例を `_cpp_normalize(..., cxx=cxx)` へ渡す。
   - `RuntimeError` を受理する既存の fail-closed predicate は変えない。

5. `orchestrator/tests/test_campaign.py:10954-10969`

   - `_require_g13()` を `cxx = _any_cxx()` に置換する。
   - base、commented、behaved の3回すべてへ同じ `cxx` を渡す。これにより `base == commented` と `base != behaved` は同一 compiler 内比較になる。

6. `orchestrator/tests/test_campaign.py:11393-11417`

   - builtin alias テストで一度だけ `cxx = _any_cxx()` を選ぶ。
   - clean `resolve`、変更後 `resolve`、`compute`、`baseline` の全呼出しへ `cxx=cxx` を明示する。
   - 挙動変更を reject するのではなく、`STOCK` でない別 identity として受理する現行集合を維持する。

7. `orchestrator/tests/test_campaign.py:11420-11458`

   - include drift テストの clean、追加、差し替え、復元の全 `resolve()` と単体 `assert_includes_match_head()` に同じ `cxx` を渡す。
   - include 追加・差し替えの `RuntimeError` を skip へ変換しない。

8. `orchestrator/tests/test_campaign.py:12159-12211`

   - TRACE 2 node の `_require_g13()` を各 node 冒頭の `cxx = _any_cxx()` に置換する。
   - stock、TRACE 非依存編集、TRACE 内編集の全 `assert_trace_diff_matches_head()` へ同じ `cxx` を渡す。
   - stockと通常編集は受理し、TRACE 内編集だけ reject する集合を維持する。

9. `orchestrator/tests/test_s1_direct_comparison.py:43-95,223-262`

   - `skiputil.skip` を import する。
   - `_require_g13()` を `_any_cxx()` に置換し、`test_campaign.py` と同じ候補順、同じ全滅時メッセージ、同じ `skip()` 呼出しにする。test module 間 import は行わない。
   - `_FAKE_MOCC_CMAKE` と、条件分岐を持たない最小 `_FAKE_MOCC_TRANSACTION_CC` を追加する。
   - `_fake_ccbench_repo()` で `cc/mocc/` を作り、次を initial commit 前に書く。

     - `cc/mocc/CMakeLists.txt`
     - `cc/mocc/transaction.cc`

   - これにより `source_digest.EVOLVE_BLOCK_SOURCES` の3 sourceと、各 source owner CMake がそろう。production の canonical tuple自体は変更しない。

10. `orchestrator/tests/test_s1_direct_comparison.py:767-799`

   - `cxx = _any_cxx()` を選択してから fake repo を作る。
   - exact predicate と全 outer-whitespace variant の `source_digest.resolve()` に `ccbench_dir=str(sub), cxx=cxx` を明示する。
   - whitespaceごとの source bytes、source token、variant ID の等値関係はそのまま残す。

11. `orchestrator/tests/test_skip_classification.py:25-82,154-178`

   - `_CONDITIONAL_NODES` の4 node censusは変更しない。
   - `_CONDITIONAL_PREPROCESS_NODES` の期待 helperを `_require_g13` から `_any_cxx` へ同期する。ただし `skip_conditional_unrun` の存在検査は残す。
   - activeな8 nodeを列挙する `_SITE_CXX_NODES` を置き、各関数が直接 `_any_cxx()` を呼ぶことをASTで固定する。
   - `test_dependency_absence_skip_stays_unclassified` は、stock node自身の直接 `skip()` ではなく `_any_cxx()` への委譲を期待する形へ更新する。`skip_conditional_unrun()` 非使用の検査は維持する。
   - 両 test module の `_any_cxx()` が同一候補順であることを検査する。
   - fake `shutil.which` と fake `skip` で helperを隔離実行し、次を固定する。

     - g++-13 不在、g++-12 在庫 → `"g++-12"` を返し、skipしない
     - 全3候補不在 → 3候補を順番どおり調べた後だけ skip
     - g++-13 在庫 → 最初の候補を返す

12. `orchestrator/tests/README.md:99-102,188-227,237-292`

   - C++依存物を exact g++-13 から site test candidatesへ更新する。
   - 候補順と「全滅時だけ skip」を明記する。
   - qualification の `prepare_toolchain()` は引き続き exact g++-13であり、今回の test-only裁定とは別契約だと記す。
   - 条件付き未実走4 nodeのcensusは維持し、compiler fallbackを導入してもtemplate patchの窓は開かないと明記する。
   - 2026-08-23の旧「未裁定」記述を択 (a) の確定裁定へ更新する。
   - digest値を版横断でpinせず、同一選択compiler内の等値・非等値だけを検査する契約を書く。

13. 非変更確認

   - `orchestrator/qualification/submission.py`
   - `orchestrator/campaign/source_digest.py`
   - `orchestrator/campaign/buildcache.py`
   - `orchestrator/tests/skiputil.py`

   以上は変更しない。

## 受入・負例 matrix

| 条件 | compiler選択 | digest / cache identity | 期待結果 |
|---|---|---|---|
| g++-13在庫 | g++-13 | 現行関係を維持 | 対象8件を実走 |
| g++-13不在、g++-12在庫 | g++-12 | 同じg++-12でcurrent/HEADを比較。literal hashはpinしない | 対象8件を実走し、skipしない |
| g++-13/g++-12不在、g++在庫 | g++ | 同じg++で関係だけ検査 | 対象8件を実走 |
| 全候補不在 | なし | identity計算を開始しない | 理由付きSKIP。PASSにしない |
| clean source | 選択済みcxx | current == baseline、token=`STOCK`、旧stock identity維持 | accept |
| コメントだけ変更 | 選択済みcxx | digest等値 | accept、同identity |
| 挙動変更またはbuiltin live枝 | 選択済みcxx | digest非等値、非stock token、stockと別cache identity | acceptするが別identity |
| missing define | 選択済みcxx | preprocess失敗 | `RuntimeError`でreject |
| include追加・差し替え | 選択済みcxx | digest計算前のHEAD整合違反 | `RuntimeError`でreject |
| TRACE内の挙動変更 | 選択済みcxx | diff-of-diffs不一致 | `RuntimeError`でreject |
| template patch未適用 | compiler選択前に判定 | identity検査を開かない | `skip_conditional_unrun`。PASS化しない |
| outer whitespace差 | 選択済みcxx | source bytes、token、variant IDがexact入力と等値 | accept、同identity |
| mocc fixture欠落 | 選択済みcxx | canonical tupleを読めない | 修正前は赤、補完後はclean tupleとして実走 |

## scope 外所見

- `submission.prepare_toolchain()` の候補一般化は行わない。変更すればexact toolchain manifestとqualification seriesの受理集合が変わり、択 (a) のtest-only射程を越える。
- `source_digest.py` の既定 `cxx="g++-13"` は変えない。D330どおりcallerから明示配線する。
- `buildcache.DEFAULT_CC/DEFAULT_CXX`、`compilers_for_current_site()`、cache schema、toolchain manifestは変更しない。
- `test_s1_direct_comparison.py:448,475,532,671,876,905,996` など、対象外のg++-13 literalは整理しない。
- 他test fileのcompiler portability、shared compiler resolver、compiler版非依存の新保証、cross-version digest比較は追加しない。
- mocc fixture追加をfixture生成一般化やcanonical source自動生成機構へ広げない。

## 未確定点

- baseline receiptは `6 passed / 9 skipped` までしか残しておらず、各nodeのskip理由を記録していない。briefは対象8件と別の条件付き未実走1件を示す一方、README census上はfixedとmissing-defineの両方がcheckout状態によって条件付き未実走になりうる。実装は両方の`skip_conditional_unrun()`を保持するため受理集合には影響しないが、親の焦点走では `-rs` 相当の理由表示で実際の9件を再分類する。
- briefはmocc source数行の補完としているが、実コード上はmocc owner CMakeも必須である。これは新機構ではなく、fixtureを既存canonical tupleで実行可能にする最小依存物として扱う。
- テスト実測、mutation、全走receiptはread-only段では行わず、親が担当する。

## 総括

実装の中心は、対象8件へ同一の選択済み`cxx`を末端まで明示配線し、全候補不在だけをSKIPにすることです。条件付き未実走の先行判定、規律2のreject predicate、digest/cacheの等値・非等値関係、qualificationのexact g++-13契約は維持します。direct fixtureにはcanonical source tupleを完成させるmocc sourceと、そのowner CMakeだけを最小追加します。