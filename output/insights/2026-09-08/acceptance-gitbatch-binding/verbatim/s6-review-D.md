## レビュー前提

read-only の静的レビューであり、pytest・性能測定・変更系 git 操作は実施していない。既存 JUnit／実行ログを「記録済み実測」、コード照合を「静的判定」として区別した。

## D-01 — p3 wiring probe の subprocess 許可形が旧実装のまま

- **severity:** blocker
- **自己判定:** **real**。[ドリフト]
- **根拠:** 新実装は `ls-tree -r -z ...` と `cat-file --batch` を起動する (`orchestrator/campaign/contract_loader_binding.py:383-392,448-454`)。一方、`p3_b4_wiring_probe` の audit hook は `rev-parse` と旧 `cat-file blob <commit>:<path>` だけを許可する (`orchestrator/campaign/p3_b4_wiring_probe.py:427-455`)。不許可の `subprocess.Popen` は即 `ProbeIsolationError` になる (`同:518-525`)。
- audit hook は runtime load 前に install され (`同:2028-2035`)、その load 中に `capture_contract_loader_binding()` が呼ばれる (`同:1271-1279`)。したがって最初の `ls-tree` で停止するという静的帰結である。
- これを直接通す正例 `test_actual_main_positive_baseline_all_drivers` は return code 0 を要求する (`orchestrator/tests/test_p3_b4_wiring_probe.py:1226-1249`) が、焦点走の選択には同 file が含まれていない (`runner-focus.sh:8-20`)。記録済み 1228 passed (`focus.log:12-38`) はこの回帰を覆わない。
- **修正案:** plan の「p3 caller は無変更」を撤回し、`_allow_read_only_git` に exact な `ls-tree -r -z <commit> -- <literal pathspecs>` と `cat-file --batch` を追加する。caller stack、repo root、sanitized env の既存制約は維持する。`test_p3_b4_wiring_probe.py::test_actual_main_positive_baseline_all_drivers` を焦点走へ追加する。

## D-02 — 「exact call sites」meta-test が第三 caller を検査しない

- **severity:** should-fix
- **自己判定:** **real**。[恒真ゲート]
- **根拠:** `test_production_contract_loader_binding_call_sites_are_exact` の expected と走査対象は `ident.py` と `artifact_admission.py` だけである (`orchestrator/tests/test_t671_source_binding.py:786-822`)。実在する第三 caller は `p3_b4_wiring_probe.py:1277` だが、追加・削除・破損してもこの meta-test は変化しない。
- 「全体として恒真」ではないが、plan が不変条件とした第三 caller に対しては恒真である。今回 D-01 を見逃した直接要因でもある。
- **修正案:** expected に `("p3_b4_wiring_probe.py", "_load_runtime", "capture_contract_loader_binding"): 1` を加え、走査対象にも同 file を含める。呼出数 inventory と D-01 の実動作 test は別々に維持する。

## D-03 — private API consumer の未追随疑惑

- **severity:** nit
- **自己判定:** **refuted**。D-01 の意味的 consumer 漏れを除けば、`_run_git`／`_blob`／`_iter_blobs` の直接 consumer は追随している。
- **根拠:**
  - artifact の2 fake は `**kwargs` 透過と batch missing 注入へ更新済み (`orchestrator/tests/test_artifact_admission.py:2329-2337,2377-2404`)。
  - 共有 helper と layer3 helper は `_iter_blobs` 化済み (`orchestrator/tests/campaign_lock_test_support.py:10-20`; `orchestrator/tests/test_layer3_report.py:72-82`)。
  - `_blob` の対象 API 直接利用は所有 test の wrapper testだけ (`test_t671_source_binding.py:889-919`)。
  - production の mocc 2 wrapper は `_run_git(root, *args)` のみで、追加 kwargs が任意のため互換 (`orchestrator/campaign/mocc_trace_pair.py:818-822`; `mocc_trace_pair_anchor.py:183-187`; signature は `contract_loader_binding.py:252-257`)。
  - `test_s8c_preregistration_predicates.py:759-772` の `_blob_at_commit` は文字列 fixture 内の別関数、`test_t139_blobref_digest_binding.py:41-64` の `_blob` は fixture の未使用値、`test_campaign_lock_codec.py:13-14` は対象 module を import していない。`test_mocc_trace_pair.py:654-660` の `git_blob_*` は receipt field である。
- 呼出元 production 3 file に diff が無いことも `unitA.patch` の6個の diff headerから確認した。ただし p3 は D-01 のため「無変更で安全」ではない。
- **修正案:** private symbol 検索に加え、旧 argv の意味的仮定である `cat-file blob` allowlist も consumer 検査対象にする。

## D-04 — DW-M01／D1712 の変異帰属

- **severity:** nit
- **自己判定:** **refuted**。静的には7件とも所有 test 内の単独 node で意図した gateを直接 killでき、worktree driftや上位層が先に赤を出す構成ではない。変異実走はしていないので、以下は緑／kill の実測主張ではない。
- **修正案:** D-01 修正後、D1712どおり表の exact nodeだけを各変異で実走し、例外理由まで記録する。

| 変異 | 実装位置 | 期待 nodeと直接の歯 | 冗長になりうる層 |
|---|---|---|---|
| 1. `input=input_bytes` 削除 | `contract_loader_binding.py:293-306` | `test_run_git_forwards_exact_batch_stdin_and_timeout`; `kwargs["input"] == input_bytes` を直接検査 (`test_t671_source_binding.py:1707-1749`) | real Gitを使う正例は timeout／parser失敗にもなり得るため単独証拠にはしない |
| 2. batch OID exact 照合削除 | `contract_loader_binding.py:472-478` | `test_committed_verifier_rejects_reordered_batch_oids_even_with_permuted_digests`; digestも同じ permutationにして後段 digest gateを中和 (`test_t671_source_binding.py:1086-1150`) | 通常の digest mismatch test。期待 nodeでは中和済み |
| 3. `_blob` を逐次 `cat-file blob` へ後退 | `contract_loader_binding.py:513-515` | `test_blob_compatibility_wrapper_uses_one_batch_query`;戻り値と exact 2-call argvを直接検査 (`test_t671_source_binding.py:889-919`) | 共有 helper／layer3 は既に `_iter_blobs` へ移行し、この変異には冗長でない |
| 4. batch header の blob type 検査削除 | `contract_loader_binding.py:479-483` | `test_batch_blob_reader_rejects_malformed_header_or_status[tree-object]` (`test_t671_source_binding.py:1153-1205`) | ls-tree non-blob test (`同:979-1020`) は別の gateであり、この変異の証拠にはならない |
| 5. exact EOF 検査削除 | `contract_loader_binding.py:505-508` | `test_batch_blob_reader_rejects_extra_output_after_last_record` (`test_t671_source_binding.py:1296-1332`) | size／record LF gateは入力 `body\nextra` では発火せず、EOF gateに帰属する |
| 6. committed digest 比較削除 | `contract_loader_binding.py:568-574` | `test_committed_verification_rejects_one_digest_mismatch`; target verifierを直接呼び、disk readerも禁止 (`test_t671_source_binding.py:1623-1704`) | admission 経由 test (`同:648-713`) と別関数 `verify_committed_contract_loader_blobs` は上位／並列の冗長 gate |
| 7. live disk 比較削除 | `contract_loader_binding.py:543-555` | `test_live_verification_rejects_each_dirty_enforcement_source[attempt_ledger.py]`; capture後にtemp repoだけをdirty化 (`test_t671_source_binding.py:620-641`) | ident経由の drift testは capture側でも落ち得るため使わない |

等価変異候補は `relatives = tuple(relative_paths)` (`contract_loader_binding.py:356`) を `relatives = (*relative_paths,)` に置き換えるもの。観測可能な tuple内容と反復順は同じであり、**SURVIVED期待**である。

## D-05 — duration ledger、自走 harness、spawn site

- **severity:** nit
- **自己判定:** **refuted**。台帳・harness・spawn-site値に実害は見つからない。
- **根拠:**
  - ledger diffは test node 190件の追加と `nodeid_count` の `19745 -> 19935` だけで、既存 map entryの削除・変更はない (`unitA.patch:278-486`)。
  - 現物は map key数と `nodeid_count` がともに19935 (`acceptance_duration_ledger.json:19938-19941`)。追加値に `0`／`0.0` はなく、最小値は0.001。
  - author event logでは最初に `--add-only` で189件、最後の追加 node後に同じ commandで1件を追加している (`attempt-0001.events.jsonl:53-56,100-103`)。手書き placeholderという疑いは反証される。
  - `_run()` と `__main__` は残る (`test_t671_source_binding.py:1752-1758`)。
  - production の `subprocess.run` source siteは1箇所 (`contract_loader_binding.py:293`) で、spawn-site台帳値1 (`test_ccbench_spawn_sites.py:111`) と整合する。これは実行回数ではなくsource site数である。
- **修正案:** なし。最終成果物には `/tmp` JUnitではなく永続的な add-only 実行receiptを残すと追跡性が上がる。

## D-06 — author.md の数値、緑、所有範囲、権限

- **severity:** nit
- **自己判定:** **refuted**。[捏造/幻覚] と [権限逸脱] は認めない。ただし「観測した範囲」の緑であり、D-01の suiteは未実走。
- **根拠:**
  - 最終 JUnitは `tests=295, errors=0, failures=0, skipped=0`。event logにも最終 `295 passed` がある (`attempt-0001.events.jsonl:100-103`)。
  - 146、44、79、3、113 passedもそれぞれ終了code 0の記録がある (`同:59,62,69,71,73,105-110,118`)。合計680は算術的にも一致する。
  - authorは `test_layer3_report.py` を緑に数えず未実走と明記している (`author.md:20-24`)。親のcommit後焦点走では選択された1228 nodeが通った記録があるが、これはauthorの680とは別実測 (`focus.log:12-38`)。
  - patchは6 file、1366 insertions、31 deletionsで、author.mdのstatと一致する。変更対象は production binding、ledger、共有helper、artifact fake、任意layer3 helper、所有testだけ (`unitA.patch:1,278,487,506,545,564`)。
  - author event logに top-level の commit／checkout／reset等はなく、最終状態も6 fileの未commit変更として記録されている (`attempt-0001.events.jsonl:111-112`)。
- **修正案:** 最終報告では「680／1228の選択範囲は緑だが、p3 wiring probeは選択漏れ」と追記し、D-01修正後の当該suite結果を別掲する。

## D-07 — captureのprocess数説明は3ではなく4

- **severity:** should-fix
- **自己判定:** **real**。[ドリフト] ただし性能見積りそのものは概ね整合する。
- **根拠:** public captureは `_validated_root` の `rev-parse --show-toplevel` (`contract_loader_binding.py:114,520`)、`rev-parse HEAD` (`同:325-333,521`)、`ls-tree` (`同:383-392`)、`cat-file --batch` (`同:448-454`) の**4 process**。所有 testの3 processは `_validated_root` を固定した条件 (`test_t671_source_binding.py:1588-1620`) である。
- `parent-measurements.md:19` の「capture 1回=3 process」はこの固定条件を書かず、public captureの説明としては誤り。
- 一方、1操作のGit費用は `ls-tree+batch 0.071〜0.091秒 + rev-parse 2回 × 0.036〜0.047秒 = 約0.143〜0.185秒`。11操作で約1.6〜2.0秒なので「約11×0.15秒」と12〜15秒予測には矛盾しない (`parent-measurements.md:11,13,16-21`)。
- disk読取4.3秒、fsync・tmp copy等は減らないことを明記済み (`parent-measurements.md:18-21`; `plan-v2.md:22`)。計算ノードでの効果も未測定と明記されている (`parent-measurements.md:20-21`; `commit-unitA.txt:17-18`)。
- **修正案:** 性能文書を「public capture全体は4 process、blob取得部分は2 process、`_validated_root` 固定testでは3 process」に訂正する。12〜15秒は未測定の推定として維持できる。

## 失敗型判定

| 型 | 判定 | 根拠 |
|---|---|---|
| [捏造/幻覚] | refuted | authorのnode数・緑はJUnit／event logと一致。未実走layer3も緑に数えていない |
| [恒真ゲート] | real | D-02。exact call-site testが第三callerに対して無反応 |
| [ドリフト] | real | D-01のp3 subprocess許可形、D-07のcapture process説明 |
| [権限逸脱] | refuted | diffは許可6 pathのみ。authorによるcommit／branch変更の証拠なし |

## 段3レンズB対応表

| 所見 | 状態 | 判定 |
|---|---|---|
| B-05 2 fake | closed | redirected fakeとmissing fakeの双方がkwargs／batchへ追随。共有helperとlayer3も追随。ただし別の意味的consumer漏れがD-01 |
| B-06 変異 | closed | 要求7件は静的に単独nodeへ帰属可能。変異実走結果は未確認 |
| B-08 台帳 | closed | add-only 190件、既存entry不変、count整合、追加zero placeholderなし |
| B-10 順序 | closed | parentのcommit後焦点走として実行された記録あり (`runner-focus.sh:2`; `focus.log:2-38`) |
| B-11 優先順位・NUL | closed | 優先順位を契約外へ狭め、全path事前検査とNUL拒否を実装・専用test化 (`contract_loader_binding.py:356-366`; `test_t671_source_binding.py:1335-1356`) |

## 総括

blocker **1件**、should-fix **2件**。  
最重要1: p3 wiring probeが新しいGit argvをaudit hookで拒否し、実動作suiteも焦点走から漏れている。  
最重要2: exact caller meta-testが第三callerを検査せず、この回帰に対して恒真。  
最重要3: public captureは3でなく4 processだが、12〜15秒予測と計算ノード未測定の表明は概ね正直。  
変異7件、ledger、authorの680 node、変更範囲には静的または記録上の不整合を認めない。