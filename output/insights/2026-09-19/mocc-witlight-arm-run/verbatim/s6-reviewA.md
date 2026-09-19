## 判定と範囲

**NO-GO（成果物の最終受入）。W のコードに阻害欠陥は見つからないが、検査範囲の記述と provenance に修正が必要。**

指定資料を読み、Git の現物、保存 source、patch を独立に比較した。ファイル変更、pytest、build、compute、identity checker の再実行はしていない。identity の実行結果は親の JSON・ログを検査したもの。

以下、`J` は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run`、`M` は指定された e9e477ca の source、`Wsrc` は `J/scratch/w/cc/mocc/transaction.cc` を指す。

## real — must-fix

**MF1：identity の証拠に、policy digest 一致という未確認の保証が付加されている。**

[insight 草稿:34](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/insight-README-draft.md:34) は、OID identity の説明に「policy 期待 digest `b713e6ab…` と一致」と書く。しかし、`check-identity.sh:20,23` は policy を渡しておらず、checker の入力・出力にもその照合はない（`tools/check_trace0_preprocess_identity.py:708–743`）。両 JSON の正規化 preprocess digest は `148e44ea…` または `4db297ef…` である。

この句を identity の説明から外すか、別検査の対象・結果・証拠を明示して分離すること。policy digest 一致自体は、今回の指定証拠では**未確認**。

**成果物影響：放置すると、選定 context の source 比較結果が、別 policy への適合証明として過大に引用される。**

**MF2：trailer の形式は適合するが、採用されたレビュー寄与の記録が欠けている。**

`W-commit-message.txt:19–20` と実 commit は author・manager の2行だけ。一方、段3 A は W の採用判断と独立検算を行い、段4はその判断を採用している（`s3-consult-A.md:3,16–23`、`s4-ruling.md:16–19`）。その receipt の記録値は `gpt-6-astra / medium`。

[provenance 規約:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-mocc-witlight-arm-run/docs/ai-provenance.md:67) は役割が違えば別行とし、採否に影響した構成を記録対象にする。author と同じ model・reasoning でも reviewer の記録にはならない。段4:37 の2行案には沿っているが、A-S4 の「例を寄与者一覧の上限にしない」（`s3-consult-A.md:150–156`）までは満たさない。

**成果物影響：W の値・動作は変わらないが、採用判断に使った独立レビューの provenance が欠落する。**

## real — should / nit

**S1〔should〕：検査スクリプトの最終 rc は、各検査の合否を保証しない。**

`check-patches.sh:19–25,34,45–51` は失敗を表示した後も進み、末尾の `echo` の rc を保存する。`check-identity.sh:20–24,45–54` も同様。したがって apply 失敗、V3 不一致、V2 の予期しない成功でも、最終 rc=0 になりうる。

今回は各ログ・JSON・source の独立照合で正例と負例を確認できたため、検査結果自体の撤回は不要。再利用するなら期待 rc と比較結果を集約して終了コードに反映すること。失敗注入によるスクリプト全体の実証は**未実測**。

**成果物影響：終了コードだけを受入根拠にすると、将来の不一致を合格扱いできる。**

**N1〔nit〕：草稿の W.patch 参照先が現配置と違う。**

`insight-README-draft.md:28,61` は `verbatim/W.patch` を指すが、現物は `probe/W.patch`。現時点で `J/verbatim/W.patch` は存在しない。

**成果物影響：SHA・W の意味は変わらないが、再現資料へ辿れない。**

**N2〔nit〕：identity の result の階層を明示するとよい。**

草稿:35 の `match` は `files[0].result`。両 JSON のトップレベル `result` は `pass`（各 JSON:1、checker:711）。

**成果物影響：合否は変わらず、機械出力との対応が明確になる。**

## refuted — W の変更境界と意味論

**R1：W に TRACE 外変更、include 追加、X/P が混入している。→ refuted。**

- plan §2 の diff と `probe/W.patch` は全文 byte 一致。
- patch をメモリ内で独立適用した結果は `scratch/w` と一致。
- `scratch/w` と Git の W source は SHA256 `432d4bd8…` で一致。
- ネストを追跡して `#if TRACE` ブロックを除いた e9/W は、**31,698 bytes 完全一致**。SHA256 は `9859f495439e11dca0eeed32a7024e84807df7b8c6f720173743d188934bdb98`。
- include 列は一致、W の `#line` は0件。変更は指定された4 hunk のみ（`W.patch:4,17,31,46`）。

**成果物影響：指定外の CC 操作変更や X/P 混入による W の意味変更は認められない。**

**R2：enabled=false でも TLS vector を構築する。→ refuted。**

宣言・clear・reserve は有効分岐内（`Wsrc:1134–1140`）。false ではポインタが null のままなので、decode・push・S 出力・出力後 clear に入らない（`1203–1208,1218–1226`）。enabled は process 内で固定される（`32–44`）。

草稿:72–73 は、残るポインタ初期化・分岐と、旧 off binary の命令列・TLS 領域・cache 同一性が未実測であることを明記している。

**成果物影響：off のソース上の不実行保証は成立する。binary・時間同一性には拡張できない。**

**R3：unlock 後の再走査で値・対応・consumer 被覆が変わる。→ 正常完走・同じ採取結果の条件下では refuted。**

decode は release publish 直後（`Wsrc:1200–1207`）。S は `unlockCLL()` 後、`RLL_.clear()` 前（`1216–1228`）。unlock は lock と `CLL_` を変更するだけで、`write_set_` は不変（M:1094–1113）。key は所有する `std::string`（W の `include/op_element.hh:20`）。

INSERT/DELETE は on で abort（M:1174–1183）。validation 失敗は writePhase に入らず、正常開始・終了で vector を clear する。helper は共有 body を再読しない。E は標準 trace、S は witness stream で、consumer は S の到着時刻を要求しない（`mocc_g2_discriminator.py:334–385`）。

異常終了時の prefix 非同一は草稿:74–75 に明記されている。

**成果物影響：正常完走時の保存値・行対応は維持される。異常終了時や別実行間の観測値同一性は保証しない。**

## identity・同内容性・行番号の確認

両 JSON（各ファイル:1）は次のとおりだった。

| 比較 | 全体／file result | context | include / preprocess |
|---|---|---:|---|
| 511c9538 → W | `pass` / `match` | 16 | 全件 `identical=true` |
| e9e477ca → W | `pass` / `match` | 16 | 全件 `identical=true` |

511c 側の basis は全件 `permitted_mocc_trace_include_addition`、追加は index 10 の TRACE=0 非活性な trace.hh。これは e9 由来であり、W の新規 include ではない。e9 側は全件 `exact_identity`。

`check-identity.sh:9–23` の old/new/compiler と JSON の束縛は一致。V2 の Git 差分は W への `<vector>` 1行追加だけで、stderr:1 は include 行契約の拒否、ログ:14 は rc=1。checker:547–552 が preprocess 比較前に拒否するため、別理由による失敗ではない。

**成果物影響：W の選定 context の identity は確認できるが、合成 binary identity や MF1 の policy digest 照合は被覆しない。**

`check-patches.log:6–9` は4系列 rc=0、:13 は V3 MATCH。独立に patch をメモリ内で再構成して `scratch/m,b` と照合し、`^#line` 行だけを除いた比較は **39,378 bytes 一致、diff 0行**だった。

V4 は `stored_index++` → `stored_index+1` の1 byte 変異。適用 rc=0（ログ:60）で、保存 source にこの差だけが残る。適用失敗や SHA 不一致による負例ではない。

4つの追加 `#line` の直後は、元 source の指定行と一致した。

| 合成 source の物理行 | 指令 | 配置・復元先 |
|---:|---|---|
| 115 | `#line 115` | `#endif` 直後、元115行 |
| 1168 | `#line 1136` | TRACE 内、C 出力 |
| 1277 | `#line 1201` | `#endif` 直後、loop の閉じ括弧 |
| 1296 | `#line 1208` | `#endif` 直後、`RLL_.clear()` |

後者3つのうち1136以外と115は、X/P の `#line 1158` と同じ配置作法。TRACE=1 の位置復元は整合する。

**成果物影響：W と測定 source の対応は確認できる。指令除去後の一致を binary identity に読み替えることはできない。**

## provenance と段3所見の反映

W の親は `e9e477ca1b55348ab4530de0b1cf663ce4555290`、指定 branch は W を指し、touch set は `cc/mocc/transaction.cc` のみ、+26/−6。Git の現物と `mk-W-commit.log:14–16,38` が一致する。

trailer は空行で区切った最終段落の2行で、文字集合・順序とも規約適合。Git の trailer parser も2行を認識した。author receipt:1 の `recorded_model=gpt-6-astra`、`recorded_effort=medium` は message:19 と一致する。ただし寄与者の網羅性は MF2 が残る。

段3 A の反映状況は以下。

- **MF1：反映済み。** 草稿:33 に TRACE=1 観測専用・性能利用不可・W OID identity と合成 binary identity の区別がある。
- **MF2：段4:17,33 で撤回済み。** 本レビューも各所見に成果物影響を記載した。
- **S1/S2：主要な限定は反映済み。** 草稿:69–75 に残る処理、reserve の観測者効果、短縮量と off binary 同一性の未実測を記載。
- **S3：反映済み。** 草稿:14–16 に規律2/7、旧束縛保持、`certified=true` / `observational_only=false` の認証上限がある。
- **S4：形式・author 属性は確認済み、寄与者網羅性は MF2。**

smoke の正例検査と runtime 不一致注入は本レビューでは**未実測**。草稿:77 の「静的確認であり runtime 注入では未検証」という限定は適切。

## 総括

**NO-GO：成果物の最終受入。W のコード・identity 2本・同内容性に阻害欠陥は見つからない。**

**must-fix**

1. **MF1：草稿:34 の policy digest 一致を削除または別証拠へ分離する。影響：identity 検査の保証範囲の過大引用。**
2. **MF2：採用された reviewer 寄与を provenance に反映する。影響：W の採用判断に関する寄与記録の欠落。**

**should：** S1、検査スクリプトが期待外の結果を最終 rc に反映するようにする。今回は個別証拠で確認済み。

**nit：** W.patch の参照先訂正、`result=pass` と file-level `match` の区別。

**B-M3 独立確認：静的確認は合格。** [W.patch:39](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/probe/W.patch:39)、:41、:54–56、:13 の追加行を独立に確認した。

```diff
+      if (!izanagi_mocc_g2_decode((*itr).rcdptr_->body_, stored_producer))
+      izanagi_stored_producers->push_back(stored_producer);
+      izanagi_mocc_g2_emit_post_store(
+          thid_, izanagi_txid, we, maxtid,
+          (*izanagi_stored_producers)[stored_index++]);
+                                     std::uint64_t stored_producer) {
```

helper の既存行は M:110 → Wsrc:108 で不変。

```cpp
      << version.tid << ' ' << stored_producer << '\n';
```

採取値 → vector → 添字読出し → helper 引数 → S の保存 producer という経路に writer txid への置換はない。consumer の `stored != txid` 検査（`mocc_g2_discriminator.py:375–376`）は非恒真のまま残る。**runtime 不一致注入は未実測。**
