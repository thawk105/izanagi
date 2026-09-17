## 総括

- **must-fix 8 件、nit 2 件**。静的検査のみ。checker・pytest は再実走していない。
- **P1 は提示候補として同意、来歴の補足が必要。P2・P3 に異議**。P4 は本レンズでは判定せず、P5 は未承認状態を維持する趣旨に同意。
- Clang の「比較前の検査不能」という分類に賛成。ただし「候補に問題がない」「Clang 一般を非対応」とする断定には反対。
- GCC 2 版は D297 の「複数 compiler」の文言を満たすと読めるが、**2 compiler family で合格したわけではない**。
- P3 の保証範囲は **8 点を訂正・補足**する。
- 最大の問題は、D986 の全面閉塞を現行実装から確認できないのに、限定説明だけで再承認の必要条件を充足したように扱うことである。

以下、`checker` は `tools/check_trace0_preprocess_identity.py`、`digest` は `orchestrator/campaign/source_digest.py`。候補ソースの行番号は **e9e477ca の tree** を指す。

## 1. 材料 (2) の合格の言い方

### F1：Clang の診断分類と、総合合格の扱いを分ける

**所見：**「今回の失敗は候補差分の不一致検出ではない」は正当。ただし親 brief P2・plan が定めた「3本とも成功」の条件は達成していない。

**根拠：** `checker:585` で old の `_cpp_normalize`、続いて new、最後に比較を行う。`digest:1704` の prefix 不一致は単一入力の正規化中の例外であり、old/new 比較による拒否ではない。`checker-run-facts.md` の空入力対 `int x;` probe は、候補を使わず同じ問題が起こることを支持する。

ただし射影には probe の全 argv・生出力がなく、記載された flag には実 checker の `BUILD_FLAGS`・context の `-D` 群が示されていない。したがって、

- **今回の診断が old/new 不一致由来である可能性**はコード経路から排除できる。
- **prefix 問題を解消すれば Clang でも old/new が一致するか**は未検証。
- 「checker が Clang を支持していない」は広すぎる。今回の版・Clang 14・入力条件で正規化できない、までである。

**分類：** 正しさ境界／**must-fix**。

**推奨是正：**

> GCC 11.4／12.3 の各実行は pass。Clang 14 の実行は環境 prefix 不一致で rc=1、比較未完了。候補差分の不一致を検出した結果ではないが、Clang での同一性は未確認。事前計画の「3本すべて成功」は未達。

これを「総合合格」へ黙って置換しない。

### F2：複数 compiler と計測 toolchain の関係を具体化する

**所見：** D297 は異なる family を要求していないため、異なる実行体である GCC 11.4／12.3 を「複数 compiler」と数えるのは妥当。ただし P2 の3本成功条件とは別問題。

**根拠：** `D297.md`、`checker-summary-gcc.txt`。計測 pilot は `tools/pegasus/mocc_trace_pilot.sh:1463` で計算ノードの `gcc`／`g++` を解決し、`:1588` 等でその絶対 path を CMake に渡す。`:1780` の checker も同じ `CXX_PATH` を使う。

login の `/usr/bin/g++ --version` に実関数 `tool_version_body()` を適用して SHA-256 を読み取り計算した結果は、

```text
b713e6ab62b67126b772f6b0a8d9751070f0d0315c7017291cb5dde67747b9c0
```

で、`mocc_trace_v1_policy.json:15` の期待値と一致した。`docs/decisions.md:46426` の D1487 は、既存 pilot receipt 37件と計算ノード calibration receipt もこの body digest だったと記録する。

**分類：** 整合・実効性／**must-fix**。

**推奨是正：**

> login GCC 11.4 の version-body digest は mocc pilot policy の期待値と一致する。これは compiler binary、依存 library、build flags、実行環境を含む admission toolchain 全体の同一性の証明ではない。今回比較が完了したのは GCC の2版である。

「計測 compiler は既定 g++-13」と書くのも、「login と計測環境は完全に別」と書くのも不正確。

### F3：16 context の分岐被覆を示す

**所見：** 今回の GCC report でも実効 define map は4種、正規化 digest は2種である。過去値の引用だけに留めず、今回の観測として示せる。一方、mocc の macro 空間全体の検査とは呼べない。

**根拠：** `checker-summary-gcc.txt`、`checker:558`、`digest:2116`。候補 `cc/mocc/transaction.cc` の条件付き指令を、同じ条件ごとに全出現箇所をまとめると次のとおり。

| 条件付き指令 | 候補での行番号 | 選定 context での状態 | 両側を検査したか |
|---|---|---|---|
| `#if TRACE` | 13, 23, 1134, 1165, 1174, 1181, 1197, 1203 | 常に0 | **否**。真側は除外 |
| `#if ADD_ANALYSIS` | 205, 238, 248, 420, 445, 480, 487, 494, 527, 534, 552, 586, 932, 1016, 1030, 1080, 1086 | 常に0 | **否**。1080・1086 は外側 BACK_OFF=0 では到達もしない |
| `#ifdef RWLOCK` | 264, 466, 573, 730, 748, 771, 838, 864, 883, 906, 957, 971, 1023, 1034, 1098 | 常に定義済み、値1 | **否**。定義済み側のみ |
| `#ifdef MQLOCK` | 268, 470, 577, 800, 845, 871, 892, 909, 961, 974, 1105 | 常に未定義扱い | **否**。未定義側のみ |
| `#if TEMPERATURE_RESET_OPT` | 925 | 常に1 | **否**。真側のみ |
| `#if BACK_OFF` | 1079, 1228 | 0／1 | **是** |

ここで「両側」は条件の真偽双方を意味する。候補にはこれら以外の `#if`／`#ifdef`、および `#elif`／`#else`／`#ifndef` はない。

`NO_WAIT_LOCKING_IN_VALIDATION`・`NO_WAIT_OF_TICTOC`・`WAL` は mocc の実供給 define map に残らず、このソースの条件指令にもない。これらによる genome の違いは検査件数を増やすが、mocc の異なる実効構成を増やさない。`GLOBAL_VALUE_DEFINE` もこのソースには条件指令がなく、include を展開しない今回の出力では digest を分けない。

**分類：** 正しさ境界／**must-fix**。

**推奨是正：** 上表を掲載し、「16件、実効4構成、出力2種」を併記する。固定された mocc 条件を勝手に新しい列挙軸へ追加する必要はないが、固定条件を隠して「mocc 全体を検証」と書かない。ヘッダ内部までこれらの軸が無関係だとは推論しない。

## 2. 保証範囲の逐語：P3

### F4：D986 全面閉塞の断定はできない

**所見：** plan の残余指摘は正しい。ただし「限界として記載した」だけでは D986 の要求を満たさない。

**根拠：** `digest:1290` は未認識 command、実行分岐、function、実行時値、展開順序差、32段制限を明記する。`:1381` は `SUPPLIES` だけを肯定し、`:1570` は解決不能な間接 CMake 値を拒否しないと明記する。対して `D986.md` は「限界の明記だけで残す」を明示的に却下している。

D723 が許したのは submodule coverage の限界であり、それだけから間接 CMake 値の非拒否まで許可されたとは読めない。

**分類：** 正しさ境界／**must-fix**。

**推奨是正：** P3 の「D986 で塞いだ3穴」を削除する。材料には **実装と射影された裁定の不整合が未解決**と記す。docs-only wave では修理も許容判断もしない。修理済み・後続裁定で変更済みとするなら、その別証拠が必要である。今回候補で実際に迂回が発生した、とまでは断定しない。

### F5：P3 は保証の機構と限界が不足している

**所見：** P3 に対する訂正・補足は以下の8点。

1. 「compiler 依存」に加え、**admission toolchain 全体の同一性を主張しない**。
2. header 差分は単に保証外なのではなく、**検出したら拒否する**。
3. include は展開しないため、ヘッダ内容を含む TU・binary 同一性は保証しない。
4. `-dD` が残すのは有効枝の define/undef。skipped 枝は出力されない。D297 当時の「`-E -P` は define を残さない」を現行実装説明へそのまま転記しない。
5. 環境 prefix は同じ argv の空入力から剥がし、builtin の条件評価は保持する。今回 Clang はこの境界で停止した。
6. 指令と include の相対位置、および `push_macro/pop_macro` の復元値に検査の限界がある。
7. 不在証明は old/new 別の commit tree **に加えて検査時 checkout** に依存する。D723 の submodule 限界と、F4 の CMake 残余を分ける。
8. mocc 特例は追加行の非活性・残余 include の対応と順序を要求する。policy 受理と生 marker bytes/hash の一致は別の証拠である。

**根拠：** `checker:180,253,421,458,493,632,664`、`digest:1503,1567,1647`、D297／D722／D723。

**分類：** 正しさ境界／**must-fix**。

**推奨是正：** 末尾の8行案へ差し替える。今回の report では policy 受理だけでなく生 marker 列も一致しているが、これは特例一般の保証と混同しない。

## 3. 材料 (1)：候補の確定

### F6：候補の来歴に、計装の性質と監査上限を加える

**所見：** e9e477ca を提示候補として固定する根拠はある。ただし「4 commit はユーザー作成」「provenance 監査済み」「通常の trace-hook だけ」という要約は不適切。

**根拠：** 指定区間の `git log --format=fuller`。4件とも author/committer は `thawk105 <thawk105@gmail.com>` だが、本文・trailer は異なる。

| commit | 内容・来歴 |
|---|---|
| ef9328a3 | correctness trace v2 hook。AI trailer なし。T-1506 archive はユーザーの commit と記録 |
| 058d0c4e | include コメントの移動。Codex author、Claude manager の trailer |
| ae6880f7 | TRACE-only payload watermark と別 witness stream。Codex author/reviewer、model・reasoning が unknown の manager |
| e9e477ca | witness 用標準ヘッダを除去し既存 include 面を利用。Codex author、unknown manager |

T-1943 archive は、submodule に provenance 導入 commit がなく **post-history 監査不能、commit 前 message 検査のみ通過**と明記する。

候補ソース `:75` の stamp は payload に書き込み、`:1165` 以降で TRACE=1 の更新処理から呼ばれる。D16 の verifier 計装と、D20 の **perf 帰属用診断計器**は目的が異なる。名前に「診断」があるだけで直ちに D20 違反とはいえないが、この witness を通常の受動ログと説明するのも誤り。

**分類：** 正しさ境界／**must-fix**。

**推奨是正：** 各 commit の本文・trailer、D673／T-1943 の既存手続き、限定 G2 witness の目的を記す。D18 の性能 variant 昇格を行う候補ではないことを説明する。TRACE=0 の一致から TRACE=1 の意味的無影響や正しさを導かない。unknown は補完しない。

### F7：「local」「未 push」「mocc 単独」の対象を限定する

**所見：** 追加差分としての mocc 単独は支持できる。共有依存や候補 tree 全体まで mocc 専用という意味にはできない。

**根拠：**

- old/new の `include/trace.hh` は同じ blob：`570e35e308e1104d53d43ea5556f54b3fb86922a`。
- 候補で直接 include するのは mocc `transaction.cc:15`、SI `:13`、Silo `:9`。
- この worktree の `origin` は GitHub ではなく primary の `/work/1/SFC/tanab/izanagi/.git/modules/external/ccbench`。
- この clone では候補は `remotes/origin/izanagi-t1943-mocc-g2-readfrom-witness` から到達する。
- T-1506／T-1943 archive は push 未実施と記録する。

**分類：** 整合・実効性／**nit**。

**推奨是正：**

> 「mocc 単独」は現 pin から候補までの追加変更範囲を指す。共有 trace ヘッダは既存版を使用し、Silo・SI の既存計装も tree に含む。候補はローカル保管された branch 先端であり、既存作業記録では GitHub へ未 push。この worktree の origin はローカル store である。

remote-tracking ref があることを GitHub 公開済みの証拠にしない。今回 GitHub の現在状態を照会したわけでもない。push は人間が行う境界を維持する。

## 4. 規律 2／規律 3 と未判定事項

### F8：必要条件の検査結果と、前進の裁定を冒頭から分離する

**所見：** plan は「判定しないこと」を材料1より前に置いており妥当。ただし F1・F4 が残る現在、「合格したので材料が揃った」と読める導入は避ける必要がある。

**根拠：** `s2-plan.md` §2・§4、D1603、D2114 項3。D1603 は検査そのものの健全性を先に要求する。D2114 は再承認を別途提示する手続きを維持している。

**分類：** 正しさ境界／**must-fix**。

**推奨是正：** 冒頭と材料2の結果直後に次を置く。

> 本資料は再承認の判断材料であり、pin 前進の承認・実行を意味しない。GCC 2版の限定検査結果、Clang の検査不能、D986 と現行実装の未解決点を併記する。mocc の正しさ、certified 化、変異探索の解禁、非 silo between-run 実測再開、性能優越は判定していない。検査結果に合わせて条件を選び直した性能上の結論も出していない。

今回、**checker の rc=1 自体は非該当ではない**。非該当なのは「old/new の比較不一致による拒否」である。

plan は拒否時の形を用意している。rc・stderr・stdout・report 有無を保存し、検査不能と比較不一致を区別する設計は妥当。空 stdout を拒否 report JSON として扱わず、今回にも適用する。

## 5. 親の実測値の一般化

### F9：実走した検査器の版を証拠へ束縛する

**所見：** 親 facts の日時は「21:4x」、検査器の版は改版説明のみ。plan が要求する実行索引を完成させる必要がある。

**根拠：** `checker-run-facts.md` と `s2-plan.md` の `runs.json` 案。今回読み取った現物は次のとおりで、作業ファイルの Git blob hash も HEAD 内の値と一致した。

| 対象 | 今回確認した値 |
|---|---|
| superproject HEAD | `38353207f719acb0871cfe3d9bbe3a02490282bb` |
| checker blob | `79dc9bbd229d23bf6a78f78b18d744eb417160d7` |
| source_digest blob | `0f062df910201f74c99ec526027b2db77e6f0c92` |

**分類：** 整合・実効性／**must-fix**。

**推奨是正：** 実走時刻、argv/cwd、host、HEAD、実行したファイルの hash、requested/resolved compiler、rc、stdout/stderr の完全 hash を保存する。上表は**今回の静的確認値**であり、実走時に同じ bytes だったことは親の記録と照合して確定する。

不在証明が checkout に依存するため、submodule checkout HEAD と初期化状態も付記する。report だけではこの依存を再現できない。

### F10：wall・bytes・digest は用途を分ける

**所見：** wall 32.7／45.5／49.5秒を compiler 性能比較、計測コストの一般値、軽量性の証明として使わない。

**根拠：** `checker-run-facts.md`、`checker-summary-gcc.txt`。report は両 GCC とも33,036 bytes だが hash は異なる一方、正規化 digest 集合は同じ。

**分類：** 整合・実効性／**nit**。

**推奨是正：**

- wall は単回の実行記録として索引に残し、本文の結論には不要。
- bytes と完全 SHA-256 は保存物の照合用。省略 digest を証拠キーにしない。
- report hash の違いは比較対象プログラムの違いを意味しない。
- 正規化 digest の一致も compiler binary・実ビルドの一致を意味しない。
- 本文で必要なのは各 rc、比較完了件数、実効構成数、固定条件、include policy、検査不能理由である。

## 訂正版の保証範囲 (逐語案)

- 本検査の保証名は「選定した macro context における TRACE=0 正規化 preprocess 出力の同一性、および include 活性の同一性」であり、対象は `511c9538e4e8efa54b45cda62e72389ed3b706ec` から `e9e477ca1b55348ab4530de0b1cf663ce4555290` への端点差分である。祖先関係と差分 path の厳密一致を確認する。
- GCC 11.4／12.3 は各16件で pass。16件は SILO_SPACE 8 genome ×2 overlay で、今回の mocc 実効 define map は4種、出力 digest は2種だった。mocc の全 macro 空間を列挙した結果ではない。
- 正規化は include を除去し、builtin を保持して `-E -P -dD -nostdinc -Werror=undef` と所定 flags・defines を用いる。有効枝の define/undef は残すが skipped 枝は出力せず、同じ argv の空入力出力を環境 prefix として除去する。
- include 活性は marker の対応と順序で別途検査する。mocc の単純な `#if TRACE` 初期枝内の exact trace.hh include 1行だけは、追加 marker の非活性と既存列の対応を条件に許す。policy 受理と生 bytes/hash 一致は区別する。
- header 差分、未対応の差分形・include 構文、比較0件・件数不足は拒否する。header を展開した翻訳単位、指令と include の相対位置、pragma push_macro/pop_macro の復元値、binary 同一性、trace の完全除去は保証しない。
- 不在 macro は old/new 別の commit tree と検査時 checkout の認識対象 text で再検査する。submodule 内部は不在証明の保証対象外であり、未解決 CMake 間接値も現行実装では拒否されない。D986 全面閉塞およびその要件充足は主張しない。
- 結果は使用 compiler と選定 context に依存する。Clang 14 は環境 prefix 不一致で比較未完了だった。login GCC 11.4 の version-body digest は mocc pilot policy と一致するが、admission toolchain 全体の同一性は主張しない。
- 本結果は規律1の限定検査材料であり、規律2の正しさ検査や性能評価を代替しない。pin 前進、旧証拠の張替え、mocc certified 化、変異探索解禁、非 silo between-run 実測再開の承認を意味しない。
