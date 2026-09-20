| 所見 | 判定 closed/partial/regressed | 根拠 (v5 の行番号) |
|---|---|---|
| F1：保全済み・verifier 未開始の初回検証再開 | closed | L356–376、L694–741、L990–998。4分類を実装し、復元後に1800秒で初回 verifier を実行する。 |
| bench 不再生成 | closed | L361–376、L870–879、L1158–1170。既存 rep から `measure` へ進まず、複数 bench attempt も拒否する。 |
| 校正 bench 失敗の pass 阻止 | closed | L342–345、L1122–1124、L1245–1246、L1362。cohort の失敗を開示し、pass と本走投入を阻止する。 |
| 失格の優先評価 | closed | L1089–1093、L1132–1142。対象・判定集合内の完走 anomaly を、構造・SHA・規約不適合より先に評価する。 |
| job 段 record の集計 | closed | L1037–1044、L1214–1219、L1116–1121。校正・本走の job 段失敗を収集し、pass を阻止する。 |
| hard timeout 3値 | closed | L38、L726、L791、L962。校正3600／本走1800／再検証3600秒。初回再開も1800秒。 |
| 校正計画の純関数 | closed | L333–339、L972–979、L1743–1758。実行ループが同じ純関数を使用する。 |
| literal define・単一理由負例 | closed | L1486–1490、L1807–1812、L1825–1829。literal 6 define と、保全欠落のみ・期待 identity 不一致のみの負例を維持する。 |
| resume の `in_judgment_set` 照合 | closed | L815–825、L877、L1996–1999。literal `True` を要求し、`False`／`None`／整数 `1` を拒否する。 |

## F1 の4分類と再検証

行番号は [v5 runner](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2807-b8-prerun/probe/verify_phase_runner.py) を指す。

| 分類 | 実装と判定 |
|---|---|
| (a) bench 失敗 | L361–362で終端・skip。`bench_failure` は witness／trace の失敗も含む。bench 未完走も再生成しない。 |
| (b) verifier 完走済み・起動済み | L364–365でskip。完走、開始時刻あり、rcありのいずれでも初回再開へ入らない。 |
| (c) 保全済み・verifier 未開始 | L375→L694–741。`restore`→trace存在・witness照合→初回 verifier の順。 |
| (d) bench 完走・保全未完了 | L366–372で `trace_missing`・`indeterminate`・`eligible=False` を保存。次回は(a)でskipする。 |

(c) の本番 callback は、指定がなければ実際の `restore`／`run_verifier` を使う（L697–698）。`restore` は保存側のSHA256・bytesをL561、展開後をL574で照合し、成功後にだけL726へ進む。復元失敗を無視して verifier を実行する経路はない。

`phase='verify'`・`verify_attempt_id=1` をL699–700で要求し、同じ `attempt-1/result.json` をL717・737で更新する。bench・保全・元bindingsは保持し、`resumed_verifier`、再開時刻、runner SHA、hostname、再開時bindingsを追加する（L713–716）。既存repの分岐から `measure` を呼ぶ経路はない。

これはv3 L902–924の「同一traceを復元して初回verifierを行う」経路に相当する。timeoutは裁定どおり3600→1800秒へ変更され、identity確認・再開履歴・trace／witness確認が加わった。verifier出力ファイルが既にある場合の拒否も維持する（L701–702）。

(d) はL318–319で規約不適合として開示され、L1122–1126でpassを阻止する。有効なanomalyが別にあれば、規定どおり失格が優先される。

`reverify` は未開始の(c)をL831–837で拒否する。(b)のうち運用上未完走・bench完走・保全済みだけを受け入れ、既存 `reverify-*` があれば拒否する（L850–855）。初回再開を再検証1回として消費する変更も、再検証回数を増やす変更もない。

## selftest と回帰検査

一律skipを肯定していた旧4ケースは、実際のbench／verify／preservationフィールドを変える6状態へ置換された（L1906–1922）。

(c)では本番の `run_rep_once` と `resume_first_verifier` を通し、呼出し列が **restore→verify、timeout=1800、出力先同一**であることを検査する（L1943–1955）。bench再生成callbackは呼ばれれば失敗する（L1930–1931）。bench・attempt・provenanceの保持、通常の判定枠への収容、次回skipも検査する（L1956–1970）。

verifier結果自体は成功stubだが、再開処理を丸ごと成功stubへ置換してはいない。したがって呼出し欠落・逆順・timeout違い・bench再生成は検出できる。ただし、実際の圧縮復元やverifierプロセスの成功を証明する検査ではない。

指定diffをメモリ上でv4へ適用すると、v5と完全一致した。selftestの変更は当該resumeブロックに限定され、それ以外の既存期待値の変更・緩和はない。親ログは `ok` 166件、`PASS 166/166 cases`、`rc=0`。

AST比較でも、`prepare`、`prerun_record`、`configure_argv`、`preserve`、`restore`、`timed_process`、`run_verifier` はv3／v4／v5で一致した。v4→v5の既存関数の変更は `run_rep_once`、`reserve_output`、`run_job`、`selftest` のみで、判定・集計関数は不変。prerunの制御経路にも変更はない。

今回は静的検査・AST比較・JSON／ハッシュ照合のみを行い、selftest・pytest・build・bench・verifierは実行していない。

## 発効束 draft の検算

v5実ファイルから計算したSHA256は、draftおよび両gateのv5試走recordと一致した。

`4ff6652a365b952cba4deb23e2ae910ba863dabba4a107503c641c7a36863430`

| 検算項目 | 結果 |
|---|---|
| identity | 両gateの `source_before`／`source_after` とdraftの両identity fieldが全桁一致 |
| verifier | ファイル名集合と9ファイルすべてのSHAが一致 |
| patch・pipeline | 各SHAが一致 |
| toolchain・compiler | toolchain辞書全体・compiler versionが一致 |
| define・genome | define 6個の値と順序、genome辞書全体が一致 |
| pin・Python・repo HEAD | 一致 |
| 試走binary・hostname・完了時刻 | gate別に一致 |
| `known_results` の試走項目 | 対応するv5 recordと一致 |
| 事前登録SHA | 指定文書の実bytesと一致 |

両試走recordは `completed`、`in_judgment_set=false`。identityは次の値で、指定された焦点1巡目報告にあるv3／v4の検算値とも一致する。

- g_rl：`b0f95b213e6d419cf31473a37c6be3246f9b0fefbd42ead2273d5ab7408a670d`
- g_rt：`a0219ce0b258e339ac6489cb5b17b3acb4158ce0d6087ca6098d1e408862f833`

v3／v4試走recordのraw JSONは今回の射影対象にないため、過去版とのrecord比較は前回報告の値との照合である。v5 recordとdraftの比較は今回独立に実施した。

## 新規所見

成立した新規所見なし。F2の参照先誤りも、今回指定された `s6-fix-1b.md` とv4実体の対応により解消している。

## 総括

**GO：段6の焦点再レビューとして、F1の修復と既存8件の維持を確認した。** 本走の発効認可を意味しない。

- 対応表：**closed 9／partial 0／regressed 0**。
- 新規所見：**must-fix 0／should 0／nit 0**。
- 発効束draft：**指定項目はすべて一致、不一致0**。runner SHAもv5実体と一致。
- 実traceの復元・verifier再開は未実走。過去版試走identityとの比較は、指定された前回報告を根拠とする。