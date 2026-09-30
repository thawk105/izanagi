## 総括

**NO-GO。** 計画のままでは、小モデル結果の自己申告を完了証拠として受理でき、既存台帳の再利用時に要求つき判定が走らない。さらに、新 driver から使えない fan-out を検証対象に含めている。これらを直せば、配線実装と fixture による生死確認には進める。

## 所見

1. **must-fix — 小モデルの「完了」が被覆証拠に結び付いていない。** 計画 `plan.md:27-29` は場面 ID と `complete=True` を要求するが、段 A の仕様は L2-5 の36順列ごとの到達、L3 の全構成など具体的な被覆を要求する（`gen-opt-stage-a-candidate/README.md` §5.3）。結果 file の `checker_identity`、digest、完了フラグはいずれも file 自身の申告である。**影響:** 探索していない結果でも関門が緑になり、候補の受理集合が広がる。**修正:** 事前登録した場面ごとに、期待構成数・探索済み数・停止理由・必要な到達 witness を閉じた schema で照合し、生成元と実行結果の束縛を md_19 と合意する。登録値を空から本番値へ変える条件も明記する。

2. **must-fix — 既存 terminal 行を再利用すると要求つき判定に到達しない。** `loop.py:884-895` は同じ variant が `done` にあれば `evaluate` を skip する。計画 `plan.md:22,37-39` は呼出し伝播と新 history を扱うが、既存の版1／要求なし結果の再利用条件を定めていない。**影響:** 台帳には旧 certified が残る一方、新しい要求を満たした結果が生成されず、参照先によって certified の意味が食い違う。**修正:** 新 driver は別 campaign identity を使い、再開時にも版2・`required=True`・D5 pass の当該 attempt だけを適格とする。旧行を昇格させず、新 history に skip と不適格理由を記す。

3. **must-fix — driver の成功判定が要求の実効値を再確認しない。** 計画 `plan.md:37-39` は `result.certified` と `verifier_digest` を履歴化するが、要求あり・意味の版2以上・D5 pass を certified 行の条件として明記しない。判定器の条件は D2321 項4、投影 field は `verifier/report.py:138-157`。**影響:** 接続漏れや古い結果を driver が certified と記録しうる。**修正:** 全 workload／反復の判定結果と receipt について `required`、版、D5、D1/D2 の状態を照合してから certified 行を作る。不足時は閉じた拒否コードにする。

4. **must-fix — fan-out の計画が現行の実行条件と合わない。** 計画 `plan.md:22,41` は新 driver の fan-out 伝播を試すが、現行分岐は `pipeline.py:2772-2783` で `GeneratorId.BACKOFF_REPRO` に限定され、task 作成も `pipeline.py:861-870`、worker も `verify_fanout_worker.py:176-180,210-234` で backoff 専用である。**影響:** 新 driver の fan-out 試験が実経路を通らず、要求の取りこぼしを検出したという主張が成立しない。**修正:** 今回は新軸の fan-out を非対応として明示し、実際に通る local／local concurrent の全反復を検査する。新軸の remote fan-out は admission・worker を含む別 scope とする。

5. **should-fix — snapshot と build の一致条件を計画に固定する必要がある。** 現行 `source_digest.py:2413-2464` が snapshot を取り、`pipeline.py:1905-1937` が再取得し、`buildcache.py:3656-3700` が build 出口で再照合する。計画 `plan.md:19-21` の変更をこの三点すべてに通せば、build 後の disk 書換えや別 root を D5 が読んでしまう問題は塞げる。一方、U-D の直 build はこの再照合経路を使わない（`plan.md:45-47`）。**影響:** U-D で snapshot と実際の build source が違っても D5 pass と報告しうる。**修正:** U-D でも正規 build 境界の入口・出口照合を実行するか、certified を報告せず「要求つき判定の配線確認」に限定する。別 root、build 中変更、build 後変更の三例を区別して試す。

6. **should-fix — 反例と失敗理由の総量・語彙が閉じ切っていない。** `schema.py:81-97,100-163` は個々の反例を制限するが、計画 `plan.md:27,39` には結果 file の場面数・反例数・総 bytes・history 行数の上限がない。語彙を渡さなければ `name`・`judgment_id`・`rule_id` は形だけを検査する。既存 `_result_history` は gate の D1/D2/D5 理由を投影しない（`p3_s4_loop_policy.py:313-336`）。**影響:** coder 入力が巨大化し、また失敗の種類が `indeterminate` に潰れて次の提案を誤らせる。**修正:** 軸固有の固定語彙、反例数・総 bytes・履歴件数の上限を設け、gate 違反を列挙コードと有界な件数で投影する。例外本文、`message`、`justification`、未登録 key は coder 入力に入れない。

7. **should-fix — 実装の所有範囲と接続点が食い違う。** brief `s1-brief.md:42-43` の U-A 所有集合は verifier・`source_digest.py`・`pipeline.py` だが、計画 `plan.md:22` の要求伝播には `loop.py` の API と二つの `evaluate` 呼出し（`loop.py:522-560,960-984`）が必須である。`plan.md:37` の新 driver もその API に依存する。**影響:** 単位をそのまま並列実装すると keyword が driver から判定器まで届かず、候補が要求なしで評価される。**修正:** `loop.py` を U-A の所有集合へ加え、引数と互換分岐を先に固定する。stock 対照、再試行、各反復、CLI 単独経路を別々に確認する。CLI は既に要求を渡す（`verifier/cli.py:72-77`）ので、その挙動を維持する。

8. **should-fix — 要求なし bytes 不変の試験範囲が狭い。** D2321 項3・理由は結果投影と receipt の byte 不変を要求する。計画 `plan.md:18-23` は主要な投影・snapshot JSON を挙げるが、source binding、fan-out の旧 task、campaign lock と再開時 WAL の比較条件を固定していない。**影響:** 要求しない既存 caller の receipt digest や lock が変わり、既存結果が drift／不適格になる。**修正:** 要求なしの旧 fixture を基準 bytes として、source evidence、task、判定投影、receipt、lock を通しで照合する。要求ありの追加 field は専用 schema／条件分岐に閉じ込める。D442 によるコード閉包の E1 drift は別件として記録する。

9. **nit — 生死確認の成功表現を限定する。** `plan.md:45-49` は fixture と patched pin C を使う一方、`source_digest.py:97-100` の allowlist は U1 の header 変更を受け入れない。判定器自身も D5 は source 文面の検査で発火の証明ではないと記録している（`gen-opt-gate-verifier/README.md` §9）。**影響:** 配線の緑を本番 pin の certified と読むと、レポートの参照が実際の評価対象から外れる。**修正:** fixture、patched source SHA、admission の可否、要求つき判定の各 field を記録し、「fixture 付き配線確認」と表示する。本番 certified は pin 前進と md_19 の実結果で再走する。

## (P) への賛否

- **P1:** 条件付き賛成。driver の明示要求と flag 強制は有効。ただし旧 terminal 再利用と `loop.py` 接続を含める。
- **P2:** 条件付き賛成。消費 schema の先行定義はよいが、自己申告の `checker_identity` と `complete` だけでは本番証拠にならない。
- **P3:** 賛成。期待 digest の独立登録と未登録時拒否は必須。fixture 注入経路を本番入口から分離する。
- **P4:** 条件付き賛成。全順列の仕様一つでよいが、L1〜L3 の被覆数と witness を検証する。
- **P5:** 賛成。名前つき対照の一周に新 role は不要。coder 入力の閉じた投影は今回の範囲に残す。
- **P6:** 賛成。計数 build は今回の certified 条件外。発火率・段 A の効果は主張できない。
- **P7:** 条件付き賛成。述語を維持するなら版2据え置きは妥当。build 境界の再照合を U-D にも適用する。
- **P8:** 賛成。現行 pin で本番 certified は言えず、fixture の成功を配線確認として刻む。

## 変異の帰属

- driver の `require_gate_witness=True` を削る変異は、P1 の flag 強制が正常なら判定は赤にならない。spy は driver の契約違反を検出する試験であり、certified の防壁を単一理由で示す変異ではない。
- pipeline の flag 強制を削る変異も、driver が明示 `True` を渡す通常経路では赤にならない。**明示要求なし・flag=1** の独立 caller で検査する。
- 新 driver の fan-out 伝播変異は現行 admission が先に遮る。新軸の remote 経路の検出力として数えない。
- snapshot D5 を disk 読みに戻す変異は、disk が同じままなら赤にならない。capture 後の書換えを入れた試験だけに帰属させる。
- `complete=False` と場面欠落の変異は別々に走らせる。両方を同時に壊すと、どちらの関門が効いたか分からない。

## scope 外に返すべきもの

- md_19 の本番モデル実行、被覆 witness と結果生成元の束縛、仕様 digest の本番登録。
- pin 前進、U1 と Silo 修正の統合、その tip での D297 と certified 再走。
- 新軸を remote fan-out で使うための build admission・worker 契約の拡張。
- 新 coder role／adapter と、仕様と候補実装の対応を読む auditor の運用接続。
- 並べ替えを使った取引数の計数 build と段 A の効果評価。