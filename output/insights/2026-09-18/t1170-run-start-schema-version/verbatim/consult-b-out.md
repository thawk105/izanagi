## must-fix 所見

**MF1 — 変異 matrix が、本題の「現行 producer 定数への再依存」を検出できない。**

plan の M1〜M3 は検査削除・対応版変更・診断分類の交換を検出するが、提案コードの比較右辺だけを `_RUN_START_SCHEMA_VERSION` から `producer.SCHEMA_VERSION` に戻す変異を検出しない。現在は双方 v4 なので、提案された正例・負例・producer 統合正例の結果は変わらない。診断文言を残せば全文期待も通る。

- **修正:** 記録済み v4 fixture を確定した後、consumer が参照する producer の `SCHEMA_VERSION` だけをテスト内で別版へ変更し、v4 の検証結果が変わらないことを確認する。同条件で、その別版を付けた run-start は拒否されることも確認する。
- **matrix:** 比較右辺を producer 定数へ戻す変異を追加し、このテストで KILLED を要求する。実装への追加 gate は不要。
- **放置時の成果物への影響:** 本来の不具合を残した実装でも受入検査を通り、producer 改版時に既存 v4 report の完全性判定が拒否へ変化し、未対応版を版検査で通す状態になる。

これは新しい仮想リスク対策ではなく、今回除去する依存そのものの回帰検査である。上記は静的判定であり、変異の実測結果ではない。

## nit 所見

1. **P1 は plan の修正説明なら妥当。D1851 を「形を変えない bump の禁止」と読んではならない。**
   D1851 の決定は、新版かつ新機能なしの結合正例を要求している。「版 ⇔ 形」の双方向の一般則ではない。今回 v5 を提案しない理由は、既存 v4 が旧 artifact の v3 と現行出力を既に分け、新たな形変更を必要としていないためである。

2. **「旧版として読む」は、旧契約を検証することとは区別する。**
   plan が実装するのは `v3 → legacy と識別して拒否` であり、旧形の内容の復号・再検証ではない。D1669 の条件付き decoder と、D2064 の生成時コード・契約による再検証を併記すれば整合する。「旧版対応済み」とは書かない。

3. **世代診断には到達条件がある。**
   `autonomous_trial_completeness.py:2238–2239` の report 版検査が先行するため、report も旧版なら run-start の世代診断まで到達しない。P6 の据え置きは許容できるが、「すべての旧 run で世代を名指す」とは保証しない。

4. **docs は worklog fragment と F332 への追記で足りる。**
   P1〜P3 を「既存 v4 境界の利用、対応版の独立所有、旧版 decoder を追加しない」と限定すれば、既裁定の適用として扱える。独立した decisions fragment は不要。worklog には対象6本の前提訂正、既存 bump を利用した事実、MF1 を含む実測結果を残す。F332 の当時の記述は保存し、恒久対応を追記する。

## brief の誤り・飛躍

**F4 の対象訂正は現物で裏付けられる。**

以下の行番号は、指定 worktree 内の `orchestrator/campaign/` 配下を指す。

| file | 確認箇所 | 判定 |
|---|---|---|
| `attempt_registry_core.py` | 883–889、1308–1312、1769–1777 | lifecycle の `start`／`pre-observation-seal` に属する receipt digest の検査・記録 |
| `s8b_attempt_profile.py` | 407–427 | 同 lifecycle event の exact-key 定義 |
| `s8b_floor_attempt_launcher.py` | 526–535、1132–1136 | reservation に digest を受け渡す |
| `s8b_attempt_registry.py` | 2582–2590 | core の slot reservation に digest を渡す |

この4本に journal run-start の版追随変更を入れる根拠はない。ただし、「当初の6本は grep 先頭6件から起草された」という経緯まではコードから証明できない。

**F2 の形の説明は plan の訂正が正しい。**
現物は非 binding 時16 key、binding 時23 key（`seq`・`ts` を含む）。producer の `5127–5138` は binding 時に7 field を追加する。指定の歴史 artifact は2行目に v3・13 key の run-start を持つ。v4 導入 commit と現在の無条件 key 集合も一致した。

**P5 の「共有定数が根本原因」は強すぎる。**
共有定数は role 改版が run-start に波及した理由である。今回直接直す原因は、consumer が自分の対応契約を持たず producer の現行定数を参照していることである。

**F5 の不在証明は限定する必要がある。**
実在 artifact は確認できるが、直接参照の検索だけで動的な読み手を含む完全な不在は証明できない。plan の留保は適切。「確認した範囲で具体的な旧版利用者が見つからないため、decoder を追加しない」と記録すればよい。

**P7 の同期検査と独立性検査は別である。**
既存の `test_transport_admission_error_persists_verified_partial_report` は、現行 producer 出力を consumer に通す結合正例として実在する。しかし、記録済み artifact の判定が producer 改版から独立している証拠にはならない。plan が残した実質的な検証上の飛躍はこの点である。

**P1 と依頼文は両立する。**
`4c6f03048` は T-304 の変更であり、D1898 の完了を当時宣言したものではない。一方、共有定数を v4 にした結果、run-start も実際に v4 を出している。これを既存の改版境界として利用し、今回 consumer と検証を追随させる解釈には根拠がある。

ここで共有定数を v5 に変えると、run-start だけでなく `p3_autonomous_workload_trial.py:2926` の role payload も v5 になり、独立した role consumer v4 と不一致になる。さらに現行対応版を v5 のみにすれば、09-16 以降の v4 記録も現行 consumer では拒否対象になる。記録された測定事実が無効になるわけではないが、今回必要な変更ではない。

## 依頼文 3 句と実装行の対応表

`C` は `orchestrator/campaign/autonomous_trial_completeness.py`。行番号は変更前の位置であり、実装は未着手。

| 依頼文 | plan の実装位置 | 満たす内容と限界 |
|---|---|---|
| 「記録済み artifact と現行 producer の世代を分け」 | `C:427` 付近に独立リテラル定数追加、`C:2240–2241` の比較を置換 | run-start の対応版を producer の現行値から切り離す。MF1 の検証追加が必要。run 全体の歴史的再検証の独立性までは保証しない。 |
| 「旧 record は旧版として読む」 | 同置換部の `recorded_version` と `generation="legacy"` 分岐 | v3 を v4 に読み替えず、記録された版のまま識別して拒否する。旧契約による内容検証は行わない。 |
| 「互換層は足さず」 | 同置換部の単一対応版比較、不一致時の `_fail` | alias・field 補完・旧版受理を追加しない。現在の版に関する受理集合 `{v4}` を維持する。 |

P4 の無変更判断も妥当である。`trial_registry.py:5967–5993` は binding field を比較し、同じ処理内の `6004` で completeness 検査を呼ぶ。`s8c_acceptance_receipt.py:1496–1506` は `arm_execution` の一致を検査する。今回これらが読む field の契約は変わらず、追加版 gate を必要とする具体的な破れは示されていない。

## 裁定パッケージ候補 (scope 外)

- **v3 内の形の混在:** 13 key の旧記録と、その後に field が増えた v3 は、版値だけでは区別できない。今回の実装は双方を legacy として拒否し、この歴史的混在を解消しない。実在する横断利用者と用途が確認された場合に、D1669 に沿って扱う。
- **v4 の binding 有無:** 現物で field の有無を識別できる、同一世代の構成差である。版値だけでは有無を表さないが、それ自体は欠陥ではない。D1851 の正例が守るべき差であり、別版化や新 gate の提案は不要。
- **producer の role／run-start 定数分離、report 契約の独立所有:** 今回の局所修正では扱わない。必要性が具体化した場合に別途判断する。
- **旧 run 全体の現行コードによる再検証:** report 版・provider・budget 等の現行 producer 依存が残る。今回の完了条件へ追加せず、必要なら生成時契約による検証との関係を別途裁定する。

## 総括

**v5 へ上げず、既存 v4 を consumer 所有の対応版として固定する方針は妥当。P1〜P7 は上記の限定を付けて採用できる。**

実装前に、producer 定数への再依存を検出する回帰テストと変異を追加すること。これが現 plan の must-fix である。静的検査のみ実施し、ファイル変更・pytest・変異実測は行っていない。