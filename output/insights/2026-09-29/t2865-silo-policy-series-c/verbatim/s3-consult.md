## 指摘

- [real] **高** — 親 brief の「`check_stop` は driver 起動時だけ」は誤り。pair と `record-reject` は開始前と結果記録後に判定する（`p3_s4_loop_policy.py:450,485,503,528`）。開始済み pair の評価は途中停止しないが、結果の `stop_reason` は終了時に予算超過へ変わりうる。この読みのままだと、insight の停止理由と次 iteration の可否を誤記する。
- [real] **高** — 保留解除 script が確かめるのは proposal file の存在と top key だけで、preview 通過・auditor 受理・審査時の digest との一致は確かめない（`release-policy.sh:7-12`）。親が解除前にこれらを照合しなければ、不適切な proposal の job が始まる。driver の gate は残るため受理集合は緩まないが、pair が reject または `AuditorGateFailure` となり、評価済み本数と分類が変わる。
- [real] **中** — submit と release の両 script は `qsub`／`qrls` 失敗後も後続コマンドへ進む（`submit-policy.sh:42-43`、`release-policy.sh:12-14`）。表示上の終了だけで成功扱いすると、未投入・未解除の job を予定本数に数え、insight の欠測理由を誤る。
- [real] **中** — pair job の終了コードだけでは候補の certified を判定できない。候補が reject・aborted でも stock が `certified-stock` なら正常終了しうる（`p3_s4_loop_policy.py:409-413,687-697`）。runbook 指定の候補・stock 両 WAL、系列履歴、計測 campaign の照合が必要（`phase3-silo-policy-runbook.md:108-116`）。省けば受理集合と stock 比が膨らむ。
- [real] **中** — 分類表には preview reject、auditor veto による reject、`AuditorGateFailure`、verifier anomaly を伴う非 certified、`eval-exception`、`stopped-before`、強制終了の欠番を別々に残す必要がある（`p3_s4_loop_policy.py:193-204,229-279,468-473`、`phase3-silo-policy-runbook.md:171-173`）。brief の「certified/reject・anomaly」だけでは、未評価や欠番を reject または評価済みに混入させうる。
- [要実測] **中** — `qsub -h --after` は依頼の「`--after` で先に待ち行列へ入れる」を形式上満たし、proposal 不在での起動を防ぐ（`submit-policy.sh:29-37`）。ただし保留中に scheduling 上の利得が蓄積するかは資料に実測がない（`s1-brief.md:13-14`）。利得を前提に評価済み pair 数を見積もると、予算内の実数とずれうる。

## 親 brief の (P1)〜(P4) への判定

- **P1: 修正。** 保留投入は採れる。解除前に親が preview・auditor・digest を照合し、`qsub` と `qrls` の実際の成否を確認する。保留の scheduling 効果は実測値として扱う。
- **P2: 修正。** 3,600 秒は `loop_state` 作成からで、待ち行列も含む（`phase3-silo-policy-runbook.md:117-121`）。判定は開始前と結果後にある。「最大 4 pair」は費用の上限例としてはよいが、LLM と待ち時間を含む達成本数の予測には使えない。
- **P3: 支持。** 同じ job の候補・stock の各 5 rep 中央値から比を出し、1 候補 1 観測とする（`s1-brief.md:16`、`t2865-silo-policy-iter2/README.md:55-64`）。系列 A・B と liveness の値は合算しない。
- **P4: 支持。** 実走と記録に絞った段構成は依頼に沿う（`request.md:11-12`、`s1-brief.md:17-18`）。上記の照合は既存 runbook に沿う運用確認であり、新しい gate や台帳は要らない。

## 総括

正しさ gate とリーク制御の方針自体に、静的資料から緩和は見つからない。  
最大の修正点は、予算判定の時点と、保留解除が保証する範囲の記述である。  
成果物では job の成否、候補の評価結果、未評価・欠番を分けて記録する。  
0.97 node 時間は投入費用の概算として妥当だが、複数 pair の達成保証にはならない。