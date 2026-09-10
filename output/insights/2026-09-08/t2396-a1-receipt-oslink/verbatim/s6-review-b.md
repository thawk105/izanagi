## 所見

### 所見 1: M-06 の v3 caller 局所変異は全テストを生存する

- 深刻度: 高
- 区分: must-fix
- 根拠 (`file:line`): 裁定は変異対象に caller も含めている [`s4-adjudication.md:79`](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2396-a1-receipt-oslink/artifacts/s4-adjudication.md:79>)。v3 completion の公開箇所は [`paper_story_a1_paired.py:4325`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2396-a1-receipt-oslink/orchestrator/campaign/paper_story_a1_paired.py:4325>) だが、completion 境界テストは helper 直接呼出し [`test_paper_story_a1_job_contract.py:2383`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2396-a1-receipt-oslink/orchestrator/tests/test_paper_story_a1_job_contract.py:2383>) と v2 `run_complete` [`test_paper_story_a1_job_contract.py:2991`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2396-a1-receipt-oslink/orchestrator/tests/test_paper_story_a1_job_contract.py:2991>) だけである。repo 全参照でも `_run_complete_v3` を実行するテストはない。したがって line 4325 だけを `lexists` と `os.replace` に退化させる M-06 は赤を生まない。wrapper 自体を退化させる解釈でも、line 2426 と line 3075 の二つが赤になり単独 owner ではない。
- 成果物影響: 放置すると、v3 の競合 completion が既存の group completion receipt を上書きでき、[`paper_story_a1_paired.py:8496`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2396-a1-receipt-oslink/orchestrator/campaign/paper_story_a1_paired.py:8496>) から materialize が読む bytes、材料レポートの参照、試行台帳の受理集合が create-only 契約から変わる。
- 提案: v3 policy で `run_complete` または `_run_complete_v3` を通し、line 4325 の直前境界で canonical staging、宛先不在、`os.link(..., follow_symlinks=False)` を観測する挙動テストを追加する。M-06 は wrapper 変異と v3 caller 局所変異を別登録にする。
- 推測か実証か: テスト不在と変異生存は repo 全参照と制御フローから静的に実証。実際の競合発生だけが故障条件付き。

### 所見 2: 同一 inode 移動負例が「staging を残す」を検査していない

- 深刻度: 高
- 区分: must-fix
- 根拠 (`file:line`): 裁定は宛先不在なら staging を unlink せず停止することを要求する [`s4-adjudication.md:17`](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2396-a1-receipt-oslink/artifacts/s4-adjudication.md:17>)。しかしテストは存在する path だけを先に `preserved` へ絞り、非空と bytes だけを検査する [`test_paper_story_a1_job_contract.py:2673`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2396-a1-receipt-oslink/orchestrator/tests/test_paper_story_a1_job_contract.py:2673>)。候補集合では存在性が恒真となり、staging と destination のどちらが残ったかを失う。cleanup が `os.link(staging, destination)`、`os.unlink(staging)`、例外送出の順で勝手に修復しても、このテストは通る。
- 成果物影響: 放置すると、裁定上は公開状態不明として停止すべきケースで完成名が復活し、CLI が非ゼロでも job が receipt を見つけて bench へ進み、試行台帳の受理集合と後続の材料レポートが変わり得る。
- 提案: 例外後に `assert staging.read_bytes() == expected` と `assert not os.path.lexists(destination)` を直接検査する。可能なら `_PublishedReceiptCleanupError` も検査する。
- 推測か実証か: 通過する反例をテスト述語から静的に実証。

### 所見 3: M-01、M-05、M-06、M-07、M-08 の単独 owner 申告は成立しない

- 深刻度: 中
- 区分: nit
- 根拠 (`file:line`): 裁定は複数同時赤を単独帰属として扱わない [`s4-adjudication.md:48`](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2396-a1-receipt-oslink/artifacts/s4-adjudication.md:48>)。実装子は全項に単独 owner を申告した [`s5-author.md:67`](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2396-a1-receipt-oslink/artifacts/s5-author.md:67>) が、実際には次のとおりである。

  - M-01: `pytest.raises` が line 2670 と line 2706 の二つで赤。
  - M-05: line 2346、2366、2394、二つの line 2593 parameter、2670、2706、2746、3075、3215 が赤。
  - M-06 wrapper 変異: line 2426 と line 3075 が赤。v3 caller 局所変異は所見 1 のとおりゼロ件。
  - M-07: line 2366、2394、FileExists parameter の line 2593 が赤。
  - M-08: line 2349、2380、2428、2670、2706、2746、2814、2844、3076、3215 が赤。

- 成果物影響: 現行 production の値、受理集合、参照は直接変わらず、M-06 の生存問題を除けば変異自体は複数テストに捕捉される。
- 提案: M-01 は「宛先不在 guard」と「identity 不一致 guard」を別変異にする。M-05、M-07、M-08 は単独 owner 登録から外し、実際の複数 failed-node 集合として扱う。単独化のため既存の正当な assertion を削らない。
- 推測か実証か: 各変異後の分岐と assert 到達点から静的に実証。

### 所見 4: `FileExistsError` 専用 catch は同一内容の冗長コードである

- 深刻度: 低
- 区分: nit
- 根拠 (`file:line`): [`paper_story_a1_paired.py:918`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2396-a1-receipt-oslink/orchestrator/campaign/paper_story_a1_paired.py:918>) と [`paper_story_a1_paired.py:922`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2396-a1-receipt-oslink/orchestrator/campaign/paper_story_a1_paired.py:922>) は同じ例外型と同じ message を生成する。`FileExistsError` は `OSError` の派生なので前者を除いても挙動は同一である。裁定は要求外の防御コードを禁止する [`s4-adjudication.md:118`](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2396-a1-receipt-oslink/artifacts/s4-adjudication.md:118>)。
- 成果物影響: 削除前後で公開結果、JSON bytes、受理集合は変わらない。
- 提案: `except OSError` 一つへ統合し、M-07 は generic catch 内の `FileExistsError` 条件を誤って成功扱いする意味変異として登録する。
- 推測か実証か: Python の例外継承と二つの branch 本文から静的に実証。

### 所見 5: 波及列挙が exact な参照グラフになっていない

- 深刻度: 中
- 区分: nit
- 根拠 (`file:line`): 実装子の一覧 [`s5-author.md:81`](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2396-a1-receipt-oslink/artifacts/s5-author.md:81>) は内部 caller を省き、逆に changed symbol を直接参照しない fixture や module consumer を同列に置いている。repo 全参照で得られる exact production graph は次である。

  - `_receipt_staging_path` は `_publish_receipt:912`、`_run_submit_v3:3141`、`run_submit:3341`。
  - `_remove_receipt_staging` は `_publish_receipt:930` のみ。
  - `_publish_receipt` は wrapper の line 945 と line 949。
  - `_publish_submission_receipt` は `_run_submit_v3:3305` と `run_submit:3408`。
  - `_publish_completion_receipt` は `_run_complete_v3:4325` と `run_complete:4414`。
  - `_PublishedReceiptCleanupError` は raise の line 938 と catch の line 3306。
  - `run_submit` と `run_complete` の CLI caller は `main:8726,8730`。

  テストから helper への直接参照は `test_paper_story_a1_job_contract.py` に限定される。`run_complete` には同ファイル line 3072 と `test_paper_story_a1_paired.py:3465` から参照がある。実装子が挙げた `materializer_admission.py` や一部 fixture は意味上の consumer ではあるが、これらの symbol の直接 caller ではない。
- 成果物影響: 現行成果物は直接変わらない。ただしこの不正確な列挙が v3 completion caller のテスト不在を隠している。
- 提案: symbol ごとの exact caller/test graph と、receipt path を読む意味上の runtime consumer を別表にする。
- 推測か実証か: repo-wide `rg` による静的実証。

### 所見 6: 改名済みテストの duration ledger entry が旧名のまま残る

- 深刻度: 低
- 区分: nit
- 根拠 (`file:line`): テストは [`test_paper_story_a1_job_contract.py:2568`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2396-a1-receipt-oslink/orchestrator/tests/test_paper_story_a1_job_contract.py:2568>) で `link_failure` 名へ改名されたが、ledger は旧 `rename_failure` の二 nodeid を保持する [`acceptance_duration_ledger.json:1331`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2396-a1-receipt-oslink/orchestrator/tests/acceptance_duration_ledger.json:1331>)。新設 5 test と改名後の 2 parameter nodeid は ledger にない。もっとも、未知 nodeid は `None` を返す設計 [`conftest.py:1534`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2396-a1-receipt-oslink/orchestrator/tests/conftest.py:1534>) で、強制条件も全件一致ではなく全 collection の 90%以上 [`test_acceptance_schedule_order.py:704`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2396-a1-receipt-oslink/orchestrator/tests/test_acceptance_schedule_order.py:704>) である。
- 成果物影響: certified 選択結果、材料レポート、試行台帳には影響せず、acceptance test の並べ替え精度だけが落ちる。
- 提案: 本 wave では ledger を触らず、親の実測後に通常の ledger 更新工程が必要かを別途判定する。現時点で hard constraint 違反や通過を主張しない。
- 推測か実証か: 旧 entry 残存と新 entry 不在は静的に実証。全 collection の 90%条件は未収集なので未判定。

## Scope と materialize の確認

差分は production と job-contract test の 2 ファイルだけである。B-1 から B-6 の混入は確認されなかった。

- `_exclusive_write_bytes` の partial staging 問題は改修されていない。
- staging は kind marker を加えただけで PID 依存のままである。
- parent fd 固定や一般的な同 uid writer 防御は追加されていない。
- completion staging の事前予約や freshness gate は追加されていない。
- `submission-failure.json` は従来どおり `_exclusive_write` を使う [`paper_story_a1_paired.py:3115`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2396-a1-receipt-oslink/orchestrator/campaign/paper_story_a1_paired.py:3115>)。
- materialize fallback、台帳、schema、互換層、一般化は変更されていない。

`_renameat2_directory`、`_publish_staging_noreplace`、`_observe_materialization_publish`、`_publish_staging_after_einval`、`_publish_complete_staging`、`_publish_materialization_bundle` の定義と本文には diff hunk がない。`PUBLISH_RENAME_NOREPLACE`、`PUBLISH_EINVAL_FALLBACK`、`_RENAME_DEFAULT`、`_RENAME_NOREPLACE` も [`paper_story_a1_paired.py:393`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2396-a1-receipt-oslink/orchestrator/campaign/paper_story_a1_paired.py:393>) のままである。旧 submission publisher から `_renameat2_directory` 呼出しを除いた一行だけは当然差分に現れるが、materialize 側の同 symbol と経路は無変更である。

`test_paper_story_a1_paired.py` の diff は空で、materialization テスト群にも一行の変更もない。

## 受領証 bytes の確認

公開機構だけが変わり、公開される JSON bytes は同一経路で作られる。

- `_canonical_json_bytes` は無変更で、`ensure_ascii=False`、`sort_keys=True`、`indent=2`、`allow_nan=False`、末尾 `"\n"` を固定する [`paper_story_a1_paired.py:496`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2396-a1-receipt-oslink/orchestrator/campaign/paper_story_a1_paired.py:496>)。
- 新 publisher は同 helper を line 911 で一度通し、`_exclusive_write_bytes` へ渡す。後者は memoryview の bytes を変換せず書く [`paper_story_a1_paired.py:800`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2396-a1-receipt-oslink/orchestrator/campaign/paper_story_a1_paired.py:800>)。
- 旧 completion publisher の `_exclusive_write` も同じ `_canonical_json_bytes` を使っていた [`paper_story_a1_paired.py:820`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2396-a1-receipt-oslink/orchestrator/campaign/paper_story_a1_paired.py:820>)。
- v2 submission の dict [`paper_story_a1_paired.py:3388`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2396-a1-receipt-oslink/orchestrator/campaign/paper_story_a1_paired.py:3388>)、v3 submission の dict `:3289-3299`、v2 completion の dict `:4398-4412`、v3 completion の dict `:4309-4323` に差分はない。

したがって schema、field 集合、sort 後の順序、indent、UTF-8、末尾 newline の変更はない。

## 旧名、meta-test、揮発値

旧 `_submission_receipt_staging_path` と `_remove_submission_receipt_staging` の repo 内参照はゼロである。同名の履歴文書参照も見つからない。

新規 test file はないため、test file 集合メタテストへの追加登録は不要である。既存 file は self-run harness を保持する [`test_paper_story_a1_job_contract.py:3458`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2396-a1-receipt-oslink/orchestrator/tests/test_paper_story_a1_job_contract.py:3458>)。新 test 名はすべて `test_` で始まり、重複名もない。plain-runner 規約は file 単位で判定する [`test_plain_runner_coverage.py:60`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2396-a1-receipt-oslink/orchestrator/tests/test_plain_runner_coverage.py:60>) ため、同一 file 内の追加では集合制約は変わらない。

新テストに実 PID、実時刻、実 working-tree hash の焼き込みはない。PID は production と test の双方で実行時に `_receipt_staging_path` から導出される。`"a" * 40`、epoch `2`、request ID は fixture 用の固定合成値であり、実環境から採取した揮発値ではない。

pytest は実行しておらず、緑は主張しない。

## 総括

must-fix は次の 2 件である。

- 所見 1: M-06 の v3 completion caller 局所変異が無検出。
- 所見 2: 同一 inode 移動負例が staging 保存という必須状態を検査していない。

変異 owner の最終判定は以下である。テスト行はすべて `orchestrator/tests/test_paper_story_a1_job_contract.py`。

| 変異 | 静的な赤集合 | owner 判定 | 落ちる assert |
|---|---|---|---|
| M-01 | 2 test | なし、多数赤 | `pytest.raises` at 2670、2706 |
| M-02 | 1 test | あり: `test_submission_receipt_cleanup_preserves_replaced_staging` | 2632-2635 の例外 message match。identity 検査削除後は foreign staging を消し、元の no-replace error が出るため match 不成立 |
| M-03 | 1 test | あり: `test_receipt_publish_orders_link_fsync_unlink_fsync` | 2746-2751 の exact event 列。最初の fsync が欠落 |
| M-04 | 1 test | あり: 同上 | 2746-2751 の exact event 列。`unlink` が最初の `fsync` より前になる |
| M-05 | 10 nodeid | なし、多数赤 | 2346、2366、2394、2593 の 2 parameter、2670、2706、2746、3075、3215 |
| M-06 | wrapper 変異は 2 test、v3 caller 局所変異は 0 test | なし。v3 caller 形は survive | wrapper 形は 2426、3075。line 4325 局所形は落ちる assert なし |
| M-07 | 3 nodeid | なし、多数赤 | 2366、2394、FileExists parameter の 2593 |
| M-08 | 10 test | なし、多数赤 | 2349、2380、2428、2670、2706、2746、2814、2844、3076、3215 |
| M-09 | 1 test | あり: `test_v3_published_cleanup_failure_does_not_write_failure_receipt` | 3215 の例外 subclass 検査。plain `PaperStoryError` は generic catch に入り failure receipt も作る |

判定: このまま受け入れてはならない。production の materialize 非変更と JSON bytes 不変は確認できるが、裁定が必須とした completion の挙動閉包と A-1 の exact fail-closed 状態がテストで閉じていない。