# 段 3 敵対検証 — レンズ B「手続き整合と実効性」

pytest・build・測定は実行していない。以下は read-only の静的検査と Git object 検査による。

## 独立再検証

| 親の主張 | 検証結果 |
|---|---|
| digest が F / HEAD / 作業木で一致 | **確認**。3 者とも `ac939af4...e9`。F は実在する commit で、現 HEAD `6cc3e59a...` の祖先 |
| core path の機械 pin が 0 件 | **確認**。FROZEN_MANIFEST、generator/role pin、実行コード内の core path・digest・F literal は 0 件。既存 manifest にも未収載（`orchestrator/tests/test_frozen_artifacts.py:38-85`） |
| 実装被覆 0 | **T139 固有 API は 0、9 層全体の 0/9 は誤り**。`resolve_effective_preregistration` 等は production に無いが、D229 が T126 の台帳・FSM・投入束縛・原子公開・identity を既存被覆として明示し、0/9 見積りを訂正済み（`docs/decisions.md:10760-10765`） |
| F object を使う合成 repo 正例 | **実行可能**。F とその履歴は main から到達可能で、F の親にも同じ core bytes が存在する。raw SHA を直接 fetch するより、source の HEAD/history を fetch 後に F の存在を assert する方が堅い |

## 所見

1. **blocker — `a01`〜`a13` 採用は「解釈」ではなく、実効的な凍結契約の書き換えである。**

   §14 は `a13 = primary 系列の有意水準` を明記する一方、§15 の機械 gate と正例は exact-key を `a01`〜`a12` とする（`preregistration.md:320-335`, `preregistration.md:404-407`, `preregistration.md:422-429`）。D234 は有意水準を A に置き、pilot 前に固定するとしている（`docs/decisions.md:11005-11015`）。

   構文上、`keys=A01..A12` の集合と `keys=A01..A13` の集合は exact-key のため互いに素で、包含関係ではない。科学的手続き上は A12 読みが primary alpha 未固定の pilot を許すため広く、A13 読みが狭い。ただし A13 読みは §15 が明示的に拒否する document を受理する。

   plan の「bytes は直さず新 D で解釈」は、凍結 bytes を保つだけで受理述語を変更している（`s2-plan.md:3-7`, `s2-plan.md:32-33`）。少なくとも「§15 は erratum であり §14/D234 を優先する」という明示的 supersede が必要で、単なる明確化として処理してはならない。最も保守的なのは新 core である。

   **未修正時の影響:** A12 なら primary alpha 未固定の pilot が通り、A13 なら凍結 §15 が拒否する追補を resolver が受理する。

2. **blocker — D234 の実装境界と段 A→B→C の衝突は、plan の読み替えだけでは閉じない。**

   core と D229 は `producer → pilot → validator/consumer → 本走` を明示する（`preregistration.md:258-268`, `docs/decisions.md:10750-10758`）。一方、後発の D234 は validator・consumer・投入 script まで「producer 実装 wave」の責務と逐語で書く（`docs/decisions.md:11065-11068`）。

   plan は D234 を「T139 全段の完了範囲」と読み替える案だが（`s2-plan.md:25-30`）、これは同一 wave という通常読解を狭める部分 supersede である。さらに T-643 は、HEAD hash を「validator が一致検査する」と裁定している（`docs/worklog.md:3182-3186`）。任意 helper の `verify_receipt()` を置くだけでは履行にならない。

   裁定パッケージでは「D234:11065-11068 を D229 の段順序に限定して supersede する」と明記すべきである。

   **未修正時の影響:** validator/consumer 不在でも「D234 の gate 実装済み」と記録できるか、逆に pilot 前に D162 の段 C 機械化を始めるかの二択になり、正本参照が分岐する。

3. **blocker — 認可を置く sink が間違っている。raw receipt の実 writer は無認可のままである。**

   T-643 の元の択一は「producer と投入 script のどちらを第一境界にするか」であり、裁定は producer 側だった（`docs/worklog.md:2284-2289`, `docs/worklog.md:3182-3185`）。D235 の sink 原則も「成果物を実際に書く関数」で必須引数を強制する（`docs/decisions.md:11085-11097`）。

   plan は qsub を行う `_submit` に binding を置くが、raw artifact を実際に書く `publish_raw_receipt(repository_root, *, receipt)` は binding を受けず、`verify_receipt()` は別の任意関数である（`s2-plan.md:159-175`, `s2-plan.md:186-211`）。これは T-609 が否定した caller 側認可の再現である。既存実装は、実際の `emit` sink が capability を再検査している（`orchestrator/qualification/artifacts.py:718-746`）。

   `publish_raw_receipt` 自体に exact `PreregBinding` または resolver が発行する writer capability を必須化し、同じ snapshot の receipt を照合してから publish させる必要がある。

   **未修正時の影響:** core/A/B/fold/measurement HEAD が binding と異なる schema-valid receipt を、qsub 側の認可と無関係に永続化できる。

4. **blocker — 追補 A 不在・PBS 本体未定義のままでは、この wave は「producer 実装」に到達しない。**

   worklog の順序は明示的に「追補 A → producer 実装 → pilot」である（`docs/worklog.md:1867-1878`）。brief は A を scope 外にし、pilot 不可と認める（`brief.md:19-24`）。plan 自身も a01〜a09 が未確定で PBS 測定本体を書けず、空 wrapper を producer 完了と数えてはならないと認定している（`s2-plan.md:379-391`）。

   それにもかかわらず、wrapper・registry・preflight を実装単位に含めている（`s2-plan.md:473-484`）。これは一 wave の量以前に、入力仕様が欠けた実装不能状態である。実装段へ進むなら、実測本体と raw receipt 呼出しまで同じ vertical slice に含める必要がある。

   **未修正時の影響:** 実測も raw receipt 生成もできない空 wrapper と dead API が land し、作業台帳だけが「producer 実装済み」へ進む。

5. **blocker — exact-key はあるが、追補 A の値契約がほぼ空で、D234 (i)〜(vii) 全実装という brief の主張を満たさない。**

   §14 は時間予算、待機、driver 引数、arm identity、J 導出、q、simulation、有意水準という実値を要求する（`preregistration.md:320-335`）。ところが plan の物理例は各 field を `{}` とし、具体的な意味検査は a03/a04 と B の q 非関与しか定義していない（`s2-plan.md:321-359`）。

   plan 自身、`allocation_observation` と名乗りながら実装が定数を返す場合や、有限だが常に通る範囲を検出できないと認めている（`s2-plan.md:353-359`）。これは §14 の恒真化禁止（`preregistration.md:345-360`）および brief の「D234 (i)〜(vii) を全条件実装」（`brief.md:9-10`）と両立しない。

   **未修正時の影響:** a01/a02/a05〜a13 が空、または環境復帰が実効的に恒真でも resolver が pilot を受理する。

6. **blocker — 「pilot 1 本目より前」の一回限りの A 束縛が無い。per-submit ancestry だけでは事後差替えを許す。**

   A の締切は各投入の直前ではなく「本 study のデータを 1 点も見る前、pilot 1 本目より前」である（`preregistration.md:318-334`）。plan の resolver は各 ref がその時点の HEAD の祖先かだけを再検査し（`s2-plan.md:341-351`）、study-wide の canonical A 登録、first-pilot watermark、series-global ledger を持たない。ファイル計画にもその authority が無い（`s2-plan.md:39-54`）。

   この形では pilot 1 後に A2 を commit し、pilot 2 を A2 に束縛しても、A1/A2 の各投入は自己整合する。`series_id` と `parent_series_id` も canonical root から導出する設計がない。

   **未修正時の影響:** pilot 1 の結果を見て q・有意水準・J 手続きを変更した A2 を後続 pilot に使え、study 全体の受理集合が事後選択で広がる。

7. **blocker — failed qsub / job-side preflight rejection を raw に残す authority と collector が存在しない。**

   core は全 attempt、理由、置換、親系列を必須とし、失敗投入を ledger と raw の双方から落とす変異を必須 kill とする（`preregistration.md:285-301`）。plan は単一 `submission-intent.json` を書くと述べるだけで、series-global ledger、qsub invocation claim、preflight 失敗の回収、accounting collector、receipt への射影を定義していない（`s2-plan.md:365-391`）。

   既存 T126 は intent の durable write と ledger reservationを qsub 前に行い（`tools/pegasus/submit_t126_qualification.sh:373-441`）、qsub invocation claim を残してから実行する（同 `:675-689`）。job preflight は最初の job-side write より前なので（`tools/pegasus/t126_qualification.sh:63-130`）、失敗を raw に残すには submit-side authority / post-job collector が不可欠である。

   **未修正時の影響:** qsub 失敗または preflight reject した attempt が raw 母集団から消え、成功した投入だけで双射を作れる。

8. **blocker — 段 A の変異は実表では 6 件あり、5 件中少なくとも 4 系統で単一理由帰属が成立しない。**

   plan の段 A 行は #1, #3, #4, #7, #8, #9 の **6 件**である（`s2-plan.md:397-407`）。D190 は、別層が同じ入力を先に拒否する場合、その node は対象 guard の存在を証明しないと明記する（`docs/decisions.md:9249-9271`）。

   | 変異 | 判定 | 前後の拒否層／再照準 |
   |---|---|---|
   | #1 failed 投入 | **帰属不成立** | intent publish 削除と raw comparator `==→<=` の二箇所・二理由。M1a「qsub 前 reservation 削除」と M1b「既存 ledger 行を raw から 1 行落とす」に分割する |
   | #3 anomaly clean | **帰属不成立** | `correctness_clean` を schema に足しても runtime exact-key が拒否。evidence row を bool 化しても schema/type 層が先に拒否。実 producer の anomaly→attempt outcome 遷移を、schema-valid な clean 遷移へ変える mutation に照準する |
   | #4 eligibility field | **帰属不成立** | `additionalProperties:false→true` を変えても `validate_raw_receipt()` の exact-key 再検査が拒否する（重複は plan 自身が明記、`s2-plan.md:304`）。closedness の権威を一層にする |
   | #7 core blob / extra field | **複合変異** | approved digest と addendum extra-key は独立。7a digest 比較削除、7b `==→subset` に分割する。7a は既存 `_blob_at_commit()` が bytes を返すだけなので実効 gate に照準可能（`trial_registry.py:755-785`） |
   | #8 a03 / a04 | **複合かつ一部実装不能** | 恒真 metric と post→pre failure remap は別理由。分割し、実装が定数を返す変異は実 producer/validator の evidence 再計算へ送る |
   | #9 pre-fold | **帰属可能** | F の親は同じ core digest を持ち、HEAD の祖先でもある。`core_ref.commit=F^` を使えば、他層を通過して F→core ancestor guard だけが拒否理由になる |

   **未修正時の影響:** 対象 guard を削除しても別層の拒否でテストが通り、変異 matrix が `KILLED` と誤記して実際より狭い受理集合を主張する。

9. **must-fix — テスト群は dead API と空 wrapper のままでも大半が通る構成である。**

   - F fixture は実現可能だが、production 定数から F を取得すると自己充足になる。テスト側で既知 F literal を独立に固定し、source HEAD/history を fetch 後に object と ancestry を確認すべきである（`s2-plan.md:428-436`）。
   - `bash -n`、preflight ordering、first-write sentinel は、測定本体も receipt writer も無い wrapper で成立する（`s2-plan.md:462-469`）。
   - raw receipt tests は手製 fixture だけで、PBS producer が同じ receipt を生成する検査が無い（`s2-plan.md:438-450`）。
   - `test_preflight_helper_is_loaded_from_binding_source_commit` の “binding source commit” は `PreregBinding` の field に存在しない。`measurement_head` を意味するなら明記と intent 束縛が必要（`s2-plan.md:85-104`, `s2-plan.md:467`）。
   - `test_positive_control_probe_bytes_are_unchanged` は oracle 未定義である。literal hash なら未裁定の恒久 pin、HEAD と比較するだけなら恒真になる。既存 probe は run commit の blob と runtime bytes を照合する設計なので（`t139_positive_control_probe.pbs:109-135`）、このテストは削除すべきである。

10. **must-fix — brief の「純増検出力」と成果物影響表は、現時点の効果と将来到達時の効果を混同している。**

   approved F digest と dependent triple は真正の T139 新規検出である。一方、canonical single-read、closed schema、atomic publish、series ledger、sink capability は既存機構であり、D229 も 0/9 見積りを訂正している（`docs/decisions.md:10760-10765`; `artifacts.py:73-108`, `artifacts.py:537-552`, `atomic_publish.py:24-123`）。

   brief の resolver・receipt・verify による効果（`brief.md:35-44`）は、A、PBS body、publisher 結線、validator caller が揃った後の条件付き効果である。現在は pilot 経路自体が無く、`verify_receipt` の production caller も計画されていない。特に「三つ組 + HEAD 不一致を検出」は helper の unit test の効果であって、成果物経路の効果ではない。

   また、T139 固有 public API が 0 件なのは確認できるが、広い意味の「実装被覆 0」は D229 の既裁定と衝突する。brief §6 の既存機構列挙（`brief.md:57-63`）とも自己矛盾している。

## scope と安全な切り方

現 plan は 1 wave に収まらない。U1→U2/U3→U4 の依存列に加え（`s2-plan.md:473-484`）、未計画の PBS 本体、study-wide binding、attempt ledger、collector、raw publisher sink が必要だからである。

半実装を避ける切断点は「段 4 で実装しないと裁定し、コードを 1 行も land しない」である。裁定パッケージ候補は次のとおり。

- A12/A13 の明示 supersede または新 core。
- D234 実装境界を D229 の段順序へ限定する裁定。
- 追補 A の concrete bytes・値 schema・study-wide canonical registration。
- その後の producer wave は、pilot 用 PBS 本体、qsub 前 ledger、job/preflight failure collector、binding 必須 raw sink、schema-valid receipt の end-to-end 正例までを一つの vertical slice とする。
- validator / consumer は段 C、追補 B・main sink は段 D 前、別 checkout 完全偽造検出は T-643 どおり scope 外。
- pilot 実投入自体も別手番。actual PBS body だけは「producer 実装済み」を名乗るなら scope 外にしてはならない。

## 総括

- **NO-GO**
- blocker: **8 件**
- A13 採用は安全側だが、現状は凍結契約の実効的書換えである。
- T-643 の producer-side sink は raw publisher まで届いていない。
- PBS 本体・attempt authority・collector が無く、producer の実経路は存在しない。
- 現 wave は段 4 で止め、裁定と追補 A を先行させるべきである。
- テストは実行しておらず、緑とは報告しない。