# 第1部 — 結合確認 probe の改修 plan

**比較対象は C `68106660686232781bca3be792a750d3e19d7a8a` と C2' `40a7f4acb174ca43cb590f40d13847216a1564bc` に固定する。** 親の照合では C → C1' `6aa7a58f` → C3 `53f6b097` → C2' という親子関係、C..C2' の変更が `include/trace.hh`・`include/tpcc.hh`・`cc/mocc/transaction.cc`・`cc/silo/transaction.cc` の4通常 file であること、各 blob が元の C1・C2・C3 と一致することを確認済みである。ただし、これは結合後の実行結果を代用しない（`mk-c2p.log:4-49`、`s1-brief.md:5-8`）。

以下の `probe/` は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-mocc-v3-emitter/probe/` を指す。改修先は単位11の job dir に置く写しとし、既存の単位3の証拠を上書きしない（`run_probe.py:1-2`、`s1-brief.md:17-21`）。

| 段 | 改修箇所と判定 |
|---|---|
| C0 | `run_probe.py:27-35, 218-311, 559-582, 835-873`。引数を `--base-oid --c1p-oid --c3-oid --c2p-oid` にし、bundle 内で **4 commit の親を逐一照合**する。raw diff は C→C1' が header 2本、C1'→C3 が mocc 1本、C3→C2' が silo 1本、C→C2' が上記4本の `M 100644` に厳密一致させる。source の展開は C と C2' の2木で足りる。現行の bare clone、`info/attributes` による `-export-ignore/-export-subst` 無効化、`ls-tree` の全通常 file 集合と blob の照合は保持する。祖先 commit の source 木まで増やす必要はない。 |
| build | `run_probe.py:175-188, 559-581, 724-728`。`TARGETS` を `tpcc_silo.exe`・`ycsb_silo.exe`・`tpcc_mocc.exe`・`ycsb_mocc.exe` とし、**C TRACE=0、C2' TRACE=0、C2' TRACE=1 の3 build 木**で4 target を build する。`executable()` は target 名から `cc/silo` と `cc/mocc` を選ぶ。等長の source/build path と stock の configure option、policy に束縛した compiler は維持する。変異専用 TRACE=1 build は別の4本目。 |
| C1 | `run_probe.py:314-420, 583-606`。C/C2' の TRACE=0 compile database から同一の **12 source / 21 `(source,target)` entry** を引き、実 argv の `-E -P -dD` 完全展開と `-E` の include 入退場を比較する。負例は `tpcc.hh` の `trace.hh` include を `#if TRACE` の外へ出し、TPC-C 9 entry の include 活性が全件変わることを要求する。旧実績でもこの負例は完全展開にも差が出るため、「include 活性だけが検出した」とは主張しない（単位1・2 insight `README.md:76-80`）。 |
| C2 | `run_probe.py:607-621`。C2' TRACE=1 の同じ21 entry を compile database の実 flag、`-Werror` 付きで `-fsyntax-only` にかける。 |
| C3 | `run_probe.py:422-440, 691-704`。4 binary それぞれについて C/C2' の `nm`・`strings` の trace 名検出と正規化 `objdump` を比較する。既存判定どおり、binary 全体の SHA や `.text` bytes 一致は主張しない（単位3 insight `README.md:52-59`）。 |
| C4・C5 | `run_probe.py:442-556, 705-712`。`run_trace()` に `protocol` を明示し、C2' の TRACE=1 から silo と mocc の TPC-C B0、YCSB B0 を各1回、計4走行する。TPC-C は現行 `v3check.check()` の構造・witness・内容判定を各 protocol に適用し、結果名を `structure+witness+content pass` とする。YCSB は v2 の7 token C 行を確認し、`orchestrator/verify.py … --protocol silo|mocc --ccbench-root <C2' source> --json` と **protocol ごとの引数**で certified を要求する。`ycsb_check()` の mocc 固定は引数化する（`run_probe.py:498-538`）。 |
| C6・C7 | `run_probe.py:623-720, 754-834` と `selftest.py:202-294` を第2部の変異契約へ改める。C7 の `v3check.py --selftest` は従来どおり親が login で実行し、計算 job の C0〜C6 と別に結果を束縛する。`v3check.py:68-258` の frame 判定は protocol 非依存なので原則変更不要。 |

21 entry が C2' でも同じ集合になる根拠は、C..C2' が上記4 file のみで、CMake の protocol 宣言も `tpcc_*.cc` の直接 include も変わらないことにある。列挙は `cc/*/CMakeLists.txt` の `SOURCES/WORKLOADS` と直接 include から期待集合を作り、compile database の target 付き entry と厳密照合する現行方式を維持する。ただし、**この静的根拠だけで合格扱いにせず**、C と C2' の各 build 木で12/21と集合一致を再確認する（`run_probe.py:314-350`、C2' `cc/silo/tpcc_silo.cc:16`・`cc/mocc/tpcc_mocc.cc:13`、`mk-c2p.log:33-49`）。この列挙は直接 include に基づくため、後述の受理方式(a)で全間接 consumer TU を保証する列挙とは区別する。

B0 の**生 trace は4走行とも圧縮して job dir に保持**し、各 raw file の byte 数・SHA と圧縮 file の SHA を記録する。変異走行は従来どおり digest と判定だけ保持する（`run_probe.py:456-494, 540-555`）。既存の file size 上限は各 file 512 MiB、走行前の空き 2 GiB 確認である。単位1・2の B0 は TPC-C 約37 MB・YCSB 約83 MB、単位3の mocc TPC-C は約36 MBだったため、4走行の raw 合計は**推測で約240 MB**、圧縮後は数十 MB 程度を見込む。`/scr` の build 木と完全展開 log がより大きいので、開始時8 GiB・build後2 GiBの容量確認を維持し、4 target 化後の実使用を `capacity` に記録する（`run_probe.py:140-168, 559-581`、単位1・2 insight `README.md:72-73`、単位3 insight `README.md:60-61`）。

**所要は推測で1 job 8〜15分、約0.13〜0.25 node 時間。** 単位1・2の191秒と単位3の206秒を単純加算した397秒が目安だが、依存 build と21 entry の前処理を共用する一方、4 target の build・4 B0・結合変異が増える。既存の60分 wall 上限と55分の停止予約は残す。受入1回の既往単価約0.25 node 時間を加えても、現見積りは合計約0.4〜0.5 node 時間で、D2212 項4の2 node 時間線より下である。2本目の計算 job が必要になった場合は残費用を再見積りする（`run_probe.py:109-126`、`s1-brief.md:14-16`、D2212 項4）。

# 第2部 — 結合固有の変異候補

変異はすべて **C2' の実 bytes を基準**に、適用直前に anchor の出現数1を assert し、差分・各段結果・復元後 SHA を逐次保存する。build または走行失敗は `ERROR` とし、kill に数えない（`run_probe.py:623-687`）。下表の anchor は静的に読んだ C2' の該当行であり、実 spec 登録時に全候補の出現数と置換後の二次 anchor を改めて照合する。

| ID・基準 | 置換 anchor と期待 | 再 build |
|---|---|---|
| **H-set、C2'** | `include/tpcc.hh:60-63` の `izanagi_trace::set_tpcc_tx_type(get_tx_type(query.type));` を呼ばない形へ。silo・mocc の両 TPC-C が v2 C を出し、各々の先頭理由 `schema` を要求する。構造破損に続く `frame/witness/content` の派生理由は許す。単位1・2の M1 と変異自体は重なるが、**同じ header 1箇所が2 protocol とも赤になる**ことを新たに判定する（`v3check.py:180-202`）。 | `tpcc_silo`・`tpcc_mocc` |
| **H-count-D / H-count-M、C2' / D の上** | `include/tpcc.hh:118-124` の `#if !TRACE` と commit 後 quit 判定を、単位3の D1 と同じ診断 marker でまず発火させる。D は両 protocol で marker、各 worker 1000 C 以上、C=E=stdout commit 数の PASS。M は D の上で `#if !TRACE` を `#if 1` にし、両 protocol とも **理由集合 `{witness}` のみ**、rc 0、E=C>commit 数を要求する。単位1・2と3で各側の計数は済んでおり、結合では共有 header 1箇所の両側への伝播だけを確かめる（単位3 `spec/mutation-spec.json:7-30`、`run_probe.py:754-775`）。 | D・M ごとに両 TPC-C |
| **H-line、C2'** | `include/tpcc.hh:63` の一意な `#line 56` を削除。C1 の完全展開で **TPC-C 9 entry が差分、他12 entry は一致、全21 entry の include 活性は一致**を要求する。`ERR` の `__LINE__` を通る header 側の共通境界である。単位1・2の M5 と同じ編集だが、C2' 上の両 protocol を含む9 entry を再確認する（単位1・2 insight `README.md:95-96`）。 | 不要 |
| **S-table、C2'** | `cc/silo/transaction.cc:628-632` の一意な `emit_write_v3` 呼出しにある `get_storage(we.storage_)` を、表6だけ5へ写す式へ。silo TPC-C は理由集合 `{content-table}` のみ、**mocc TPC-C は PASS のまま**を要求する。silo の旧 M3 と機構は同じだが、結合後の非影響側を新たに判定する（`v3check.py:80-113`）。 | silo TPC-C。非影響側も変異 build 木の mocc TPC-C を走らせる |
| **M-type、C2'** | `cc/mocc/transaction.cc:1162-1165` の `read_set_.size(), write_set_.size(), 0, 0, izanagi_tx_type);` にある最終引数だけ、1と2を入れ替える式へ。mocc は `{content-txtype}` のみ、silo は PASS を要求する。単位3の M4m に非影響側の検査を足す（`v3check.py:83-94, 240-250`）。 | mocc TPC-C。非影響側も変異 build 木の silo TPC-C を走らせる |
| **S-line / M-line、各 C2'** | `cc/silo/transaction.cc:692` の一意な `#line 658`、および `cc/mocc/transaction.cc:1283` の一意な `#line 1187` を各別変異で削除。該当 transaction.cc の **4 entry だけ完全展開が差分**、他17 entry は一致、include 活性は21 entry とも一致を各々要求する。S-line は結合後の silo 側の論理行、M-line は単位3 M5m の非影響側まで見る（`run_probe.py:374-420, 777-794`）。 | 不要 |

「他方は緑」は、既存の B0 結果を参照するだけでは弱い。S-table と M-type では、変異 source を使う専用 build 木で両 TPC-C target を build・走行し、影響側の登録理由と非影響側の全 PASS を同じ変異 row に記録する。逐次変異の間に変更 file を pristine bytes へ戻し、影響 target を再 build してから次へ進む。header 変異では両 target が影響対象であり、片側だけの赤を kill と呼ばない（`run_probe.py:623-687, 754-799`）。YCSB は B0 の両 certified を C5 で担保する。C6 で毎回走らせる必要は示されない。

`load_spec()` は現行の「6 entry、mocc file または tpcc.hh、target は tpcc_mocc 固定」という契約を結合 spec に更新し、判定を `protocol → reasons/conditions` の組にする。`selftest.py:202-260` は「片側だけ赤」「共有 header で片側だけ赤」「4/17または9/12の entry 数不足」「派生理由を単一理由と誤認」の負例を追加する。`v3check.py:68-258` の判定理由そのものは維持する（`run_probe.py:809-833`）。

費用は**推測**で、前処理だけの line 変異は1件あたり21 entry × 2 mode × 2側の前処理で数十秒、実行変異は対象 target の再 build と2秒前後の B0 に加え verifier ではなく `v3check` の走査で数十秒を見込む。D/M は両 target を2回 build するため高めである。C6 全体は推測で3〜7分を第1部の8〜15分に含める。単位1・2・3の既存変異を全量再演する構成にはしない（単位1・2 insight `README.md:85-100`、単位3 insight `README.md:63-78`）。

# 第3部 — D297 の header 差分の受理方式案

## 3.1 現行検査器の拒否と保証

D297 の理由欄は、**「file 単体の前処理は consumer TU を代表しない」**、かつ **「`-E -P` は `#define` を残さない」**ため、header 内の macro 変更が正規化出力から消え得る、と明記する（`verbatim/D297.md:8-16`）。現行検査器は raw diff を列挙後、`.hh` 等を `_validate_diff()` で無条件に拒否するため、C→C2' は `include/tpcc.hh` で止まり、前処理比較には進まない。親の実走も rc=1 で同じ理由だった（`tools/check_trace0_preprocess_identity.py:127-199, 670-699`、`d297-C-to-C2p.stderr:1`、`d297-C-to-C2p.rc:1`、`orchestrator/tests/test_check_trace0_preprocess_identity.py:624-635`）。

なお、`source_digest._cpp_normalize()` は後年 **`-dD` を追加して**有効な `#define/#undef` を残す実装になっているが、include を除去し `-nostdinc` で file 単体を処理するため、header が consumer TU でどの macro 定義・順序・include 経路の下に展開されるかはなお分からない。D297 の上記二理由のうち、現在の実装で特に本質的なのは後者の consumer TU 不足であり、「`-dD` があるから header をそのまま許せる」とは言えない（`orchestrator/campaign/source_digest.py:1647-1708`、`tools/check_trace0_preprocess_identity.py:571-665`）。現行保証名は選定 macro context に限る正規化前処理出力と include 活性の一致であり、trace 完全除去の**必要条件の一つ**である（`tools/check_trace0_preprocess_identity.py:1-6`、D780 項1）。

## 3.2 Header を変えない実装はあるか

**別候補としてなら、構成上はある。ただし現 C2' の小変更をそのまま移す方法ではなく、C++ の実証が要る案である。** `tpcc.hh` の `run()` は `tx.begin()` 後に取引種別を知り、成功した `tx.commit()` の後に quit 判定と per-tx counter を持つ。`tpcc_silo.cc` と `tpcc_mocc.cc` は同じ `TPCCWorkload<Tuple,void>` を runner へ渡すだけなので、現状の protocol `transaction.cc` だけでは query.type や「commit 成功後、counter 前に return した」事実を完全には復元できない（C2' `include/tpcc.hh:47-126`、`cc/silo/tpcc_silo.cc:24-39`、`cc/mocc/tpcc_mocc.cc:21-36`、`common/runner.hh:169-193`）。

可能な形は、**各 `tpcc_<protocol>.cc` の `#if TRACE` に trace 専用 workload 型を置き、`TPCCWorkload::run()` の取引 dispatch と成功後計数を各側で実質的に複製して runner へ渡す**ことである。`tx.begin()` 直後にその `.cc` から取引種別を protocol の `transaction.cc` に外部 linkage の trace 専用 setter で伝え、後者の既存 `#if TRACE` 内に v3 helper と context を移す。YCSB は従来の v2 経路のままにする。TPC-C の成功後 quit 判定は複製した trace 専用 `run()` で counter の後へ移す。TRACE=0 では元の workload を使い、`.cc` の include 行を保ち、追加を `#if TRACE` 内に閉じ、必要な `#line` で論理行を戻せば、**D297 の現行受理集合に入る可能性がある**。これは build・実走未確認の**推測**であり、C2' と別 tree を作る作業になる（C2' `include/trace.hh:122-169`、`include/tpcc.hh:59-63, 110-124`、`cc/silo/transaction.cc:601-632`、`cc/mocc/transaction.cc:1159-1195`、`tools/check_trace0_preprocess_identity.py:178-199, 571-665`）。

費用と損失は大きい。取引 loop を2箇所へ複製し、将来の TPC-C 修正と同期させねばならず、TRACE=1 と TRACE=0 で workload 本体の経路が分かれる。現 C2' と単位1〜3の証拠は新候補の証拠へ移せない。これを今回の受理策として選ぶなら別 C++ author・レビュー・再計算が必要で、brief の「C++ 新規編集なし」を変更する。軽い代案である「W の署名から transaction.cc で取引種別を推定」は、`v3check.finish()` 自身が W の署名から種別を作って C の宣言値と照合するため、**宣言値と照合値が同じ W 由来になり `content-txtype` の検出が恒真化する**。これは採らない（`v3check.py:80-94, 240-250`）。

## 3.3 受理方式の比較

| 案 | 保証と現行 D297 に比べた不足 | 必要な裁定変更・費用・強い反対理由 |
|---|---|---|
| **(a) consumer TU を D297 検査器へ追加** | 変更 header を読む TU を旧新両 commit で列挙し、既存の genome × overlay の各 context、複数 compiler で TRACE=0 の**完全展開 `-E -P -dD` 相当**と include 活性を比較する。source 単体比較・raw diff の全件検査・0件拒否も維持する。これなら選定 TU/context/compiler に対する保証は現行より強い。一方、列挙に漏れた TU、実 admission command・全 link object・間接値を含む trace 完全除去は保証しない（D780 項2）。compile database 由来なら「選んだ stock configure で現れた TU」に閉じる。全 `.cc` を前処理して変更 header の活性 include 経路を旧新双方から引けば、repo の source 母集合に近づくが、生成 TU・別 option の活性枝・解決不能な間接 include には別途 fail-closed 規則が要る。直接 include の12/21をそのまま全 consumer と呼ぶのは過大である（`run_probe.py:314-350`、`source_digest.py:1567-1615, 1647-1715`）。 | **D297** の header 一律拒否を、列挙・文脈・件数・比較が揃った場合だけ許す規則へ改訂する。**D2207** の「検査器の include 規則を緩めない」は当時の mocc source の `<set>` 追加を許さない判断として保ち、今回の header 検証規則の新設は別件として明示する。**D2225 決定6** の「この候補は D297 合格を名乗らない」は、新検査器を実走して合格した場合に限る形へ改訂する。**D780 項2** の別防壁を単独設計しない線は維持し、今回の TU 比較を完全除去防壁と呼ばない。費用は推測で設計・実装・敵対変異・複数 compiler 実走に追加1〜2 wave、計算は数十分〜数時間の再見積りが必要。最も強い反対理由は、**C2' を通すために最後の防壁の受理集合を変更し、consumer 母集合の閉包証明を急ぐと新しい偽緑を作る**ことである。 |
| **(b) 今回の計算証拠だけで C2' を例外受理** | stock 1 context・GCC 11.4 の21 entry 完全展開/include 活性と、4 binary の正規化逆アセンブル、nm/strings、B0 を結合した**特定構成の経験的証拠**を得る。現行 D297 の genome × overlay と複数 compiler の比較を満たさず、将来の build 構成や全 TU も保証しない。binary 比較は nm/strings の限界と、正規化により捨てた bytes の限界を持つ（`run_probe.py:374-440`、D297 理由欄、D780 項1）。 | **D297** に C2' OID 固定の例外、または別名の限定保証で pin 承認を許す裁定が必要。**D2225 決定6** は「D297 合格とは呼ばない」を維持し、代替証拠による pin 受理だけを新裁定にする。**D2207** の source include 規則は変更しない。**D780 項2** を変えず、binary 比較を完全除去の別防壁と呼ばない。追加計算は結合 job 内でほぼ吸収できるが、裁定と pin wave は別に要る。最も強い反対理由は、D297 が pin 前進の最後の防壁として設けられた理由に対し、**ちょうど候補が赤になる時に検査対象の context・compiler を狭めて受理する**点である。 |
| **(c) Header を含む C2' を pin に入れない** | pin C は現行 D297 の既往検査結果のまま。D297 の保証を削らず、今回の結合確認は branch 上の研究証拠として保持する。ただし campaign pin の tpcc binary は v2 のままで、段1の silo・mocc v3 認定への最後の材料を運用へ渡せない（`s1-brief.md:3-8`、単位1・2 insight `README.md:15-20`）。 | **D297・D2207・D2225 決定6・D780 項2 の変更は不要。** 追加計算も不要。最も強い反対理由は、T-2854 の研究前進を branch の証拠段階で止め、段1の認定を campaign pin で実行できないことである。 |

## 3.4 推奨と諮問

**推奨は (a) の設計を別 wave で審査し、その完了までは (c) とする。** (b) は stock 1 context・GCC 1版の結果を D297 の複数 context・compiler の代わりに置くため、pin 前進の正しさ防壁としては不足が具体的である。(a) は受理集合を変えるが、変更 header が実際に読まれる consumer TU の展開を直接比較する設計なので、D297 が header を拒否した理由に正面から対応できる。今回の scope では検査器を編集せず、C2' の結合証拠と方式案まで作る（`tools/check_trace0_preprocess_identity.py:178-199`、`verbatim/D297.md:8-16`、`s1-brief.md:9-21`）。

ユーザーへ諮る問いは次の択一が明確である。

1. **推奨：(a) を別 wave で設計・実装・敵対確認してから C2' の pin 承認を審査する。** D297 と D2225 決定6の限定改訂を先に承認対象として示す。検査器が赤なら pin は進めない。
2. **(b)：今回の stock/GCC 11.4 の結合証拠に限り、D297 合格とは呼ばず C2' の例外受理を認める。** 失う context・compiler・consumer 母集合の保証を明記して裁定する。
3. **(c)：C2' は branch に保持し pin C を維持する。** 既裁定は変えず、TPC-C 段1の campaign 認定は保留する。
4. **別候補：header 無変更の再設計を許可する。** C++ 実装と結合証拠を作り直すため、現 wave の完了条件・費用を改める。

(a) と (b) はいずれも**既裁定の変更を要する**。header 無変更案は現行 D297 で通る可能性があるが、未実証の別候補であって C2' を受理する解ではない（D2225 決定6、D2227 項1、D2235 項1）。

## 総括

- **P1：賛成。** C→C1'→C3→C2' の親子・4 file・blob 照合は親の実測と一致する（`mk-c2p.log:4-49`）。
- **P2：条件付き賛成。** 3 build 木で4 target、21 entry 共通比較、両 protocol の B0 と YCSB verifier を実施する。C7 は親の自己試験である。直接 include からの21 entry は全 consumer TU の証明ではない（`run_probe.py:314-350, 559-720`）。
- **P3：賛成。** 共通 header 変異は両側の赤、protocol 変異は影響側の登録理由と非影響側の PASS を同一変異で要求する。旧変異の単なる再演を減らす（`run_probe.py:623-687, 754-833`）。
- **P4：修正して採用。** Header 無変更の別候補は構成上あり得るが、TPC-C `run()` の複製を要し、今回の C2' の受理策にはならない。推奨は consumer TU を扱う (a) の別 wave 審査、その間は pin C 維持である（C2' `include/tpcc.hh:47-126`、`tools/check_trace0_preprocess_identity.py:178-199`）。
- **P5：賛成。** 受理方式は防壁の設計択一なので、敵対相談と後段レビューを残す理由がある（`s1-brief.md:13`）。
- **P6：概ね賛成。** 1計算 job は推測8〜15分、受入を加えて約0.4〜0.5 node 時間。4 target と両側変異の実測で再見積りし、2 node 時間線を監視する（`s1-brief.md:14`、D2212 項4）。
- **P7：賛成。** superproject の実装面差分は作らず、probe・生証拠・insight を job dir と記録に束縛する。pin・gitlink・push はこの plan の作業対象ではない（`s1-brief.md:9, 15-21`）。
- **未確定：** C2' の結合 job の実測、共有変異の正確な所要、方式(a)の consumer 母集合と複数 compiler の閉包設計、そして C2' を pin に受理するユーザー裁定。現時点で D297 合格も TPC-C certified も主張しない（`d297-C-to-C2p.stderr:1`、単位3 insight `README.md:16-20`）。