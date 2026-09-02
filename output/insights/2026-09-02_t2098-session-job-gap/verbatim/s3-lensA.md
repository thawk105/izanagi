## 所見一覧

| ID | severity | 所見 | 放置時の影響 |
|---|---|---|---|
| F1 | BLOCKER | `median(S_s-J_s)` は `338-263=75` の分解ではなく、別に定義した paired estimand である。 | 値: 見出し値が 75 秒から別分布の中央値へ変わる。受理集合: 元の受入受理集合は不変だが解析集合は別物になる。参照: D1320 の 75 秒へ誤って接続される。 |
| F2 | BLOCKER | `max_j(E_j-C_j)` は Created がずれる場合の session critical path や scheduler makespan ではない。 | 値: dispatch skew を残差へ混入させ、中央値と4項内訳を変える。受理集合: 不変。参照: 「session が待つ最大 shard」という説明が成立しない。 |
| F3 | MAJOR | D1320 の session 集計式と対象 cohort が未確定のまま、743 directory の別集合を解析する。 | 値: 338、263、75および分母を再現できない可能性がある。受理集合: `n_paired` が D1320 の549 sessionと異なる。参照: D1320 再現という位置付けが失効する。 |
| F4 | MAJOR | checkout、期間、hostname、queue 状態を識別せず、743 session の混合集団を一つの分布にする。 | 値: 構成比で中央値や裾が変わる。受理集合: scan 時点の混合集団へ依存する。参照: 単一の「受入の姿」への一般化が不正になる。 |
| F5 | MAJOR | 独立検査の多くは自己整合確認または閾値のない診断で、主 estimand を反証できない。 | 値: parser、選択、時計モデルの系統誤りが値に残りうる。受理集合: 誤った除外集合を検出できない。参照: 「独立検査済み」とは記載できない。 |
| F6 | MAJOR | sample oracle は shard-0 の accounting しか与えられておらず、shard-0 が `argmax(E-C)` だと検証できない。 | 値: 15秒の算術だけが通り、critical shard 選択の誤りを見逃す。受理集合: 不変。参照: parser の review oracle として過大評価される。 |
| F7 | MAJOR | `compute-visible`、report、junit、login marker の mtime を単一の「Lustre clock」と扱える根拠がない。 | 値: offset/drift 範囲と collection 分類が変わりうる。受理集合: raw 主集合は不変だが auxiliary 有効集合が変わる。参照: 「同一時計で証明」の主張が成立しない。 |
| F8 | MAJOR | brief の P3 は未計測の `Ended→handled` を poll、収集、merge へ先に帰属させている。 | 値: raw 値は不変だが原因別内訳が捏造されうる。受理集合: 不変。参照: D1320 の却下事項に逆行する。 |
| F9 | MAJOR | 固定行帯、汎用 CLI、expected-count gate、構造化プロトコル、20超の counter は本題の実測を越える。 | 値: 主値は変わらなくても成果物面が膨張する。受理集合: 不変。参照: 「gate・検査・台帳を追加しない」という scope 宣言と衝突する。 |
| F10 | MINOR | 入力 root と `--output-dir` の非重複は親の運用に依存し、script 契約では固定されていない。 | 値: 誤指定時は inventory 自体が変わりうる。受理集合: 受入側は不変だが解析集合が汚染される。参照: read-only 解析という主張が条件付きになる。 |
| F11 | MINOR | 同率時の shard 番号最小という canonical 化と quantile の方式が、要約値の規約として不足している。 | 値: 4項の要約と p25、p75、p90 が実装選択で変わりうる。受理集合: 不変。参照: tie 候補を全保存しても単一内訳の代表性は得られない。 |

## estimand への異議

D1320 の 75 秒は、549 session の中央値と1297 job の中央値との差である。観測単位も母集合も異なるため、個々の session に対応する残差ではない。したがって「75秒を分解する」という元の問いは量として成立しない。

一方、プランの

```text
R_s = [max(H)-min(F)] - max_j(E_j-C_j)
```

は量として計算できるが、「session envelope が最長 job duration を何秒上回るか」という新しい問いである。`median(R_s)` が 75 秒と一致する必要はなく、一致しても偶然である。成果物は「75秒の分解」ではなく、新 estimand の測定として明示的に再定義しなければならない。

さらに、session が待つ対象は最長 duration の job とは限らない。Created がずれると、短いが遅く開始した job が最後に終わりうる。session の scheduler envelope を問うなら候補は `max(E)-min(C)`、最長単体 job との差を問うなら現行 `max(E-C)` だが、両者は別の estimand である。現行プランは後者を選びながら前者の critical-path 意味を与えている。

`S_s` も D1320 の実式が確定していない。`max(H)-min(F)` と `max(H-F)` を併記するだけでは、どちらが338秒の出所だったかは確定しない。D1320 の cohort と集計式を固定できない限り、「再現」ではなく「別定義との比較」に留まる。

## 独立検査の恒真性

検査の性質は次のように分かれる。

| 検査 | 独立性と落ちる条件 |
|---|---|
| 4項 closure | 定義を展開した恒等式。算術実装が壊れた場合だけ落ち、estimand や原因帰属は検査しない。 |
| coverage partition | 同じ inventory から行と counter を作る限り自己整合確認。重複出力などの実装誤りでは落ちるが、母集合の選び間違いでは落ちない。 |
| critical shard 一致率 | 観測値であり合否条件がない。不一致率が何％でも script は成功する。 |
| receipt 比較 | 別出所なので比較自体は独立だが、不一致を受容する設計のため主値の検査にはならない。 |
| collection 分類件数 | 測定結果であって検査ではない。期待値または反証条件がない。 |
| NQSV 時刻順序 | `Created <= Started <= Ended` は明確に落ちうる。ただし accounting 内部だけの検査で、paired estimand は検証しない。 |
| 時計因果範囲 | lower bound が upper bound を超えれば落ちうる。ただし marker の時計 provenance と因果順序が正しいことを別途前提にしている。 |
| D1320 照合 | exact cohort と選択規則が同じ場合だけ外部検査になる。現状は不一致が parser 誤りか cohort 差かを識別できない。 |
| sample oracle | 442、457、15秒の算術は検査できるが、他2 shard の accounting がないため `b=0` の選択は検査できない。 |

従って、現状の結果から「独立検査を通った」と総括することはできない。主 estimand に直接効く独立検査は、exact cohort を固定した D1320 再現と、全3 shard の accounting を備えた sample oracle に限って成立しうる。

## 規律 2 との関係

standalone の事後解析であり、受入コードへ接続せず、新規 session も投入しないため、計画どおりなら受入の判定・排他・選択・受理集合を変える経路は見当たらない。解析上の `primary_included_sessions` は解析分母であって、既存受入の受理集合ではない。

入力側を `stat` と read-only open に限定し、lock や mtime 更新を行う処理も記載されていない。この点は規律 2 と整合する。

ただし安全性は `--output-dir` が入力 root 外であることに依存する。brief にある `output/insights/...` を実際に使う限り問題ないが、script 契約単体では対象 directory 配下への出力を排除していない。対象 root 外への固定を実行条件として扱わなければ、read-only という主張は条件付きになる。

## 射程の宣言

この設計から言えるのは、次の限定された事後分布だけである。

「2026-09-02 の scan 時に指定 root 直下に存在し、完全性条件を満たした `n_paired` session について、保存された mtime と NQSV 表示時刻から計算した retrospective distribution」

以下へは一般化できない。

- D1320 の exact 549-session cohort
- 特定 checkout の受入
- 特定 hostname または機体群
- 特定月または queue 状態
- 現在または典型的な受入所要
- clock 補正後の物理的な原因別遅延

743 session の混合中央値は archive の構成比に依存する。checkout、期間、hostname、queue 状態を識別しないまま「受入の中央値」や「主項」と呼ぶのは不可である。追加の一般化分析を行わないなら、混合集団であることと一般化不能を成果物本文で明記すれば足りる。

## 親 brief 自身の欠陥

親 brief は scope 冒頭で「75秒を分解する」と宣言しながら、P1 では75秒が非対差であると正しく認めている。この二つは両立しない。P1 を採るなら本題そのものを paired estimand の新規測定へ改題する必要がある。

P1 の「対で引くべき量は session 合計 − max shard job span」という結論も未証明である。これは最長 duration との差であり、Created がずれた session の scheduler critical path ではない。

P3 はさらに強く、実測前から主項を `confirm→Created` と `Ended→handled` に決め、後者へ poll、収集、merge という名前を与えている。保存測点はこれらを分離せず、plan 自身も parent merge が handled 後なら主 estimand に含まれないと認めている。P3 は仮説一覧から原因内訳へ昇格させてはならない。

P4 は scheduler clock と「Lustre clock」の二時計モデルに単純化しているが、各 mtime の writer と時計源を固定していない。特に compute 側 artifact と login 側 marker を同一時計とみなす箇所は、物理範囲および collection の off-path 判定を支えられない。

一方、D1420 の51.7秒を job/session 層へ転用しないこと、測点のない poll・収集・merge を未分解のまま残すこと、新規走行をしないことは正しい。

## 総括

現 plan はそのまま author 段へ進めない。BLOCKER は二点である。

- 75秒の分解ではなく別の paired estimand を測っている。
- 最長 job duration を session critical path と同一視している。

まず「最長 job との差」を測るのか、「scheduler envelope 外の時間」を測るのかを決め、75秒とは別の問いだと明記する必要がある。その上で D1320 の exact cohort と session 式を確定できない場合は、D1320 の分解・再現という参照を外すべきである。

独立検査は、恒等式、自己整合確認、閾値のない診断、実際に反証可能な照合を区別する必要がある。raw 境界差以外を原因へ帰属させず、結果の射程を scan 時点の混合集団に限定すれば、D1320 と D1420 の測定規律には戻せる。pytest は制約どおり実走しておらず、緑は主張しない。