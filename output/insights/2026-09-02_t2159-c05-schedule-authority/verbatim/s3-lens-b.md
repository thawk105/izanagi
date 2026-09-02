## 所見 1 — D959 と直接抵触し、D1448 が順序を上書きしたとは逐語から確定できない

- **主張:** 本 wave は D959 の下流症状 (e)「schedule authority の無条件 raise」を、上流 (a) を解かないまま解除する計画であり、明示的な順序抵触である。D1448 は同じ実装を命じる後発裁定だが、D959/D992、新事実 N2〜N4、着手順序への言及がなく、知情の上での supersede とは判定できない。
- **根拠:** D959 は (b)〜(e) を (a) に従属させ、「順序を入れ替えて先に解除してはならない」と明記する (D959:3-14)。プランは無条件 raise を production authority loader に置換する (`s2-plan.md:30-76`) 一方、C05 は最終的にも `EVIDENCE_UNDEFINED` のままとする (`s2-plan.md:213-235`)。brief も (a) が未解決と実測している (`brief.md:36-43`)。D1448 の逐語は「schedule 正本を新設する」と「raise 据え置きを却下」だけである (D1448:3-11)。
- **成果物へどう効くか:** 実装しても正式起動は通らず、D959 が禁止した順序で dormant capability と test state だけが増える。D1448 を暗黙の上書きと扱うと、ユーザーが N2〜N4 を知らずに出した裁定を拡張解釈することになる。
- **これが正しければプランのどこを変えるか:** `s2-plan.md:1-8` の「実装可能」を撤回し、段 4 で「D1448 は D959 の順序を、(a) 未解決のまま明示的に上書きするか」をユーザーへ再裁定する。上書きされないなら loader 実装を延期する。

## 所見 2 — D549 は本 wave を禁じないが、親 brief の「配線側だけ」という整理は広すぎる

- **主張:** schedule artifact と seed を変更しない点では D549 に抵触しない。D992 の主文も「査読済み凍結 spec の candidate producer / durable 発行 lifecycle」が対象なので、今回の artifact 非発行はその狭い禁止対象ではない。一方、プランは単なる配線ではなく authority schema と値の射影を新設するため、D959 からは逃れられない。
- **根拠:** D549 は artifact/seed を保留し、配線と実 authority 供給を別 wave へ送っている (D549:3-24)。プランも artifact と §5 を編集しない (`s2-plan.md:299-311`)。D992 の主文は frozen spec の producer/lifecycle に限定される (D992:3-6) が、理由では無条件 raise を D959 の下流症状として再確認する (D992:8-12)。プランは `s8c_schedule.py` の validator まで変更する (`s2-plan.md:138-158`)。
- **成果物へどう効くか:** 「artifact を出さないから全先行裁定と非抵触」という brief の結論は成立しない。D549/D992 の狭い対象を避けても、D959 の順序規定には触れる。
- **これが正しければプランのどこを変えるか:** `brief.md:78-83` を「D549 の artifact 同時発行規則には抵触しないが、D959 の (e) 解除には該当する」に修正する。D992 は直接禁止ではなく、未発効状態と順序を補強する根拠として扱う。

## 所見 3 — 18-key の三矛盾は、実値を見つけた一方で projection contract を発明している

- **主張:** `leakproof_context`、`whiteboard`、`descriptor_binding` は、基礎データの出所こそ実コードにあるが、schedule authority に入れる JSON shape と受理規則には権威がない。三件とも「解いたつもりで発明した」に分類すべきである。
- **根拠:**
  - `leakproof_context` の production 値は文字列 (`s8c_generation_projection.py:22-26`; `p3_autonomous_workload_trial.py:3988-4005`) だが、schedule は object を要求する (`s8c_schedule.py:91-105,235-249`)。`{"text": ...}` の field 名・shape はプランの新設である (`s2-plan.md:132,140-142`)。
  - fresh `whiteboard` が `[]` であること自体には実装上の根拠がある (`p3_autonomous_workload_trial.py:1707-1709,3925-3959`)。しかし現 schedule validator は空配列を明示的に拒否する (`s8c_schedule.py:167-208,235-249`)。「whiteboard だけ exact empty を許し、非空を拒否」は新しい schema 裁定である (`s2-plan.md:144-154`)。
  - resolver は cell ごとの sealed `ResolvedArmInput` を返す (`s8c_arm_inputs.py:74-84,434-494`)。それを six-cell の四フィールド表へ集約する schema はプランが新設している (`s2-plan.md:129,156-158`)。
  - T-1380 は D530 が裁定したのは caller 供給・閉 key・型・非空性までで、18 field 名と型対応は実装著者の選択だったと確認済みである (`verbatim-t1380-insight.md:35-55`)。
- **成果物へどう効くか:** これらは `initial_state_sha256` を決め、最終的な schedule artifact bytes を変える。実装自身が作った projection を同じ実装で検証する自己権威となり、「正本を解決した」証明にならない。
- **これが正しければプランのどこを変えるか:** `s2-plan.md:111-158` の三 projection を確定案から外す。各 shape を protected spec または新しい明示裁定で定義するか、D1448 の範囲を call wiring のみに狭めて authority は caller-supplied のまま延期する。

## 所見 4 — path・定数・schema・既定値・cell id・ledger の出所は一様ではない

- **主張:** schedule path、既存定数、cell ID には既存権威がある。一方、budget の exact 4-key schema と ledger の配置には権威がない。
- **根拠:**
  - **schedule path:** `output/s8c-preregistration/schedule.v1.json` は D549:5 と evidence contract (`s8c_preregistration_evidence_contract.v1.json:190-228`) が固定している。
  - **定数:** schema/generator version、arms、holdouts、six-cell は既存 module に固定されている (`s8c_schedule.py:51-54,317-345`)。§5 field 名も既存文書が固定する (`docs/phase3-8c-preregistration.md:194-206`)。
  - **schema:** schedule の現行 18-key schema は既存だが、所見 3 の三 projection と `whiteboard` 例外は新設である。
  - **既定値:** seed・予算について fallback を設けない方針 (`s2-plan.md:181-197`) は正しい。`whiteboard=[]` は fallback ではなく live fresh-state 値だが、その値だけを受理する規則は新しい。
  - **cell ID:** manifest の `trial_id` を使う案は既存権威に沿う。manifest schema が `trial_id` を必須化し (`trial_registry.py:114-117,266-280,743-781`)、settlement も binding の同じ ID を使う (`p3_autonomous_workload_trial.py:3531-3541`)。
  - **ledger:** `s8c_budget.reserve_all_cells` は caller-supplied path をそのまま使い、canonical path を定義しない (`s8c_budget.py:533-590`)。プランの `budget-ledger.<manifest sha>.v1.json` は新規発明である (`s2-plan.md:19-28`)。roadmap にも canonical path は dormant 未決として残っている (`docs/phase3.md:664-672`)。
- **成果物へどう効くか:** ledger の単一性と再利用単位が実装者の命名に依存する。同じ manifest に別 freeze/schedule を使った場合は同名 ledger が identity mismatch で拒否されるため、これは単なるファイル名ではなく lifecycle 方針の決定でもある。
- **これが正しければプランのどこを変えるか:** `s2-plan.md:17-28,325-330` の ledger path を未裁定 blocker とする。canonical path、identity の単位、再生成・再利用規則をユーザー裁定または protected spec で決める。

## 所見 5 — §5 budget の第4キーは無権威で、既存の値域規約も検査しない

- **主張:** `reserved_bench_s` の six-cell matrix を §5 の「上限」欄へ追加する案には規範上の出所がない。またプランは既存規約である arm 上限の対称性と holdout 上限合計＝総上限を検査していない。
- **根拠:** §5 の欄名は「総上限と arm ごと・holdout ごとの上限」である (`docs/phase3-8c-preregistration.md:194-206`)。規範は arm 上限の対称性と holdout 上限合計の一致を要求する (`同:163-165`)。`BudgetLimits` は三種の上限だけを持ち、`ReservationCell.reserved_bench_s` は別の runtime 型である (`s8c_budget.py:83-128`)。同 module は coverage・有限性と「予約値が上限以下」しか検査せず、上限の対称性・合計一致を強制しない (`s8c_budget.py:517-530`)。プランはこの二型を独自の exact 4-key JSON に合成する (`s2-plan.md:160-179`)。
- **成果物へどう効くか:** 凍結対象外の値セルに、protected 規範へ記載のない reservation schema が入り、consumer 実装自身がその意味を決める。さらに既存規範に反する非対称上限でも通り得る。
- **これが正しければプランのどこを変えるか:** `s2-plan.md:172-179` の exact 4-key schema を採用しない。reservation の導出元・単位・cell 配分を規範側で裁定し、既存の対称性・合計一致 validator も production 経路に追加する。その裁定なしには budget loader を完成扱いしない。

## 所見 6 — schedule cell と attempt-registry の schedule row が結線されていない

- **主張:** manifest の `trial_id` への対応だけでは §6.4 の一対一束縛を満たさない。プランは `consume_schedule` の cell と genesis slot の `schedule_row_sha256` を比較しない。
- **根拠:** attempt slot は `schedule_row_sha256` を必須とする (`trial_registry.py:144-147,1964-2001`)。事前登録は slot を schedule 行・run-start・process identity・出力・terminal status へ一対一に束縛する (`docs/phase3-8c-preregistration.md:227-234`)。プランの loader は全 ordinal を consume して manifest の pair/trial ID に対応させるだけで、attempt capability または row hash を受け取らない (`s2-plan.md:54-75,81-85`)。現行起動順でも attempt slot の予約・分類・lifecycle start が先で、schedule loader は後から budget 準備内で呼ばれる (`p3_autonomous_workload_trial.py:4628-4715`)。
- **成果物へどう効くか:** registry が束縛する schedule row digest と、C05 が検証する schedule artifact が別物でも両方通り得る。schedule の一対一消費責任を registry 層へ委ねるという module 契約 (`s8c_schedule.py:3-14`) が未完のままである。
- **これが正しければプランのどこを変えるか:** canonical schedule-row preimage/hash を先に裁定し、genesis producer、slot capability、実際に consume した cell を同じ digest で照合する設計を追加する。これは T-1380 の genesis 未確定を解く作業であり、本 wave の「配線だけ」には収まらない。

## 所見 7 — T-1380 の三未確定値は解かれず、前提 artifact の背後へ迂回されている

- **主張:** `campaign_id`、`freeze_id`、genesis slot 集合は本プランでは未解決である。
- **根拠:** T-1380 は正式 site 未確定の `campaign_id`、identity 規則不在の `freeze_id`、`n` と retry 集合未確定の genesis slot を列挙する (`verbatim-t1380-insight.md:57-68`)。プランは campaign ID を absent manifest に委ね (`s2-plan.md:67-84`)、freeze は absent ratified freeze の既存検査へ残し (`s2-plan.md:99-107,136`)、genesis を生成・検証しない。現行コードは loader より先に committed genesis を要求する (`p3_autonomous_workload_trial.py:1379-1427,4628-4639`)。
- **成果物へどう効くか:** 合成 test では loader を通せても、production では manifest、effective binding、genesis、active freeze、§5、schedule がすべて不在のため正例経路を構成できない。これは「解決」ではなく fail-closed な迂回である。
- **これが正しければプランのどこを変えるか:** 総括を次の分類へ直す。
  - 三矛盾: 基礎値は発見したが projection contract は発明。
  - campaign/freeze/genesis: 未解決のまま上流 artifact に委譲。
  - cell ID: manifest authority の再利用として解決済み。

## 所見 8 — N2/N3/N4/N6 は D1448 の実装準備前提を覆す。§6.6 はこの順序違反を救わない

- **主張:** N1 と N5 は D1448 を覆さないが、N2/N3/N4/N6 は「今この wave で authority を確定できる」という前提を覆す。§6.6 が認めるのは「値より consumer が先」という局所順序であり、「D959 の (a) より (e) を先に解除してよい」という意味ではない。
- **根拠:**
  - N1 は stale runbook の訂正だけである (`brief.md:34-35`)。
  - N2/N3 は C05 が SATISFIED にならず、正式 admission が上流で閉じることを示す (`brief.md:36-41`; `s8c_preregistration.py:1925-1956`)。
  - N4 は D992 の ratified-freeze 前提が今も偽である (`measurements.md:29-35`)。
  - N5 は §5 未記入なので受理分岐が発火しない (`brief.md:44-47`)。consumer-first の向き自体は §6.6 (`verbatim-prereg-s5-s6.md:42-46`) と整合する。
  - N6 は三つの authority projection に新しい仕様裁定が必要なことを示す (`brief.md:48-51`)。
  - §5 規範も、budget は consumerと正式事前コスト計画が揃ってから、seed は generator/schedule/arm 順序と同じ改訂単位で記入すると定める (`docs/phase3-8c-preregistration.md:163-174`)。
- **成果物へどう効くか:** consumer-first という一点だけを根拠に実装すると、D959 の上流順序と authority 未裁定を取り落とす。正式成果物は増えず、未批准の schema choice だけが source に固定される。
- **これが正しければプランのどこを変えるか:** 段 4 へ N2/N3/N4/N6、三 projection、budget/ledger、schedule-row binding を一括して返す。ユーザーが D959 を明示的に上書きし、各 authority を裁定した場合にだけ実装へ進む。

## 所見 9 — C05 の「現行値」の記述が親実測と一致しない

- **主張:** プランの `現行: UNSATISFIED / schedule-consumer-unreachable` は HEAD の実測値ではない。artifact をメモリ注入した合成状態なら、その前提が欠落している。
- **根拠:** 親実測の HEAD は `EVIDENCE_UNDEFINED / schedule-schema-absent` である (`measurements.md:3-25`)。一方、プランは「現行」を `UNSATISFIED / schedule-consumer-unreachable` とする (`s2-plan.md:230-233`)。実 artifact は不在である (`measurements.md:65-69`)。
- **成果物へどう効くか:** 実装前後の差分を誤って説明し、artifact 不在と consumer 不在を混同する。C05 の価値や到達性 test の前提が再び過大評価される。
- **これが正しければプランのどこを変えるか:** `s2-plan.md:230-233` を「HEAD 実測」と「schedule blob を注入した synthetic probe」に分け、各状態の前提を明記する。

## 総括

最も重い所見は次の三件である。

1. D959 が禁じる (e) の先行解除に直接該当し、D1448 の逐語だけでは知情の supersede と確定できない。
2. 三つの authority projection、§5 の予約 matrix、ledger canonical path が無権威の新仕様である。
3. 実 schedule cell と attempt-registry の `schedule_row_sha256` が結線されず、T-1380 の genesis 問題が残る。

**本 wave は実装してよいか: ユーザー裁定へ返すべき。**
D1448 が D959 の順序を上書きするかを明示し、projection schema・reservation schema・ledger path・schedule-row preimage を裁定する必要がある。§6.6 の consumer-first 規則だけでは、この上流順序と権威不足を解消しない。

**自分が確かめられなかった箇所:** active ratified freeze、§5 数値、schedule artifact、正式 manifest/genesis が不在のため production 正例は確認不能。指定された必読ファイルは全件・全文確認したが、read-only 境界に従い pytest・実走・書き込みは行っておらず、緑とは報告しない。