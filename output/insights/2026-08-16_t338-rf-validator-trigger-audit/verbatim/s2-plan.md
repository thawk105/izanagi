## 発火条件の判定

以下、`refs/...` と `s1-brief.md` は親 job の `t338-rf-validator/` 基準、その他は repo 基準で示す。D162 決定 (10) の発火条件は三つの連言である (`refs/D162.md:49-55`)。

| 条件 | 判定 | 実地確認 |
|---|---|---|
| (i) 3 arm、事前登録を実走前に commit | **path/ID を書ける** | request `892042.nqsv`、`output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/`。事前登録は engineering screen・J=1・nonqualification だが実走前凍結を宣言し (`output/insights/2026-08-05_t139-alt-x-probe/preregistration.md:1-15`)、stock/mode1/modeX の 3 arm を固定している (`:31-32,50-62`)。witness は repo head `425ed190...` と事前登録 digest を持つ (`.../preregistration-witness.tsv:2-10`)。submission receipt は request `892042.nqsv`、同 commit と不変 digest を記録する (`output/insights/2026-08-05_t139-alt-x-probe/submission-receipt.md:55-73`)。commit 時刻は完走時刻 `steps.log:1` より前で、F157 も「成立していたのは (i)」と確定している (`docs/failures.md:4499-4518`)。 |
| (ii) 同じ計測に環境タグ・測定 checkout・pin・attestation | **書けない** | `892042` には checkout (`.../preregistration-witness.tsv:3`、`.../state/terminal-state.tsv:3`) と依存 pin (`.../dependency-witness.tsv:3-8`) はある。しかし artifact 内の `env_tag` と `attestation` はともに 0 hit。これは F157 の確定事実 (`docs/failures.md:4501-4518`)。`orchestrator/qualification/contract.py:150-159` の Pegasus 環境契約は T-126 の別機構であり、この計測の証拠ではない。T-126 artifact の遡及昇格も D162 決定 (8) が禁止する (`refs/D162.md:42-44`)。四項すべてを持つ計測 path/ID は見つからない。 |
| (iii) 判定を読む consumer の実 hook | **書けない** | `recovery_fraction`、`rf_acceptance`、`pairing_valid`、`weak_denominator`、`fieller`、`delta_D` の `orchestrator/`・`tools/` 検索は 0 hit。Q11 自身も RF consumer 不在を明記する (`refs/t338-package.md:291-300`)。現行設計メモも consumer 0 件、実装は将来形としている (`output/insights/2026-08-05_t337-qualification-authority/mechanization-design.md:1-7,19-22,47-55,98-102`)。 |

したがって、(i) の path/ID は実在するが、三条件をすべて満たす path/ID は書けない。`DW-G04` (`refs/dev-wave-core.md:60-63`) により production code・schema・test の機械化は発火しない。

## 親実測の検証

| # | 判定 |
|---|---|
| 1 | **誤りなし。** 現在の 19 worktree を再走査し、対象 2 ファイルに main 差分を持つ branch 0、dirty copy 0。 |
| 2 | **誤りなし。** 親記載の六トークンを `orchestrator/ tools/` で再検索して 0 hit。 |
| 3 | **誤りなし。** D162 決定 (10) と D229 決定 (6) はそれぞれ発火条件と `producer → pilot → validator/consumer → 本走` を固定している (`refs/D162.md:49-55`、`refs/D229.md:43-51`)。 |
| 4 | **結論は正しいが、根拠の種類と行番号を要訂正。** `pilot_ready` は `orchestrator/preregistration/stress_check_simulation.py:737`、未充足 `[1,4,5,6,7,8,9]` は `:738`。ただし同 module は admission gate ではない (`:1-6`)。機械的な正しい状態値は `pilot_submission=forbidden`、`main_submission=forbidden`、`source_main_run_gate=not_implemented` (`docs/decisions.md:13470-13482`) であり、解除権限は canonical decision のみ (`docs/decisions.md:13581-13588`)。 |
| 5 | **誤りなし。** `2026-08-15-rulings-full-33rulings.md` は採番済み 26 件 (`:16-45`) と未採番 7 件 (`:47-57`) の計 33 件で、本件語彙の hit は 0。 |
| 6 | **誤りなし。** Q11 は producer、attempt registry、schedule validator、RF calculator、consumer、双射・変異検査等を T-339 として明記する (`refs/t338-package.md:302-312`)。 |

親 P1 の「三条件を満たす path は書けない」という連言の結論は正しい。ただし条件別には (i) の `892042.nqsv` を明記しないと、F157 と同じ粒度不足になる。

## 実装可能 slice の探索

1. **独立 validator と consumer の本体**

   - 抵触: D162 決定 (10)、`DW-G04`、D229 決定 (6)、Q11 の T-339 境界。
   - (ii)(iii) が不成立で、pilot より先の validator 実装にもなる。
   - **却下。**

2. **D229 決定 (2)〜(5) の純粋統計核だけを実装**

   - 仕様面は固定済みであり、受理三条件、ratio projection、閉表、`d=1.0` と J 導出規則には抵触しない (`refs/D229.md:13-41`)。
   - しかし実体は Q11 が T-339 に置いた「RF calculator」である。pilot 前の機械化となり D229 決定 (6) に抵触する。consumer なしの library/test は D147 決定 (3) の未結線 leaf (`docs/decisions.md:7202-7215`) と D163 決定 (1) の fixture 限定 leaf (`docs/decisions.md:8084-8104`) にも当たる。
   - **却下。**

3. **既存 `verify_floor_artifact` を利用または硬化**

   - 生 session から cells/floors を再計算する有効な先例である (`orchestrator/campaign/s8b_floor_stats.py:593-624,667-715,798-883`)。実 consumer も存在する (`s8b_holdout_freeze.py:1391-1395`、`s8b_ratified_freeze.py:2235-2246`)。
   - ただし同 verifier 自身が attempt registry・schedule・raw 真正性を保証しないと明記する (`s8b_floor_stats.py:598-602`)。さらに RF を floor 閉表へ混載することは D162 決定 (9) と Q11 推奨 2 に反する (`refs/D162.md:46-47`、`refs/t338-package.md:306-309`)。
   - RF と独立な既存欠陥も見つからず、`DW-G02`・`DW-G05` の成果物影響を書けない。
   - **却下。将来実装の構造的先例にのみ採用。**

4. **既存の自己申告経路を先に硬化**

   - 凍結 ledger と driver は `research_goal_eligible=False`、`recovery_measurement_eligibility=False` 等を既に exact 検査する (`orchestrator/campaign/silo_ladder_rung1.py:1264-1274,4713-4721`、`silo_ladder_rung1_contract.py:538-565,620-631`)。
   - D162 決定 (7) により、これは entry-local な負制約であって正例への昇格権威ではない (`refs/D162.md:35-40`)。修正対象となる自己申告 consumer は存在しない。
   - **却下。現行負制約は維持。**

5. **J 禁止を approval payload・erratum・blobref へ結線**

   - 規範は既に十分具体的で、pilot slot は exact `[1..8]`、main は消費 slot 数を J と一致させ、予備を母数へ加えない (`output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:306-347,677-684`)。J の選択規則と `J_max=13` も凍結されている (`output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:607-628,738-753`)。
   - しかし record-items は要件文書で実装ではなく (`record-items-v2.md:14-28`)、semantic validator が無いため制約は発火しない (`:801-827`)。現行 package は gate でないと宣言し (`orchestrator/preregistration/__init__.py:1-6`)、D264 は gate 完成前の resolver・submit・receipt API を export しないよう命じる (`docs/decisions.md:12185-12204`)。approval payload も descriptor を読むだけで台帳実在を証明しない (`orchestrator/preregistration/approval_payload.py:129-155`)。
   - digest や文書を検査するテストだけでは、追加 qsub、別 family root、結果後の slot 追加を止めない。
   - **却下。**

6. **`892042` を固定 fixture にした拒否テスト**

   - (i) を持ち (ii) を欠く負例としては有用。
   - ただし D162 決定 (10) は負例の存在を機械化根拠にしないと明記する (`refs/D162.md:54-55,63-70`)。accept branch と consumer が無い拒否専用 leafになる。
   - **却下。**

抵触しない production implementation slice は 0 件である。

## 起草

**実装しない。** 本 wave の成果物は docs-only とし、次の構成を親へ提案する。

- `output/insights/2026-08-15_t338-rf-validator/README.md`
  - `authority: none`、`default_effect: no-state-change`
  - 実装差分・schema 差分・受理集合変更が 0 であること
  - T-339 非実装境界

- `output/insights/2026-08-15_t338-rf-validator/trigger-audit.md`
  - (i) `892042.nqsv`、(ii)(iii) 不成立の四項別証拠
  - 実行した限定検索と 0 hit の範囲
  - F157 を再発防止根拠として引用

- `output/insights/2026-08-15_t338-rf-validator/s2-plan.md`
  - 本起草を逐語保存

- `output/insights/2026-08-15_t338-rf-validator/s4-adjudication.md`
  - 候補六件を real/refuted、scope 内外、採否で固定
  - `DW-S04` に従い「実装差分ゼロ」と裁定

- `output/insights/2026-08-15_t338-rf-validator/package.md`
  - ユーザーへ次の択一を返す。

  **A、推奨:** D162・D229・D264・D291・D292 と T-339 境界を維持し、本 wave は NO-GO。canonical decision による pilot 解禁、(ii) を満たす pilot artifact、(iii) の実 consumer hook が実在してから validator wave を再起票する。

  **B:** 今すぐ実装する必要があるなら、D162 決定 (10) と D229 決定 (6) を明示的に supersede し、T-339 除外を解除した別 wave とする。producer・attempt registry・receipt/schedule validator・RF calculator・consumer・J admission を scope に戻し、pilot 投入は D292 に従う別の canonical 解除裁定を経る。

- `docs/spool/worklog/2026-08-15-t338-rf-validator.md`
  - T-338 を「(i) のみ実在、(ii)(iii) 待ちの実装待ち」と記録
  - certified 選択、材料レポート、proof chain、凍結 bytes、受理集合が不変であること
  - pytest は親が行い、本段は read-only 静的検査のみだったこと

択 A の場合、新しい decisions fragment は不要である。既存裁定を変更せず、新事実と NO-GO を worklog/insights に記録すれば足りる。

## 落とし穴

- `stress_check_simulation.py` の固定 `pilot_ready=False` を検査して「投入 gate」と呼ぶ。これは状態表示であり qsub を止めない。
- 同じ共分散・同じ臨界値から作った Fieller 集合と ratio projection を別々に比較する。D229 決定 (3) により同値なので恒真検査になる (`refs/D229.md:20-25`)。
- producer が書いた `J` と、producer が選んだ `consumed_cluster_slots` の長さだけを比較する。両者を結果後に一緒に増やせる自己根付き gate になる。
- approval payload、erratum、blob digest の pin をテストして「J 追加禁止を機械化した」とする。固定できるのは文書 bytes までで、投入履歴・全 attempt・slot 消費は止めない。
- `rf_stats.py` の純関数を合成 fixture だけで緑にする。raw receipt の真正性、producer、consumer 同一呼出しが無く、未結線 leaf になる。
- `892042` を拒否できるだけの validator を置く。正の発火経路がなく、accept 集合が空の deny-only adapter になる。
- producer の decision、validator source hash、`pairing_valid`、`rf_acceptance_status` を consumer が読む。D162 決定 (2)(4) が禁止する自己申告・偽 decision 経路である。
- hash 用読取と parse 用読取を分ける、または検査前後で再読する。単一 fd/snapshot を欠き ABA と symlink 差替えを許す (`refs/D162.md:22-29`)。
- T-126 の Pegasus contract/artifact や S8b floor 閉表を流用して RF 正例を昇格する。D162 決定 (8)(9) と別 namespace 要求に反する。
- failed submission を台帳から落とす、新しい parent/family ID でやり直す、予備を新しい slot として J に加える、未使用 slot を追加反復へ転用する。D229 決定 (8) の必須変異 (`refs/D229.md:60-65`) と record-items の同一 slot 置換規則 (`record-items-v2.md:677-684`) で将来必ず kill すべき経路である。

## 総括

**NO-GO。** 条件 (i) は request `892042.nqsv` で満たすが、同じ計測に `env_tag` と attestation がなく条件 (ii) は不成立、RF 判定を読む実 consumer hook もなく条件 (iii) も不成立である。純粋統計核、既存 verifier 流用、J 凍結の部分結線はいずれも D162/D229/D264、T-339 除外、未結線 leaf 禁止のどれかに抵触するため、規律を破らず land できるコード slice はない。本 wave は実装せず、発火条件監査と択 A/B を持つ docs-only 裁定パッケージへ進めるべきである。