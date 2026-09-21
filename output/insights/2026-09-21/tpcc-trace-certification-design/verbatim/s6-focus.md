判定: GO

| 所見番号 | 判定 | 根拠（本文の §／照合した一次資料の path:line） |
|---|---|---|
| M1 | closed | §4.4 は si の最終時刻だけによる判定を撤回し、読取り時の Q を優先した。`external/ccbench/cc/si/transaction.cc:68-73` の snapshot 採番、`:153-158` の status・cstamp 条件、`:509-519` の公開処理と整合する。 |
| M2 | closed | **refuted として閉じる。攻撃は成立しなかった。** §4.4・§4.5・§11 は不在版が一意の場合と選言の場合を区別した。下記の履歴で検討。操作の根拠は `external/ccbench/cc/silo/transaction.cc:299-318`、`:663-684`。 |
| M3 | closed | §4.4・§6.2 は境界を走査終了へ変更した。反例の順序では `scan終了 < 挿入直前` が成立する。物理走査は `external/ccbench/cc/silo/transaction.cc:299-302`、node 検証は別段の `:477-485`。実 CC と合成 fixture の区別も記載された。 |
| M4 | closed | §4.4 の契約 (a)〜(e) と §7.1 単位6に、保存先・対応・順序・保護・成功／失敗／abort の区別を追加。既存採番が relaxed なのは `external/ccbench/include/trace.hh:41-46`。wrapper は `external/ccbench/include/masstree_wrapper.hh:194-208`、依存 pin は `external/ccbench/cmake/ThirdParty.cmake:35-45`。走査保証は未証明として認定を止める条件が残る。**設計文書としての閉鎖で、実装完了ではない。** |
| M5 | closed | §4.7 の候補数と辺数を再計算して一致。宛先集合による重複除去は `orchestrator/verifier/dsg.py:641-643`。比較実績の 594,786,279 辺・896 秒は `output/insights/2026-09-20/verifier-capacity/README.md:47` と一致する。 |
| S6 | closed | §5.1・§5.2 が冷経路と高温／RLL 経路を分離。`external/ccbench/cc/mocc/transaction.cc:280-309` では lock 成功後に `needVerification=false`、`:341-364` では absent 検査が冷経路内にある。段3の指摘 `output/insights/2026-09-21/tpcc-trace-certification-design/verbatim/s3-consult-A.md:106` が反映された。 |
| S7 | closed | §1・§7.4・§8項5は同一タスクの合計 **2 node 時間以上なら確認、未満は不要**。`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-09-21-vldb-direction-verdicts.md:20-22` と整合する。 |
| N8 | closed | §3.4・§4.4・§5.1・§5.2の引用を照合。si の read-set 消去は `external/ccbench/cc/si/transaction.cc:361-365`、mocc の明示 abort は `external/ccbench/cc/mocc/transaction.cc:1173-1182`。silo の P emitter は `external/ccbench/cc/silo/transaction.cc:432` の1箇所、X は `:629`・`:653`・`:674` の3箇所。§7.4の throughput 記述も検索範囲を限定した。 |

静的検査のみ。build・binary 実行・pytest・性能測定は行っていない。

**M2 への攻撃**

不在版が一つの場合について、取りこぼしを別の点依存で拘束する履歴を構成した。

- **挿入のみ:** 初期 `k=unborn, y=y₀`。I が `k₁` を挿入し `y₁` を書いて commit。S の壊れた scan が k を落とし、その後 `y₁` を読む。辺は不在から `S→I`、y の読取りから `I→S` となり、cycle を検出する。y の依存を除けば直列順 `S,I` が結果を説明する。実時間では I が先でも、今回の認定対象への反例にはならない。
- **初期存在＋削除:** 初期 `k=k₀, y=y₀`。S が削除前の k を取りこぼして `y₀` を読み、D が k を削除して `y₁` を書く。版列は `k₀<k_D(dead)`、`y₀<y_D`。不在から `D→S`、y の旧版読みから `S→D` が生じ、cycle を検出する。y の依存を除けば直列順 `D,S` が成立する。

いずれも、非直列化可能なのに非巡回となる反例にはならなかった。不在版が一意という前提の下では、親の論拠を再開する根拠は得られなかった。

**派生値・量化の照合**

| 対象 | 再計算・コード照合の結果 |
|---|---|
| `10 × N_D(N_D−1)/2`、`N_D=12,000` | **719,940,000 候補** |
| `N_D(N_D−1)/2` | **71,994,000 辺**。全10 districtで同じ取引対が生じるという例の条件付き |
| 比較実績 | **594,786,279 辺＝5.94786279億辺、896秒**。本文の丸めと一致。今回の再測定ではない |
| si snapshot | 各 thread の `lastcstamp` を読みながら最大を取り、最後に **+1** |
| si `read_internal` | committed／deleted かつ `cstamp ≤ txid_` が選択条件。等号だけでは公開状態を保証しない |
| 既存 trace 採番 | `memory_order_relaxed`。新しい物理順序の証拠とは区別されている |
| mocc absent | 冷経路の検査を高温／RLL 経路へ全称化していない |
| silo emitter | X **3箇所**、P **1箇所** |

**訂正による回帰**

新たな所見として成立する回帰は見つからなかった。

走査区間への変更は、§4.4、§6.2の反例、§7.1単位6、§8項6で整合する。反例では挿入前番号が走査終了後なので `S→I` を導ける。一方、物理候補の版読取りは Masstree 呼出し後にも行われるため、その観測は Q の領分となる。本文は Q を優先し、木からの除去番号を tombstone 観測の証拠としないことで、この区別を維持している。

§6.2の実 CC における期待結果は、§4.4・§7.1に記された計装契約と走査保証の成立を前提とする。未証明の現在に G2 検出を実証済みとしたものではない。

§8の親の決定への書換えも、項5をユーザー確認ラインとして明示的に分離しており、計算投入の一括承認には変わっていない。

## 総括

前回8所見は、M2の反証不成立による閉鎖を含め、docs-only の焦点再レビューとして閉じてよい。GO は訂正文に対する判定である。Masstree の走査保証、通し番号の実装契約、実 CC の control 実証は、本文どおり後続実装の完了条件として残る。