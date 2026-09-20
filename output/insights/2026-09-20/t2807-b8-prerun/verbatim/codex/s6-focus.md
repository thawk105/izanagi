| 所見 | 判定 closed/partial/regressed | 根拠 (v4 の行番号) |
|---|---|---|
| A3/B1：bench 再生成 | partial | L348–360、L803–812、L921–932、L1089–1105。失敗 rep は attempt-1 で終端し、resume でも再生成しない。複数 attempt の最終値採用も撤去。ただし、保全済み trace の初回 verifier 再開まで削除した回帰がある（下記）。 |
| A1：校正 bench 失敗 | closed | L342–345、L1053–1059、L1176–1177、L1293。校正・本走の失敗は pass を阻止し、校正失敗は `stage_B_allowed=false`。`not_run` は bench 失敗に数えない。 |
| A2：失格の優先順位 | closed | L1021–1024、L1063–1073。対象・gate/workload・phase が整合する集合内 record の完走 anomaly を、混入・SHA 不一致・規約不適合より優先する。 |
| B2：job 段失敗の読落とし | closed | L968–975、L1145–1150、L1047–1052、L1234–1237。校正・本走の job 直下 `result.json` を収集し、規約不適合として開示・pass 阻止。`job.json` はこの収集対象ではない。 |
| A4：phase 別 hard timeout | closed | L37–38、L725、L895。校正 3600／本走 1800／再検証 3600 秒を実際の呼出しへ適用。保全済み trace の再検証も 3600 秒。初回 verifier の resume 経路消失は別記。 |
| B3：校正計画の検査 | closed | L333–339、L903–912、L1382–1384、L1674–1689。純関数を実行ループから呼び、その停止・継続を selftest で検査。校正 anomaly fixture も修正済み。 |
| B4：自己参照・複合負例 | closed | L1417–1421、L1741–1743、L1758–1760。期待 define は literal 6 個。preservation 負例は wall を適格値へ戻し、bundle 負例は before/after を一致させて期待値不一致だけにした。 |
| B5：resume の判定集合照合 | closed | L749–751、L808–810、L1861–1864。`in_judgment_set is True` を必須とし、`False`・`None`・整数 `1` を拒否する。 |

## 新規所見

- [must-fix] verify_phase_runner.py:358 — 保全済み trace の初回 verifier を再開できなくなった — 成立 — 根拠: v4 L356–360、L765–770、L921–927、v3 L902–924。  
  bench 完走・保全完了後、verifier 起動前に中断した record は、v3 では同じ trace を復元して初回 verifier を実行できた。v4 は既存 rep を無条件にスキップし、`reverify` も `rc` と開始時刻がともに `None` なら拒否する。これは bench 再生成の禁止とは別の経路である。  
  **判定への影響：残り23枠が緑でも、同じ trace の初回検証が緑なら到達できた pass に到達できず、未確定に固定される。**  
  失敗 bench の終端は維持し、保全済み・verifier 未開始の初回検証経路を本走の1800秒で復元すべき。L1836–1845 の追加 selftest は状態名だけを変更して一律スキップを肯定しており、この回帰を検出しない。

- [should] codex/s6-fix-1.md:3 — 指定された fix 報告が v4 の修正報告になっていない — 成立 — 根拠: 同 L3–33 と v4 実体・差分の不一致。  
  報告は「編集前に停止」「改版なし：1785行」、v3 の SHA、全項目 partial と記載している。実体は1968行の v4 で、修正と追加 selftest が存在する。  
  実際に修正した版の SHA・対応表・検証記録へ報告を差し替える必要がある。本レビューの対応表は報告を根拠にせず、実体から判定した。

## 評価順・失敗集計・selftest

`decide` の失格候補には、`in_judgment_set is True`、対象一致、gate/workload 整合、`calibrate / verify / reverify` の条件がある。`anomaly()` 自体も verifier 完走を要求する（L286–288）。したがって、集合外 prerun の verify field が失格へ混ざる経路は確認しなかった。判定木への混入は L1216–1217 で開示され、通常の prerun 台帳は L1254–1255 の別欄に置かれる。

bench の rc 失敗・timeout・witness 欠落は終端状態を保持し、count／preserve 中の例外で失敗状態を消さない（L699–729）。本走の再生成禁止、校正失敗の本走禁止、複数 attempt の構造エラー化は実装されている。正常 job の `job.json` を失敗 record と誤読する glob はない。

既存 selftest の差分では、期待 verdict を実装に合わせて緩めた変更は確認しなかった。B3/B4 の変更は fixture・検出力の修正である。ただし、追加された一律 resume スキップの期待値は、上記回帰を正当化する証拠にはならない。

親ログは `ok` 160件、`PASS 160/160 cases`、`rc=0`。今回は静的検査と JSON・AST・ハッシュ照合のみで、selftest・pytest・build・bench・verifier は実行していない。

## 発効束 draft の独立検算

全桁比較の結果、各 gate の `src_token` と `source_bytes_sha256` は、draft、v3／v4 の `source_before`／`source_after` のすべてで一致した。

| gate | 両 identity field の値 |
|---|---|
| g_rl | `b0f95b213e6d419cf31473a37c6be3246f9b0fefbd42ead2273d5ab7408a670d` |
| g_rt | `a0219ce0b258e339ac6489cb5b17b3acb4158ce0d6087ca6098d1e408862f833` |

| 検算項目 | 結果 |
|---|---|
| `template_patch_sha256` | v3／v4・両 gate の record と一致 |
| `verifier_module_sha256` | ファイル名集合と9ファイル全 SHA が、4 record と一致 |
| `toolchain` | path・version hash を含む辞書全体が4 record と一致 |
| `configure_defines` | 6個の値・順序が4 record と一致 |
| `genome` | protocol・flags・canonical が4 record と一致 |
| pin・compiler version・pipeline hash | 4 record と一致 |
| draft の試走 binary SHA・hostname・finished_at | 対応する v4 record と一致 |
| 各試走の runner SHA | v3／v4 それぞれの実ファイルと一致 |

draft の `runner.sha256` は、v4 の実ファイルから独立計算した次の値と一致する。**再生成前ではない。**

`f98360ad0c8256a80c198df84de3ec46219d53e5f9dcfe2f741e76bc84455856`

4件の試走 record はすべて `completed`、`in_judgment_set=false`。v3→v4 の SourceEvidence は一時 checkout の `source_root` だけが異なり、残る8 field は一致した。

## 回帰検査の範囲

指定 unified diff をメモリ上で v3 に適用し、v4 と完全一致することを確認した。

`prepare`、`prerun_record`、`configure_argv`、identity 導出・照合、`preserve`、`restore`、`timed_process`、`run_verifier` は v3 と AST が一致する。prerun の prepare→build→identity 後→`prerun.json` の制御経路も維持され、試走 record の一致がこれを裏付ける。

ただし、関数本体の不変性は呼出し経路の不変性を意味しない。今回の回帰は、`restore`／`run_verifier` を呼んでいた resume 分岐の削除にある。

## 総括

**NO-GO：v4 の校正・本走・再開を含む受入れ。** 保全済み trace の初回 verifier 再開経路を修復する必要がある。prerun 経路自体の回帰は確認しなかった。

- 対応表：**closed 7／partial 1／regressed 0**。A3/B1 は再生成禁止を達成したが、関連する再開経路の回帰により partial。
- 新規所見：**must-fix 1／should 1／nit 0**。
- 発効束 draft：**指定検算項目はすべて一致、不一致0**。runner SHA も現行 v4 と一致。追加修正後は runner SHA の再生成・再照合が必要。