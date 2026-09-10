# 段 1 brief — [T-419] U-2 世代移行の実行 + D143 (b) + [T-987] (b)

dev-wave (2026-08-16)。branch `worktree-dev-wave-t419-generation-migration`、起点 main `10813338`。
実測はすべて本 worktree (submodule pin `511c9538`) で親が取得した。

## scope

pegasus 実行環境契約を **g1 から g2 へ活性化 (activate) し、その移行に追随して壊れる面を閉じる**。
床値 v2 の再測定そのものは本 wave の外 (同一 chain の後続段)。

## 確定済みユーザー裁定 (2026-08-16 一括裁定、authority = ユーザー)

- **D143 決定 (3) = 択 (b)**: 述語を正とし、較正を取り直して登録し直す + 取得時受入検査。
  択 (a) 述語緩和は受理集合を広げるため不採用。択 (c) attestation 除去は規律 2 違反で却下済み。
- **[T-987] = 択 (b) + 条件**: 床値 v2 の再測定は世代移行 wave と同一 chain でのみ実施する。
- **横断所見 (§3.1)**: D143 (b)・[T-987] (b)・床値の再登録は同じ未実装機構に突き当たるため 1 本にまとめる。
- **新規 T 番号は振らない。** D143 (b) の所有は [T-420]、chain の所有は [T-419]。

## 段 1 前提実測 (親が本 worktree で実測。裁定文の前提を 2 件覆す)

1. **世代移行機構は既に実装済みである。** `GENERATIONS` は pegasus g1/g2 を保持し
   (`orchestrator/campaign/env_contract.py:245-303`)、活性化権限・遷移検査
   (`env_contract_activation.py`)、履歴解決 `resolve_by_contract_sha256` +
   `ever_active_contract_sha256s` (`env_contract.py:671-703`) が WAL・ratified freeze・
   oracle report・floor campaign・reflux closure・trial completeness へ結線済み。
   発行 CLI `tools/issue_env_contract_activation.py` も存在する。
   **したがって本 wave は「機構の実装」ではなく「移行の実行」である。**
2. **g2 較正は取得・登録済みだが活性化されていない。**
   `output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json`
   (`quality.status=accepted`、`reasons=[]`、`host.node=bnode048`、48 CPU)。
   活性化 record は `00000001.json` の serial=1 = pegasus **g1** のまま。
3. **g2 は canonical clock 述語を自己充足し、g1 は充足しない。** 実測: 両者とも n=48・
   median=2101.0・tolerance 2.0%・帯 [2058.98, 2143.02]。**g1 は帯外 1 件 (3080.935)、g2 は帯外 0 件。**
   `KNOWN_SELF_INCONSISTENT_CALIBRATIONS` はちょうど g1 の 1 件で、
   `test_env_contract.py:832` に「[T-419] の U-1/U-2 が閉じたときに削除する」と明記されている。
4. **D143 (b) の「取得時受入検査」は 2026-08-06 の wave で既に land 済みである。**
   `orchestrator/calibrator/cli.py` の publish 後自己比較 (`published-self-comparison.json`)・
   attempt/publish 間 policy 同一性検査・early 拒否 proof。g2 はこの経路を通って取得されている。
   **裁定のうち未実施なのは「登録し直す」= 活性化だけである。**
5. **活性化は一時変異で実際に通る。** serial=2 record (`activation_state_sha256 =
   398b192013e0e3996ca225454049a14cb2866ef256b581fc3dfbfda02476bed8`) を置き head 定数 2 件を進めると
   `authorize("pegasus")` は g2 を返し、`ever_active` は g1 を保持する (履歴解決は生存)。
   **record bytes は canonical JSON + 末尾 LF が必須** — LF を欠くと authority 検証が全面的に落ちる (実測)。
6. **[T-475] が予言した破綻は実在する (実測)。** g2 活性化後、凍結済み
   `output/s8b-freeze/floor_protocol.json` (記録 hash = g1 `e576e9cd…`) に対し
   - `s8b_floor_campaign.validate_protocol` (歴史検証) = **OK**
   - `s8b_floor_campaign.validate_protocol_against_current` (live admission) =
     **拒否「protocol.contract_sha256 と resolver が返した env 契約が不一致」**
   `_current_protocol_contract` (`s8b_floor_campaign.py:465-476`) は記録 hash を捨てて
   `lookup(env_tag)` を返し、共通 core が hash 一致を要求するためである。
   この経路は `certified_writer_admission.py:209` の floor 投入 admission が使う。
7. **`docs/decisions.md:17896` は runtime attestation を `unmet — D143 のユーザー裁定待ち` と
   書いており、本裁定で前提が変わる。** 本 wave が更新する。
8. **blast radius を一時変異下の焦点走で実測した (bounded local、rc=1、赤 9 件)。**
   赤は `test_env_contract.py` と `test_env_contract_activation.py` の 2 file に閉じ、
   `test_env_attestation.py` は全緑。赤 9 件は次のとおりで、**いずれも「g1 が active である」
   ことを固定している面**である。逐語 = `focus-g2-envcontract.txt`。
   - `test_env_contract_activation.py::test_initial_record_is_exact_canonical_hash_bound_and_selects_both_g1`
   - `test_env_contract.py::test_registry_effective_clock_self_failures_are_exact_known_exception`
   - `test_env_contract_activation.py::test_held_lock_fork_reinitializes_child_cache_without_deadlock`
   - `test_env_contract_activation.py::test_issued_valid_suffix_is_not_active_until_source_head_update_and_restart`
   - `test_env_contract.py::test_registry_and_lookup_follow_activation_not_generation_tail`
   - `test_env_contract.py::test_pegasus_contract_sha256_golden`
   - `test_env_contract.py::test_lookup_pegasus_golden`
   - `test_env_contract_activation.py::test_registered_but_never_active_hash_has_distinct_refusal_reason`
   - `test_env_contract.py::test_resolver_rejects_registered_never_active_pegasus_g2`
   最後の 1 件は **「g2 は never-active でなければならない」を不変条件として書いている**。
   移行はこの不変条件そのものを反転させるので、単なる期待値の付け替えではなく
   「何を固定し直すか」を段 2・3 で確定する。
9. **一時変異は復元済み。** `git checkout --` で bytes を戻し、`git status` は
   本 insights ディレクトリ (untracked) のみ。
10. **移行前 baseline を実測した (復元後の g1 木)。** 凍結 `floor_protocol.json` は
    `validate_protocol_against_current` / `validate_protocol` の **両方が OK**。
    したがって前後関係は「g1: 両方 OK → g2: 歴史 OK / live 拒否」であり、
    live 拒否は本 wave が導入する新しい縮小である (既存の赤の露出ではない)。
11. **(P1) の循環は存在しない (実測)。** `s8b_floor_campaign.build_protocol_document` は
    `contract = _env_contract.lookup(env_tag)` で **current 契約から** `contract_sha256` を
    焼くため、g2 の下で組み立てた新 protocol は g2 hash を持ち current 検証を通る
    (`s8b_floor_campaign.py:629-659`)。
    残る障害は 2 つで、いずれも**後続段の所有**である:
    (a) `_write_protocol_document_create_only` は create-only であり、
        `output/s8b-freeze/floor_protocol.json` は既に g1 期 bytes で占有されている。
    (b) 凍結 protocol の `ccbench_pin = d706650c…` に対し
        `s8b_approved.CCBENCH_FULL_SHA = 511c9538…` で、**現 gitlink は 511c9538 と一致する**。
        つまり [T-987] 択 (b) が要求する pin は既に承認定数側に入っている。
    なお `validate_protocol_against_current` は `ccbench_pin` を承認定数と照合しない
    (照合は builder 側だけ) ため、この差は現時点の live 検証を落としていない。

12. **F97 の恒久対応は「未実施」のままであり、本 wave がそれを閉じる。**
    F97 (`docs/failures.md:3023`) は恒久対応を「未実施。述語と凍結較正のどちらを正とするかは
    ユーザー裁定へ返す (D143)」とし、再発検知を「登録済み較正自身を観測値として与えると
    受理される positive control」と定めている。既存の
    `test_registry_effective_clock_self_failures_are_exact_known_exception` がその positive control
    だが、**既知例外 1 件を許しているため現在は恒真でない検査になりきっていない。**
    既知例外を空にすることで初めて F97 の再発検知が本来の形になる。
    段 7 では F97 の恒久対応欄を実施済みへ更新する。

13. **【親 brief の自己訂正】g2 活性化は実行時の受理挙動を変えない (実測)。**
    canonical 述語は **期待列の中央値だけ**を使い、帯検査は **観測列にのみ**適用する
    (`execution_guard.py:405-414`)。g1 と g2 は中央値 2101.0・`tolerance_pct` 2.0 が同一なので
    受理帯は両者とも [2058.98, 2143.02] で **完全に一致する**。
    `compare_profiles` の 21 field のうち g1/g2 で差があるのは 4 つだけで、
    そのいずれも実行時の合否を変えない:
    - `tsc.raw_samples_mhz` / `tsc.median_mhz` — `round(median)` 比較で両者 2100 (`env_attestation.py:942-949`)
    - `effective_clock.samples_mhz` — 上記のとおり帯が同一
    - `effective_clock.method` — 後述 (14)
    **したがって「移行しなければ Pegasus 実行が落ち続ける」という当初の DW-G05 記述は誤りである。**
    F97 の smoke (2026-08-04) が落ちたのは **実行時観測**の帯外標本 (index 34 = 3076.13) であり、
    登録較正が自己不整合であることが直接の原因ではない。
    壁 1 を実際に開けたのは probe 側の方式 α 結線 (2026-08-05 `t419-alpha-wiring`) である。
14. **`effective_clock.method` の比較は恒真ゲートである (実測)。**
    `_recorded_verdict` は当 field を「expected と observed が**ともに非空 str** であること」
    だけで pass にする (`env_attestation.py:935-939`)。値の一致を見ない。
    その結果、g1 の期待側が `"proc-cpuinfo"` (素朴法) で、実行時観測側が
    `"proc-cpuinfo-rotating-min/k5/interval-ns50000000/sysfs-affinity-intersection-evenly-spaced-v1"`
    (方式 α) であっても **receipt には pass と記録される**。
    g2 の期待側は方式 α なので、活性化すると expected と observed が実体として一致する。
    **恒真ゲート自体の是正は受理集合を縮小する変更であり、本 wave の scope 外として
    裁定パッケージへ返す候補とする** (段 4 で裁定)。

15. **壁 1 (実行時 attestation) は既に開いている可能性が高い (一次資料 + 実測)。**
    `output/insights/2026-08-04_t419-probe-causality/README.md` の 2×3 判定表は、
    方式 α が **静穏時 9/9 通過・過剰拒否 0** であることを、
    **凍結較正の中央値 2101.0 の帯そのもの**に対して実測している。
    実行時の observed は現行 probe が生成し、その `method` は `EFFECTIVE_CLOCK_METHOD`
    (方式 α、`env_attestation.py:38-42`) である。
    さらに `EFFECTIVE_CLOCK_METHOD` を要求する consumer は probe 自身以外に存在せず
    (`grep` 実測、production では `env_attestation.py:680` の 1 箇所のみ)、
    登録較正側の `method` が素朴法であっても loader は拒否しない
    (`calibration_verify.py` に method 検査は無い)。
    **したがって「g1 が active だから計算ノードで何も走らない」は成り立たない。**
    ただし probe 因果実験と certified campaign の実走は別経路であり、
    本 wave は certified 経路の実走を実測していない。この点は段 4 で敵対レンズの判定と突き合わせる。

## 不変条件 (規律 2 を緩めない)

- **受理集合を広げない。** 述語 (`effective_clock` 全標本が帯内) と tolerance は不変。
  移行を通すために gate・許容・除外を緩めない。
- **歴史検証を壊さない。** g1 期に凍結された成果物 (`floor_protocol.json`、
  `silo_ladder_rung1.json`、その receipt) は `ever_active` 経由で従来どおり検証できること。
- **live admission が g1 期 protocol を拒否することは仕様どおりの縮小であり、
  「直すべき赤」ではない。** 通す道は床値 v2 の再測定 (後続段) だけである。
- **凍結成果物の bytes を書き換えない。** 旧 protocol・旧 receipt は据え置く。
- 活性化 record は create-only。既存 `00000001.json` を改変しない。

## DW-O09 pin 閉包 (親が実測した全列挙。段 2 が file:line で精緻化する)

| 面 | path | 分類 |
|---|---|---|
| 世代 registry / head 定数 | `orchestrator/campaign/env_contract.py:245-303,373-376` | live copy (変更) |
| 活性化 record | `orchestrator/campaign/env_contract_activations/00000001.json` | 凍結 (据置) / `00000002.json` (新規) |
| 既知例外 | `orchestrator/tests/test_env_contract.py:62-78,841,864-869,885` | live copy (変更) |
| 世代 golden | `orchestrator/tests/test_env_contract.py:70-78` (`EXPECTED_GENERATION_HASHES`) | 独立 golden (据置 = 2 世代を既に列挙済み) |
| record bytes literal | `orchestrator/tests/test_env_contract_activation.py:42` | 独立 golden (要確認) |
| g1 較正 literal | `test_env_contract.py:278-281,1133-1136`、`test_env_attestation.py:1299-1300`、`test_s8b_floor_campaign.py:5914-5917`、`test_silo_ladder_rung1_evidence.py:73` | live copy / 歴史記録の別を段 2 で分類 |
| 凍結 protocol | `output/s8b-freeze/floor_protocol.json` | 凍結 snapshot (据置) |
| 凍結 silo ladder | `output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json` | 凍結 snapshot (据置) |
| source identity pin | `orchestrator/qualification/contract.py:64-65` が `env_contract.py` / `env_contract_activation.py` を pin | 再発行要否を段 2 が判定 |
| docs | `docs/decisions.md:17896`、`docs/pegasus-runbook.md:711`、`docs/phase3-8b-restart-runbook.md:94` | 記述更新 (親が docs として書く) |

## 成果物の形

1. 活性化 record `00000002.json` (Codex author が発行)。
2. `env_contract.py` の head 定数 2 件の前進 (同一 commit)。
3. `KNOWN_SELF_INCONSISTENT_CALIBRATIONS` の空化と、それを守る負例テスト。
4. 移行後も歴史検証が通ること・live admission が縮小することを固定する positive/negative テスト。
5. 新 D (D96 手続に要る決定記録) — 活性化の権威と移行意味論。
6. worklog fragment ([T-419]/[T-420]/[T-475]/[T-478]/[T-987] の更新)、本 insights ディレクトリ。

## 分割方針

段 2 は read-only codex 1 本で pin 閉包と移行順序を file:line 化。段 3 は敵対 2 レンズ
(レンズ A = 規律 2・受理集合、レンズ B = 凍結 chain と歴史検証の生存)。
段 5 は Codex author 1 本 (面が 1 つの chain に連なるため分割しない)。

## provisional 裁定 (親の暫定であり攻撃対象)

- **(P1)** 「live admission が g1 期 floor protocol を拒否するのは正しい縮小である」。
  代案 (predecessor 許容) は受理集合を広げるので採らない。
- **(P2)** 「`KNOWN_SELF_INCONSISTENT_CALIBRATIONS` は本 wave で空化してよい」。
  g1 は登録上残るが active でなくなるため、既知例外の対象が消える。
- **(P3)** 「凍結成果物の bytes は 1 件も変えない」。歴史記録は測定時の契約を指したままが正しい。
- **(P4)** 「D143 (b) の『取得時受入検査』は既 land であり、本 wave で再実装しない」。
- **(P5)** 「[T-987] (b) の `ccbench_pin = 511c9538` は本 wave では記録のみ。
  床値 v2 の実測は後続段」。

## DW-G05 成果物影響 (実測 13・14 を受けて改訂)

移行を実行しない場合、**実行時の合否は変わらない** (実測 13)。変わるのは次の 3 点である。

1. **certified な run の receipt が、自己不整合な較正を「現行環境契約」として記録し続ける。**
   その較正は自分自身の受理条件を満たさないので、第三者が受理条件を再計算すると
   **参照側が不合格になる**。materials レポートの proof chain がこの参照を含む限り、
   「登録された環境契約が自分の判定を通る」という最も基本的な健全性が示せない。
2. **receipt の `effective_clock.method` が実体と食い違ったまま pass と記録される** (実測 14)。
   期待側は素朴法、観測側は方式 α である。論文で「同一の計測条件であること」を主張する根拠に
   ならない。
3. **床値 v2 とその先の certified 選択が開かない。** [T-987] (b) が要求する
   「現 gitlink で床値を測り直す」は、g2 期の環境契約の下で行わなければ
   環境と床値の世代が食い違う。

一方 (P1) を誤って「緩和」で解いた場合: 環境契約が変わったのに旧環境で凍結した床値を
現行として受理し、**certified 選択の比較基準が測定環境と食い違ったまま論文値になる。**
