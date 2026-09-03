# 段 4 裁定 — [T-2231]+[T-2199] 段 4 loop へ site-aware 環境契約配線を移植する

基準 commit c7ed56589。段 2 プラン 1 本、段 3 敵対 2 レンズ (sol=レンズ A、luna=レンズ B) を裁定する。

## C0 — 親自身の brief 前提を 1 件撤回する (実測による)

親 brief は「移植は `_resolved_site` / `_contract` 注入込みでなければ既存テストを壊す」と書いた。
**これは誤りである。**

`orchestrator/tests/conftest.py:239-255` に autouse fixture `_declare_default_test_site` があり、
`site_policy.socket.gethostname` を `"test-host"` へ、`_has_nqsv` を `False` へ差し替える。
`site_policy.classify_site` はこの入力を `OTHER` に分類する。したがって
**pytest 実行中の `_current_site()` は、この機体が `pegasus02` であっても常に `OTHER` を返す**
(`_detect_site_under_test` を宣言したテストだけが例外)。

実走で確認した (計算ノード dispatch、2026-09-03 20:5x JST):

- `test_p3_s4_loop.py::test_backoff_value_raw_canonical_source_and_genome_are_one_chain`、
  `::test_drive_iteration_checkpoint_survives_across_calls`、
  `::test_main_emits_planner_context_from_new_state` — 3 passed
- `test_p2_2_site_aware.py` — 21 passed

移植元 `p3_s4_loop_trigger_gating.py:889-893` の `run_one_iteration` は `_current_site()` を
**無条件で**呼んでおり、それでも trigger 側のテストはこの機体で緑である。これが機構の正例である。

## C1 — レンズ B の「この機体で赤になるテストの一覧」26 件は refuted

根拠は C0 と同一。レンズ B 所見 4 (別 test file の直接 caller が赤になる) も同じ根拠で refuted。
`test_p3_exploration_namespace.py` / `test_p3_b4_closed_critic.py` の caller も同じ fixture 下にある。

**ただし** 受入全走で実測して確認する (段 6)。ここでの refuted は「静的主張の反証」であり、
実測の代用にしない。

## C2 — レンズ A 所見 6 を採用: 注入は `drive_iteration` だけに置く

C0 により、テスト hermetic 化のための注入は**不要**になった。移植元を実見すると:

- `p3_s4_loop_trigger_gating.py:734` `_run_one_iteration_resolved` — 解決済み site/contract を取る内部
- `:863-907` 公開 `run_one_iteration` — 自分で `_current_site()` を解決し内部を呼ぶ。注入引数を持たない
- `:984-1031,1118` `drive_iteration` — `_resolved_site` / `_contract` の paired injection を持ち、
  解決済みの値で内部を呼ぶ

**base もこの 3 分割をそのまま写す。** 公開 `run_one_iteration` と `main` へ
`_resolved_site` / `_contract` を足すのは移植元に無い新しい公開 seam であり、採用しない (DW-G05)。
プラン `s2-plan.md:47,59-63` の該当部分は plan v2 で置き換える。

## C3 — レンズ A 所見 1 (公開 `run_campaign` seam) は real だが本 wave 起因でない

移植元 `p3_s4_loop_trigger_gating.py:600-621` の `default_cfg` も環境契約を bind せず
`ident.bind_admission_policy` だけを返す (親が実見)。つまり「未束縛 cfg を公開 `run_campaign` へ
直接渡せば admission を迂回できる」性質は**移植元に既にある**。本 wave が新設する穴ではない。

新しい gate を足すのは移植の scope 外 (DW-G05)。**保証範囲を正確に書くことで閉じる**:
本 wave が保証するのは driver 自身の入口 (`main` / `drive_iteration` / `run_one_iteration`) を
通る経路であり、再 export された `run_campaign` への直接呼出しは保証しない。
これを insight と worklog に明記する。裁定パッケージにも残す。

## C4 — レンズ B 所見 1 を採用 (must-fix、scope 内)

`default_cfg` から環境契約 bind を外すと、次の 2 経路が壊れる。親が実見して確認した。

- `orchestrator/campaign/p3_b4_wiring_probe.py:1470,1474` — `cfg.bound_environment_contract` を
  受けて `.contract_sha256` を直読する。`None` になると停止する
- `orchestrator/tests/test_p3_b4_raw_record_producer.py:149-160` — 同 field を非 None と assert する

**我々の変更が壊すので、同じ実装単位で直す。** 直し方は「呼び手側で契約を解決してから読む」を既定とし、
`default_cfg` を再び bind する方向へは戻さない (C5 の理由)。

## C5 — P4 は反転する (プラン採用)

親 brief の P4 provisional (`default_cfg` は `ENV_TAG` のまま残す) を撤回する。
`orchestrator/campaign/ident.py:113-117` は、別契約が bind 済みの cfg へ異なる契約を bind すると
`ValueError` を投げる (親が実見)。`default_cfg` が先に `linux-baremetal` を bind すると、
`_campaign_cfg_for_site(PEGASUS_COMPUTE)` が必ず例外になる。よって `default_cfg` は未束縛で返す。

identity は守られる。`ident.py:196-224` `canonical_preimage` は `bound_environment_contract` を
覆わず、`measurement_env` は通常の `search_config` key として覆う。したがって OTHER の
campaign_id は不変、PEGASUS_COMPUTE だけが別 ID に分かれる。

## C6 — P1 / P2 / P3 の裁定

- **P1 採用**: `run_campaign` へ `contract.env_tag` / `contract.clocks_per_us` /
  `list(contract.numactl)` / `authorize(contract.env_tag)` を渡す。
  **レンズ A の訂正を採る**: 移さなくても成果物の値が静かに誤るのではなく、
  `execution_guard` が最初の書込み前 gate で拒否する。つまり現コードでの帰結は
  「Pegasus で build へ到達しない」である。親 brief の書き方はこの点で不正確だった。
- **P2 採用 (条件付き)**: `campaign_options` の PEGASUS_COMPUTE 分岐を移植する。
  **レンズ A の訂正を採る**: `env_contract` と `dependency_prefix` を一括して「無ければ build 不可」と
  するのは一般化しすぎ。`env_contract` は contract-aware build に必要、`dependency_prefix` は
  非空のときだけ渡す形にし、その実効値の所有者は本 wave の scope 外 ([T-2232]) と明記する。
- **P3 採用**: `_assert_resume_allowed` / `_receipt_provenance` / `_append_provenance_entry` は
  scope 外。**プランの記述は過大なので訂正して記録する**。プラン `s2-plan.md:105` は
  「常に iteration を増やし checkpoint を上書きする」と書いたが、レンズ A の裏取りどおり正確には
  「pre-build recovery・停止・reject 面は変更されうるが、既存 claim 下の build は
  `loop.py:198-229` の one-shot claim と `campaign_claim.py:383-434` が止める」である。

## C7 — レンズ B 所見 3 (main の gate 順序) は test-red 主張としては refuted、設計 nit として採用

C0 により、テスト中は site=OTHER なので `ExecutionGuardError` は発生せず
`test_cli_authority_boundary_rejects_before_build_spy` は赤にならない。よって「must-fix」ではない。

ただし既存の拒否境界を動かさない方が良いので、**site 解決は coder build authority gate の後に置く**。
新しいテストは要求しない。

## C8 — レンズ A 所見 5 (paired 判定と B4 gate の順序) を採用 (nit)

C2 で注入を `drive_iteration` だけに限るので、移植元 `p3_s4_loop_trigger_gating.py:1013-1031` の
順序 (paired 判定を B4 gate より前) にそのまま合わせる。

## C9 — レンズ B 所見 5 を採用 (must-fix、scope 内)

プランのテスト計画は注入経路に偏っており、**自動解決経路の正例が実体を名指ししていない**。
C2 で公開入口から注入を外した結果、`run_one_iteration` と `main` では自動解決が唯一の経路になる。
よって次を必須にする。

- 自動解決経路 (`_current_site()` → `_admit_env_contract()` → `_campaign_cfg_for_site()`) を通る正例で、
  **exact な contract object 同一性** (`cfg.bound_environment_contract is contract`)、
  compute の `measurement_env` marker、`run_campaign` が実際に受け取った cfg を同時に検査する
- `_campaign_cfg_for_site` が入力 cfg をそのまま返す実装でも通ってしまう検査を作らない
  (候補集合に含意されて恒真になる型を避ける)

## C10 — scope 外と裁定した real 所見 (実装しない。裁定パッケージへ)

1. **base B4 launcher の site 射影漏れ (レンズ A 所見 2 = レンズ B 所見 2、独立 2 件)。**
   `orchestrator/campaign/p3_b4_launcher.py:165-170` は `driver_kind == "trigger"` のときだけ
   site 射影する (親が実見)。base の B4 経路は legacy ID のまま context/sidecar を束縛するため、
   PEGASUS_COMPUTE では `p3_s4_loop.py:1814-1825` の launcher gate が campaign-ID 不一致で拒否する。
   **scope 外の理由**: (a) carry が名指ししていない別 file である、(b) OTHER では ID が不変なので
   現に動いている経路の回帰ではない、(c) compute 経路は [T-2232] が着地するまで到達不能である。
   **新規 carry として残す。**
2. **`_assert_layout_matches_campaign` / `_with_campaign_location` の移植漏れ (レンズ A 所見 3)。**
   base の既存検査 `p3_s4_loop.py:1438-1446` は `do_build=True` にしか効かない。
   production は `layout=None` なので露出は dry/test 注入だけであり、compute でしか差が出ない。
   `DW-G02` に従い 1 cycle 後へ送る。**新規 carry として残す。**
3. `p3_s4_loop_sort.py` は依然として linux-baremetal の定数と契約を直接使う (レンズ B)。別裁定。
4. `site_policy.current_site(require_evidence=False)` の OTHER fallback (レンズ A)。移植元にもある
   既存境界であり、本 wave では触らない。

## C11 — 変異事前登録 (DW-M01)

本 wave は `p3_s4_loop` の受理集合を**縮小する** (無条件 → 2 site)。よって承認外の過剰拒否の
正例も登録する (M2)。各変異は 1 箇所、赤理由が 1 つに絞れることを実装後に確認する。

| # | 変異位置 | 変異内容 | 期待する赤 |
|---|---|---|---|
| M1 | `_site_admits_measurement` | `return True` | 未受理 site が契約 lookup へ到達。admission matrix の負例が赤 |
| M2 | `_site_admits_measurement` | `return site == PEGASUS_COMPUTE` (過剰拒否) | OTHER の通常経路が全て赤 |
| M3 | `_campaign_cfg_for_site` | PEGASUS_COMPUTE 分岐を削除 | compute の campaign_id が OTHER と同一化。identity split が赤 |
| M4 | `_campaign_cfg_for_site` | site 条件を外し常に marker 付与 | OTHER の golden ID が変化して赤 |
| M5 | `run_campaign` 呼出し | `contract.env_tag` → `ENV_TAG` | contract 値の流入検査が赤 |
| M6 | `run_campaign` 呼出し | `contract.clocks_per_us` → `CLK` | 同上 (sentinel clk) |
| M7 | `run_campaign` 呼出し | `list(contract.numactl)` → `NUMA` | 同上 (sentinel numactl) |
| M8 | `run_campaign` 呼出し | `authorize(contract.env_tag)` → `authorize(ENV_TAG)` | compute の authorization 不一致が赤 |
| M9 | `default_cfg` | 環境契約 bind を復活 | compute 射影が `ValueError`。再 bind 検査が赤 |
| M10 | `drive_iteration` の paired 検査 | 片側注入の `TypeError` を削除 | atomic pair 検査が赤 |
| M11 | `drive_iteration` の paired 検査 | 注入 site の admission 検査を削除 | 不受理 site 注入が通り赤 |
| M12 | `drive_iteration` の paired 検査 | `contract.env_tag` 照合を削除 | 不一致注入が通り赤 |
| M13 | `campaign_options` | compute で `env_contract` を渡さない | forwarding 検査が赤 |

## plan v2 (段 5 実装子へ渡す確定形)

編集面は `orchestrator/campaign/p3_s4_loop.py`、`orchestrator/campaign/p3_b4_wiring_probe.py`、
`orchestrator/tests/test_p3_s4_loop.py`、`orchestrator/tests/test_p3_b4_raw_record_producer.py` に限る。

1. import へ `execution_guard` と `site_policy` を追加 (`p3_s4_loop.py:62-65`)。
2. `:112-114` の直後へ `_SITE_ENV_TAGS` / `_CAMPAIGN_ENV_KEY` / `_current_site` / `_lookup` を追加。
   `ENV_TAG` / `CLK` / `NUMA` の定義自体は残す。
3. `_site_admits_measurement` / `_admit_env_contract` / `_campaign_cfg_for_site` を移植元
   `p3_s4_loop_trigger_gating.py:444-472` と同型で追加する。
4. 現 `run_one_iteration` (`:1374-`) を `_run_one_iteration_resolved(..., contract, resolved_site, ...)`
   へ改名相当で内部化し、解決済み contract を使う形にする。公開 `run_one_iteration` は
   移植元 `:863-907` と同型で自分で site を解決して内部を呼ぶ。**注入引数は持たせない。**
5. `drive_iteration` に移植元 `:984-1031` と同型の `_resolved_site` / `_contract` paired injection を
   追加する。paired 判定は B4 gate より**前**に置く。解決済みの値で内部を呼ぶ。
6. `run_campaign` 呼出し (`:1497-1502`) を移植元 `:802-819` と同型にする。
   `contract.env_tag` / `contract.clocks_per_us` / `list(contract.numactl)` /
   `authorize(contract.env_tag)` と `**campaign_options`。`campaign_options` は
   PEGASUS_COMPUTE のときだけ `env_contract=contract` を入れ、`dependency_prefix` は非空のときだけ入れる。
7. `record_diff_reject` の呼出し 3 箇所へ `env_tag=contract.env_tag` を明示する。署名の既定値は残す。
8. `default_cfg` (`:1090`) から `ident.bind_environment_contract(...)` を外す。
9. `main` は coder build authority gate の**後**で site を一度解決し、
   `--emit-planner-context` 経路と通常経路の両方へ `_campaign_cfg_for_site` を適用する。
   **`main` に注入引数を足さない。**
10. C4 の consumer 2 経路を直す。
11. C9 の正例を含むテストを追加し、M1〜M13 を殺す。

**実装しないもの**: `_assert_resume_allowed`、`_receipt_provenance` / `_append_provenance_entry`、
`_assert_layout_matches_campaign`、`_with_campaign_location`、`p3_b4_launcher.py` の base site 射影、
公開 `run_campaign` seam を塞ぐ新 gate。すべて C3 / C10 で scope 外と裁定した。
