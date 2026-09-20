## 所見

**判定は条件付き NO-GO です。** 主な未解決点は、TRIGGER_GATING の観測範囲と D2161 の整合、および未定義検査と I1 の衝突です。HEAD は指定の `947fd160a`。以下は静的検査であり、編集・pytest・実 TU の再実走はしていません。

以下、G＝`orchestrator/campaign/condition_meaning_gate.py`、C＝`orchestrator/campaign/s8a_trigger_coverage.py` と略記します。

1. **real／must-fix — P3 は D2161 の部分観測禁止を解消していない。**

   [plan.md:91](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2153-witness-bc/artifacts/dev-wave-t2153-witness-bc/plan.md:91) は skeleton の12箇所だけを観測し、診断用複合条件を除外します。しかし実際の配線先は instr patch を重ねます（C:148–153）。[instr patch:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-bc/patches/instr-silo-backoff-trigger-gating-tally.patch:9) の `#if BACKOFF_TRIGGER_GATING && TRACE` も、同じ所有 TU で当該 macro によって選択が変わる枝です。

   「12箇所まで」と文章で限定しても、admission は macro 単位です。複合枝を例えば `#if TRACE` に変えても12箇所の counts は維持でき、この witness はその欠落を検出しません。`#ifndef` の供給番兵と、実際に出力を生成する診断枝は同列に除外できません。

   **放置時の成果物変化:** 診断枝が未観測のまま `BACKOFF_TRIGGER_GATING` が未確立一覧から消え、レポートが D2161 より強い確立を示します。

2. **real／must-fix — 提案の不在検査は既存 cache macro にも効き、I1 と衝突する。**

   [plan.md:46](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2153-witness-bc/artifacts/dev-wave-t2153-witness-bc/plan.md:46) の条件は全 macro に対する `expected_value is None and not stock_identity` です。G:947–979 は既存 macro にも `default=None` を許し、G:1699–1703 は cache 対照で対象 option を指定しません。

   具体例は既存 `BACKOFF_NOINLINE` の要求 `1/None`。fixed patch:15,24 により対照にも `-DBACKOFF_NOINLINE=0` が供給されます。現行 G:2261 はこの対照値を検査しませんが、提案後は必ず `supply-value-mismatch` になります。これは受理を狭める変更ですが、「既存 macro の全 green/red record 不変」とは両立しません。

   **放置時の成果物変化:** 既存要求の supply 判定・reason・record bytes が変わるのに、I1 達成として台帳へ記録されます。

3. **real／must-fix — E/F の材料は coverage の両実配線を網羅していない。**

   [gating-1v0.stdout.jsonl:1](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2153-witness-bc/login-pre/gating-1v0.stdout.jsonl:1) の configure/source operand は **`ccbench-511c953-gating-misattr`** です。一方、C:148–153 の preflight は skeleton＋instr、C:156–164 は skeleton＋instr＋misattr。F の `gating` 木には instr がなく、`gating-misattr` 木には両追加 patch があります。

   したがって E の gating green を、coverage の最初の腕の exact な実測とは扱えません。静的には同じ12箇所を予測できますが、供給閉包・record の実証は別です。

   **放置時の成果物変化:** 実際には測っていない patch 構成を、driver 同形の完了 cell として実測表に載せます。

4. **refuted／nit — 全箇所計装が不活性箇所を黙って除外する、という攻撃は成立しない。**

   G:2958–2983 の挿入を全 index に適用し、静的件数 N と両腕の `completed=N` を別々に要求するなら、外側 `#if 0` に入った箇所は completion を失って赤になります。同一 macro の自己入れ子も、既定腕で内側の completion が消えるため赤です。外側に合わせて N を再計算してはいけません。

   実 TRIGGER_GATING 12箇所には自己入れ子はありません。BACK_OFF 内の3箇所、NO_WAIT 内の1箇所、残り8箇所です。自己完結した probe を元 directive の直前へ挿入するので、元の `#else`／`#elif` の対応も保たれます（gating patch:101–107,143–148）。

   **放置時の成果物変化:** 提案どおりなら不活性箇所は認証されません。ただし「任意の多重 include でも総数だけで箇所別観測を証明する」まで一般化すると過大主張になります。

5. **refuted／nit — None 対応が直ちに旧宣言や既存 `#if` witness を広げる、という攻撃は成立しない。**

   G:990–1002 の既存 `1/0` 制限を残し、`#ifdef` 登録だけ `1/None` にするなら、既存 `#if` の None 要求は factory 宣言を得ません。旧型は G:649–651、3428–3430、3884–3905、CLI は4217–4225で BACKOFF_FIXED 固定です。

   また、compile argv に出る同名 define は供給元を問わず G:2055–2075 で検出できます。単独なら新不在検査、二重なら duplicate 拒否です。companion の裸 `-D` と CMake target define が重複する説明も、G:1704–1707 と gating patch:26 に整合します。

   ただし **factory=None は family 拒否ではありません**。G:3350以降と4099以降では unestablished のまま admit 可能です。「既定を偽った要求をすべて拒否する」とは言えず、これは既存の境界です。

   **放置時の成果物変化:** 新たな旧経路拡大は確認できませんが、factory 制限を admission 全体の保証と書くと受理集合の説明を誤ります。

6. **real／must-fix — schema 変異の帰属条件を明文化する必要がある。**

   plan の「公開 record の digest を再計算して拒否」は、family を通常呼出しするだけでは不十分です。G:4090付近の issuer 検査が、count 検査を緩めた mutant でも公開 record を拒否します。既存 test:1776 は実際に `_validate_arm_record_integrity(..., require_issuer=False)` を使っています。

   新規 schema 変異も同じ条件で、正常な公開証拠は通ることを先に確認し、count／None／argv 差分だけを改変すべきです。評価側の緩和を `_assert_compile_time_branch_selection` 直接呼出しで検出する案は妥当です。

   **放置時の成果物変化:** schema 検査を壊しても issuer 拒否で test が通り、変異台帳が証拠再検証の有効性を示さなくなります。

7. **refuted／nit — REQUESTED_US 未登録と receipt 分離の判断は妥当。**

   requested-us patch:29,41,60,178 の4箇所を確認しました。G:2998 の owner 専用 shadow は header を別途計装できず、G:3023 の全木経路も単一 source 用です。二回呼ぶだけでは同一 shadow になりません。`#pragma once` は include 回数の助けになりますが、元木と shadow の別ファイルへ include が分岐しない保証ではありません。G:3083付近の `-ffile-prefix-map` も include 解決を変更しません。

   supply は元木の dependency closure を検査します。meaning の shadow を supply に混ぜる変更は避ける必要があります。今回は未登録とする費用判断を支持します。

   C:247–248 の `admission_receipts` は build admission、C:347 の `condition_gates` は preflight の condition 証拠です。MISATTR だけ None にすることによる、この receipt 契約の直接破壊は見当たりません。

   **放置時の成果物変化:** 未登録なら REQUESTED_US は未確立のまま残り、部分観測による誤った確立を防げます。

## 親 brief への反論

- **「全箇所が活性」は対象を限定すべきです。** 現物と保存済み argv からの静的予測は、MISATTR `(1,1)/(0,1)`、RUNG1 `(2,2)/(0,2)`、gating の完全一致12箇所 `(12,12)/(0,12)`。REQUESTED_US は正しく同時計装できれば `(4,4)/(0,4)` です。requested-us の実 argv でも `BACK_OFF=1` を確認しました。これらは新 witness の実走結果ではありません。
- **nest.sh は箇所網羅性の証明ではありません。** 行番号を手で列挙し、nest.awk は物理行で深さを数えます。今回の対象行にコメント・raw string・行継続による偽 directive は見当たりませんでしたが、instr の複合条件は列挙対象から落ちています。
- **MISATTR の login 赤の説明は支持できます。** 保存 argv は両腕とも gating/no-wait=1、MISATTR だけ1対0。実 patch は `#ifdef` なので同じ枝になります。1対未定義で digest が変わる保存結果とも整合します。ただし動的な誤帰属発火の証明ではありません。
- **件数は plan の訂正が正しいです。** 現物は枝選択18件＋BACKOFF_FIXED＝19件。三件追加案なら21件／22件であり、17→20ではありません。
- **I1 の同一入力再生は必要ですが、十分ではありません。** 同じ observation を再生して bytes が一致しても、所見2のように observation に到達する前の供給判定が変わる経路は検出できません。
- **I5 の負例は限定が必要です。** 無関係 comment や、directive・include・define を変えない本文編集について counts／判定不変を要求するのは妥当です。source digest と record bytes 全体の不変は要求できません。

## 段 5 実装子へ渡すべき条件

1. P3 を段4で確定すること。診断複合枝を除外して macro 全体を確立扱いするには、D2161との整合を明示的に解決する。未解決のまま登録を完了しない。
2. 未定義検査の適用範囲と I1 の対象要求を一致させること。全 macro に適用するなら、既存 None 要求の判定変更を明示し、無変更と報告しない。
3. N は登録値に固定し、静的件数と両腕 completion を独立検査する。自己入れ子、不活性箇所、`#else`／`#elif` を負例に含める。
4. 再検証では N・選択数・`None`・同名 define 不在を検査する。argv 正規化は対象の `-D` token だけを除去し、他 macro や `-U` を消さない。
5. schema 変異は issuer 検査を除いた検証でも正常対照が通り、改変だけが落ちる構成にする。
6. 最終 production 登録簿で、coverage の二つの patch 構成と rung1 を別 cell として実測する。MISATTR/RUNG1 の共有 build root 化による supply 差も分離する。
7. coverage/frequency の `condition_gates` と rung1 の永続化結果を確認する。build receipt を meaning 確立の証拠に代用しない。

## 総括

機構案の中心部分は妥当ですが、**P3 の部分観測と I1 の適用範囲を未解決のまま実装へ渡すべきではありません**。REQUESTED_US の延期は支持します。実測表の patch 構成と変異の帰属条件も訂正したうえで進めてください。