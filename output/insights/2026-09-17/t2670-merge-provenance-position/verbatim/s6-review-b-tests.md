## 所見 (既存 test の期待値)

**B01 / refuted / nit / 対象：`orchestrator/tests/test_dev_wave_wait.py:757,6305,6679,7306`**

根拠：patch の全 test hunk を plan 更新表・裁定 §3 と照合した。helper の分離、history の順序移動、段別 queue／完全イベント期待の更新は整合する。abort 期待の変更は指定の2本に限られ、unexpected-rc の既存 assert は維持されている。malformed-message の history 期待削除も、message 拒否で移設先へ到達しなくなることに対応する。裁定外の主張削除・skip 追加はない。

成果物影響：既存の拒否・投入回数・lease 解放・理由保持の検出力を弱める変更は認めない。  
推奨 fix：不要。

## 所見 (新規負例の実効性)

**B02 / refuted / nit / 対象：`orchestrator/tests/test_dev_wave_wait.py:8636`、`tools/dev_wave_wait.py:3770,3839,3862`**

根拠：

- 実装は history に `--message-file` を渡さず、message にだけ渡す。偽 checker の分岐と一致する。
- preclaim は開始 tip・lease 不在、message は未commit の開始 tip・lease 存在、移設後 history は merge tip・lease 存在となり、trace の3行と一致する。
- runner 計数0だけでなく、rc=70、stage、source_rc=1、違反理由と SHA、到達性、2親、終了時 lease 不在まで確認するため、別 stage の拒否で全体が通る構成ではない。
- M1 では違反 SHA が監査時 HEAD の祖先でなく監査が緑になる。commit 後の後段検査も通過可能で、CLI の受入 argv は `python <repo>/tools/run_tests.py`。launcher が実行する tested-main にも計数 runner が入っている。`_write_exact_runner` は binding 報告後に計数するため、投入されれば先頭の計数0 assert が赤になる。M2・M3 も同じ検出点へ到達する。

成果物影響：main-only 違反の見逃しを、順序文字列だけでなく実際の runner 投入で検出できる。  
推奨 fix：不要。変異実走では計数値と最初の失敗 assert を記録する。

**B03 / refuted / nit / 対象：`orchestrator/tests/test_dev_wave_wait.py:8649,8680,8707`**

根拠：新規 subprocess には `timeout=120` がある。小規模なローカル Git 履歴と短い Python subprocess が中心で、通常は数秒程度と見積もれる。ただし静的見積りであり、共有 fixture の初期化まで含むテスト全体の120秒上限ではない。

成果物影響：正常系で120秒を要する構成ではないが、個別所要は焦点走全体の68.90秒から確定できない。  
推奨 fix：コード変更不要。親の正常系・変異走で個別 duration を記録する。

## 所見 (変異被覆と帰属)

**B04 / refuted / nit / 対象：`ruling-s4.md:69`、`tools/dev_wave_wait.py:3862`**

根拠：現物の文字列出現数を静的に確認した。以下の文脈付き anchor は各1箇所。

| 変異 | 一意に取れる anchor | 赤の帰属 |
|---|---|---|
| M0 | 移設先の4行コメント | SURVIVED 対照 |
| M1 | stage を含む監査 block と message 監査 block | runner 計数1による意味的な赤。queue 順序の赤は補助 |
| M2 | stage を含む監査 block | runner 計数1による意味的な赤 |
| M3 | 同監査 block | 非0無視による runner 投入の赤。catch は当該 block に限定する |
| M4 | pending 解除＋直後の HEAD pin、移設先の message-postcheck block | cleanup 挙動の赤 |
| M5 | `"merge-history-provenance",` の行 | 診断感度のみ。KILL に数えない |

裁定 §5 は実行可能な old/new spec 自体ではないため、最終 spec の累積置換後の一意性・期待 node 完全集合は別途確認が必要。

成果物影響：順序 pin や M5 を意味的 KILL に混ぜなければ、事前登録の分類は妥当。  
推奨 fix：変異の追加・削除は不要。最終 spec と probe 結果で DW-M04／M07／M08 を満たすこと。

**B05 / refuted / nit / 対象：`tools/dev_wave_wait.py:3119,3287,4285`、`orchestrator/tests/test_dev_wave_wait.py:1377,7328,7360,8720`**

根拠：M4 の実 Git 経路では監査赤の時点で commit 済み。pending が残るため cleanup が `git merge --abort` を実行し、MERGE_HEAD 不在で失敗する。cleanup failure が primary を上書きし、返却は70から74へ変わるため新規負例が赤になる。

一方 routing fake は abort を成功として返すため、既存 history 赤2本では rc=70が残り、**abort 不在 assert** が赤になる。実 Git と fake の赤理由を同一視してはいけない。これは禁止された cleanup 操作の発生を検出しており、stage 名だけの変更とは異なる。ただし受理集合の拡大を証明する変異ではない。

成果物影響：M4 は後始末契約の検出証拠となる。監査の見逃し検出として数えると matrix の意味を誤る。  
推奨 fix：実測記録で「実 Git＝cleanup rc」「fake＝abort 操作」を分ける。

## 所見 (consumer 波及)

**B06 / refuted / nit / 対象：指定 consumer 各 file**

根拠：

| consumer | 静的判断 |
|---|---|
| `test_dev_wave_land.py:2193,2313` | waiter をコピーするが、束縛値は fixture の Git blob から導出。checker は緑の fixture で、位置移動による固定 hash 不一致は見当たらない |
| `test_resume_gate_acceptance_boundary.py:273` | 実際に postclaim merge を通る。history checker は常に緑、両 branch の実装 bytes も同一に構築され、移設後も runner 1回の期待と整合 |
| `test_dev_wave_wait_compute.py:19` | import 先は同じだが対象は compute 待機経路。変更 block を通らない |
| `test_run_tests_shards.py:190` | waiter との shard 定数契約は不変 |
| `test_check_docs.py:7800` | waiter consumer pin は docs の本文を検査。今回のコード位置を pin していない |
| `test_fold_gate_nodes_contract.py:511` | 禁止 launcher 検査は spool test の到達関数群が対象。新規負例は対象外 |
| `test_plain_runner_coverage.py:60` | ファイル単位の harness／allowlist 検査。ファイル追加・改名・harness 変更なし |
| `test_pytest_collection_config.py` | collection／除外契約に変更なし。新規 node の追加登録を要する依存は見当たらない |

成果物影響：位置移動だけで赤になる consumer は静的には認めない。  
推奨 fix：不要。

**B07 / real / nit / 対象：`focus-f1.log:1`**

根拠：ログは存在し、child rc=0、**1713 passed, 4 skipped in 68.90s** を確認した。静的判断と矛盾しない。ただし実行対象 argv／node 一覧がなく、このログ単独では上記 consumer 全件の実行済みを特定できない。

成果物影響：この集計を consumer 全件の緑の証拠とすると、検証済み範囲を過大に報告する。  
推奨 fix：親の記録に焦点走の対象 argv または対象一覧を添える。再実行を要求する所見ではない。

## 所見 (報告と実体の照合)

**B08 / refuted / nit / 対象：`author.md:46,54`**

根拠：10関数のうち段別1関数が14ケースなので23ケース。新規1＋追加3で27となり、報告の件数は整合する。M2 の runner 計数1も上記の実行経路と矛盾しない。現在の指定2ファイルの `git diff` は author.patch とバイト単位で一致し、監査 block も復元された配置にある。

ただし、27ケースの過去の成功、M2 の実測値、復元操作時の比較そのものは、今回の静的検査で再実証したものではない。

成果物影響：報告と現物の矛盾はない。DIRECT_CALL を正式な変異 matrix 完了と扱う根拠はない。  
推奨 fix：追加コード修正不要。親の harness 記録と区別して保持する。

## 総括

GO