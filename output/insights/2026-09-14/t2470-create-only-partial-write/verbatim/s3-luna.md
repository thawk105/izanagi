## L-1 — cleanup 条件を狭める変異が生存する

**real・scope 内。変異事前登録と正例の補完対象。**

現行 writer は `os.write` が `0` 以下を返した場合にも失敗する（`orchestrator/campaign/trial_registry.py:2455`）。しかし計画の注入は「1 byte 書いてから例外」と、書き終わった後の fsync 失敗だけである（`s2-plan.md:88`）。

次の未登録変異 **M9 は SURVIVED と予測する**。

```python
except BaseException:
    if written > 0:
        # 計画どおりの unlink・cleanup エラー処理
        ...
    raise
```

計画された write・割り込み注入では `written == 1`、fsync 注入では最後の write が正数なので、すべて cleanup される。一方、write が進まない既存の失敗経路では残骸が残る。

**成果物影響:** 進捗なしの write 失敗後、genesis または同一内容の分類受領証が再発行不能になる。

既存の正例 parameter に「部分 write → 次の write が 0」を加え、不在と同一引数の再試行成功を確認すれば殺せる。新規 test file・検査機構は不要。

## L-2 — 焦点走の集合は production file の consumer を閉じていない

**real・scope 内。ただし成果物の誤り自体は未立証なので nit。**

計画は公開 caller への直接参照を優先し、別 API の consumer を受入全走へ送っている。しかし今回指定された基準は、変更する production **file** の consumer も焦点走へ含めることだった。

少なくとも次が提案集合から漏れている。

| consumer test | 現物の参照 |
|---|---|
| `test_holdout_observation.py` | `:22` で import、`:264` で `trial_registry.HOLDOUT_BINDINGS` と比較 |
| `test_campaign.py` | `:10761` で `autonomous.trial_registry.admit_unregistered_exploratory` を実行 |
| `test_paper_story_a1_paired.py` | `:578` で `paired.trial_registry.issue_a1_registered_noncertifying_projection` を実行 |
| `test_paper_story_a1_job_contract.py` | `:58` の source 集合に対象 file、`:407` 以降で閉包を検査 |

後二者は計画の「受入全走へ回す追加参照」の列挙にもない。production 側でも `paper_story_a1_paired.py:179` が対象 file を source 集合へ含め、`:7081` が公開 API を呼ぶ。

**成果物影響:** source binding・projection の consumer 検証が焦点走から欠落する。具体的な値・受理集合の回帰は静的検査では確認していないため、成果物破損の must-fix とはしない。

## L-3 — P1 の一般論は D205 の例外を立証していない

**real・scope 内の説明訂正。nit。今回の修正を止める根拠ではない。**

逐語射影 `rulings-verbatim.md:36` は採用対象を、

> 科学的妥当性 (測定・検証・台帳の正しさ) に直接効くものだけ

としている。一方、同 `:26` の T-1854 は、復元不能による slot 停止でも「現行claimへの具体的影響が立証されない追加防御」として除外されている。

現物の create-only 契約は「canonical path が存在しない場合だけ作成を受理する」と述べるが、失敗時の再試行可能性までは明記していない（`trial_registry.py:2484`）。また、受領証の digest 不一致は拒否される（`:2332`）。したがって、**「既存 writer の欠陥」という呼称だけでは T-1854 と異なる扱いの根拠にならない。**

ただし、今回には逐語射影 `:86` の明示的な修正指示がある。これが scope 内で進める直接の根拠になる。D730 の文言も、見送り台帳へ滞留した項目を対象としており（`:60`）、全修正への一律の実害三例要件ではない。

**成果物影響:** P1 の説明だけでは既発行成果物の値・受理集合は変わらない。一般的な堅牢化許可へ転用しないよう説明を限定する nit。

## L-4 — 分類側の「slot が恒久的に分類不能」は一般化しすぎている

**real・scope 内の影響説明訂正。nit。**

分類受領証の名前は payload の SHA-256 で決まる（`trial_registry.py:3282`）。payload には `classified_at` が含まれる（`attempt_registry_core.py:1834`）。production caller も `_now_iso()` を渡す（`p3_autonomous_workload_trial.py:4884`）。

writer 失敗は分類行 append と capability 更新より前である（`trial_registry.py:3288,3322,3327`）。したがって、同じ capability でも日時が異なる分類は別 path を使い、旧残骸との衝突を避け得る。これは production 全体の再起動成功を保証する話ではないが、slot 全体の恒久拒否という断定への反例になる。

**成果物影響:** 確実に塞がるのは同一 payload の分類再試行。slot 全体が必ず受理集合から欠落するとは導けない。

genesis は固定 canonical path なので、この反証は当てはまらない。計画の「同一引数で再試行」は維持すべきである。

## L-5 — 計画された主要注入点は、手前の別 I/O へ逸れるという攻撃では破れなかった

**refuted・scope 内。**

- genesis の準備は `_genesis_cli_fixture` 内で完了する（`test_trial_registry.py:6772`）。公開 API の前処理と `_open_registry_parent` は対象 write/fsync より先に別の write/fsync を行わない（`trial_registry.py:2492,1108`）。
- classification の予約は注入前に完了させる設計。`_assert_attempt_capability` は値検証であり、writer 前に台帳を書かない（`:3052`）。
- `R.os` の monkeypatch は共有 `os` object に作用するが、確認した同期経路では注入を先取りする呼び出しは見つからなかった。

修正前は write・file fsync・directory fsync の全ケースで file が残り、不在 assertion が赤になる（`:2454`〜`:2461`）。修正後は patch 解除後に同一引数で公開 API を呼び直すため、単なる不在確認で終わらない。

**成果物影響:** 計画どおり実装されれば、両 caller の同一内容再発行を検証できる。実走結果ではない。

負例は修正前から緑でよい。純増は次のとおり。

- genesis 既存テストは既に拒否後に file を読むため、削除変異を殺せる（`test_trial_registry.py:6763`）。追加の完全一致は bytes 改変検出の強化。
- CLI は既に完全一致を検査する（`:6849`）。純増なし。
- classification は既存テストが例外だけを見る（`:7168`）。新規負例の純増は、拒否後の受領証残存・bytes 保持。

## L-6 — 登録済み八変異の生存は予言できなかったが、nodeid はまだ実在しない

**refuted・scope 内。登録済み変異の検出設計への攻撃結果。**

計画された assertion が実装される前提では、各変異は次で赤になる。

| 変異 | 検出箇所 |
|---|---|
| 1 unlink 削除 | genesis-write の残骸不在 |
| 2 FileExistsError でも unlink | 拒否後の bytes 再読込。既存 genesis・CLI でも検出可能 |
| 3 親 fsync を cleanup 外へ移動 | classification-directory_fsync の残骸不在 |
| 4 絶対 path の unlink | wrapper の basename・親 fd 検査 |
| 5 cleanup エラーを再送出 | 元 write エラーとの `__cause__` 同一性 |
| 6 BaseException → Exception | KeyboardInterrupt 後の不在 |
| 7 裸の raise 削除 | 期待例外が出ない |
| 8 fsync 順序反転 | 成功時の順序比較 |

根拠は現行 writer `trial_registry.py:2448` と、計画の注入・assertion・変異表 `s2-plan.md:88,100,104,162`。

新規 nodeid 名は現行 `test_trial_registry.py` に存在しない。段4では予定名として登録し、実装後に実在と検出を確認する必要がある。現時点で KILLED と報告できる変異はない。

**成果物影響:** 八変異について見逃す具体例は得られなかった。ただし、所有・撤去条件を狭める L-1 の変異は表にない。

## L-7 — caller 二件は反証できた漏れなし。「実発生ゼロ」は検証不能

**caller 漏れは refuted、ゼロ件の測定根拠不足は real・scope 内の nit。**

private symbol、公開名、別名を production 全体で検索し、次を確認した。

- 対象 writer の直接 caller は `trial_registry.py:2530,3288` の **二件**。
- genesis の CLI 入口は `:6559`。
- classification の module 属性経由入口は `p3_autonomous_workload_trial.py:4876`。
- `classify_attempt_failure` は `trial_registry.py:3336` の別名。別名の production 呼び出しは見つからない。
- fixture 経由も、`test_p3_autonomous_workload_trial.py:7070` → fixture → `test_reflux_originless_compatibility.py:48,133`、等価性 helper の `test_attempt_registry_core_equivalence.py:392,414` まで確認した。

同名の別 writer や core の純粋 API を第三の caller に数える根拠はない。

reader は `classification_receipt_sha256` と `classification-receipts` の両検索から `trial_registry.py:2311` に到達する。**reader ゼロは反証されるが、現行 brief は既に自己訂正済み。** 計画の未訂正扱いは古い。

部分書き込みについては、`partial write`・`作りかけ`・具体的なエラー文・`ENOSPC`・`EIO` へ検索語を変えた。対象 writer の実障害記録は確認できなかったが、起票一次資料も障害発生ログではなくコード欠陥の記述である（逐語射影 `:19`）。検索不検出から「実発生を測ってゼロ」とは言えない。提示された現行 brief には pin 閉包件数の記載もなく、その数値は照合できない。

**成果物影響:** 計数の説明自体は成果物を変更しない。未観測を実害不存在や scope 判断へ一般化しないための nit。

## scope 外の所見

新たな scope 外の real 所見は挙げない。

計画には新規 production gate・検査関数・台帳・module・test file、同名 writer への横展開、staging＋hard-link publish は見つからなかった（`s2-plan.md:3,47,62,64`）。追加テストは対象 writer の cleanup と既存不変条件を検査する範囲にある。

## 総括

最優先は **L-1 の生存予測変異と「write が進まない」正例を事前登録へ追加すること**。焦点走は file consumer 基準に合わせて補完する。

P1 は一般的な D205 例外の立証としては不足するが、今回の明示修正指示が実施根拠になる。分類側の影響は「同一 payload の再試行阻害」へ限定すべき。

静的検査のみ。編集・commit・pytest・変異実走は実施していない。