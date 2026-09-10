# 段 1 brief — [T-2067] 残件 3 点の実装

**scope.** D1313 が列挙した 5 残余のうち、D1325 で終端した設計択一 2 件を除く 3 件を実装する。
(1) load-only consumer 3 群への選択強制、(2) 起動証明書の実時間性、(3) s8c production final claim 配線。
**非 scope.** D1241 / D1313 の advisory / non-certifying 上限の解除。g2 の挙動定義 (拒否枝を含む)。
新しい署名・nonce・一回性台帳・汎用 framework・仮想リスク向けの gate / 検査 / 台帳 / 一般化。
C05 schedule authority の実装。予算数値の確定。

**確定済みユーザー裁定.** D1325 (2 件は終端。g2 は実在してから設計) / D1313 (上限は解除しない。
追加主張は (a)(b)(c) の 3 点だけ) / D1312 (強制点は candidate と launch。**loader は投影だけ**。
historical reverify に選択規則を課さない) / D1241 (署名・台帳・nonce・one-shot 代替を作らない) /
D95 (実装面は Codex author) / 引数 (本題の実装だけ。s8b_oracle_manifest 系が稼働 wave と重なるなら
s8c 側から着手)。

**不変条件.** (i) 上限が解除・緩和されたと読める文言も述語も作らない。(ii) loader
(`_verify_generation_semantics`) に current build admission policy を持ち込まない (D1312)。
(iii) historical reverify の受理集合を変えない。(iv) g2 の受理・拒否を新たに定義しない。
(v) 規律 2 を緩めない。(vi) 凍結成果物の bytes を変えない
(`s8b_holdout_freeze.py` の自己 blob hash は future candidate の `generator.sha256` に入る)。

**親の実測 (段 1 前、worktree = local main `2bf9cf387`).**
1. **編集面の重複は実在する。** `dev-wave-t1999-define-gate-family` の作業ツリーが
   `orchestrator/tests/test_s8b_oracle_manifest.py`、`orchestrator/campaign/s8b_oracle_driver.py`、
   `orchestrator/tests/test_s8b_oracle_driver.py` を未 commit で変更中 (branch 差分は
   `s8b_oracle_driver.py` のみ)。production の `s8b_oracle_manifest.py` は非接触。
   → **着手順は s8c 側が先。** oracle manifest 側に触るなら production module と新規 test file だけにし、
   `test_s8b_oracle_manifest.py` は触らない。
2. **依頼文の file 名を訂正 (非抵触).** s8c C06 予算の site は `s8c_budget.py` ではない。
   `s8c_budget.py` に floor 参照は 0 件で、実 site は `p3_autonomous_workload_trial.py:1807-1878,4640`。
   s8c 側の実編集面は `s8c_result_judge.py` と `p3_autonomous_workload_trial.py`。
3. **load-only 3 群のアンカー** (前 wave consult-b の閉包を再測して一致):
   oracle manifest = `s8b_oracle_manifest.py:1205` (`build_approved_manifest` が
   `load_ratified_freeze` だけ)、s8c 床値 verifier / publish = `s8c_result_judge.py:2108`
   (`verify_floor_bytes`)・`:2188` (`publish_result_table` の current binding)、
   s8c C06 予算 = `p3_autonomous_workload_trial.py:4640`。
   強制済みの 2 点は candidate `s8b_holdout_freeze.py:2053` と launch
   `s8b_ratified_freeze.py:3305` (先行 gate `:3107` が g2 を拒否)。
4. **起動証明書の実時間性 — 既存機構の穴を特定した。** 選択経路が呼ぶのは非 strict の
   `s8b_launch_cert.validate_launch_certificate` (`s8b_holdout_freeze.py:1674`) で、
   `clean_scan_digest` を expected と照合しない。strict 版
   `validate_launch_certificate_strict:129` は既に存在し、campaign 起動側
   (`s8b_floor_campaign.py:5389,7333`) だけが使っている。**新機構を作らずに使える既存の締め代がある。**
   ただし strict 版が要求する `expected_clean_scan_digest` は起動時の worktree 走査値であり、
   凍結時に再計算できるとは限らない。ここが (P1-2) の争点。
5. **3 群はいずれも現に発火していない。** active ratified freeze・v2 generation・approval・
   official floor run は 0 件、`BUDGET_APPROVAL_SHA256` は `None`。さらに C06 経路は
   `p3_autonomous_workload_trial.py:1798-1803 _load_s8c_schedule_authority` が
   **無条件に例外を投げる** (C05 schedule authority 未実装)。→ `DW-G04` の発火 artifact path は
   書けず、発火実績は合成 fixture の test だけである。
6. **s8c_result_judge の production importer は 0 件** (tests を除いた全 repo grep)。
   公開 3 関数は `judge:1947` / `verify_floor_bytes:2103` / `publish_result_table:2384`。
   production の s8c driver は `p3_autonomous_workload_trial.py` で、s8c_arm_inputs /
   s8c_generation_projection / s8c_preregistration / s8c_budget は import するが
   s8c_result_judge は import しない。

**(P1) 親の provisional 裁定 — 攻撃対象.**
- **(P1-1)** 残件 (1) は「load-only consumer が current な公開物を作るときだけ、既存の
  `launch_validate` 相当を経由させる」で足りる。loader 自体は変えない (D1312)。
  historical / reverify 経路は現状のままにする。
- **(P1-2)** 残件 (2) は選択経路の証明書検証を strict 版へ寄せることで実装する。
  `expected_clean_scan_digest` を凍結時に再構成できないなら、証明書内の値を
  **selected run の同一 namespace 内の他 run と突き合わせる**等の既存材料だけの締め代に落とす。
  それも成立しないなら **実装せず、測った値域と不能理由を裁定へ返す** (D1241 が禁じた新機構に
  なるため)。「実時間性を証明した」とは書かない。
- **(P1-3)** 残件 (3) は C05 schedule authority が未実装である限り、production final claim の
  **到達可能な**配線を作れない。作れるのは「s8c driver が final claim を出すときに
  s8c_result_judge の 3 関数を通る」という配線だけで、その driver 経路自体が現に到達不能である。
  `DW-G05` の成果物影響行を書けるかがこの wave の分岐点。書けなければ (3) は設計メモに留め、
  (1)(2) を完遂して (3) の不能理由を裁定へ返す。
- **(P1-4)** 3 件とも受理集合を**狭める**方向にしか変えない。緩める変更は 1 つも入れない。

**成果物の形.** 実装面 = `orchestrator/campaign/` の該当 module と対応 test。
docs = `docs/spool/worklog/` fragment 1 本 + 必要なら decisions fragment。
insight = `output/insights/2026-09-01_t2067-residual3-impl/`。変異 matrix は `DW-M01` に従い事前登録する。

**分割方針.** 段 2 plan 1 本 (codex read-only)。段 3 敵対 2 本 —
レンズ A =「(P1-1)(P1-4) を攻撃。選択強制が D1312 の loader 不変・historical 不変・上限不解除を
破っていないか。受理集合の変化を正確に数えたか」、レンズ B =「(P1-2)(P1-3) を攻撃。
strict 版への寄せが実際に成立するか、再構成不能でないか。C05 未実装下で (3) が
`DW-G04`・`DW-G05` を満たせるか。満たせないと結論するなら、それが本当に不能か」。
段 5 実装子は s8c 側 (unit A) と s8b 側 (unit B) に分ける。編集面を排他にする。

**受入.** `python3 tools/dev_wave_wait.py acceptance --wave t2067-residual3-impl
--lease-dir /work/1/SFC/tanab/dev-wave-jobs/land-lease -- python3 tools/run_tests.py`
(実行場所は Pegasus runbook §7.0.0 の既定自動判定に従う)。

**変更面アンカー表.**
| file | 行 | 役割 |
|---|---|---|
| `orchestrator/campaign/s8c_result_judge.py` | 1947, 2103, 2384 | 公開 3 関数 (final claim 配線先) |
| `orchestrator/campaign/s8c_result_judge.py` | 2033-2060, 2108, 2188 | load-only の floor binding |
| `orchestrator/campaign/p3_autonomous_workload_trial.py` | 1798-1803 | C05 authority (常時拒否) |
| `orchestrator/campaign/p3_autonomous_workload_trial.py` | 4640 | C06 予算の load-only site |
| `orchestrator/campaign/s8b_holdout_freeze.py` | 1654-1686, 1928-1963, 2053 | 証明書検証・選択規則・candidate 呼出 |
| `orchestrator/campaign/s8b_launch_cert.py` | 50, 129 | 非 strict / strict 検証 |
| `orchestrator/campaign/s8b_oracle_manifest.py` | 1201-1215 | load-only (**test file は非接触**) |
| `orchestrator/campaign/s8b_ratified_freeze.py` | 1054-1085, 3107, 3305 | 投影 g1 枝・g2 gate・launch 選択 |
| `docs/decisions.md` D1241/D1312/D1313/D1325 | — | 参照のみ・追記しない |
