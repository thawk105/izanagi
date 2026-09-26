## 所見

### 1. (a)(b) の「失う保証」は、context と compiler の性質を言い分ける必要がある

**重大度: must-fix｜成立。** plan は (b) が「D297 の複数 context・compiler」を失うことを主な反対理由にする。しかし検査器の 16 context は **silo の8 genome × `GLOBAL_VALUE_DEFINE` の有無2通り**であり、実 compile command の16通りではない。`GLOBAL_VALUE_DEFINE` は実際に `tpcc_silo.cc` と `tpcc_mocc.cc` の冒頭で定義されるので、TPC-C のその2 TU では「無」の側は探索用の文脈である。さらに `_compare_file()` は登録された `cc/mocc/transaction.cc` には mocc 所有の define を選ぶが、`tpcc_mocc.cc` は登録対象外であり、同じ方式を consumer TU に延ばしても mocc の実 define を自動では選べない。[checker:558–584](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-unit11-combined/tools/check_trace0_preprocess_identity.py:558)、[source_digest:344–351](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-unit11-combined/orchestrator/campaign/source_digest.py:344)、[source_digest:2116–2128](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-unit11-combined/orchestrator/campaign/source_digest.py:2116)、[genome:106–116](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-unit11-combined/orchestrator/campaign/genome.py:106)、C2' `cc/mocc/tpcc_mocc.cc:1–13`、`cc/silo/tpcc_silo.cc:1–16`。

一方、(b) の stock 1 context は silo の有効 genome 全域を検査しない。したがって差は名目だけではない。ただし、**16対1を「実 TPC-C build の16構成対1構成」と読ませるのは過大**である。また検査器は `--cxx` を一つ受け取る設計で、複数 compiler は別々の実走を揃える運用上の要求である。[checker:728–749](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-unit11-combined/tools/check_trace0_preprocess_identity.py:728)、[D297:20–23](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/verbatim/D297.md:20)、[plan:60–68](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/out/s2-plan.md:60)。

**代替案:** (a) の提案では TU ごとに実際の protocol と compile define の対応を確定する条件を明記する。(b) の不足は「silo の他 genome と追加 compiler で未比較」「列挙した21 entry の外は未比較」と正確に書く。

### 2. D297 の `#define` 理由を、現在も同じ強さで掲げられない

**重大度: should｜成立。** D297 の制定理由にある「`-E -P` は `#define` を残さない」は、現行 `_cpp_normalize()` の **`-E -P -dD`** にはそのまま当てはまらない。有効枝の `#define/#undef` は出力へ残す実装である。ただし include を除去して file 単体で処理するので、consumer TU の先行定義、include 順、展開結果は依然として分からない。plan 3.1 はこの後者を本質と認めており、結論自体は正しいが、前者を現行拒否の独立した理由のように引用する冒頭は弱い。[D297:17–19](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/verbatim/D297.md:17)、[source_digest:1666–1675](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-unit11-combined/orchestrator/campaign/source_digest.py:1666)、[source_digest:1686–1709](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-unit11-combined/orchestrator/campaign/source_digest.py:1686)、[plan:44–48](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/out/s2-plan.md:44)。

**代替案:** 「制定時の理由2は `-dD` で部分的に解消した。現行の header 拒否を支える未解決点は consumer TU の文脈と列挙である」とする。

### 3. header 無変更の別候補は D297 を通る可能性があるが、「既裁定を変えずに済む」は言い過ぎ

**重大度: must-fix｜成立。** `.cc` だけを変更し、既存 include 行を保ち、TRACE=0 の正規化出力と include marker 活性を一致させれば、検査器の現行受理集合に入る構成はある。例外関数が許す追加 include は `cc/mocc/transaction.cc` の `trace.hh` 一行だけであり、`tpcc_*.cc` に include を足す案なら拒否される。`#line` による `__LINE__` の復元も必要になり得る。**可能性として述べた plan の判断は妥当**で、実走合格を断言していない点も正しい。[checker:180–201](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-unit11-combined/tools/check_trace0_preprocess_identity.py:180)、[checker:421–455](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-unit11-combined/tools/check_trace0_preprocess_identity.py:421)、[checker:539–550](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-unit11-combined/tools/check_trace0_preprocess_identity.py:539)、[plan:50–56](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/out/s2-plan.md:50)。

しかし D2225 は `tpcc.hh` での setter、同 header での quit 判定変更、header を含む C1/C2 構成を**実装方式として決定**している。D2230 も C1' を使う mocc 系列を決めている。別候補を pin に採るなら、D297 の受理規則を変えずに済んでも、少なくとも**D2225 の決定2・3・5と D2230 の系列決定との関係を再裁定する**必要がある。[D2225:3–9](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/verbatim/D2225.md:3)、[D2230:3–6](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/verbatim/D2230.md:3)、[plan:75–77](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/out/s2-plan.md:75)。

さらに TRACE=1 だけで workload の取引 loop を複製する設計は、TRACE=0 の除去という規律1の一面を満たし得ても、correctness trace が**性能 build と同じ workload 経路を観測するか**という検証上の新しい負担を作る。元の `run()` には query 生成、abort/retry、commit、quit 判定、per-tx 計数が一続きであり、複製がずれる余地は具体的である。C2' `include/tpcc.hh:47–126`、`common/runner.hh:183–194`。[plan:52–56](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/out/s2-plan.md:52)。

**代替案:** 別候補を第5の択として残すなら「D297 は現行のまま通る可能性があるが、D2225/D2230 の方式・系列の再裁定と、両 workload 経路の対応確認が必要」と記す。

### 4. (a)(b) に要る裁定の同定は一部過大、一部不足

**重大度: should｜成立。** C2' の header 差分を現行 D297 が拒否すること、(a) の header 許可には D297 の改訂が要ること、(b) の代替証拠による pin 受理には新裁定が要ることは正しい。[checker:194–199](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-unit11-combined/tools/check_trace0_preprocess_identity.py:194)、[実測 stderr:1](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/d297-C-to-C2p.stderr:1)、[request:3–5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/request.md:3)。

ただし D2225 決定6は「この候補は**現行検査器の D297 合格と呼ばない**」「pin 前進時の受理方法は未決定」と明記する。将来の改訂検査器が合格したとき、過去の証拠を D297 合格へ読み替えない限り、**決定6の改訂が必須とは限らない**。また D2207 の「受理集合を変えない」は mocc X/P 計装候補で `<set>` include を避ける裁定である。(a) はその方向と衝突するが、D2207 を無条件に改訂対象と断定するより、射程を明示して新しい判断を求めるべきである。[D2225:9,14,21](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/verbatim/D2225.md:9)、[D2207:1–4,9–18](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/verbatim/D2207.md:1)、[plan:62–63,72–77](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/out/s2-plan.md:62)。

逆に別候補を選ぶ場合の D2225 決定2・3・5、D2230 の扱いが問いから抜ける。D780 項2について plan は別防壁を単独設計しないと明記しており、**この点への攻撃は不成立**。[D780:5–9](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/verbatim/D780.md:5)、[plan:62–64](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/out/s2-plan.md:62)。

**代替案:** 裁定欄を案別に絞る。(a) は D297 の受理規則変更を必須、D2207 との整合を説明、D2225 決定6は過去の名乗りを維持。(b) は D297 合格ではない限定的な pin 例外の新裁定。(別候補) は D297 変更不要の可能性と D2225/D2230 の方式変更を並記する。

### 5. 推奨は安全側だが、費用と選択の提示が誘導的

**重大度: should｜成立。** C2' をこの証拠だけで pin に進めない判断には賛成する。D297 は pin 前進の「最後の防壁」とされ、C2' はそこで実際に拒否された。(b) の21 entry と binary 比較は有益でも、その合格を現行 D297 の合格と同一視できない。[D297:9–12](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/verbatim/D297.md:9)、[実測 stderr:1](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/d297-C-to-C2p.stderr:1)。

ただし「(a) 追加1〜2 wave」は consumer TU の母集合、間接 include、protocol 別の実 define、複数 compiler の扱いが未設計の段階では**根拠ある上限ではない**。本依頼は検査器拡張も代替証拠受理も委任しておらず、求めているのは方式案と諮問である。四択の先頭で (a) の実装・敵対確認を「推奨」とすると、方式を審査する裁定と実装着手の委任が一つの選択に束ねられる。[request:3–9](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/request.md:3)、[plan:62,66–75](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/out/s2-plan.md:62)。

(b) を推奨しない理由は単なる検査形式への固執ではない。stock 一構成の経験的証拠では、他の有効 genome と compiler で TRACE=0 の trace 除去を検査していない。ただし所見1のとおり、その差を「実 build の16対1」と誇張しないことが条件である。

**代替案:** 今回の結論は「C2' は branch 証拠として保持し、pin C を維持」に留める。ユーザーには次段階として、**(i) 現行 D297 を保つ別候補の検討、(ii) D297 の header 受理規則の設計審査、(iii) C2' の限定例外受理**のどれを検討するか問う。設計審査と実装の委任は分け、1〜2 wave は暫定見積りと明示する。

### 6. 親 brief の実測値と拒否の一般化

**重大度: nit｜一部成立。** `mk-c2p.log` の親子関係、C..C2' の4 file、blob 一致は plan と整合する。D297 の stderr も `include/tpcc.hh` での拒否を裏付ける。**この実測値への攻撃は不成立**。[mk-c2p.log:4–30](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/mk-c2p.log:4)、[実測 stderr:1](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/d297-C-to-C2p.stderr:1)。

一方、brief の「`_validate_diff()` で止まる」は正しいが、そこから得られるのは**C2' が現行検査器の受理集合外という結果**だけである。結合後の TRACE=0 同一性が偽と実測されたわけではない。plan は概ねこの区別を守っている。[brief:6,13](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/s1-brief.md:6)、[checker:673–680](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-unit11-combined/tools/check_trace0_preprocess_identity.py:673)。

## 総括

- **成立した攻撃:** 16 context を実 TPC-C 構成の16通りと読む説明、現行 `-dD` 下での古い `#define` 理由の扱い、header 無変更案の既裁定変更漏れ、(a) の費用と委任を束ねた問い。
- **不成立の攻撃:** C2' の OID・4 file・blob 照合、現行 D297 が header で拒否する事実、`.cc` のみの別候補が現行受理集合に入り得るという限定的な主張、D780 項2との整合。
- **推奨への賛否:** **C2' の pin 保留には賛成。** (a) を最有力の設計検討先とすることは可能だが、実装まで含めた1〜2 wave の推奨は現時点で強すぎる。
- **ユーザーへの問いの修正案:** 「結合証拠を得た後も C2' は D297 で拒否される。pin C を維持した上で、次に①現行 D297 を保つ別候補、②header を扱う D297 規則の設計審査、③C2' に限る代替証拠受理、のどれを検討するか。②の実装と③の受理は今回の依頼には含まれず、別途裁定を要する。」

以上は指定資料とコードの静的検査による。新候補の build・検査器実走は行っていない。