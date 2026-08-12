# 裁定パッケージ — [T-1005] 受入全走フレーク (F57 族) の帰属

- wave: `worktree-dev-wave-t1005-acceptance-flake-attribution`
- 実装差分ゼロ (診断 wave)。段 3 敵対 2 レンズの 16 所見はすべて real、refuted ゼロ。
- 段 4 裁定の全文は同 dir の `ruling.md`、逐語は `lens-a.md` / `lens-b.md`。

---

## 1. 結論 (先に 3 行)

1. **F57 の族は「予算の縁に張り付いた設計」である。** 48 並列下で launcher の job 全体所要が
   テスト予算 3.0 秒に対し実測 **3.01〜3.26 秒** に達しており、余裕がほぼゼロだった。
2. **どの近接原因が発火したかは、原理的に事後判定できない。** launcher は判定に使った情報
   (どの latch が発火したか・強制停止の理由・`residual=None` の出所・phase 別時刻) を
   1 つも保存しない。F57 が 20 回以上「未確定」だったのはこのためである。
3. **したがって恒久対応の第 1 手は計装 (O1) しかない。** ただし計装は赤を消さない。
   予算是正 (O2) と実時間依存の分離 (O6) が続くが、いずれも壊れる既存テストが具体的に判明している。

---

## 2. 観測された事実 (一次資料)

一次資料 = `/work/1/SFC/tanab/dev-wave-jobs/cleanup-cherry-3stage/` の受入 8 走分。

| 走 | log | ノード | request | 失敗 | 述語 |
|---|---|---|---|---|---|
| A | `acceptance.log` | bnode130 | 908484 | 21 | 全件 `["limit_trigger"]` = `max_wall_clock_s` |
| B | `auto-acceptance-2.log` | bnode019 | 908548 | 8 | 全件 `["metering_status","codex_exit_code","validator_rc"]` |
| C | `auto-acceptance-3.log` | bnode010 | 908562 | 3 | 2 件 `["process_group_residual","termination_verified"]` / 1 件 `["codex_exit_code"]` |
| 緑 | `auto-acceptance-1.log` / `-4.log` | — | 908528 / — | 0 | — |

走ごとに別ノード。走間の main 差分は docs のみ。単独走は 114 passed / rc=0 で非再現。

### 2.1 決定的な実測 — 予算の余裕がほぼゼロ

走 A の 21 件すべてに `receipt_actuals.wall_clock_s` (= job clock) が記録されている。

```
3.009903377  3.046011080  3.115954915  3.136876877  3.232447072  3.264959750 ...
```

**予算は 3.0 秒ちょうど。超過幅は 0.010〜0.265 秒 (0.3%〜9%)。**

これは「多秒の停止が起きた」ではなく、**所要が常時 3 秒の縁に張り付いていて、
わずかな揺らぎで境界付近のテストが一斉に越える**という状態である。

この 1 点が、F57 が説明できずにいた性質をすべて説明する。

- **失敗 node が毎回移動する** — 境界付近にいるテストは走ごとに違う
- **単独再走で再現しない** — 単独なら所要が予算を大きく下回る
- **loadavg と相関しない** (F57 既載に 0.80 での発火と 17.42 での発火が併存) —
  必要な摂動が極小なので、負荷指標に現れる必要がない
- **件数が 1〜21 と振れる** — 摂動の大きさで、境界を越える集合の大きさが変わる

### 2.2 テスト fixture の予算は production より桁違いに厳しい

| 引数 | テスト `_base_command` | production 実効値 | 比 |
|---|---|---|---|
| `--max-wall-clock-s` | `3` (test:961) | `3600` (`dev_wave_codex.py:20`) | 1200 倍 |
| `--evidence-grace-s` | `1.0` (test:1039) | `5` (launcher 既定 `:3104`) | 5 倍 |
| `--termination-grace-s` | `0.05` (test:1041) | `2` (launcher 既定 `:3108`) | 40 倍 |
| `--poll-interval-s` | `0.01` (test:1043) | `0.1` (launcher 既定 `:3113`) | 10 倍の高頻度 |

**重要:** production dispatcher (`dev_wave_codex.py`) が渡すのは wall / model / token だけである。
evidence と termination は **launcher parser の既定値に暗黙依存**している。
したがって「テスト値の是正」と「launcher 既定の是正」は影響範囲がまったく違う (§4 の O2)。

---

## 3. 機序 (どこまで言えるか)

### M1 — wall gate は job clock で判定し、失敗診断は attempt clock を印字する — **立つ**

- gate: `:1244` が `job_wall_clock_s > limits.max_wall_clock_s` を見る。
  job clock の起点は `:35` の module import 時刻 (`launcher_started_ns`)。
- 失敗診断が出す `wall_clock_s` は attempt clock (`:1540`、起点は `:1347` の `AttemptState` 生成)。
- 段 3 レンズ A は attempt clock で wall 判定する経路を探索し、**存在しないことを確認**した。
- したがって「予算 3 秒に対し `wall_clock_s=0.72` で wall 超過」という一見矛盾した記録は、
  **異なる 2 つの時計を同じ名前で読んでいる**ことによる。

**親が撤回した付随主張 (段 3 が壊した):**
- 「起点は `Popen` 直前」→ 誤り。`:1347` で hook 検証 (`:1403`) より前。
- 「job clock は receipt に残らない」→ 誤り。`:1702-1704` で `actuals.wall_clock_s` を上書き。
- 「`max_wall_clock_s` を立てるのは 3 箇所」→ 誤り。`_latch_final_job_limit` (`:1954-1977`) が
  attempt 後にも設定する (`:2069` / `:2085` / `:2124`)。
- 「0.716 秒から前処理 2.28 秒以上が逆算できる」→ 誤り。差分に post-attempt 監査が入る。

### M2 — evidence grace 満了 → 強制停止 → SIGKILL — **判定不能**

コード経路は実在する (`:1427` → `:1497` → `_terminate` → SIGKILL)。走 B の 8 件と強く整合する。
**しかし確定できない。**

- `codex_exit_code=-9` は外部 SIGKILL (OOM・scheduler) でも同じ値になり、識別する情報が無い。
- 必須同伴と思われた `metering_status='missing'` には**一次資料内に反例がある**
  (`auto-acceptance-3.log`: -9 かつ metering complete / validator_rc=0)。
- `evidence_forced_stop` は代入されるだけで receipt にも受理判定にも出ない (`:349` / `:1497`)。

### M3 — `residual=None` → `termination_verified=False` — **経路は立つが出所は判定不能**

`_normal_reap` (`:1200-1209`) が `residual == 0` だけを成功とするのは事実。
しかし `None` の出所は少なくとも 4 つあり (`identity` 自体が `None`、`/proc` の `scandir` 失敗、
個別 `stat` 読取失敗、parse 失敗)、receipt はどれかを記録しない。

### バーストの述語が均一なのは「1 原因」の証拠ではない — **P1 は撤回**

実装が `if/elif` で wall → model → token を単一 `pending_limit` へ縮約し (`:1461-1475`)、
`limit_trigger` が立つと evidence deadline を見ずに break する (`:1487-1499`)。
複数原因が同時に成立しても記録は 1 つになる。
走ごとに失敗集合が違うのは、**たまたまその phase にいたテストだけが終端述語を出す** selection effect
で説明できる。

---

## 4. 併発条件 (依頼の主眼)

- **計算ノードの co-tenancy ではない。** gen_S は 1 job = affinity 全数 48 で実質専有。
  3 バーストは別ノード (bnode130 / bnode019 / bnode010)。
- **並行 codex 子は必要条件でも判別子でもない。** 2026-08-13 の窓では codex 子は
  **緑の走 (02:03・02:45) とも重なっている**。F57 既載にも「子ゼロで発火」の対照がある。
- **48 並列という条件は支持される。** F57 既載の `-n 8` 緑との対照、および §2.1 の縁張り付き。
- **「共有 Lustre が原因」までは分離できていない。** 候補は M1 の preflight/post-attempt 監査の
  git I/O、M2 の rollout 発見、M3 の `/proc` 走査と複数あり、phase 別時刻も I/O latency も
  記録されていない。**原因を 1 つに固定せず、未分離として返す。**
- **限界:** 併発 worktree の多くが既に撤去され dispatch receipt が残らないため、
  クラスタ横断の同時実行数は事後再構成できなかった (残存 log の完了時刻の重なりまで)。

### [T-139] land2 K5 (受入 lease を他 wave の codex 子まで広げるか) への含意

**親推奨「現状維持」を支持する。** codex 子は緑の走とも重なっており判別子になっていない。
lease を広げても支配的な寄与を掴めない一方、wave の並列性を大きく削る。
ただし K5 の裁定そのものは本 wave の scope 外であり、触っていない。

---

## 5. 再現手順

- **決定的 (機序ごと):**
  - M1 型 — `--max-wall-clock-s` を `0.30` へ縮める。F57 既載 ([T-663]) が決定的再現を記録済みで、
    §2.1 の縁張り付きと整合する。
  - M2 型 — `--evidence-grace-s` を `0.05` 級へ縮める。
  - M3 型 — 未確立。`/proc` 読取失敗か `identity=None` の注入が要る。
- **確率的:** 他 wave が受入全走・変異走を回している時間帯に 48 worker 全走を投入する。
  2026-08-13 の実測では 8 走中 3 走がバースト。
- **測定 (最重要):** O1 を入れたうえで全走を回し、`receipt_actuals.wall_clock_s` の**分布**を取る。
  §2.1 は 21 件の失敗側しか見ていない。**緑の走で予算にどれだけ余裕があるか**を測れば、
  O2 で選ぶべき値が証拠から決まる。

---

## 6. 恒久対応の選択肢と親推奨

| 案 | 親推奨 | 決め手 |
|---|---|---|
| **O1 計装** | **採る (最優先)。ただし「直った」と数えない** | 現状は判定に使った情報が 1 つも残らない。最低限: 発火した latch の識別、強制停止の理由、`residual=None` の出所、phase 別時刻、失敗時 receipt の保存 (= F57 の [T-190])。これ無しでは次の再発も判定不能に終わる |
| **O2 予算是正** | **条件付きで採る (O1 の測定後)** | **test file 内の値だけを変える。launcher parser の既定 (`5` / `2`) は触らない** — production が暗黙依存しているため。段 3 が壊れる 12 nodeid を具体列挙済み (下表) |
| **O3 時計起点の移動** | **却下** | `test_launcher_process_wall_clock_includes_version_preflight` (`test:2705`) が「wall clock は version preflight を含む」ことを明示 pin。意図した不変条件であり緩めれば規律 2 違反。「予算 3600 秒だから安全」は恒真ゲート |
| **O4 `/proc` 観測** | **「理由を別 field に出す」部分だけ採る** | `unknown` を残留なしとして受理する解釈は残留 process の見逃し。`termination_verified=False` と受理条件は維持 |
| **O5 並列度引き下げ** | **恒久対応にしない** | 発火率が下がるだけ。F57 は「テスト再試行で緑にする」を既に規律 2 違反として禁じており同じ論法が及ぶ。暫定緩和として使う場合も `-n 8` の緑を修正済みと数えない |
| **O6 実時間依存の分離** | **条件付きで採る** | `_monotonic_ns` は seam だが `_terminate` / `_normal_reap` は `time.monotonic()` / `time.sleep()` を直に使う (`:1192` / `:1204`)。政策テストは仮想化し、setsid・SIGTERM・`/proc` の少数 integration test は実プロセスのまま残す |

### O2 で個別対応が要る nodeid (段 3 レンズ A の列挙)

| nodeid | 依存 | 引上げ時の影響 |
|---|---|---|
| `test_launcher_failure_diagnostic_reports_failed_predicates` | 診断に `3` / `1.0` / `0.05` を literal assert | 値変更だけで失敗 |
| `test_check_receipt_marks_self_asserted_limits_and_accepts_external_expectations` | 既定 wall=3 を外部期待 `"3"` と照合 | 既定変更だけで失敗 |
| `test_attempt_preflight_delay_exhausts_wall_clock_before_spawn` | wall=3 + 論理時計 +4 秒 | 4 秒超へ上げると gate 不発 |
| `test_launcher_process_wall_clock_includes_version_preflight` | wall=0.1 + version delay 0.2 | 0.2 秒超へ上げると gate 不発 |
| `test_receipt_staging_wall_overrun_flips_to_not_accepted_and_removes_output` | 既定 wall=3 + staging 後 +4 秒 | production 級へ上げると accepted のまま (**恒真化**) |
| `test_receipt_audit_wall_overrun_flips_to_not_accepted` | 同上 | 同上 |
| `test_rollout_missing_after_grace_is_stopped_and_not_accepted` | evidence=1 / wall=3 / fake 30 秒 sleep | evidence だけ 5 へ上げると wall が先に発火し期待破壊 |
| `test_thread_missing_after_grace_kills_process_group` | evidence=1 / termination=0.05 / TERM 無視 | 引上げで wall 先行、または 10 秒 harness timeout |
| `test_sigterm_ignoring_child_is_killed` | wall=3 / termination=0.05 / fake 30 秒 sleep / harness timeout 10 秒 | wall を大きく上げると timeout。termination を 30 秒級にすると自然終了でも assert が通り「killed」が**恒真化** |
| `test_cli_reported_token_limit_stops_process` ほか 2 件 | TERM 無視 fake と termination grace | 大幅引上げで timeout、さらに長くすると cleanup assert が恒真化 |

---

## 7. 要裁定

- **R1:** O1 (計装 + 失敗 receipt 保存) を後続タスクとして起票してよいか。**親推奨: 可。**
  F57 が 2026-07-30 から起票し続けている [T-190] と同じ対象であり、本 wave はその
  **具体的な必要 field 4 種**を初めて特定した。
- **R2:** O2 (予算是正) を O1 の測定結果に条件づけて起票してよいか。**親推奨: 可。**
  ただし **launcher parser の既定は触らない**ことを起票時の制約に含める。
- **R3:** O3 / O4 / O5 / O6 の採否。**親推奨: O3 却下・O4 は理由 field のみ・O5 は運用緩和に留める・
  O6 は可 (政策テストの仮想化と integration test の実プロセス維持を分ける)。**
- **R4 (本件と別):** `tools/check_wave_startup.py` の `_check_worktree_handoff` は
  tracked/untracked を区別しないため、main に handoff が landed していると
  **`--external-handoff` を必須とする背景 job の wave はすべて起動時 rc=1 になる。**
  land は handoff 削除を拒む (rc=21) ので wave 側では解消できない。
  **本 wave が 2026-08-13 07:32 JST に踏み、その 36 分後に別セッションが独立に同じ赤へ当たって
  main で直接 `docs/handoff/2026-08-13-known-red-octopus.md` を撤去した** (`a3168d85`、08:08 JST)。
  **`DW-G03` の独立 2 例が成立している。**
  ただし撤去されたのは file だけで **checker は直っていない**。land は handoff の追加を許すので、
  次に wave が handoff を land した時点で同じ赤が再発する。
  **親推奨: checker 側で tracked file を除外して機械側で閉じる。**
