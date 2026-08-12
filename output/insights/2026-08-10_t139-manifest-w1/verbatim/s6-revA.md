# 防御レビュー結果: NO-GO

blocker 2 件、must-fix 3 件です。現状のまま wave を閉じてはいけません。pytest は実行せず、指定ファイルの静的検査と副作用のない validator probe のみ行いました。

## Blocker

### B1. 第 2 erratum の `new_text` が凍結されておらず、強い主張へ再置換できる

起草された実際の置換文は、「事前固定した stress model のもと」という限定が明示されており、core §7 の一般的な cluster-level 較正義務を、限定モデル下の確認へ適切に弱めています。[erratum-core-s7-stresscheck.md](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w1/output/insights/2026-08-10_t139-manifest-w1/erratum-core-s7-stresscheck.md:84>)

しかし検査契約は exact replacement を固定していません。

- 文書の検査 4 は「1 行かつ `事前 simulation` を含む」だけです。[同文書](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w1/output/insights/2026-08-10_t139-manifest-w1/erratum-core-s7-stresscheck.md:87>)
- 実装はさらに弱く、新旧がそれぞれ 1 行かだけを検査し、`事前 simulation` の存在すら検査しません。[erratum.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w1/orchestrator/preregistration/erratum.py:390>)
- テストも複数行の拒否しか固定していません。[test_t139_preregistration_binding.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w1/orchestrator/tests/test_t139_preregistration_binding.py:467>)

実 core を用いた probe では、次の両方が validator を通りました。

```text
事前 simulation で cluster level の型 I 誤りを較正済みである。
型 I 誤りは問題ない。
```

前者は文書上の検査 1〜4 もすべて満たしながら、除去対象だった強い主張を復活させます。`expected_composed_sha256` は caller が与えるため、変更後 digest の照合も防壁になりません。

修正には、erratum ID 固有 validator で承認予定の `new_text` bytes または SHA-256 を exact 固定し、上記 2 反例を拒否するテストが必要です。

影響: 放置すると `compose_core` の受理集合に任意の 1 行置換が入り、材料レポートが未証明の cluster-level 型 I 誤り制御を主張できるようになります。

### B2. Q-A 第三分岐は「実行していない」を証明せず、偽の試行台帳を受理する

§3.2 の 6 条件をすべて満たしながら、実際には performance run を実行済みの attempt を構成できます。[record-items-reissue.md](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w1/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:88>)

具体例:

1. `scope=preflight` の observation を 1 件置く。
2. producer が作った 7 列の偽 `/proc/stat` bytes を `stat_before_raw` / `stat_after_raw` として pin する。
3. validator は `short_columns` を raw から再計算できる。
4. monotonic 時刻を単調かつ 10 秒窓にする。
5. `malformed_reason_or_null=short_columns` とする。
6. marker を `null`、`actual_runs[]` の当該 attempt 参照を削除する。

実 run の存在とは独立に全条件が成立します。§6 はこの偽造可能性を正しく認めていますが、非保証の記載は台帳の真正性を回復しません。[同文書](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w1/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:254>)

producer 権限外の collector、または同等の外部 provenance が投入前条件です。この残余を「承認時に引き受ける」だけでは、再現可能な試行台帳という成果物には不足します。

影響: certified 数値は記載上の完全性 gate で直接は上がらなくても、試行台帳とそこから作るレポートは「実行済みの不利な run を実行しなかった」と記録できます。

## Must-fix

### M1. nested 閉包 7 件は列挙されたが、`translation_units{}` が全 nested object 閉包宣言と矛盾する

前版が未閉包とした 7 object はすべて再登場しています。

1. `attempts[]`
2. `allocations[]`
3. `liveness[]`
4. `admission_telemetry[]`
5. `phase_caps[]`
6. `cluster_slots[]`
7. `translation_units{}`

ただし、文書は「全 nested object に `additionalProperties: false`」と宣言する一方、`translation_units{}` では個数無制限の動的 key を `additionalProperties` schema で受けるとしています。[record-items-reissue.md](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w1/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:126>) [同 §4.7](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w1/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:228>)

値 object は閉じていますが、key 名の機械的制約は未定義です。「repo 相対 path」という散文だけでは、絶対 path、`..`、空 key、非正規化 alias の受理が実装依存になります。map 型を明示的な例外とし、`propertyNames`/`patternProperties` と正規化規則を固定する必要があります。

影響: schema 実装ごとに `translation_units{}` の受理 key 集合が変わり、同じ受領証から適格 cluster 集合が分岐します。

### M2. `malformed_reason_or_null` は実際には受理条件の入力である

条件 5 は、非 null 値が再計算結果と不一致なら受領証を拒否します。[record-items-reissue.md](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w1/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:101>)

したがって、この値は失敗成立の「正の証拠」ではありませんが、数学的には受理集合を狭める入力です。「受理条件の入力にはしない」は不正確です。「失敗成立は raw のみから導出し、非 null の申告値は負方向の整合性検査にだけ使う」と書くべきです。

影響: 現文のままでは、条件 5 を実装する validator と「入力にしない」を字義どおり無視する validator で、不一致理由を持つ受領証の受理集合が変わります。

### M3. 「三値」は排他的な三状態ではなく、registry 軸と承認状態軸の混同である

decision fragment は `validator_registered / draft_unapproved / approved` を三状態としています。[decision fragment](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w1/docs/spool/decisions/2026-08-10-dev-wave-t139-manifest-w1-1.md:9>)

しかし実装では、すべての approved/draft ID が同時に registered でなければならず、`validator_registered` は他 2 状態と排他的ではありません。[erratum.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w1/orchestrator/preregistration/erratum.py:24>) [registry 検査](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w1/orchestrator/preregistration/erratum.py:428>)

正しいモデルは、概ね次の二軸です。

```text
validator: unregistered | registered
approval:  draft_unapproved | approved
```

影響: 後続 resolver が「approved は registered ではない別状態」と実装すると、承認済み erratum の validator を飛ばすか、逆に承認済み文書を拒否し、承認 errata の受理集合が実装依存になります。

## 個別レンズへの判定

- 検査 1〜3 は恒真ではありません。2 operations、ゼロ SHA、対象語句 2 件という具体的拒否入力があります。
- 実 core で対象語句は実際に 221 行の 1 件だけです。[凍結 core](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w1/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:219>)
- 置換後 core への再適用は対象語句が 0 件になり、`OccurrenceCountError` で拒否されます。
- `compose_core` が draft を合成できること自体は、D264 の純関数分離と整合し、現時点の admission fail-open ではありません。[D264](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w1/docs/decisions.md:12185>) 実際、テストも draft 合成を正例にしています。[test](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w1/orchestrator/tests/test_t139_preregistration_binding.py:758>)
- ただし `approved_erratum_ids()` の production caller は 0 件です。したがって三値分離は現時点では承認を強制しておらず、単なる問い合わせ部品です。pilot が止まっている理由は承認検査ではなく admission API が存在しないことです。
- D263 の決定本文を残し、誤った理由上の事実だけを新 decision で前向きに supersede する形式自体は妥当です。[D263](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w1/docs/decisions.md:12162>) 問題は、置換先の「三値」モデルの表現です。

## 総括

**NO-GO。**

最低限、次を満たすまで閉じられません。

1. 第 2 erratum の `new_text` を ID 固有の exact bytes/digest として固定する。
2. Q-A 第三分岐を外部 collector 等で実行事実へ束縛するか、未解決 blocker として承認・wave closure を止める。
3. `translation_units{}` の動的 key 閉包、条件 5 の位置付け、registry/approval の二軸モデルを文書で一意化する。