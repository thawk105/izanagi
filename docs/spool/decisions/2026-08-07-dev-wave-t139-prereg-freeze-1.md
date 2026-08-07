---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-07
wave: dev-wave-t139-prereg-freeze
seq: 1
---

## {{D:t139-paired-prereg-gate}}. paired cluster 例外を T-139 の RF study に限定し、事前登録 core を commit/blob 束縛で凍結して投入順序 gate を置く

**背景:** D19 は、通常の variant/baseline 比較を同一セッションで測らないことを前提に、採否の floor を
between-run に置いた。D134 決定 (3) は、T-139 の回復率 (RF) study が paired 設計を採るなら
D19 と roadmap §3.6(3') の例外新設として扱い、限定を同じ変更単位で行うことを要求した。決定 (4) は
pairing 不成立時の自動 unpaired fallback を禁じた。この履行が未了のまま、roadmap は
「variant と baseline は決して同一セッションで測らない」と書き続けていた。2026-08-07 に本走設計の
裁定 11 件が全件確定 (最後が劣化幅の閾値 κ = 20%) し、事前登録を凍結できる状態になった。

**決定 (1): D19 の適用前提を限定する。** D19 の「同一セッションで測らない」という前提は、
通常の campaign compare と、独立 run を標本とする比較に適用する。T-139 の RF study で
元の版・劣化版・候補の 3 arm を同一割当て (cluster) 内で測り cluster 内 contrast を作ることだけを
限定例外とする。**この例外を他の study へも通常の campaign compare へも一般化しない** — 族一般化には
独立 2 例が要り、現時点の根拠は T-139 の 1 例だけである。D19 の within-run / between-run の区別、
`BETWEEN_RUN_CV` の値、roadmap §3.6(2) の品質ゲート、同 (4) の floor 丸めはいずれも変更しない。

**決定 (2): 例外の発効点は fold 後とする。** 本決定が canonical 台帳へ fold された land 以後にのみ
例外は効力を持つ。roadmap の改訂と本決定の fragment と凍結事前登録は同一の wave commit に置くが、
`docs/spool` 規約により canonical 台帳を wave が直接編集することはできない。fold 前の中間状態
(roadmap だけが見え canonical 決定が無い状態) で例外を発効させない。**本決定は「同じ変更単位」の
定義を変更しない** — 定義を下位の決定で書き換えて適合を宣言することはしない。docs のみで到達できる
最も強い形が同一 wave commit + fold 後発効であり、最厳格解釈 (canonical と roadmap が同一 Git commit)
との差はユーザー裁定へ返す。

**決定 (3): cluster level の推論に限る。** 1 割当てを 1 cluster とし、cluster 内の反復は arm ごとに
算術平均で 1 個の代表値へ縮約する。推定量・検定統計量・区間は cluster 間の標本平均と標本共分散だけから
構成し、cluster 内の反復・block・個々の測定値を独立標本や追加の自由度として数えない。

**決定 (4): 適格条件と fail-closed。** 各適格 cluster は 3 arm の全 6 順列をちょうど 1 回ずつ含み、
arm 位置と直前 arm を厳密に均衡させる。block の実行順は事前 seed で許容集合から選び runtime 乱数を
使わない。workload の block 順は cluster 間で差 1 以内に均衡させる。結果を見た後の cluster 選別・順序変更を
しない。性能を測る 3 arm はすべて trace-disabled ビルドで揃え、correctness 検証は trace-enabled の
別ビルド・別 run で行う (絶対規律 1 は不変)。pairing・順序均衡・受領証のいずれかが成立しなければ
結論は「判定不能」とし、unpaired 推定へも通常 compare へも自動 fallback しない。correctness anomaly は
**候補の終端 reject** とし (D134 決定 (6) と同じ単位。1 cluster の失敗に留めない)、性能測定の開始後の
失敗を予備割当てで置き換えない。適格性は producer の自己申告では決まらず、保存した生の受領証から
独立 validator が再計算した結果だけを権威とする (D162)。消費側は producer の申告値を読まず、
信頼された validator の再計算結果だけを受理判定の入力にする。

**決定 (5): 事前登録は 2 段階とし、core 1 本 + exact-key の追補で構成する。** 推論の**構造**
(問い・estimand・受理条件・状態空間・設計・失敗規則) を固定した core を
`output/insights/2026-08-07_t139-mainrun-design/preregistration.md` に凍結する。**core 単独では
完結した事前登録ではない** — 数値パラメータは、core が閉集合として列挙する **追補 A**
(本 study のデータを 1 点も見る前、すなわち pilot 投入より前に commit する) と **追補 B**
(本走の投入より前に commit する。verdict の直前ではない) で確定し、完結するのは core と追補の組である。
追補 A は時間予算表・待機秒数・環境復帰の指標と許容範囲・失敗の写像先・割当て外 build の binary 束縛・
要求 walltime に加え、**workload の driver 引数一式、3 arm の build identity、実行順の事前 seed と
許容 schedule 集合、`J_max` と割当て内訳と `J` の導出手続き、同時信頼領域と臨界値 `q` の構成、
weak null 較正 simulation の仕様、primary 系列の有意水準**を含む。追補 B は候補数上限、
個別公表系列の spending、累積台帳を束縛する正規の根の同定方法だけを持ち、**`q` に影響する量を
一切持たない** — これにより primary の判定基準は pilot より前に完全に固定される。
**追補は core の文章を変更できない。**追補は閉集合を **exact-key** で満たさなければならず、
欠落も余剰も解決失敗とする。追補は環境復帰の判定を恒真化してはならず、性能測定の開始後の失敗を
開始前の infra failure へ写してはならない。変更が必要になったらそれは別 study であり、
新しい core を起こしてユーザー裁定へ戻す。これにより「第 2 の完結版が κ・受理条件・状態表・
有意水準を書き換える」経路と、pilot の結果を見てから `q` や有意水準を選ぶ経路を塞ぐ。

**決定 (6): 凍結の実装は commit/blob 参照束縛だけとする。** 結果の記録が core と追補の
`<commit>` / `<path>` / blob SHA-256 を参照し、検証側が指定 commit の tree から blob を読んで digest を
照合し、その commit が測定 checkout の祖先であることを確認する。**現在の作業木の bytes を固定する
検査は置かない** — main の前進を妨げる検査を作らない。現作業木の同 path が過去の blob と異なることは
検出対象ではない。事前登録は自分自身の digest を本文へ書かない (自己参照の禁止)。

**決定 (7): 投入順序 gate。** 禁止を次の署名で書く。receipt の照合は投入**後**に置く — 投入前に
存在しない値を admission の前提にすると時間逆転になる。

```text
resolve_effective_preregistration(
    repository_root, *,
    core_ref   = (commit, path, sha256),
    addendum_a = (commit, path, sha256),
    addendum_b = (commit, path, sha256) | None,
) -> PreregBinding   # measurement_head は repository_root の実 checkout から導出し binding に含める

submit_pilot(*, binding: PreregBinding) -> submission_id
submit_main(*, binding: PreregBinding) -> submission_id

verify_receipt(*, binding: PreregBinding, receipt) -> None
```

`submit_pilot` は、次をすべて満たす `binding` が `resolve_effective_preregistration` から返っていない
限り実行してはならない。(i) `core_ref.path` が本決定の定める canonical core path と byte 一致する
(producer は core を自由選択できない)。(ii) `core_ref.commit` の tree に当該 blob が実在し SHA-256 が
一致し、かつその digest が**承認済み core** — 本決定を fold した commit `F` における同 path の blob —
の digest と一致する (caller が渡した digest との自己整合だけでは、`F` の子孫で同 path を
書き換えた blob を core と申告できてしまう)。(iii) `core_ref.commit` が、本決定を canonical 台帳へ fold した commit の子孫である
(決定 (2) の発効点。fold 前の branch 上の core を根拠にできない)。(iv) `addendum_a` も同型に解決でき、
その追補が従属先として記す core の **path・commit・blob digest の三つ組**が `core_ref` と一致する
(path だけでは同じ path の別 blob へ従属を付け替えられる)。(v) `addendum_a` が core の列挙する閉集合を
**exact-key で満たす** — 全件が存在し、その外の field を持たない (欠落も余剰も解決失敗)。(vi) `core_ref.commit` と `addendum_a.commit` が
`measurement_head` の祖先である (`orchestrator/campaign/trial_registry.py` の
`assert_prereg_ancestor` と同型)。**`measurement_head` は caller の引数ではなく、`repository_root` の
実 checkout から resolver が導出する。**(vii) core の `pilot_admission` が要求する追補が
(iv)(v) ですべて解決済みである。`submit_main` はこれに加えて `addendum_b` を同型に要求する。

**通る正例:** 本決定を fold した commit を `F` とする。core が `F` の子孫 `C` の path `P` に blob `B` と
して存在し `h = SHA-256(B)`、追補 A が commit `C2` の path `P2` に blob `B2` として存在し
`h2 = SHA-256(B2)`、`B2` が従属先として `(P, C, h)` を記し閉集合の field だけを設定しており、
`C` と `C2` がともに実 checkout の HEAD の祖先であるとき、
`resolve_effective_preregistration(repo, core_ref=(C,P,h), addendum_a=(C2,P2,h2))` は成功し、
他の admission 条件を満たせば `submit_pilot` へ進める。この正例は追補 A が land した時点で
到達可能になる (現時点では追補が無いので不成立)。gate は恒真な deny ではない。
ただし**追補 A が land しただけでは pilot は走らない** — 本 gate を実行する resolver と producer が
まだ実装されていないからである (下記の実装境界)。

**実装境界:** 本決定は文書上の契約だけを定める。gate の機械配線 (producer の投入前検査、受領証への
三つ組の必須記録、validator の独立再計算、consumer の受理判定、投入 script) は producer 実装 wave の
責務であり、本変更ではコードもテストも追加しない。**本決定をもって「投入 gate を機械的に実装した」と
記録してはならない。**

**却下した選択肢:**
- paired cluster 例外の一般化 — 独立 2 例が無く、免除の根拠 (協議合意) も T-139 の射程しか持たない。
- pairing 不成立時の自動 unpaired fallback — D134 決定 (4) の直接違反。
- 現在の作業木 bytes を pin する manifest 型の検査 — main の land を妨げる。
- 事前登録後の作業木の前進を禁じる freeze — 同上。
- 受領証の一致を投入の前提条件に置く設計 — 投入後にしか存在しない値への時間逆転。
- 「変更単位」の定義を本決定で置き換えて D134 決定 (3) への適合を宣言する — 下位の決定で上位要求の
  意味を変える読み替えであり、規律の緩和になる。

**研究状態への影響:** 本決定によって pilot 投入 gate が実装されたとは扱わない。事前登録 core と
追補の commit/blob 記録・祖先検査を producer が実装し、独立 validator が受領証を再計算するまで、
paired study の適格 verdict を生成しない。
