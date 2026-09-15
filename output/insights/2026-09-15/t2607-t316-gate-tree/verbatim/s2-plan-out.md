## 現状の機序

以下の略記はすべて指定 worktree 内のファイルを指す。

- **P** = `tools/pegasus/probes/t316_sandbox_backend_probe.py`
- **G** = `orchestrator/campaign/condition_meaning_gate.py`
- **T** = `orchestrator/tests/test_t316_sandbox_probe.py`
- **S** = `orchestrator/tests/test_ccbench_spawn_sites.py`
- **H** = `orchestrator/campaign/patchharness.py`

**直接の欠陥は、別の requested 木を検査していることではなく、build 対象の素の木に、存在しない patch 由来条件を要求していることである。**

| 箇所 | 現行動作 |
|---|---|
| P:2029、2056–2064 | `external/ccbench` を outside / inside 共通の `source` とする。 |
| P:1850–1865 | configure list。`CCBENCH_BACKOFF_FIXED=-1`、未参照の `RULE_LAUNCH_COMPILE`、`IZANAGI_GFLAGS_SRC_HEAD`、`IZANAGI_GLOG_SRC_HEAD` を含む。 |
| P:1887–1895 | `source` のコピーを stock control とし、requested 側には **build と同じ `source`**、引数には `configure[5:]` を渡す。 |
| P:1944–1957 | 引数から exact な `-DCCBENCH_BACKOFF_FIXED=-1` だけを除く。その後、`BACKOFF_FIXED=-1 / default=None / stock_comparison=True` を要求する。 |
| G:1683–1715 | captured 引数に要求 define を再付加して configure。`failure_reason="configure-failed"` を指定する。 |
| G:1617–1622 | rc=0 でも stderr が非空なら失敗。 |
| G:1889–1897 | requested → stock の順で configure。requested が失敗すると stock に到達しない。 |
| P:1967–1985 | admission 拒否を stderr の detail と例外で報告する。 |
| P:2570–2574 | 例外は `S6 raised` の blocked observation になる。 |

素の `external/ccbench/cmake/Options.cmake:19–23,60–68` には `BACK_OFF` はあるが `BACKOFF_FIXED` はない。後者を CMake cache とコンパイラ define へ追加するのは `patches/silo-backoff-fixed.patch:12,23`。CMake ファイル群の検索でも上記4変数の参照は見つからなかった。

親 brief の追加訂正：

1. **「案 A では拒否枝と専用テストを落とす」は今回の不変条件と衝突する。** 後述のとおり、変更可能な部分と成立しない部分を分ける。
2. `backoff_sweep.py:437–438` は、checkout の返り値を **stock control** にし、patch は元の `ccbench_dir` に適用する。案 B の「使い捨て requested 木へ patch」をそのまま実装している先例ではない。
3. source identity は HEAD 一致だけではない。P:1765–1793 は **未追跡を含む clean、replace refs 不在、tree SHA の形状**も要求する。

## 案 A の変更面

**素の configure に揃える変更は記述できるが、今回の不変条件を保ったまま S6 go まで成立する案 A は構成できない。** 以下はその境界を含む変更面であり、禁止された削除・緩和を実装提案するものではない。

| 面 | 対象と扱い |
|---|---|
| configure | P:1853 の `CCBENCH_BACKOFF_FIXED=-1` と、P:1857、1862–1863 の未参照3変数を build argv から除去する。`TRACE=0`、実効 compiler 指定、依存 source 指定は維持。 |
| 関門呼出し | P:1887–1895、1932–1986。define を外すだけでは `_require_condition_gate` が要求を再生成するため解消しない。条件要求自体をなくすなら、この呼出しは不要になるが、以下の S6 契約を満たせなくなる。 |
| `S6_CONDITION_GATE_UNPROVEN` | P:399–403 を**維持**する。関門 family を作らなければ、build 成功後もこの枝で inconclusive。削除・条件付き迂回は今回禁止。 |
| `_condition_gate_family_valid` | P:357–386 を**維持**する。空 family や「条件なし」を真にする変更は受理集合の拡大であり禁止。 |
| `_INERT_CONDITION_GATE_PAIRS` | P:124–133 を**維持**する。空要求用の組や汎用成功値を加えない。 |
| receipt | P:320–354、1922–1926、2066–2079。`condition_gates=[]` は既存の表現だが、go の証拠にはならない。架空 family の発行や field の削除で辻褄を合わせない。 |
| configure 支配テスト | T:30–40 は define の存在と関門先行を要求する。案 A の define 除去で現行テストは失敗する。期待値の反転・削除は今回の許可範囲外。 |
| 拒否・family テスト | T:43–137、1026–1160 を維持する。特に「記録なし成功を拒否」「未発行 record を拒否」「receipt 不一致を拒否」は条件要求の消滅とは独立した現行 S6 契約。 |
| fixture / receipt テスト | T:238–408 の family と `_good_s6`、T:1405 以降の receipt 検査も維持。空 family を成功 fixture に変更すると同じ契約変更になる。 |
| spawn-site 被覆義務 | S:2225–2253 は source 中の macro token / `-D` を収集し、S:2678–2683 が未被覆を拒否する。**configure の一語を消しただけで source inventory が空になるとは限らない**。P:379、1946、1953 に macro が残る。実際の sink 分類を確認せず「義務消滅」と断定できない。S 側に除外を追加する提案はしない。 |

### S6 受理集合の具体的な差

他の成功条件を満たす観測を \(C\)、現行 family 検査の合格を \(F\) とすると、現行 go は概ね \(C \land F\)。

親 brief の「関門契約を落とす案 A」は \(C\) となり、次が新たに go になりうる。

- outside / inside build と trace 検査は成功したが、`condition_gates` または live family が欠落している。
- canonical JSON は同じでも evaluator が発行していない record が渡された。
- receipt の結論と live family の結論が一致しない。
- family admission は真でも、requested/default の preprocess 差を示し、許可された inert exact pair ではない。

それぞれ T:1026、1035、1056、1142 が現在拒否する観測である。**条件を消すことだけでは、これらの観測を受理してよいという契約上の根拠にはならない。**

## 案 B の変更面

### 木の生成・寿命・configure

1. **P:2041–2064：identity 確認後、両 build を一つの context で包む。**

   ```text
   元 source と依存物の現行 identity 検査
   checkout(expected_ccbench_head, base_dir=元 source) → requested 木
   requested 木の patch 前 identity 検査
   applied(patch, expected_ccbench_head, requested 木)
       outside: gate(requested 木, 素の stock control) → build(requested 木)
       inside:  gate(requested 木, 素の stock control) → build(requested 木)
   revert → checkout 破棄
   ```

   H:246–260 が apply の前提検査、H:346–364 が checkout 作成を担う。**patch 適用は outside / inside 合計1回、host 側**。inside が実行されなければ outside だけで context を終了する。

2. **P:1826–1829、1887–1895：stock control を明示的に別引数で渡す。**

   現行の `copytree(source, stock_copy)` を patch 後の requested 木に対して続けると、control も patch 済みになる。コピー元は identity 確認済みの素の `external/ccbench` とする。requested の gate と build は同じ Path を使用する。

3. **P:1857、1862–1863：未参照3変数を共通 configure list から除去。**

   案 B では `CCBENCH_BACKOFF_FIXED=-1` を維持する。関門に渡す引数だけから3変数を除く変更にはしない。

4. **P:357–403、1932–1986、1922–1926、2078–2079：既存の判定・診断・receipt を維持。**

   inside / outside とも関門を呼ぶ。現在も inside の関門呼出し自体は host 上であり、`inside=True` は build subprocess の sandbox 化を切り替える（P:1889、1908–1910）。

### source identity の保持

**patch 後の木へ `_git_source_identity` をそのまま適用してはいけない。** HEAD は維持されても clean が偽になる（P:1780–1787）。

変更方針は次のとおり。

- 元 `external/ccbench` と依存物の現行検査を維持する。
- checkout 直後の requested 木にも、同じ expected HEAD を使う現行検査を行う。
- `source_identities` は**patch 前の基底 identity**として保持する。patch 後の木を clean と記録しない。
- 基底確認 → 固定 patch の適用 → gate capture → 両 build、という同一 context の構造で導出関係を保つ。`source_identity_valid=True` は基底検査を実行せず代入しない。
- 新たな実行入力となる patch と harness を、P:2304–2309 と `t316_sandbox_backend_probe.pbs:54–60` の既存 commit 束縛対象に追加する。新しい schema や一般化された identity 台帳は不要。

これは「patch 後も clean」という契約ではない。**基底の同一性と、固定 patch からの生成手順を組み合わせる設計**なので、段4ではこの意味を明示して確定する必要がある。

### sandbox 契約

P:847–851 は `/tmp` を read-only、repo / dependency roots を read-only、scratch だけを writable にする。

- `git worktree add` は作成先だけでなく base repository の Git 管理領域へ書く（H:364）。**現在の base に対して sandbox 内から実行する設計は成立しない。**
- checkout / apply / revert / remove は host 側で完結させる。
- requested 木を S6 用 profile の readonly roots に追加し、inside から同じ絶対 Path を読ませる。
- scratch 内へ置くだけでは、P:851 の writable bind によって source も書込可能になる。source は scratch 外へ置いて明示的に read-only mount する構成が単純。

### A-2 の第2層

**確認したキャッシュでは、`config.h` 不在という第2層は再発しない見込みである。**

根拠：

- P:1859 は `FETCHCONTENT_SOURCE_DIR_MASSTREE=<cache>/masstree` を gate / build 共通に渡す。
- `ThirdParty.cmake:57–58` は archive と `config.h` を **masstree_SOURCE_DIR 内**に定義する。
- 同:85 はその source directory を include path にする。
- `masstree_wrapper.hh:20` が `<config.h>` を要求する。
- 今回 pegasus02 で、該当キャッシュの `config.h` と archive の実在を確認した。

したがって、関門用 build directory が新規でも、それだけでヘッダ不在にはならない。キャッシュにファイルがなければ、configure では生成されず、同:66–78 の build custom command が必要になる。

`buildcache.prepare_masstree_fetchcontent` は現在 **SOURCE_DIR 指定も受け取れる**（buildcache.py:2030–2037、2056–2075）。ただし、今回確認した cache に対して無条件の prebuild を追加する根拠はない。

### テスト変更面

- T:30–40：既存の関門先行・define 存在の期待を維持。
- T:1026–1160、1405 以降：拒否集合と receipt 検査を維持。
- T に追加する本題の検査：
  - gate requested root と build `-S` が outside / inside とも同一。
  - control が patch 前の素の木である。
  - checkout / apply が両 build を包み、apply が1回だけである。
  - wrong HEAD / dirty 基底を patch 前に拒否する。
  - inside に渡す profile が requested source を read-only にする。
- T:1637、1671、1690、1709 周辺：既存 execution-binding 検査の対象へ patch / harness を加える。
- S:2678 の被覆検査は維持し、production source の再分類を確認する。未被覆を allowlist で消さない。

## 択一を決める実測の設計

### 判定式を先に固定する

次を driver の出力から求める。

- \(E_A\)：素の木で flag 有無の実効 compile/link 入力と binary が一致する。
- \(C_A\)：flag と未参照3変数を外した configure が rc=0、stderr 空。
- \(G_B\)：patch 木と素の control に対する**既存**関門 family 検査が真。
- \(B_B\)：その同じ patch 木を build でき、trace-disabled が真。
- \(K_A,K_B\)：それぞれ今回の不変条件と両立する。

```text
A の技術的成立 = E_A ∧ C_A
B の技術的成立 = G_B ∧ B_B
採用可能性     = 技術的成立 ∧ K
片方だけ成立   = その案が技術的候補
両方成立       = 実測だけでは択一できず、段4で契約と変更面を判断
両方不成立     = 最初の拒否原因を返す。関門を緩めない
```

**現在の制約では \(K_A\) が成立しない。** binary 一致を測っても、この契約上の矛盾は解消しない。これは案 B の採用決定ではなく、親 brief の択一前提の不足である。

### 依存物の所在と今回の実在確認

過去 receipt の mount argv から実経路の root を特定し、**pegasus02 上で `ls -ld` による存在確認だけを実行した**。

| 依存物 | 実経路の所在 | 今回の確認 |
|---|---|---|
| masstree | `/work/1/SFC/tanab/izanagi-thirdparty-cache/masstree` | directory、`config.h`、`libkohler_masstree_json.a` が存在 |
| mimalloc | 同 cache の `/mimalloc` | directory が存在 |
| googletest | 同 cache の `/googletest` | directory が存在 |
| gflags | `/work/1/SFC/tanab/izanagi-thirdparty-deps/gflags` | directory が存在 |
| glog | 同 deps の `/glog` | directory が存在 |

現在の shell では2つの root 環境変数は未設定だった。`policy.json:15–18` の別の gflags / glog source path も存在したが、実経路との比較には上表を使用する。

確認 command：

```bash
hostname
ls -ld /work/1/SFC/tanab/izanagi-thirdparty-cache/{masstree,mimalloc,googletest}
ls -l /work/1/SFC/tanab/izanagi-thirdparty-cache/masstree/{config.h,libkohler_masstree_json.a}
ls -ld /work/1/SFC/tanab/izanagi-thirdparty-deps/{gflags,glog}
```

存在確認は pin / clean / toolchain 適合の証明ではない。driver は P:1765 の検査を使い、`policy.json:37–61` の pin と照合する。

### 100行以内の使い捨て driver

**以下は実装設計であり、未作成・未実行。** Python driver を最大90行に収める。生ログは scratch に置き、stdout に1件の JSON を出す。

| 行予算 | 処理 |
|---:|---|
| 1–12 | repo、cache、deps、既存依存 install prefix、scratch、compiler / cmake を引数で受け取る。probe と harness を import。 |
| 13–24 | HEAD / clean / replace refs、依存物と masstree生成物の存在を確認。実際の path と pin を出力へ記録。 |
| 25–36 | P:1850–1865 に対応する argv を作成。未参照3変数を除いた共通引数を用意。完全な argv を保存。 |
| 37–50 | 同じ素の source・同じ build path で、fresh configure を flag 無し／有りについて実行。rc、stderr、compile commands、link command を保存。 |
| 51–62 | 同じ条件で `ycsb_silo.exe` まで build。各回は build directory を空に戻す。binary と関連 object / archive の SHA-256 を保存。差があれば flag 無しを再走して非決定性を切り分ける。 |
| 63–77 | `checkout → applied` 内で、素の control と `_require_condition_gate` を実走。family を `_condition_gate_family_valid` へ渡す。同じ requested source を build。 |
| 78–90 | \(E_A,C_A,G_B,B_B\)、最初の失敗、trace cache 値、使用木、patch hash を JSON 出力。context cleanup。 |

補足：

- gflags / glog の install prefix がなければ、P:1843–1848 の設定による準備を先に行い、その実行記録を入力へ添える。
- login driver は生死確認であり、S7・TPS・性能比較を実行しない。
- build 部分は既存の `tools/run_tests.py` 経由で実行する。実際にコードを用意する段では、その runner の build 用入口を確認する必要がある。今回その未読 API を推測して command は書かない。
- B の login 成功は inside build 成功を証明しない。最終確認は既存 t316 の計算ノード実経路で行う。

依存物が欠ける場合、供給済み fixture の関門テストは機構確認には使えるが、**t316 の択一の代替証拠にはならない**。pin と生成物を揃えたローカルコピーが用意できなければ、同じ依存入力を持つ計算ノードで測る。

### P1-3 は configure だけで足りるか

- **コンパイラへ値が届かないことの確認**：compile commands と link / build rule の比較で確認できる。
- **binary が一致するという主張**：build まで必要。
- **「build 生成物が全部同じ」**：成立しない。少なくとも CMake cache は指定変数の有無で変わりうる。

source / build / prefix の path を揃え、毎回 fresh configure とする。単に flag を次回 argv から消すだけでは、前回の cache 値が残るため比較にならない。

## 変異事前登録の候補

以下の nodeid の接頭辞 `T::` は  
`orchestrator/tests/test_t316_sandbox_probe.py::` を意味する。**すべて KILL 予測であり、今回は変異を実行していない。**

### 案 A：親 brief が想定した契約除去の変異

案 A の合法な完成 baseline がないため、現行契約に対する差分として登録する。

| 変異 | 新たに受理する観測 | KILL するはずの既存 nodeid |
|---|---|---|
| A-M1：P:399–403 の判定を迂回 | family 欠落の成功観測 | `T::test_s6_injected_success_without_condition_records_is_not_go` |
| A-M2：P:369–375 の再 admission を省き、内容だけ一致する record を許容 | evaluator 未発行 record | `T::test_s6_unissued_condition_records_cannot_replace_live_family` |
| A-M3：P:376 の receipt 一致条件を除去 | receipt と live conclusion の不一致 | `T::test_s6_receipt_summary_must_match_live_condition_conclusions` |

この3件を KILL するテストを削除して案 A を緑にすることは、今回禁止されている。

### 案 B

| 変異 | 受理集合への影響 | KILL 予測／穴 |
|---|---|---|
| B-M1：P:1967 の admission 拒否を無効化 | 赤 family でも呼出しが正常終了 | `T::test_require_condition_gate_rejection_reports_detail_to_stderr` |
| B-M2：P:384 の inert pair 判定を恒真化 | inert でない admitted family を S6 go にする | `T::test_s6_rejects_requested_default_preprocess_difference` |
| B-M3：reason / comparison の交差組を許容 | 契約の異なる組合せを S6 go にする | `T::test_s6_rejects_crossed_inert_condition_gate_pair[identical_reason__root_location_comparison]` |
| B-M4：gate だけ patch 木、build は元の素の木へ戻す | build と無関係の関門証拠で go | **射影された既存テストに KILL を保証するものはない。穴。** |
| B-M5：stock copy の元を素の木から patch 済み requested 木へ変える | patch の stock 枝自体の改変を control にも混入できる | **既存の real-root 配線テストがなく、穴。** |
| B-M6：checkout の pin 検査を飛ばし、基底 identity を無条件で真にする | wrong HEAD / dirty 基底を受理 | **既存 S6 fixture は identity を注入しており、この実配線を KILL するテストは確認できない。穴。** |

B-M4〜M6 は今回の修正の中心にある。段4では、既存テストによる KILL と、新しい配線検査を必要とする穴を混同しないこと。

## 親の暫定裁定の検査

| 暫定裁定 | 検査結果 |
|---|---|
| **P1-1：条件が消えるため防壁の弱体化ではない** | **そのままでは支持できない。** P:399–403 は無条件の S6 契約であり、T:1026、1035、1056 が偽証拠や欠落を拒否する。条件要求の撤去を理由にこれらの拒否を外すことは、少なくとも現行契約の弱化である。今回の不変条件とも衝突する。 |
| **P1-2：案 B の次は A-2 の config.h 欠落** | **確認した入力については反証。** P:1859 と `ThirdParty.cmake:58,85` は cache 内のヘッダを参照する。その実在を pegasus02 で確認した。「専用 build tree が空だから欠落する」という推論は成立しない。関門全体が緑になるかは未実測。 |
| **P1-3：素の木では flag が binary を変えない** | **コード上は支持、t316 の binary 一致は未実測。** 素の Options:60–68 はこの値を emit せず、patch:12,23 が初めて供給する。ただし cache 等も含む「生成物全部が不変」への拡張は誤り。 |

## 総括

案は選んでいない。段4へ渡す主要な判断材料は次の3点。

1. **案 A の契約撤去は今回の不変条件と両立しない。実測だけでは解消できない矛盾である。**
2. **案 B は、素の control を保ち、host で1回 patch を適用し、同じ requested 木を両 build と関門に渡す構成で具体化できる。**
3. **A-2 のヘッダ欠落は、今回確認した cache では予想する根拠がない。次に測るべきは既存関門の実際の結論と、同じ木の build 成否である。**

編集・commit・Git 状態変更・pytest・configure・build は実施していない。実行した環境確認は hostname、環境変数、および依存ディレクトリ・生成物の存在確認に限る。