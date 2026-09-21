**NO-GO。must-fix は 3 件です。** 主因は実挿入点の検査欠落と既存検査の回帰です。静的確認では、Tier0 が certification を迂回する実装経路や、smoke 数値の性能値への流入は見つかりませんでした。編集・テスト実行はしていません。

1. **must-fix — 実挿入点の検査が通常走で任意 skip になる**

   対象: [test_b5_tier0.py:119](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-tier0/orchestrator/tests/test_b5_tier0.py:119)、同 :147、:199、:218、:250。

   根拠: `_live_args` は receipt 未設定で `pytest.skip(...)`。4 関数、parameter 展開後 5 node が対象です。M2/M3/M9/M10 の順序・perf binary・拒否後 submission・digest 非生成を実挿入点で検査する部分がここに集中しています。driver の `FakeRunner` は完成済み sidecar/WAL を生成するため、子の挿入点を変異させても、その変異は fixture に反映されません。

   **影響:** submission 前後の逆転や拒否後処理の退行を、通常受入が検出できないまま通す可能性があります。

   推奨修正: 所有内の新規 test に、実挿入点を通る必須の検査を追加する。実 CCBench の生死確認は別に残してよいですが、順序・拒否分岐・例外境界の検査まで任意 receipt に依存させないでください。検査対象の分岐そのものを stub で置換しないこと。F60［テスト代表性］に該当します。

   変異対応の静的評価は次のとおりです。**KILLED の実測判定ではありません。**

   | 変異 | 通常検査の到達範囲 |
   |---|---|
   | M1 | 削除の粒度によって AST 検査は赤になる。driver の証拠欠落 test は子を実行しないため、呼出し配線の代替証明にはならない |
   | M2/M3/M9/M10 | 登録された実挿入点の動的検査が skip 対象 |
   | M4〜M8 | fixture executable と実 gateway/parser/flock を通る検査がある |
   | M11 | live は skip 対象。ただし :279 の AST が捕捉型の字面を固定しており、「通常走で全く検出されない」とは言えない |
   | M12〜M15/M17 | 実 driver/classifier を合成 producer 証拠で検査。driver の変異には対応するが、子の配線は検査しない |
   | M16 | 実 report の契約不一致検査がある |

2. **must-fix — Tier0 前倒しに既存 consumer fixture が追従していない**

   対象: [p3_s4_loop.py:2374](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-tier0/orchestrator/campaign/p3_s4_loop.py:2374)、[test_p3_s4_loop.py:10360](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-tier0/orchestrator/tests/test_p3_s4_loop.py:10360)。

   根拠: `_b5_candidate_fixture` は checkout を git 管理外の template directory に置換しています。追加した `_b5_tier0_build_inputs` が `source_digest.resolve_evidence` を先に実行するため、既存の campaign 境界へ届く前に rc=128 で例外になります。f1 の既存 test 2 件がこの経路で失敗しています。

   **影響:** authority・submission identity と duplicate 非復元の既存保証が検査されず、受入も赤のままです。

   推奨修正: **所有外** `test_p3_s4_loop.py` の fixture を新しい準備境界に追従させ、既存 assertion を維持する。別途、所見 1 の実挿入点検査を必須化してください。production の source evidence 検査を緩めて通す修正は不適切です。［consumer 取り残し］型です。

3. **must-fix — 新規 test の自走入口がない**

   対象: [test_b5_tier0.py:297](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-tier0/orchestrator/tests/test_b5_tier0.py:297)。

   根拠: ファイル末尾まで `_run()`／`__main__` がなく、f1 の `test_every_test_file_is_self_runnable_or_allowlisted` が当該ファイルを明示して失敗しています。

   **影響:** 素の runner では検査 0 件のまま正常終了し得て、現行受入にも不適合です。

   推奨修正: 隣接 test と同じ pytest 自走入口を追加する。**所有 7 file 内で閉じます。**

焦点走 f1 の赤 3 件の帰属は、個別に次のとおりです。

| 赤 node | 本差分への帰属・根拠 |
|---|---|
| `test_machine_no_authority_guard_and_sidecar_before_campaign` | **帰属する。** 追加された Tier0 evidence 解決で停止し、期待した `CampaignBoundary` と authority／sidecar assertion に到達しない |
| `test_b5_duplicate_skip_returns_failure_without_restore` | **帰属する。** 同じ追加経路で停止し、stub campaign の duplicate 結果および rc=1／digest 非生成の確認に到達しない |
| `test_every_test_file_is_self_runnable_or_allowlisted` | **帰属する。** 新規 `test_b5_tier0.py` の自走入口欠落を直接検出 |

残る観点の照合結果です。

- **認証・計測境界:** Tier0 passed 後も既存 `run_campaign` を呼び、verify／bench の短縮引数は追加していません。classifier の certified 判定も WAL の stage 列・anomaly・bench/fitness 一致を要求します。smoke は実 gateway の使い捨て cwd と同期 subprocess、bench lock 内で実行されます。数値は sidecar に留まり、event への射影は `{status, reason, sidecar_sha256}` です。
- **A/B:** 初回 Tier0 拒否は非投入・非 retry で次の A へ進みます。前 attempt 投入済みの場合は `submitted_once` と増加済み B を保持します。score 拒否は fallback なしで停止。投入済みで passed 証拠が欠落・不正なら、B を保持した分類不能欠測になります。
- **build:** 現行 B-5 呼出しでは genome、pin、compiler、cache root、dependency、grammar、context/capability の対応が取れています。`qualification_policy`／`canonical_build_pin`／`sort_oracle_contract_id`／`expected_toolchain_manifest` は、この B-5 経路では有効化されません。省略だけを cache 不一致とは判定しません。ただし、後続 perf build の cache hit と hash 一致は任意 live test に残り、実効性の証拠は未充足です。
- **例外・追加 authorization:** build は指定の 2 型だけを捕捉し、evidence/admission 準備はその外側です。smoke の 4 型捕捉も裁定と整合します。追加 writer authorization は契約照合であり、認可の消費や certified 記録を発行する処理ではありません。
- **契約:** `--` 付き flags はそのまま実 argv に渡されます。ratio は固定 50。`clocks_per_us`／`numactl` の文字列は参照元を表す記述で、実行時は contract の値を使います。header/report の契約比較との直接の矛盾はありません。ただし、この文字列比較だけで実行値の一致を証明しているわけではありません。

## 総括

**NO-GO — must-fix 3 件。** 実挿入点の必須検査、所有外 consumer fixture 2 件の追従、新規 test の自走入口が必要です。f1 の **3 failed / 4,747 passed / 20 skipped** は、Tier0 の実挿入・cache 再利用・verify 継続が確認済みである証拠にはなりません。
