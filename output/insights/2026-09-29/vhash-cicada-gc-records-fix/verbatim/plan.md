## 修理案の比較

| 案 | commit / abort の受理集合と直列化可能性 | 並行処理・D1 への適合 | 差分 |
|---|---|---|---|
| **X1: `gc_records()` で先頭から連続する aborted 版を読み飛ばす** | 検証と commit 経路を変えないため、取引の受理集合は変えない。削除済みかどうかの GC 判定だけを直す。 | D1 の「aborted → deleted」9 件と「aborted → aborted → deleted」1 件を扱える。版鎖の CAS や `REUSE_VERSION` に触れない。ただし回収時の版鎖走査が安全であるという既存の寿命前提に依存する。 | `transaction.cc:851–854` の数行。**推奨。** |
| X2: abort 時に install 済み版を外す | 意図上は受理集合を変えないが、外す CAS と読者・他 writer の参照を安全にする設計が必要。 | `latest_` と `next_` の双方が install 対象 (`transaction.cc:515–525`)。読者の走査 (`transaction.cc:102–117`)、`gc_versions()` の切離しと再利用 (`transaction.cc:831–838`; `include/transaction.hh:173–196,229–244`) に干渉する。D1 は塞げても、小修理ではない。 | 大。 |
| X3: install 時に deleted / pending なら abort | 既存なら後段で abort する取引まで早期 abort し、競合時の受理集合を変え得る。 | 見た直後の状態変更と CAS の競合を再検査する必要がある。pending を一律拒否すると正常な競合も失う。D1 の `read_recheck` abort 後に残る版そのものは除去しないため、単独では ERR を塞げない (`transaction.cc:490–530,543–569`)。 | 中。 |

`ERR` を削るだけの案は採らない。最初の非 aborted 版が committed などなら、削除済み tuple を回収しようとしている真の不整合として `ERR` を残す (`transaction.cc:845–856`)。D1 で観測した abort 理由は **10/10 が read set 再検査 (a)** であり、(b) による abort と一般化してはいけない (`d1-result-summary.md:14–18,34`)。

## 不変条件の表

| 必要な条件 | 担当するコードと評価 |
|---|---|
| 削除版の上に install された後発版は commit しない | install は最新版の wts を見るが deleted を拒まない (`transaction.cc:490–519`)。後段 (b) が新版の下の pending / aborted を越えて最初の確定版を調べ、deleted なら abort する (`transaction.cc:576–593`)。ただし先に (a) が失敗すれば (b) には達しない。D1 は全件その経路 (`d1-result-summary.md:17,34`)。 |
| aborted 版は鎖に残る | `writeSetClean()` は install 済み版を aborted にするだけ (`include/transaction.hh:343–349`)。D1 では連続 2 段も観測した (`d1-result-summary.md:16,22`)。従って一段だけの読み飛ばしは不可。 |
| 回収時に pending 版はない | `begin()` は Wts を先に公開し、`rts = MinWts − 1` を Rts 配列に公開する (`transaction.cc:38–43`)。leader は全 thread の値の最小を `MinRts` に公開し、GC 実行旗を立てる (`util.cc:281–322`)。通常は活動中 writer の Rts が回収を抑える設計。ただし **コード上 `wts >= rts` への clamp はない** (`include/time_stamp.hh:30–40`; `transaction.cc:39–43`)。時計ずれなどで `rts > wts` となる経路を静的には排除できず、P3 の「pending は無い」は証明済みと書けない。`abort()` の clock boost は次回 timestamp 用で、現在の pending 版を直接守らない (`transaction.cc:745–767`)。 |
| 鎖を辿る間、版・tuple が生存する | `gc_versions()` は別 thread の GC lock 下で鎖を切り、古い版を再利用候補に入れる (`transaction.cc:815–840`; `include/transaction.hh:173–196`)。`gc_records()` はその lock を取らず `delete rec` する (`transaction.cc:845–855`)。**既存の寿命保証をこの資料だけでは証明できない**。X1 の走査はこの既存リスクを明示して実測する。 |
| 削除済み tuple の再利用はない | delete commit は木から外し、版を deleted として回収待ちへ入れる (`transaction.cc:708–718`)。既に保持された tuple ポインタの寿命は別問題で、X1 は解決しない。 |

## 編集

`external/ccbench/cc/cicada/transaction.cc:850–854` のみを変更する案。先頭版の wts による既存の待機判定を保った上で、連続する aborted 版を辿る。

```cpp
Version* latest = rec->ldAcqLatest();
if (latest->ldAcqWts() >= MinRts.load(memory_order_acquire)) break;
if (latest->ldAcqStatus() != VersionStatus::deleted) ERR;
```

```cpp
Version* latest = rec->ldAcqLatest();
if (latest->ldAcqWts() >= MinRts.load(memory_order_acquire)) break;
while (latest != nullptr &&
       latest->ldAcqStatus() == VersionStatus::aborted)
  latest = latest->ldAcqNext();
if (latest == nullptr || latest->ldAcqStatus() != VersionStatus::deleted) ERR;
```

この形なら pending、committed、invalid、鎖の途切れは引き続き異常として止まる。**留保:** 上表の P3 が未証明なので、pending に実際に遭遇した場合は即 `ERR` とせず回収を延期する X1 派生案も検討対象。その変更を採る場合は pending 発生の診断を先に取り、真の不整合を単に先送りしていないことを確認する。上記コードの clang-format 14 適合と適用は本段では未実測。

## 置き場と適用順

- CCBench local branch は `izanagi-cicada-gc-records-fix`、親を F `25898d00b9a6bbf09329ff8e8318c77d4f08b46e` とする 1 commit。F が pin C の `cc/cicada/` を変えていないという brief の照合結果に依る (`s1-brief.md:11,33`; `t2854-ccbench-format-ci/README.md:14`)。
- commit 本文案: `Fix Cicada deleted-record GC behind aborted versions`／空行／`Skip consecutive aborted versions when checking the latest effective state of a deleted record. Preserve the error for every other state. D1 observed one or two aborted delete versions above the committing delete.`／空行／`AI-Agent: product=codex; model=gpt-6-sol; reasoning=medium; role=author; scope=cc/cicada/`／`AI-Agent: product=codex; model=gpt-6-sol; reasoning=medium; role=reviewer`／`AI-Agent: product=claude; model=claude-opus-5-5-1m; reasoning=unknown; role=manager`。trailer のモデル・role は実際の担当者に合わせて確定する (`t2854-ccbench-format-ci/commit-msg-record.txt:14–16`)。
- out-of-tree 版は `patches/fix-cicada-gc-records.patch`。pin C の clean checkout で `git apply --check` と適用を確認し、同じ条件で起動器の `patchharness.patch_files()` → `apply_patch()` も確認する。同 harness は `git apply --numstat` で touch set を取り、適用は通常の `git apply` で index を動かさない (`patchharness.py:155–170,204–211`; `launch_gcfix_run.py:1105–1111`)。**patch file は未作成なので適用成功は未実測。**
- trace 二本の transaction.cc hunk は `writePhase()` / `commit()` 付近 (`instr-cicada-trace.patch:104–130`)、TPC-C 重ね patch は header と main (`instr-cicada-trace-tpcc.patch:1–76`)。修理箇所 `transaction.cc:849–855` との hunk 重複は静的には見えない。適用順は **C1′以降 → instr → instr-tpcc → fix**。別の `-instr` file が要るかは厳密適用で決める。pin C 単体で instr-tpcc の TRACE=1 を作れないという制約は既存資料どおり (`patches/README.md:938–952`)。
- version-lifetime は `gc_versions()` の 833 付近と `mainte()` の 883 付近を触るが、`gc_records()` の hunk はない (`instr-cicada-version-lifetime.patch:789–824`)。forwarding variant は `abort()` / `writePhase()` 付近、forwarding-gc は install / `gc_versions()` 付近 (`cicada-forwarding-variant.patch:340–365`; `cicada-forwarding-gc.patch:468–510`)。行番号移動は大きいので、**前後両順の `git apply --check` と harness 適用を実測するまでは共存を保証しない**。broken 系も GC hunk は無いが、trace 上の壊しの期待結果は別途確認する (`broken-cicada-skip-read-recheck.patch:52–66` など)。
- `patches/README.md` の trace 節の近くに、欠陥・X1 の判定・pin C / F の基点・適用順・TRACE=0 と trace の確認結果・寿命上の留保を書く。`ledger.json` は登録しない (`patches/README.md:913–952`)。

## テストへの波及

`tests/` は存在せず、`orchestrator/tests/` を調べた。新 patch に `IZANAGI_` マクロを入れなければ、全 patch を走査する裸マクロ登録テストには新しい許可項目が不要 (`test_p3_s4_loop.py:8547–8550,8684–8719`)。同じく全 patch を走査する mocc marker テストは内容を読むが、Cicada の修理だけなら marker 条件は変わらない (`test_mocc_template_proof.py:94–110`)。`ledger.json` の entry 数を前提にするテストがあるため、登録しない方針と整合する (`test_silo_ladder_rung1.py:20`; `patches/README.md:913–917`)。新しい patch 名や README 節を直接照合するテストは、今回の `rg` 範囲では見つからなかった。**全 suite の実行結果ではない。**

## 確かめ方と事前登録案

起動器の `CUSTOM --build-spec` は base、順序付き patches、trace、schema、target、cell、thread、repeat を指定できる (`launch_gcfix_run.py:1251–1261,1289–1315`)。同じ job に以下を置く。

1. `F_FIX_T0`: base F、fix、TRACE=0、TPC-C F、t4 と t8 を各 **10 回**。`F_T0`: base F、patch なしで同数。D1 の無修理は t4 5/5、t8 4/5 が ERR (`d1-result-summary.md:7–12`)。
2. `F_FIX_TRACE`: base F、instr → instr-tpcc → fix、TRACE=1、schema v3、F×t4 を **3 回**。各回 rc=0、巡回 0、integrity 数値項目と存在履歴違反 0、C 行数 = commit 数、並行実行で W の op D が正数 (`launch_gcfix_run.py:818–834`; `vhash-cicada-verifier-ext/README.md:29–33,59–72`)。
3. `M_TRACE` / `M_FIX_TRACE`、`R2_TRACE` / `R2_FIX_TRACE`: 同じ job で各 **2 回**、t4。delete なしの対照として判定項目が前後とも通ることを要求する。M と R2 の負例側の既存実測は合格 (`vhash-cicada-verifier-ext/README.md:63–70`)。
4. `C_FIX_T0`: base pin C、fix の厳密適用、TRACE=0、F×t4 を **3 回**。

事前登録文面案: 「上記全修理 run は timeout・signal・非 0 rc が 0 件。無修理対照は少なくとも 1 件で既知の `gc_records()` ERR を再現する。trace run は各回の列挙した判定項目がすべて 0、C 行 = commit 数、F の W-D > 0。合格判定に throughput、単なる `ERR` 行の消失、または trace の `integrity.clean` は用いない」。判定器の上限は `indeterminate` であり、serializable の完全証明とは呼ばない (`vhash-cicada-verifier-ext/README.md:53–55,70`)。D1 の build 2・run 20 が約 1 分で、提案の本走は 2 node 時間より十分下と**推測**する (`d1-result-summary.md:1,7–12`)。

起動器には `CUSTOM` の trace run にも `stock_pass` 相当を記録して失格扱いする最小変更が必要。現状 `CUSTOM` は verifier 自体の error しか失格にせず、`stock_pass` は `GC-PROBE` のみ (`launch_gcfix_run.py:1138–1147`)。また対照の「既知 ERR を再現」は起動器の総合 rc とは別に結果 JSON で判定する。

## 上流 CI

修理 commit の clean checkout で、format.yml 相当の `git ls-files -- cc include common | grep -E '\.(cc|hh|cpp)$' | xargs clang-format-14 --dry-run --Werror` を全 file に実施する。F の先例は 213 file・rc=0 (`t2854-ccbench-format-ci/README.md:14–17`)。build は CI image `:ci` 内で Release、sanitizer OFF、全 protocol の `cmake --build build -j` を行う (`run_ci_build.sh:92–105`)。T-2854 の script を写すなら、固定親 OID を C2′ から **F の完全 OID** に変え、エラーメッセージ、作業名、出力ラベルを新 commit 用に変える (`run_ci_build.sh:8–9,21,34–40,110–145`)。cache の依存 pin と `--userns` は先例のまま使えるが、CI image / cache の実体は再照合する (`run_ci_build.sh:24–31,46–89`; `t2854-ccbench-format-ci/README.md:44–50`)。GitHub Actions の結果とは区別して報告する。

## 正例 (任意)

この段では設計を採用しない。delete を単一 site で壊して **commit した**異常を作るには、install 時の wts、read set 再検査 (a)、write set 検査 (b) の複数の防壁を越える必要があり、単一理由性が立たない (`transaction.cc:490–519,543–593`)。md_17 の R4 も同じ制約を記す (`vhash-cicada-verifier-ext/README.md:94`)。既存の insert 正例と read 再検査の壊しは、判定器の検出力の対照として残せる (`同 README.md:74–92`)。

## brief への指摘

- **P1** は D1 の 10 件で支持されたが、今回観測された abort 段は (b) ではなく全件 (a) (`s1-brief.md:27–30`; `d1-result-summary.md:14–18,34`)。
- **P2** の「deleted より上は必ず abort」は (b) に到達した場合の説明として妥当。ただし (a) が先に失敗する経路と、時刻順が異なる挿入位置を含めた無条件の証明とは書けない (`transaction.cc:511–525,543–593`)。
- **P3** の pending 不在は、`rts = MinWts − 1` と生成 wts の大小が強制されないため、静的には未証明 (`transaction.cc:39–43`; `include/time_stamp.hh:30–40`)。
- **P4** の「aborted 版は delete rec で解放されない」は `delete rec` が版鎖全体を辿らない点では正しい。一方、別の `gc_versions()` による版の切離し・再利用との競合と tuple ポインタの寿命は、単なる leak として片付けられない (`transaction.cc:831–855`; `include/transaction.hh:173–196`)。
- **P5** の cc/cicada 同一性から修理差分の基点は共有できるが、重ね patch の厳密適用と trace build の成立までは導けない (`s1-brief.md:33`; `patches/README.md:938–952`)。

## 総括

**X1 を修理の第一候補とする。** D1 の 2 段の aborted 版を扱い、commit 判定を変えず、非 deleted 状態への `ERR` を残せる (`transaction.cc:845–856`; `d1-result-summary.md:14–18`)。ただし pending 不在と版の寿命は静的には閉じていない。親の実装・実測では、その二点を明示した上で pin C と F の厳密適用、修理・無修理の同時対照、trace 判定、上流 CI を完了条件にする。本段は read-only のため、patch 作成・適用・テストの成功は主張しない。