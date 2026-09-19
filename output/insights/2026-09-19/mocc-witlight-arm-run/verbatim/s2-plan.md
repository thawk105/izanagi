## 1. 採用判断と検算範囲

**P1・P2・P5・P6 は採用、P3・P4 は保証の表現と実装を補正する。** runner v5、verifier、discriminator、X/P patch、gitlink は変更しない。W は D16 の trace-hook として別 branch に保全する。

以下、`M:n` は `mocc-transaction-e9e477ca.cc`、`R:n` は `t2779_probe-v5.py`、`G:n` は `orchestrator/campaign/mocc_g2_discriminator.py` の行番号を指す。

実施したのは資料読解、メモリ内の source 変換・X/P 文脈照合、標準ライブラリだけによる検出力・回転の計算、Git の読取りである。ファイル書込み、pytest、preprocess identity checker、build、測定は行っていない。

主な補正点は次のとおり。

- W の identity 検査に、物理行番号を戻す `#line` は必須ではない。checker が使う `_cpp_normalize` は `-E -P` で処理する。ただし `__LINE__` の展開値まで一般に無視する検査ではない。
- witness off で TLS vector を構築しないよう、宣言を有効時の分岐内に置く。「追加命令までゼロ」「旧 source の off binary と同一」は保証しない。
- smoke の H 行は **witness ファイルごとに1行**。write 数と照合するのは S 行である。
- v5 は非 G2 走の生 trace/witness を削除する。smoke の件数検査には削除前の保存が必要。
- CLI は `--selftest` ではなく **`selftest` サブコマンド**である（R:734–757）。

## 2. hook commit W の逐語設計

branch は `izanagi-t1943-mocc-g2-witlight`、親は `e9e477ca1b55348ab4530de0b1cf663ce4555290`、変更ファイルは `cc/mocc/transaction.cc` のみとする。

採用する W の diff は以下。`#line` を置かない判断は直後に説明する。

```diff
diff --git a/cc/mocc/transaction.cc b/cc/mocc/transaction.cc
--- a/cc/mocc/transaction.cc
+++ b/cc/mocc/transaction.cc
@@ -100,10 +100,8 @@
 void izanagi_mocc_g2_emit_post_store(std::size_t thid,
                                      std::uint64_t writer_txid,
                                      const WriteElement<Tuple>& write,
-                                     const Tidword& version) {
-  std::uint64_t stored_producer = 0;
-  if (!izanagi_mocc_g2_decode(write.rcdptr_->body_, stored_producer))
-    std::abort();
+                                     const Tidword& version,
+                                     std::uint64_t stored_producer) {
   izanagi_mocc_g2_stream(thid)
       << "S " << writer_txid << ' '
       << izanagi_trace::key_to_hex(write.key_) << ' ' << version.epoch << ' '
@@ -1133,6 +1131,13 @@

 #if TRACE
   const std::uint64_t izanagi_txid = izanagi_trace::next_txid();
+  std::vector<std::uint64_t>* izanagi_stored_producers = nullptr;
+  if (izanagi_mocc_g2_enabled()) {
+    thread_local std::vector<std::uint64_t> stored_producers;
+    stored_producers.clear();
+    stored_producers.reserve(write_set_.size());
+    izanagi_stored_producers = &stored_producers;
+  }
   izanagi_trace::stream(thid_) << "C " << izanagi_txid << ' ' << thid_ << ' '
                                << maxtid.epoch << ' ' << maxtid.tid << ' '
                                << read_set_.size() << ' ' << write_set_.size()
@@ -1195,8 +1200,12 @@
     __atomic_store_n(&((*itr).rcdptr_->tidword_.obj_), maxtid.obj_,
                      __ATOMIC_RELEASE);
 #if TRACE
-    if (izanagi_mocc_g2_enabled())
-      izanagi_mocc_g2_emit_post_store(thid_, izanagi_txid, *itr, maxtid);
+    if (izanagi_stored_producers != nullptr) {
+      std::uint64_t stored_producer = 0;
+      if (!izanagi_mocc_g2_decode((*itr).rcdptr_->body_, stored_producer))
+        std::abort();
+      izanagi_stored_producers->push_back(stored_producer);
+    }
 #endif
   }

@@ -1205,6 +1214,17 @@
 #endif

   unlockCLL();
+#if TRACE
+  if (izanagi_stored_producers != nullptr) {
+    std::size_t stored_index = 0;
+    for (const auto& we : write_set_) {
+      izanagi_mocc_g2_emit_post_store(
+          thid_, izanagi_txid, we, maxtid,
+          (*izanagi_stored_producers)[stored_index++]);
+    }
+    izanagi_stored_producers->clear();
+  }
+#endif
   RLL_.clear();
   gc_records();
   read_set_.clear();
```

**採取位置と生存期間。** 新たな witness 処理のうち、publish 後・unlock 前に残すものは、分岐、decode、従来の decode 失敗 abort、確保済み保持先への push である。共有 body の採取位置は M:1195–1199 相当を維持し、unlock 後には共有 body を再読しない。S 出力だけを M:1207 と1208の間へ移す。

`unlockCLL()` が変更するのは lock と `CLL_` であり、`write_set_` は変更しない（M:1094–1113）。採取 loop と出力 loop の間で `write_set_` は不変、clear は M:1211。そのため同順の1要素1 push・1 S が対応する。witness 有効時、INSERT/DELETE は従来どおり abort する（M:1174–1176、1181–1183）。完走する write は UPDATE なので、保存した producer と再走査時の `maxtid.epoch/tid` の対応を維持する。

`stored_producer != izanagi_txid` の abort は追加しない。不一致値をそのまま出力し、G:375–376 の `witness-post-store-token-mismatch` の被覆を維持する。helper の S 行書式、L 行、stamp、E 行、validation、publish、CC lock 操作、`WriteElement` は変更しない。

**初期化と reserve。** TLS vector は M:1135 直後の有効分岐内で初めて構築する。各 transaction の開始時と正常出力後に clear する。`reserve(write_set_.size())` は採用する。capacity を先に確保することで、当該 transaction の publish 後の push に再確保を持ち込まない。ただし初回・capacity 増大時の確保は write lock 保持中であり、その観測者効果は残る。確保失敗による異常終了も新しい計器の限界として記録する。

通常の validation 失敗は `writePhase()` に入らない（M:1215–1221）。INSERT/DELETE、decode 失敗等のプロセス終了では次 transaction への残留値持越しはない。一方、S の出力が遅れるため、異常終了時に保存される prefix は旧版と異なりうる。**正常完走時の行対応を論証しており、異常終了時の prefix 同一性は保証しない**（T-2779 §3）。

**include と TRACE=0。** `M:10` の `include/transaction.hh` が同ヘッダ3行目で `<vector>` を取り込み、`M:15` の trace.hh が28行目で `<cstdint>` を取り込む。追加 include は不要。メモリ内の変更前後比較でも include 列が一致した。

`source_digest.py:1686–1687` は include を除去し、`-E -P -dD` で前処理する。行マーカーそのものは比較出力に残らない。今回の source に直接の `__LINE__` 使用はなく、include 由来のマクロ定義もこの比較では取り込まれないため、**W に行番号復元用の `#line` は不要と判断する**。W の実行コード変更はすべて `#if TRACE` 内に留める。

これは選定 context の正規化前処理と include 活性の同一性の見込みであり、実ヘッダを展開する全 build の命令列同一性まで意味しない。identity 2本の実行結果は親が確定する。

**off の保証。** M:32–44 の enabled 値は process 内で固定される。false なら TLS vector の構築・clear・reserve・push・decode・S 出力を実行しない。ポインタの初期化と分岐まで「完全に実行されない」とするのは不正確なので、P4 はこの保証に限定する。TRACE=0 ではポインタも分岐も含めて前処理で消える。

**commit message。** e9e477ca の実 message は、要約、変更理由、`AI-Agent:` trailer の形式であり、author と manager を別記している。W も D95 に従い、実際の author の属性を記録する。

```text
perf(mocc): defer payload witness formatting until after unlock

Capture post-store producers while the write locks are held and emit S
records after unlockCLL. Preserve witness grammar and decode failures
without adding include lines or changing TRACE=0 executable source.

AI-Agent: product=codex; model=<実際のmodel>; reasoning=<実際の設定>; role=author
```

山括弧は author が実値へ置換する。e9e477ca のモデル名を流用せず、不明項目は推測しない。

## 3. 測定用 witlight.patch の導出と同内容性

**P2 を採用する。** 測定 source は `e9e477ca + X/P + witlight.patch`、正式成果物は W とする。R:335–338 の pin 条件を維持でき、問い(ii)の discriminator が対象外にならない。

導出は次の順で固定する。

1. author が X/P を含まない W を作る。
2. author の専用 scratch で、e9e477ca に不変の X/P を適用した source A を作る。
3. 別の scratch で W に同じ X/P を適用した source B を作る。
4. B に下記の行番号復元指令だけを追加した B′を作る。
5. **A → B′** の diff を、path が `a/cc/mocc/transaction.cc` / `b/cc/mocc/transaction.cc` になる形で生成する。これを `witlight.patch` とする。

W の diff をそのまま二つ目の patch として配布する方式より、X/P 適用後の実 preimage から生成する方式を採る。`patchharness.py:155–171` と R:547–554 に従い、各 patch の `patch_files(...)` が厳密に `["cc/mocc/transaction.cc"]` になることを確認する。

測定 patch の `#line` は以下の位置とする。これは W への追加ではない。

```cpp
} // namespace
#endif
#line 115

/**
```

```cpp
    izanagi_stored_producers = &stored_producers;
  }
#line 1136
  izanagi_trace::stream(thid_) << "C " << izanagi_txid << ' ' << thid_ << ' '
```

```cpp
      izanagi_stored_producers->push_back(stored_producer);
    }
#endif
#line 1201
  }
```

```cpp
    izanagi_stored_producers->clear();
  }
#endif
#line 1208
  RLL_.clear();
```

最初の `#line 115` は helper の行数減少を吸収する。`#line 1136` は TRACE=1 の既存 C/L/W の位置を戻す。TRACE=0 では同指令は inactive だが、X/P が持つ `#line 1158` がその直後の元コード位置を復元する。X/P の `#line 1169/1187/1195` はそのまま保持する。採取部と遅延出力部は、それぞれ外側の `#line 1201/1208` で後続位置を復元する。

**文脈照合の結果。** 上記 W をメモリ内で構成し、X/P の各 hunk の旧文脈が W 上に一意に存在することを照合した。さらに、行番号指令追加前では、

```text
modify(e9e477ca + X/P) == modify(e9e477ca) + X/P
```

が byte 単位で一致した。これは独自のメモリ内文脈照合の結果であり、`git apply` の実行成功とは区別する。

X/P の1154 hunk の文脈 M:1154–1160 は変更しない。stamp hunk の M:1165–1171、DELETE hunk の M:1184–1189 も不変。publish hunk は M:1192–1197 までを文脈に使い、W の変更開始は M:1198 なので重ならない。従って P2(a) の「W では X/P の文脈が必ず衝突する」という懸念は、今回の設計には該当しない。実 `git apply --check` は未実測。

親の同内容性検査は、次の二つから **`#line` 指令行だけ**を除き、空白・改行を含めて byte 比較する。

```text
A: e9e477ca + X/P + witlight.patch
B: W + X/P
```

一致しても `#line` 自体の妥当性は証明しないので、上記アンカー照合と分けて記録する。manifest の `source_oid=e9e477ca` は patch 適用前の pin であり、測定 source 全体の OID ではない。W、patch SHA、最終 source SHA、同内容性結果を insight で接続する。

代替案は次の3行に限定する。

- pin=W は測定物と正式 commit の対応を直接表せるが、v5 のままでは discriminator が `pin-outside-t1943` になる。
- v6 の allow-list 化には runner 実装修正、束縛、selftest、レビューが増える。discriminator 自体の pin 制限ではない（G:130–136、485–487）。
- 今回は P2 の構成で問い(ii)へ到達できるため、v6 を作る費用を負わない。

## 4. arm 定義と4 node の回転

node1 用 JSON は以下。X/P は不変の repo patch、witlight は親が退避した job-dir patch を参照する。

```json
[
  {
    "name": "e9-witlight-wit",
    "pin": "e9e477ca1b55348ab4530de0b1cf663ce4555290",
    "patches": [
      "/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-mocc-witlight-arm-run/patches/instr-mocc-lock-coverage.patch",
      "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/probe/witlight.patch"
    ],
    "witness": true,
    "observational_only": false,
    "defines": {}
  },
  {
    "name": "e9-witlight-nowit",
    "pin": "e9e477ca1b55348ab4530de0b1cf663ce4555290",
    "patches": [
      "/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-mocc-witlight-arm-run/patches/instr-mocc-lock-coverage.patch",
      "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/probe/witlight.patch"
    ],
    "witness": false,
    "observational_only": false,
    "defines": {}
  },
  {
    "name": "e9-witlight-wit-bo1",
    "pin": "e9e477ca1b55348ab4530de0b1cf663ce4555290",
    "patches": [
      "/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-mocc-witlight-arm-run/patches/instr-mocc-lock-coverage.patch",
      "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/probe/witlight.patch"
    ],
    "witness": true,
    "observational_only": false,
    "defines": {
      "CCBENCH_BACK_OFF": "1"
    }
  },
  {
    "name": "e9-witlight-nowit-bo1",
    "pin": "e9e477ca1b55348ab4530de0b1cf663ce4555290",
    "patches": [
      "/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-mocc-witlight-arm-run/patches/instr-mocc-lock-coverage.patch",
      "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/probe/witlight.patch"
    ],
    "witness": false,
    "observational_only": false,
    "defines": {
      "CCBENCH_BACK_OFF": "1"
    }
  }
]
```

`defines={}` は R:34–42 の基底を使用する。bo1 は BACK_OFF のみ置換される（R:440–469）。実効 define は要求された6項目に `CCBENCH_CCACHE=OFF` を加えたもの。warmup の define は基底のままなので、**bo1 の確認には arm 別 `configure_defines` を使う**（R:559–576）。

A/B/C/D を上記の順とすると、4 JSON の順序は次のとおり。

| JSON | 初期順序 |
|---|---|
| node1、k=0 | A B C D |
| node2、k=1 | B C D A |
| node3、k=2 | C D A B |
| node4、k=3 | D A B C |

R:435–437 の回転を15 round適用すると、各 node の位置頻度は4/4/4/3の回転になる。4 node を合算した独立計算では **A/B/C/D の全16組の「arm×位置」が15回**となった。各 arm は15×4=60走。JSON はオブジェクトの値を変えず並びだけを変え、4 SHA を保存する。

R:568–578 は4 armを別々に build する。同 source・同 defines の on/off も build を共有しない。共有可能な2種類に対して2 build余分だが、runner を変更しない方針を優先する。source SHA の一致は確認するが、scratch path 等が異なる binary SHA の一致までは要求しない。

## 5. 標本・検出力の独立計算と事前登録文案

片側 Fisher の表を `[[a,K-a],[b,K-b]]`、a=on の G2 数、b=off の G2 数とする。

\[
p_K(a,b)=
\sum_{x=\max(0,a+b-K)}^{a}
\frac{\binom Kx\binom K{a+b-x}}{\binom{2K}{a+b}}
\]

独立 Bernoulli の設計仮定下で、全 a,b に対し `p<0.05` となる確率を二項確率で加算した。runner の統計実装は再利用していない。

| K/arm | off=.0417 / on=0 | off=.058 / on=0 | off=.119 / on=0 | off=.0417 / on=.014 |
|---:|---:|---:|---:|---:|
| 56 | 0.083635 | 0.223817 | 0.811578 | 0.041344 |
| 60 | **0.104776** | **0.267752** | **0.856111** | **0.049961** |
| 120 | 0.563965 | 0.831467 | 0.999108 | 0.199299 |

operational-facts §6 の表と丸め精度で一致する。ここで `.0417`、`.058`、`.119` は指定された小数であり、厳密な5/120、7/120、5/42とは区別する。

K=60、on=0 のとき、off=1〜7 の p は順に、

```text
0.500000, 0.247899, 0.121849, 0.059362,
0.028658, 0.013706, 0.006492
```

したがって off≥5 が必要。0/60 の CP 両側95%区間は `[0, 0.0596295]` である。

事前登録文案：

> 本走は4 block×15 round×4 arm、各 arm 計画数60とする。smoke および過去 wave は分母へ含めず、結果による追加・補充・早期成功打切りを行わない。固定 cell は3秒、48 thread、10,000 records、rratio 50、rmw 0、max_ope 10、zipf 0.9である。
>
> 主表示は arm 別の G2 検出走数 k、有効 verdict 数 m、k/m、Clopper–Pearson 両側95%区間とする。計画数、保存済み N、failure、indeterminate、decisive_m を併記する。m は v5 の定義どおり indeterminate を含み、failure を含めない。indeterminate を「G2なし」とは記述しない（R:197–227）。
>
> 主比較は BACK_OFF=0 の `e9-witlight-wit` 対 `e9-witlight-nowit`、on 側が低い方向の片側 Fisher とする。副比較は BACK_OFF=1 の on/off。同じ方向の未調整 p を参考値として示す。副比較を含めた family 全体の効果を、いずれか一つの p<.05 で宣言しない。
>
> block 別件数も表示する。CP/Fisher は独立・同率 Bernoulli の仮定による参考値であり、node 内相関、順序、時間変動をモデル化しない。固定時間の走あたり検出率を比較しており、同じ commit 数への曝露を比較したものではない。
>
> 実用上の到達点は、on arm に G2 が1件以上出て discriminator の入力へ到達することとする。ただし、呼出成功と `supported/contradicted` による識別成功を別々に数える。blocker や入力拒否だけなら識別達成とはしない。この到達点は率差の有意性、根因同定、認証を意味しない。
>
> T-2779 の通常 arm 5/120 は、旧 witness source・別 block・別日の参考値として並記し、今回の off arm と合算しない。旧 heavyweight on arm を含まないため、本実験だけで旧 witness からの改善量を因果的に推定しない。

R:143 は現象名を確認せず正の cycle を `g2` と分類する。親は保存済み verifier JSON の `phenomenon` を全正例で照合し、非 G2 があれば cycle 正の数と真の G2 走数を分ける。原本・runner は変更しない。

## 6. 問い(ii)の事前登録と主張上限

on arm の G2 正例は、走単位の結論表と、`comparisons` 全件の表を保存する。複数 anomaly がある走では、run 全体の結論を各 anomaly 固有の結論へ勝手に分配しない（G:600–624）。

| block/run | arm | anomaly/cycle | discriminator rc/status | conclusion | blockers（原名） | comparisons件数 |
|---|---|---|---|---|---|---|

| block/run | reader_txid | key | reader_version | expected_payload_producer | observed_payload_producer | 一致 |
|---|---:|---|---|---|---|---|

`comparisons` の field は G:607–615 をそのまま使う。blocker があれば G:602–603 により結論は `indeterminate`、comparisons は空になる。入力拒否は `indeterminate` と混同せず、rc と stderr を併記する（R:149–165）。

| 結果 | 言える範囲 | 言えないこと |
|---|---|---|
| `supported` | 報告された rw reason すべてで、reader version が示す producer と先頭8 byteの stamp producer が一致。実 anomaly と整合する | 全 payload の整合性、静的候補(ii)の実行順序、根因の確定 |
| `contradicted` | 少なくとも一つの比較で producer が不一致。版と先頭 stamp の食違いがあり、torn read と整合する | 候補(i)固有の証明、他の実 anomaly の不存在、verifier/hook由来の可能性の排除 |
| `indeterminate`＋blocker | 名指しの入力整合性条件が比較を妨げた | producer の一致・不一致、torn read の有無 |
| `input-rejected` | discriminator が入力を受理できなかった | 正常比較の実施 |
| on の G2=0 | 今回の条件・標本では比較対象を得なかった | G2不在、観測者効果消失、discriminator の実例での識別性能 |
| off の G2 | verifier の G2 signal。`not-run (witness-off)` | payload lineage による識別 |

`witness-post-store-token-mismatch` は **S の blocker**であり、それ自体を reader lineage の `contradicted` と置換しない（G:375–376、602–624）。

限定は T-2774 §6 および G:648–653 と同じである。writer version、post-store token を超える store 順序、commit 順序、MOCC 根因は検証しない。certified 昇格を認可しない。`observational_only=false` は診断 patch がないという arm 属性であり、本 wave 全体の非 certifying という位置づけを変えない（D2114、D2134）。

## 7. 親が行う検査列

identity の2本は次の形とする。`<Wの40桁OID>` は実 commit 後に置換する。

```text
python3 tools/check_trace0_preprocess_identity.py \
  --repo /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-mocc-witlight-arm-run/external/ccbench \
  --old 511c9538e4e8efa54b45cda62e72389ed3b706ec \
  --new <Wの40桁OID> \
  --cxx /usr/bin/x86_64-linux-gnu-g++-11

python3 tools/check_trace0_preprocess_identity.py \
  --repo /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-mocc-witlight-arm-run/external/ccbench \
  --old e9e477ca1b55348ab4530de0b1cf663ce4555290 \
  --new <Wの40桁OID> \
  --cxx /usr/bin/x86_64-linux-gnu-g++-11
```

511c9538→e9e477ca の祖先関係は今回の読取りで rc=0 を確認した。W を e9e477ca の子として作れば、checker:670–672 の祖先条件を満たす見込みである。compiler version body と policy の一致は親の既測定事実を使用する。

| 検査 | 合格条件 |
|---|---|
| identity 511c9538→W | rc=0、期待した差分 path と全選定 context の preprocess/include 活性比較が一致 |
| identity e9e477ca→W | rc=0、差分 path は transaction.cc のみ、include列を変更せず比較が一致 |
| `python3.10 -B <runner-v5> selftest` | rc=0、21/21。`--selftest` は使わない（R:716、737） |
| sequential apply | clean な e9 scratch で X/P の `git apply --check`→適用→witlight の `--check`→適用がすべて成功 |
| W＋X/P | W scratch への X/P の `--check` と適用が成功し、patch SHA は不変 |
| touch set | 各 patch の `patch_files` が厳密に transaction.cc 1本 |
| 同内容性 | 二つの最終 source から `#line` 行だけを除いた bytes が完全一致 |
| TRACE=1 build | compute smoke 内の実 build 成功、対象 binary が生成され、source/define/compiler が binding と一致 |

TRACE=1 の実 build は compute smoke に任せる。login で同じ build を追加する必然性はない。login で行う場合も親の正規 build 実行経路と headroom 判定を通し、直接 build しない。

include 追加版を identity checker が拒否する負例は、契約の感度を示す追加検査候補である。実施時には別 scratch に閉じ、W・測定 patch へ混入させない。今回の静的読解では拒否分岐を確認しただけで、負例実行済みとは記録しない（checker:547–550）。

## 8. smoke・本走・回収の投入設計

generic dispatch は `dispatch_compute.py:155–160` の clean env、compute gate 内で行う。CLI は同:4727–4763 に従う。

```text
python3 tools/pegasus/dispatch_compute.py \
  --task generic \
  --walltime 02:30:00 \
  --queue-wait-timeout 3600 \
  --overall-grace 4200 \
  -- \
  <computeで使用するPython>=3.10 <runner-v5の絶対path> run \
  --repo-root <当該nodeのouter-worktree> \
  --third-party-cache <親が確認したcache絶対path> \
  --scratch-root <当該job専用scratch絶対path> \
  --output-dir <job-dir>/arm-W/W1 \
  --policy <固定policy絶対path> \
  --arms-json <job-dir>/probe/arms-witlight-node1.json \
  --rounds 15 \
  --block-id W1
```

上記 interpreter 表記は説明用の placeholder であり、実投入では確認済み絶対 path に置換する。W2〜W4 は detached outer worktree、出力先、JSON、block-id をそれぞれ替える。各 submodule で e9e477ca が解決できることを投入前に確認する。測定用 pin に W を使わないため、4 node への W 配布は測定の前提ではない。

**smoke は1 node、4 arm、`--rounds 1`。** 本走と別 directory/block にする。親指定の基本条件は、4走保存、benchmark rc=0、verifier rc=0、binding一致とする。

ただし二つの補正が必要である。

1. **H/S の検査条件。** witness on の各ファイルは先頭に `H IZANAGI_MOCC_G2_WATERMARK_V1 1` が1行。H総数は witnessファイル数と一致する。S は標準 trace の W と `(txid,key,epoch,tid)` の Counter が一致し、各 identity は1件。write件数は C の write数合計とも照合する。L と R の対応も確認する（M:47–59、G:504–507）。
2. **非G2 rawの保存。** R:359–363 が raw を削除するため、完了後の v5 出力だけでは上記を検査できない。

最小の補足実装として、**smoke 限定の保存 wrapper**を author の所有物に追加する案を採る。v5 を読み込み、`command` 呼出のうち verifier 起動境界だけで、標準 trace と witness を別の smoke 証拠 directory へ保存してから元の `command` を呼ぶ。境界は R:308–323、すなわち benchmark 終了・全 file 移送後である。argv、env、返値、verifier/discriminator を変更しない。runner 本体 SHA と wrapper SHA の両方を記録し、本走では wrapper を使わない。

これは brief の author 所有 file に1本加える小さい scope 補正である。wrapper を採らない場合、v5 無変更かつ完了後の出力だけで H/S 件数検査済みとは報告できない。非同期コピーの成功を前提にする設計は採らない。

smoke に整合した G2 が出た場合、verifier rc=1 は通常の非直列化可能判定である（R:125–143）。親指定の「全rc=0」条件は未達として記録するが、build/計器故障と混同しない。**rc=0になるまで smoke を繰り返す運用は採らない。** 段4で、完全な正例と discriminator 証拠が得られた rc=1 も技術的 smoke 合格に含めるかを事前に固定することを推奨する。

**所要。** T-2779 の90走2222秒から、走あたり22秒を引いた build3＋warmup等の残差は約242秒。ただしこれは build 時間の独立測定ではない。4 buildへの増分を含めて約250–400秒と置くと、

```text
60走 × 22秒 + 準備250–400秒 = 1570–1720秒
                               ≈26–29分/node
```

したがって30分/nodeは妥当な中心見積だが、未実測である。実務予算は30–45分/node、smoke は数分を見込む。walltime 9000秒には大きい余裕があるが、verifier/discriminator 各300秒、build各900秒等の timeout を全走が消費する最悪条件まで収まる保証はない（R:342–347、472–475、748–749）。

**回収と欠測規則。** T-2779 §4 と同じく、各 block を次に分ける。

| 区分 | 判定 |
|---|---|
| (a) 保存済み | `result.json.runs` に収載 |
| (b) 開始証拠あり・未収載 | run directory・初期 run.json 等があるが未収載 |
| (c) 未開始確認済み | 終端と開始記録の照合で未開始と確定 |
| (d) 状態不明 | 上記へ確定できない |

主解析は(a)から作る。欠けた block/走を補充しない。原本を書き換えず、run.json と result の照合、計画ordinalとの差、failure/indeterminateを別記する。R:601 の単純な `planned_runs-len(runs)` だけでは(b)〜(d)を識別できない。

dispatcher成功、runner完了、各走の成功は分けて確認する。`.done`、result、終了時刻入り accounting を突合し、G2 raw は manifest の集合・サイズ・SHAと照合する。T-2780 の教訓どおり、投入成功や `.done` 到着だけを終端確認としない。待ち短縮目的の qdel は計画に含めない。

## 9. 成果物の構成と実装・レビュー分割

insight は T-2779 と同型で、次の節構成とする。

| 節 | 内容 |
|---|---|
| §0 | 問い・認可範囲・非 certifying・認可しないこと |
| §1 | 結論と主張上限。率比較と識別到達を分ける |
| §2 | W、pin、patch、runner、4 JSON、policy、compiler、source/binaryの束縛 |
| §3 | 軽量 witness の実装、採取/出力位置、identity、同内容性、prefix/offの限界 |
| §4 | 結果前に固定した標本・回転・比較・欠測・smoke条件 |
| §5 | 4 block の結果、欠測会計、k/m＋CP、主/副 Fisher、全正例の識別表 |
| §6 | T-2774/T-2779との参考比較、観測者効果の残り、結果別上限 |
| §7 | 実装/検査/レビュー/回収記録、再現資料とverbatim一覧 |

worklog fragment は1本、decisions fragment は **0本**。D16・D2114・D2134 を変更せず、今回のユーザー認可を引用する。failures fragment は実装・配線・回収の欠陥が実際に確認された場合だけ作る。G2 正例、陰性、低検出力それ自体は失敗記録にしない。

**段5 author：1本。** 所有範囲は以下。

- wave専用 submodule の `cc/mocc/transaction.cc`、W commit、指定branch。
- outer worktree の一時ファイル `tools/t_mocc_witlight.patch`。
- `tools/t_mocc_witlight_arms_node{1..4}.json`。
- 採用する場合のみ `tools/t_mocc_witlight_smoke_capture.py`。
- 導出・照合に必要な一時資材も `tools/` 配下の明示した専用範囲に限定。

子は job dir に書かない。親が成果物を job dir の `probe/` へ退避し、SHAとbytes一致を確認してから一時 file を repo から除く。JSON 内の最終参照先は退避後の job-dir patch とする。W には X/P・測定用 `#line`・outer一時資材を入れない。

submodule git dir は今回の読取りでも、

```text
/work/1/SFC/tanab/izanagi/.git/worktrees/dev-wave-mocc-witlight-arm-run/modules/external/ccbench
```

と確認できた。子の W commit はユーザー認可と D95 の担当範囲に含まれる。ただし **worktree専用 git dir であることと、sandboxから書けることは別条件**である。段5 launcher は `sandbox=workspace-write` に加え、この専用 git metadata への実効書込み権限を確認する。現在の read-only plan 子にはその権限はなく、commit可否は未実測。主 checkout の module git dir は子の書込み範囲に含めない。

**段6 reviewer A：read-only。** W の4変更点、include列、TRACEガード、enabled=false時のTLS初期化不在、採取時点、同順再走査、異常prefix、identity2本、X/P文脈、strip-line byte比較、branch/commit provenanceを点検する。

**段6 reviewer B：read-only。** 4 JSONと回転、実効define、smoke保存面、4×15の実走数、各走のrc/phenomenon、終端会計、manifest、欠測(a)〜(d)、CP/Fisher、全G2の結論とcomparisonsを点検する。runner自身の分母・分類を無検算で採用しない。

P6 は採用する。親が段7で主 checkout の module git dir へ指定branchを fetch し、ref が W と一致することを確認する。bundleも job dir に保全する。既存同名refが異なる場合は強制上書きしない。outer gitlink は511c9538のまま、pushは人間が行う（D16）。

## 10. 親 brief への異議

| 論点 | 評価・補正 |
|---|---|
| P1 | 数値は一致。「80%」は高い旧推定率 .119 の仮定であり、通常5/120相当では約10.5%。問い(ii)への到達と率差検出を分ける |
| P2 | 構成は採用。今回のWはX/P文脈と衝突しないことをメモリ内照合した。v5のpin条件が採用理由として残る |
| P3 | include追加禁止は正しい。TLSを有効分岐内へ置く。Wのchecker通過のための`#line`必須説は撤回し、測定patch側で位置を復元する |
| P4 | 同source・同defines・env差を採用。offでTLS/採取/I/Oは発火しないが、旧off binaryとの命令列・時間同一性は未実測 |
| P5 | 正しい。全16組のarm×位置が各15回 |
| P6 | 保全方針は正しい。専用git dirの実在は確認、author sandboxの書込み可否は別途確認が必要 |
| smoke | H件数条件とraw保存設計を補正。全rc0条件は正常なG2正例にも不合格となるので事前に扱いを固定 |
| 費用 | 30分/nodeは中心見積。旧onを含まないため軽量化そのものの改善量は今回だけでは同定しない |
| 受入 | runner selftest・smoke・identityだけでwave全体の受入完了とはしない。親の関連検査・docs/agents/provenance確認を別に残す |

## 総括

- **W** は M:100–106 の helper を保存値出力に変更し、M:1135直後で有効時だけTLS vectorを初期化・reserve、M:1198–1199をdecode・既存abort・pushへ置換、M:1207直後でSを出力する。include・L・stamp・E・CC操作は不変。Wの`#line`は不要と判断し、identity2本は通過見込みだが未実測。
- **P2採用。** X/P適用後sourceから測定patchを生成する。W＋X/Pとの文脈可換性はメモリ内で確認した。実`git apply`、測定patchの`#line`、指令除去後のbyte一致は親が検査する。
- **4 arm** は指定どおり、全arm同source、bo1だけBACK_OFF=1。nodeごとの初期回転により各armが各位置15回、各arm計60走となる。
- **K=60の検出力** は0.104776／0.267752／0.856111／0.049961。主表示はk/m＋CP、主比較はbo0の片側Fisher参考値。onのG2獲得、discriminator実行、識別成功を分け、過去5/120とは合算しない。
- **主要な異議** はoffの完全同一性という表現、Wの`#line`必須説、smokeのH件数・raw削除・rc0限定、`--selftest`表記。smoke証拠保存wrapperをauthor範囲へ1本加える。
- **予算** はbriefどおりCodex子6本（plan1、consult2、author1、review2）、修正子は欠陥時のみ。測定computeはsmoke1＋本走4の計5 job、4走＋240走。本走30–45分/node、並行稼働時の計算elapsedはsmoke込み概ね35–55分を予算とし、queue待ち・レビュー・親の受入時間は別枠。walltimeは各02:30:00を維持する。
