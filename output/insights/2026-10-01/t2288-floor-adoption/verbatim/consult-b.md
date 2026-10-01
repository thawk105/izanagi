## 所見

1. **refuted / should —「本 wave で記入し、実装子に直させる方が筋」**
   [依頼逐語](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-floor-adopt/verbatim/request-md_3.txt)は「docs のみ」、所有は floor セルと自分の fragment に限定している。委任しても所有範囲は広がらない。binary 未配置時の材料レポート停止は実在するため、その状態で記入を着地させない判断は妥当。D2103 が登録 wave でのテスト更新を予告していても、本依頼にコード変更権限を追加するものではない。ただし後続を広い consumer 再設計へ膨らませる必要はない。

2. **real / must — P1 の障害範囲と完了主張は絞る必要がある。**
   [焦点走ログ](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-floor-adopt/verbatim/focus-with-entry.log:212)が示すのは、この木での **34 failed＋2 errors**。「main の全 checkout で binary 不在により36件失敗」は過剰である。binary は配置でき、実文書の `None` 固定テストは配置後も期待値が古く、wiring probe は別原因として brief 自身が区別している。両ログには受入全走ではない旨の警告もある。
   また、依頼は「採用なら記入」を要求する。**「集約の採用判断・pin は確定、§5 転記と接続確認は未完」**とは記録できるが、依頼完了とは書けない。D1641 との整合性を説明するために、採用と記入を分離する一般制度を新設する必要はない。

3. **real / must — 後続は原則 (a)＋(c)。各案は同等ではない。**

   | 案 | 判定 | 受理集合・必要性 |
   |---|---|---|
   | **(a) 通常の材料レポート系テストを fixture 文書へ接続** | **real / should** | 製品コードの受理集合は不変。floor 不在を検査するテストの意味を維持できる。ただし実運用の binary 不在は解消しない。 |
   | **(b) 消費時の binary 検査を省略** | **refuted / must** | 現在拒否する binary 不在・hash 不一致等の入力を受理し得る。測定側の検査を残しても、consumer の受理集合は拡大する。本件の「規律2を緩めない」修復としては不適合かつ不要。 |
   | **(c) レポート実行 checkout へ既存 `place` で配置** | **real / should** | 入力環境を満たす措置で、受理述語は不変。[既存運用](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-floor-adopt/verbatim/runbook-binary-place.md)を使える。ただし古い `None` 期待値は直らず、配置後の全検査通過も未確認。 |
   | **(d) pin 拒否を `None` に戻す／集約を v1 へ差し替える** | **refuted / must** | 前者は拒否を成功経路へ変え、後者は §5 が要求する集約の契約から外れる。ともに不要。 |

   根拠となる経路は、`load_authoritative_floor` → `_load_aggregate_authority` → `_aggregate_authority_value` → `_load_expected_specs`／`load_floor_pair_summary` → `load_frozen_spec` → [`_bind_checkout_inputs`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-adopt/orchestrator/campaign/floor_pair_driver.py:1122)。最後の関数が binary の実在・hash に加え receipt と calibration も検査する。`load_frozen_spec` 全体を飛ばす案は、binary 要求だけの除去よりさらに広い緩和になる。

4. **real / should — 最小差分はテスト3ファイルと floor セルで足りる設計が可能。**
   後続への一手は、**「通常テストの文書入力を fixture 化し、実文書回帰を登録後の期待へ更新する。実文書を消費する checkout に既存 `place` を適用して確認し、同じ commit で floor セルを記入する」**でよい。

   | ファイル・関数 | 最小変更 |
   |---|---|
   | [test_p3_b4_material_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-adopt/orchestrator/tests/test_p3_b4_material_report.py:77)：`_write_floor_preregistration`、`_inputs`、`_document` と通常テストの fixture 配線 | 既存 helper の `present=False` を再利用し、テスト中の `R._REPOSITORY_ROOT` を fixture 文書へ向ける。直接 builder を呼ぶ通常テストも対象とする。`test_m08_floor_absence_runs_existing_evaluator_as_protocol_violation` の不在期待は維持する。 |
   | 同ファイル：`test_cli_clean_subprocess_runs_twice_and_refuses_overwrite` | 親プロセスの monkeypatch は届かない。最小案では既存の実文書統合テストとして残し、その実行 checkout に (c) を適用する。完全な fixture 化まで求めるなら子プロセス側の fixture checkout が別途必要。製品 CLI にテスト専用 override を足す必要はない。 |
   | [test_p3_b4_raw_record_producer.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-adopt/orchestrator/tests/test_p3_b4_raw_record_producer.py:964)：`test_unterminated_tail_is_truncated_before_the_next_single_write`、`recorded_rejection_report` | レポート生成部分を fixture 文書へ接続する。後者は module scope なので、パッチもその呼出しを覆う必要がある。 |
   | [test_p3_b4_floor_artifact_issuer.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-adopt/orchestrator/tests/test_p3_b4_floor_artifact_issuer.py:826)：`test_resolver_real_preregistration_is_absent` | 登録後の実 pin・非 `None` を確認する回帰へ改名・更新する。sentinel 不在の検査は既存 `test_resolver_exact_sentinel_is_the_only_absence` が保持する。 |

   この案では `p3_b4_material_report._load_and_evaluate`、issuer、driver の製品コード変更は不要。wiring probe の受理条件を緩める変更も、この証拠だけでは不要である。上記は静的な変更候補であり、修正後の通過を実測したものではない。

5. **real / must — 記録から削るべき一般化と、区別すべき実挙動がある。**
   削る対象は「全 checkout で生成不能」「36件すべて同原因」「consumer の binary 不要化が記入の必須条件」「採用したので今回の依頼は完了」。全 checkout の準備状況台帳、新しい admission gate、manifest、real-repo 分類追加も不要。n＝62・24時間分離の自動検査追加は、D1974 が人手に残した責任まで変更する。

   `floor_domain_error` の影響は次の区別で足りる。

   - **未記入を維持**：resolver は `None`。分析に到達すれば従来の `floor_domain_error` が残る。
   - **pin を検証できる**：非 `None` が評価器へ渡り、floor 欠落による固定理由が外れる。他の分析結果や実走完了は保証しない。
   - **pin を拒否**：[`_load_and_evaluate`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-adopt/orchestrator/campaign/p3_b4_material_report.py:212)は `authoritative_floor_rejected` を送出し、評価器を呼ばない。§11.0 追記の「拒否時も floor 不在を渡す」は現コードと一致しないため、記録へそのまま転記しない。

   D に判断・根拠・却下肢、worklog に未完部分と上記一手を置けば足りる。同内容を insight に重複保存する必要はない。

6. **refuted / nit — submit-tree の撤去手順・承認待ちを新しく残す必要はない。**
   与えられた不存在の事実に基づき、次の一文で足りる。
   **「指定 submit-tree は既に存在せず、撤去対象なし。本 wave での撤去操作は行っていない。」**
   不存在だけから撤去者・撤去日時は推定しない。新しい撤去待ち項目も作らない。

## 総括

GO（本 wave の記入保留に限る）。採用判断・pin 確定と、依頼の転記・接続未完を明記する。
後続はテスト入力整理＋既存 `place`＋同一 commit のセル記入へ絞り、binary 検査の緩和を前提にしない。
「全 checkout・36件すべて」の一般化と追加 gate・台帳を削る。今回は静的検査のみで、テストは実行していない。
