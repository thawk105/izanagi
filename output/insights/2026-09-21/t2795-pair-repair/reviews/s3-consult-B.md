# 判定と読解範囲

**session 案は条件付き支持。ただし、結合正例の成功条件と変異の帰属を修正してから author に渡すべきです。**

指定資料は読めました。以下はすべて **未実走・静的読解**です。実装・pytest・計測・書込みは行っていません。

以下の `plan` は [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair-repair/codex/s2-plan.md)、`brief` は [s1-brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair-repair/s1-brief.md) を指します。行番号は変更前です。

# B1 — real / must-fix：結合正例の必須 assert が「両評価成功」を固定していない

**位置:** `plan:227–237`、`orchestrator/campaign/loop.py:797`、`orchestrator/campaign/p3_s4_loop.py:2092`。

**成果物への影響:** 両 arm に BUILD_START と ABORT だけが残る実装でも、列挙された主要 assert を満たし、stock 未測定の修復を完了扱いできる。

plan の必須条件は「BUILD_START／terminal record が存在」「stock outcome は実 WAL の STOCK 条件で決まる」です。terminal は COMMIT に限りません。実 `loop` は評価例外を ABORT に変換します。また既存候補 CLI は aborted を必ず非零にする設計ではありません。

**推奨:** 結合正例を次の成功条件まで明記してください。

- 候補は `certified`、stock は `certified-stock`、driver rc は 0。
- 同一 WAL に、異なる両 variant の BUILD_START・BUILD_DONE・VERIFY_DONE・BENCH_DONE・COMMIT がある。
- stock の variant と BUILD_START の `src_token` が STOCK 条件を満たす。
- build／trace／bench の stub が両 arm について呼ばれ、その順序が候補→stock。
- claim 取得は 1 回、stock 終了後も同じ claim record。

さらに一つだけ、**stock の bench 呼出しを欠落させる変異**を加えると、claim が通るだけの検査との差が明確になります。成功 WAL は引き続き実 pipeline に生成させます。

# B2 — real / should：独立した性質として数えられない変異が混在する

**位置:** `plan:323–345`、`orchestrator/campaign/loop.py:198–224`、`orchestrator/tests/test_p3_s4_loop.py:9820`。

**成果物への影響:** 到達不能な入力や別防壁による拒否を KILLED に数えると、検証レポートの被覆が実際より強くなる。

帰属は次のように整理できます。

| 変異群 | 静的判定・推奨 |
|---|---|
| 再利用でも claim 取得／stock に S を渡さない／正しい S を拒否 | いずれも結合正例の到達性を壊す。別の配線ミスとして残せるが、独立した三つの保証とは数えない |
| 初回 claim を省く | 実取得回数・file 存在を調べる正例で有効 |
| identity 比較を外す | protocol digest・claim path 比較でも拒否され得る。単独比較の削除が受理集合を広げるとは限らない |
| 契約 SHA 比較を外す | 契約を束縛した identity／digest が変わるため、同じ問題がある |
| resolved root 比較を外す | 再構成 claim path 比較でも止まる。root 異常一つで独立 KILLED を期待しない |
| PID 比較を外す | factory PID・record PID・proc starttime のどれを外すか特定が必要 |
| record 比較を外す | 他の束縛に影響しない `created_utc` の変更などなら帰属を作りやすい |
| stock に候補 context／checkout を渡す | 二つの異なる性質。authority と source root の変異に分割する |
| STOCK 条件を外す／逆転 | 既存 `test_stock_control_rejects_non_stock_certified_source` は片方だけ不一致の結果を合成しており、最終判定の単体検査として適切 |
| candidate reject／例外で early return | sink 未到達 reject と claim 後例外を分ける。S の未束縛／束縛済みという異なる状態を検査する |

**推奨:** identity・契約・root は、まず「異なる束縛を受理しない」という性質単位で事前登録してください。単一比較の削除が他防壁で止まる場合は survivor／冗長防御と報告し、都合よく他比較まで stub して独立防壁の実証にしないこと。拒否点のメッセージ検査は診断順序の検査であり、受理集合の検査とは分けます。

# B3 — real / should：session が「変更行数で最小」とする根拠はまだない

**位置:** `brief:12–15`、`plan:11–27,45–64`、`orchestrator/campaign/loop.py:347,765,782`。

**成果物への影響:** 最小性を未検算のまま採用すると、共有認可 sink に不要な一般化を持ち込み、他 driver の認可経路の回帰面を増やす。

比較結果は以下です。

| 観点 | session | loop 不変の 1 call |
|---|---|---|
| 共有 sink | `loop.py` を変更。既存 inventory は **17 file・22 call** | 変更なし |
| 既存先例 | 呼出し間で claim 所有を引き継ぐ先例は確認できない | A-1 の二つの call site、sweep に実例あり |
| S4 の局所変更 | 既存二つの評価関数・結果処理を維持できる | 候補検疫、別 tree、別 authority、結果の arm 対応を組み直す必要 |
| 壊れ方 | claim 所有不一致、S 転送欠落を局所に診断できる | source 切替・skip・結果対応の誤りが絡みやすい |
| 変更行数 | 未実装なので未算定 | 同じく未算定 |

現行通常経路は `ccbench_dir`・`build_context`・resolver が各一つです。A-1 用 source context は balanced schedule 専用で、S4 の別 checkout・coder authority 分離をそのまま満たす先例ではありません。

したがって、**既存の責務を維持する最小設計としては session を推奨**します。ただし「変更行数も最小」とは確定できません。親の「coder 編集木だから stock 不可能」という棄却理由も強すぎます。STOCK は digest の結果で決まり、plan がこの点を訂正したのは妥当です。

**推奨:** 新しい session は pair が明示して渡す内部値に限定し、他 driver の自動 session 化、汎用 registry、永続 session 台帳、callback framework を作らないこと。`single_process=False` 用にも別の認可管理機構を育てず、既存 CLI の互換に必要な範囲だけを扱ってください。exact 型・発行元・所有束縛自体は、claim を省く新経路の根拠になるため削除対象ではありません。

# B4 — real / should：fixture＋stock の削除理由は「経路がない」ではなく「今回の対象外」

**位置:** `brief:20`、`plan:151`、`tools/pegasus/p3_s4_loop_pegasus.sh:679,689`、`orchestrator/tests/test_p3_s4_loop_job_contract.py:1932`。

**成果物への影響:** fixture＋stock の既存受理集合を狭める変更が、未使用経路の整理と誤記される。

fixture＋stock は現物の shell にあり、job contract test にも正例があります。`tools/pegasus/README.md:375` も proposal **または fixture** を契約として記載しています。「発火する artifact／計測 ID がない」は、**指定された K2 production 記録に見当たらない**という意味なら支持できますが、既存経路・利用例が存在しないという意味では反証されます。

**推奨:** rc=2 拒否は今回の最小化として条件付き支持です。理由を「今回修復する production 入力は proposal。fixture pair の新規対応は広げない」と記録し、既存公開契約の縮小を明示してください。拒否は plan どおり prebuild／trap 前でよく、fixture 単独は維持します。

stock-only は削除不可です。`b5_generator_contrast.py:484` が `--stock-control --b5-slot ...` を生成します。B-5 が必要とするのはこの単独口であり、fixture＋stock ではありません。

# B5 — real / nit：親の数値と条件判定には、事実・下限・未検証を分ける必要がある

**位置:** `brief:23–24,34–38`、`orchestrator/tests/test_campaign.py:5408`、`output/insights/2026-09-20/t2795-k2-pair-attempt/README.md:63`。

**成果物への影響:** 設計資料の被覆数・条件充足・工数見込みが、再現していない実測として引用される。

- `_AuthorizationResult` の参照は読解・検索範囲では loop 内だけです。ただし、この名前の参照数だけで「repo 全体に意味的に同等な機構が 0 件」とは証明できません。
- 「1 call 先例 2 件」は **二系統**なら正確。指定アンカーは A-1 の 2 call site＋sweep の 1 call siteです。網羅的な総数ではありません。
- caller 数は plan の **17 file・22 call** が既存 semantic inventory と一致します。「約19 driver」は置換すべきです。
- 条件13の新しい受理形は実在します。実 claim の八 field も一次資料に載っています。
- 「時間予算の述語は無い」は「新規追加しない」と限定すべきです。既存 `loop.py:209` の reservation presence 検査には `required_s=1` があり、stock 完走分の残時間を保証しません。
- 条件08の submodule 実測、09の全 SHA 出現範囲・85 path、10の非該当は、今回の静的照合では独立再現していません。
- 指定 brief に数値の所要時間見積りはありません。工数・実走所要の検算結果は出せません。

**推奨:** 確認できた数値へ修正し、それ以外は親の実測記録への帰属か未検証を明記してください。

# refuted 候補 — 実効性、二重適用、共有 cache

**重大度:** 指摘不成立。
**位置:** `p3_s4_loop.py:2051,2083,2230,2280,2294`、`loop.py:517,579,782`、`patchharness.py:247,346`。
**成果物への影響:** plan の配線どおりなら、旧 one-shot claim 拒否を除き、既存 STOCK 判定と WAL 生成経路を維持できる。
**推奨:** 別の評価 framework を足さず、既存経路を保持する。

予定される実行順は次のとおりです。

1. shell が proposal＋stock を **一つの driver** に渡す。
2. 候補 checkout 内で TEMPLATE_PATCH→quarantine→condition gate。
3. 候補 `run_campaign` が実認可・reservation・claim を取得し、直後に S を束縛。
4. 実 pipeline が候補の build→verify→bench→WAL 終端を生成。
5. 候補の applied と checkout を退出してから、別の stock checkout に入る。
6. stock 自身の TEMPLATE_PATCH・stock condition gate・専用 resolver を使う。
7. stock `run_campaign` は所有再確認を経て実 pipeline へ進む。
8. `p3_s4_loop.py:2096` が実結果と WAL の STOCK 条件で outcome を決める。

`checkout()` は patch を適用しません。したがって、各 helper 内の `applied()` 一回ずつなら二重適用ではありません。cleanup 例外も候補 step の捕捉範囲に含め、stock には必ず新しい context manager を作る必要があります。

共有 cache も、それ自体は反証材料になりません。`buildcache.py:625` のキーは genome・commit・trace・source token・admission を含み、v2 の束縛にも genome と source token が入ります（`:1302`）。`pipeline.py:1812` は渡された evidence と現在の source を再照合します。候補の正の `BACKOFF_FIXED` と stock の −1 も異なります。通常の配線で候補 binary を stock として拾う経路は見つかりませんでした。

候補の分岐も整合しています。

| 候補状態 | stock の動作 |
|---|---|
| quarantine reject、sink 未到達 | 未束縛 S を用い、stock が最初の claim を取る |
| claim 後の通常例外 | 束縛済み S を保持し、stock を試す |
| duplicate-skip | 認可は skip 判定より前なので S は束縛済み。stock を試す |
| 認可途中の失敗、claim／reservation 不整合 | stock も拒否され得る。救済しない |
| stock に既存 terminal | 新規測定ではなく skipped。pair 成功にしない |

「試す」と「必ず成功する」は別です。plan はこの区別をおおむね守っています。

# refuted 候補 — F1019 対応が全面的に無効、または pin 更新が全面的に不足

**重大度:** 指摘不成立。ただし B1 の補強が必要。
**位置:** `plan:191–254,258–310`、`verbatim/F1019.md:12`。
**成果物への影響:** 結合検査は claim 認可の再発を検知できるが、実 compiler による STOCK 成立や production 完走の証拠にはならない。
**推奨:** この二つを記録上も分離する。

main→実認可→実 claim→実 layout→実 pipeline→実 WAL を通す案は、今回の OTHER 契約による取り逃しを直接塞ぎます。build 等が stub でも、この認可経路の結合検査として有効です。同 process・S 無しの二回呼出しも、同 path の one-shot 拒否の負例として十分で、二つの subprocess を追加する必要はありません。

一方、checkout・patch・condition gate・source evidence・build の代用があるため、F1019 全体を「production 経路まで恒久対応完了」と閉じてはいけません。記録は次の範囲が適切です。

> 認可／claim 結合の再発検査を追加。実 compiler の STOCK 成立、実 checkout／patch と build の統合、Pegasus production pair は未実施。

pin／consumer について、指定された主要箇所は plan が拾っています。

| 対象 | 判定 |
|---|---|
| layout 11、run_campaign 2、既定 runtime 1 | `test_p3_exploration_namespace.py:426` と一致 |
| semantic caller 17 file・22 call | `test_campaign.py:5408` と一致 |
| import 閉包49 | `test_p3_b4_wiring_probe.py:329`。実装後に再計数 |
| job 逐語 pin・起動点3→2・既定 argv | plan に更新箇所あり |
| process 起動点目録 | subprocess を追加しない限り更新理由なし |
| B-5 stock-only／PIN 読取り | 維持対象として把握済み |
| Pegasus README §7、phase3、F1019 | 更新担当まで明示済み |

追加の参照確認候補は `docs/paper-story/README.md:78` の「修復方向は裁定パッケージ」です。今回の修復後も現況説明として残すなら、修復 insight への日付付き導線が必要です。過去の不成立・数値・稿は変更しません。必須 pin の新たな取り落としは、この読解では確認できませんでした。

## 総括

**real: must-fix 1、should 3、nit 1。**

- **must-fix:** B1 — 結合正例で両 arm の certified・verify・bench・COMMIT を固定。
- **should:** B2 — 重複防御を独立変異と数えない。B3 — 最小性の主張を限定。B4 — fixture pair の契約縮小を明記。
- **nit:** B5 — 被覆数・条件判定・所要見込みの根拠を限定。

| 裁定 | 判定 |
|---|---|
| P1 | 条件付き支持。既存二つの評価経路を保持する限定 session を推奨 |
| P2 | 支持。候補 authority と stock-only／B-5 を分離 |
| P3 | 条件付き支持。通常例外・cleanup 例外を候補 step 内で捕捉し、stock を試行 |
| P4 | 条件付き支持。1 起動化は支持、fixture 拒否は既存契約の縮小として記録 |
| P5 | 支持。rc ではなく両 attempt の実 WAL outcome で判定 |

最小設計は、pair 内だけで S を共有し、最初の sink 到達で claim を取得、stock は所有を再確認して再利用する形です。候補・stock は別 checkout・別 authority、同 policy・identity・WAL。旧二 process と shell 集約を削り、stock-only は残します。結合正例一つに成功経路を集約し、未到達 reject・claim 後例外・S 無し再取得を狭い負例で補います。leaf・identity preimage・admission は不変。production pair は未実走のまま別予算へ残します。