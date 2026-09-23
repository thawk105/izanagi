## 判定

NO-GO

## 前巡所見の対応表

以下、`J` は指定 job dir の `runs/`、節番号は修正後 README を指す。

| 所見 | 状態 | 根拠 |
|---|---|---|
| must-fix 1：V03 の分類・集計 | partial | 4 thread を「別の層で検出」に変更した点は正しい。`J/s3-1/verifier/0003.json` の X＝1,213,194、巡回＝5,510、version dup＝6,692 と一致。ただし新しい「期待した層で検出8」に、検出のない S を含めている。 |
| must-fix 2：動的発火の過大表現 | closed | §1 を「build・実走」に変更。ptrswap の発火は未確認、erase・forge の平均差は取引ごとの直接証拠ではないと限定し、§3.2・§4 と整合した。 |
| must-fix 3：差し替え説明 | closed | §2.1 が `build(cc,cxx,cache_root)` と `resolve_evidence(cxx)` を分離。s3・s5 の `meta.json/replaced_names` と一致。 |
| should 1：emitter だけへの帰属 | closed | §3.2 は「設計上の期待と整合する」に限定。設計書§4.3 の期待に沿い、emitter だけを変えた比較とは主張していない。 |
| should 2：opswap の原因・履歴の限界 | closed | driver の `abort_exercised=true`、verifier の `abort_reasons={}`、1取引・6書き込みと一致。原因と時系列を仮説に留め、§4 に1取引の履歴という限定を追加した。 |
| nit：参照節 | closed | §1項3 の参照先は正しい §3.2 に修正済み。 |

## 新しい所見

- **must-fix：期待一致数を検出数と呼んでいる。**
  [README §1](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2847-patch-verify/output/insights/2026-09-23/t2847-patch-verify/README.md:16) と [§3.4](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2847-patch-verify/output/insights/2026-09-23/t2847-patch-verify/README.md:107) の「期待した層で検出8」は不正確。列挙の8件目である highkey legacy は、`J/s2-1/verifier/0004.json` で certified=true、巡回・違反counterとも0。条件付き期待への一致ではあるが、異常の検出ではない。**「期待どおり12＝期待した層で検出7＋対象外条件で期待どおりS 1＋盲点としてS 4」**に直せば、総数を維持して解消できる。V03 の4 threadは、期待した層も検出したが「別の層」に分類した1 runとして別計上する。

- **should：§3.4 の run 数列に patch 数が混在する。**
  [§3.4](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2847-patch-verify/output/insights/2026-09-23/t2847-patch-verify/README.md:103) は「集計はrun数」「patch単位は最後の行」と宣言する一方、「その他」に `1 (patch)` が入る。注記により識別はできるが、4分類のrun集計として加算できない。その他を **0 run（別記：未実走1 patch）** とするか、列を分ける。

- **nit：なし。**

## 再計算した値

verifier 全18出力を読み、`raw/verifier-summary.jsonl` の判定・取引数・書き込み数・巡回・integrity等と照合した。不一致はなかった。

| 対象 | 再計算・判定 |
|---|---|
| 変異run数 | s2＝4、s3＝3、s5＝2、t152＝4。合計 **13**。対照等5 runは除外。 |
| §3.1「6本（9 run）」 | V01〜V06 の6本、2＋2＋2＋1＋1＋1＝**9 run**。一致。 |
| 期待どおり | **12 run**。内訳は検出7＋到達しない条件のS 1＋盲点S 4。 |
| 別の層で検出 | **1 run**：V03 の4 thread。 |
| 未発生 | **0 run**。highkey legacy は対象に届かない条件で期待したSであり、schedule依存の未発生に数えない。 |
| その他 | 実走分は **0 run**。sort-nonswo は未実走 **1 patch**。 |
| 「10本とも少なくとも1条件で」 | 成立。V01・V02はS2、V03は1 thread、V04〜V06は各単独条件、V09〜V12は各盲点条件で期待に一致。 |
| §1と§3 | 総数は一致。「検出8」の意味上の誤りを両節が共有している。 |

「8」の列挙自体には重複・欠落がない。内容は次のとおり。

| run | 観測 |
|---|---|
| norw S2 | 巡回3,262 |
| norw legacy | 巡回703 |
| highkey S2 | 巡回3 |
| lockskip 1 thread | X＝910,280 |
| early-unlock | X＝494,700 |
| permutation-erase | P＝251,087 |
| permutation-swap | P＝756,171。commit 0でもPの観測はある |
| highkey legacy | S、巡回・違反0。**この1件は検出ではない** |

取引あたりの平均は、原出力の `writes / txns` から再計算した。

| 条件 | 計算 | 平均 | stockとの差 |
|---|---|---:|---:|
| stock | 1,176,794 / 133,991 | 8.7826346546 | — |
| erase | 1,094,995 / 140,714 | 7.7817061557 | −1.0009284988 |
| forge | 1,269,833 / 129,883 | 9.7767452245 | ＋0.9941105700 |
| opswap | 6 / 1 | 6.0 | −2.7826346546 |
| ptrswap | 1,190,447 / 135,589 | 8.7798198969 | −0.0028147577 |

**7.78・9.78・8.78、および「約1少ない／多い」は正しい。** §3.2 の小数4桁も一致する。平均差を直接的な発火証明にしない限定も妥当。

## 総括

前巡6件は **closed 5・partial 1・regressed 0**。opswap、emitter帰属、§4の追加は、確認した証拠の範囲を越えていない。

残る必須修正は「期待一致8」を「検出8」と呼ぶ箇所。READMEの記述修正で解消でき、追加実走は不要。今回は静的照合のみで、ファイル変更は行っていない。