# bytes 級 provenance 番人の棚卸しと受入 wall の構造 (2026-08-12)

wave = `dev-wave-freeze-chain-hold` / branch `worktree-dev-wave-freeze-chain-hold`。
2026-08-12 rulings 第 4 束が起票した凍結チェーン保留タスクの執行として開始し、
**実装は並行 2 wave へ移譲**して棚卸し・実測・独立検証に集中した。

## 1. 受入 wall の構造 (本 wave の最大の成果)

**wall = `@real-repo` 直列鎖 + 定数。鎖外を何秒保留しても wall は動かない。**

| 量 | 実測 |
|---|---|
| 全走 wall | **186.38 秒** |
| 全 node / 直列総和 | 9,459 node / **4,562.18 秒** |
| `REAL_REPO_SERIAL_NODES` (conftest 正本、関数単位 43) の総和 | **161.06 秒** |
| 鎖外 (4,401.12 秒) を 48 worker で割った相当 | 91.7 秒 → **鎖に埋もれる** |
| 差 (collection・startup) | 25.3 秒 |

計測 = branch tip main `7b6f91a8`、Pegasus 計算ノード 48 worker、非受入形 `-q --junitxml`、
request `906295.nqsv`。

### 鎖の内訳

| | node | 秒 | 鎖に占める割合 |
|---|---|---|---|
| 上位 5 node | 5 | **143.53** | **89%** |
| s1 freeze 番人 (known_axes 9 + measurement 10) | 19 | **2.29** | **1.4%** |
| 残り | 19 | 15.24 | 9.5% |

**独立裏取り**: growth-tests wave が別 tip・別走行・別集計経路で 44 node / 167.15 秒、
上位 5 で 150.5 秒 (90%) を得ている。node 数差 43 vs 44 は関数単位 (conftest 定義) と
実行時 node (`test_s8b_protocol_builder` の parametrize 2 展開) の数え方の違いで、どちらも正しい。

## 2. 並列全走の per-node 秒は「鎖外でだけ」雑音支配である

当初、並列 junit の per-node 秒を無条件に「雑音支配で使えない」と警告したが、**訂正した**。

| node | 並列 baseline | 直列 (`-n 0`) | 差 |
|---|---|---|---|
| `s8b_oracle_driver::test_cli_subprocess_returns_rc_2_on_gate_refused` (鎖内) | 53.15 | 49.24 | -7.4% |
| `s8b_binding_driftguards::test_run_block_broken_binding_manifest_...` (鎖内) | 29.32 | 29.21 | -0.4% |
| `s8b_oracle_driver::test_real_freeze_gate_lists_floor_and_budget_null` (鎖内) | 22.20 | 21.98 | -1.0% |
| `s8b_repo_scan_invariant::test_real_repository_scan_...` (鎖内) | 21.52 | 21.82 | +1.4% |
| `ruleops::test_real_checkout_independent_maximum_package_...` (鎖内) | 17.34 | 18.16 | +4.7% |
| `codex_reasoning_ab::test_verify_replays_complete_fake_codex_experiment` (鎖外) | 144.31 | 121.59 | **-15.7%** |
| `s8b_holdout_freeze::test_verify_cli_accepts_active_t080_receipt_exact_match` (鎖外) | 63.18 | 47.63 | **-24.6%** |

**機序**: 鎖内 node は `xdist_group("real-repo")` でもともと直列化されているため、並列走でも
順番待ちの押し付け合いが起きない。雑音は並列側で共有資源 (submodule clone / build cache) を
奪い合う node にだけ生じる。

**雑音の実例** (並列 baseline を前日の別 tip と比較): 同一テストの parametrize 違いが
`test_m3_focus_artifact_directions[NEG-focus2.md]` 1.45→93.82 (**+92.37**)、
`[POS-focus2.md]` 88.48→1.46 (**-87.02**) と入れ替わる。共有 fixture のコストを
「最初に掴んだ node」が全部計上し、次走では別 node へ移るため。

**帰結**: 保留候補の秒数は鎖内なら並列値でよい。鎖外は直列焦点走 (`-n 0`) で測る。

**1 日分の成長** (共通 9,425 node): 直列総和 4,516.63 → 4,559.50 秒 (+42.87 秒 / +0.95%)。
node 集合差は **new のみ 34 / old のみ 2 = 正味 +32 node/日**。集合差は雑音の影響を受けない。

## 3. 棚卸し — 331 node → 26 function → hold 4 / keep 18 / unsure 4

機構語の総当たりは 331 node / 73 file を拾ったが**大半が誤マッチ**だった。実測した誤マッチの型:
`signature` → Python の関数 signature、`reservation` → 予算・メモリの予約
(`test_login_headroom.py` 19 node、`test_s8b_budget.py` 6 node)、
`test_reflux_origin_ledger.py` 28 node → campaign の live origin 台帳。**語で拾うと live 機構を巻き込む。**

| 族 | 結果 |
|---|---|
| F1 承認署名・外部 trust root | **production に実装が存在しない。** 親が grep で検算 — 署名機構は皆無 (`--no-gpg-sign` は署名を*無効化*する側)、`t810_preregistration.py:446` の `approval_receipt_trust_root_absent` は「trust root が無い」宣言そのもの、`tools/dev_waves/git_state.py:954` の `trust_root` は checker の bytes pin = 防壁の自己完全性 (第 4 束が対象外と明記)。**保留対象なし** |
| F2 commit 束縛 | **14 function すべて keep。** `dev_wave_land` の provenance receipt 照合 (audit 中の HEAD 移動を拒否する TOCTOU 防壁を含む)、`spool_fold` の commit identity gate。成果物 provenance ではなく live admission |
| F3 公表台帳の原子性 | **hold 4 function (= 5 node)。** `orchestrator/publication/ledger.py` の `(root, kind, ordinal)` 一意性 + append-only 履歴 |
| F4 同一性証明 | **unsure 2 / keep 1** |

**保留確定 4 function の直列実測**: `duplicate_root_kind_ordinal` 0.01 /
`unchanged_ledger_bytes_across_merge_history` 0.04 /
`committed_non_prefix_ledger_history` 0.03 + 0.03 (2 node) /
`committed_delete_and_recreate` 0.03 = **合計 0.14 秒、全部鎖外 = wall 効果ゼロ**。

**根拠は速度ではない。** [T-793] R2 が [T-499]「手番が不要になったもの」に入っており、
`orchestrator/publication/ledger.py` の**非 test caller がゼロ**である (親が grep で全列挙)。
D320「使途の無い保証に維持費を払わない」が根拠。4 件とも唯一検出者であり、消える検出力は
実在するが裁定された縮小である。

## 4. 判定に迷い保留しなかった 4 件 (ユーザーへ返す)

1. `test_t793_publication_ledger.py::test_publication_identity_literals_and_schema_are_exact`
   — R2 原子性ではなく実装済みの識別束縛。D320 対象とも [T-793] R3 の訂正基盤とも読める。
2. `test_t793_publication_ledger.py::test_one_canonical_publication_entry_is_structurally_readable`
   — 未使用公表層の正例だが R2 より広い schema/admission を覆う。一括保留は危険。
3. `test_t139_approval_payload.py::test_real_fr_payload_has_exact_approved_values`
   — 追補 P の未承認 blob だけでなく D282 の**既承認 7 blob・alpha 台帳まで一括固定**する。
4. `test_t139_approval_payload.py::test_alpha_reservation_missing_descriptor_key_is_rejected`
   — 公表 R2 と恒久 approval parser の境界。**追補 P だけを分離できる検査点が現状ない。**

3・4 は「見送った機構」と「既に承認済みの基盤」が同じ node に同居しており、分離する検査点が
無い。段 3 の敵対レビューも「保留しないのが安全」と独立に判定した。

## 5. 裁定の衝突 1 件 (ユーザーへ返す)

第 4 束は「[T-902] のファイル数比例 live scan は**保留対象そのもの**」と書いている。その [T-902] が
指す `s8b_holdout_freeze.search_repository` は `verify_document:879` で呼ばれ、次行 `:880` の
`_assert_search_pass` (`:576-596`) が検査するのは **holdout 構成が repository へ漏れていないこと**
(conjunction hit 0 件) と **rr50 陽性対照が非 0** (検索式の偽保証の排除) である。これは
provenance の同一性証明ではなく**実験の妥当性 = 測定の公正**で、同じ裁定が「対象外」と明記した側。

**推奨 = 保留でも除去でもなく最適化。** [T-902] を阻んでいた「実装を 1 byte 変えると freeze 再発行が
要る」の正体は `_verify_source` の generator pin (`SCRIPT_REL` の bytes 完全一致) であり、
凍結チェーン保留が入った時点でこの阻害要因が消える。保証を 1 つも落とさずに 11,988 file ×
`re.search` 107,721 回を 1 パスへ畳める。

## 6. 3 wave の分界 (peer 交渉で確定)

| wave | 担当 | 層 |
|---|---|---|
| t816 | 凍結チェーン 5 系統の保留 | production 検査点。解除 = 定数の人手編集。可視化 = 発火ごとに stderr へ機械可読 1 行 |
| growth-tests | 成長比例軸の保留 + 台帳機構 | test 層 skip。解除 = env `IZANAGI_RUN_GROWTH_HELD_TESTS` |
| 本 wave | 凍結チェーン外側の棚卸し・実測・独立検証・[T-902] | 上記台帳へ相乗り |

land 順 = t816 → growth-tests → 本 wave。台帳 schema (peer 合意) =
key `basename::function` / `hold_axis` / `ruling` / `reason` / `correctness_gate` /
`release_condition` (固定値 `"explicit-user-command-only"` 完全一致) / `measured_seconds`。
**`hold_axis` への改名と `ruling` field の追加は本 wave の提案が採用された** — 台帳を 3 束で
共有すると「なぜ止まっているか」の根拠が混ざるため。

**残る欠陥**: 保留が 3 層に散り、ユーザーが「今なにが保留中か」を 1 箇所で読めない。解除も 2 経路。
恒久保留の解除がユーザー明示命令のみである以上、これは運用上の欠陥である。

## 7. 実測で分かった罠

- **`-p no:xdist` は使えない。** `tools/run_tests.py` が注入する `-n <N> --dist loadgroup` が
  pytest から unrecognized になり **rc=4 で走行ゼロ** (request `906469.nqsv`、6 秒で END)。
  直列化は **`-n 0`**。
- **鎖外 node へ `xdist_group("real-repo")` を付けると赤くなる。**
  `test_real_repo_serialization.py:567-615` が collection の real-repo group 集合を canonical
  golden として固定している。順序規則 (`xdist_group` を先に付けてから skip) は**鎖に居る node に
  だけ**適用される。段 2 の子はこれを全保留 node へ適用すると書き、段 3 の luna が BLOCKER にした。

## 逐語

`verbatim/` に段 2 プラン、段 3 敵対 2 本、段 4 裁定を凍結した。解析 probe
(`inventory.py` / `rank.py` / `chain.py` / `compare.py` / `nodes.py`) は repo 外
(`dev-wave-jobs/dev-wave-freeze-chain-hold/`) に置いた — repo へ入れると実装面になり
Codex author が要るため。junit は同 dir の `baseline.xml` (並列全走) と `measure.xml` (直列焦点走)。
