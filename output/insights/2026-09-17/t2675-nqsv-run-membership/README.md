# [T-2675] NQSV が request を RUN に留める判定方式の分離 — session / process group / 追跡集合

authority: none / default_effect: no-state-change

wave = `dev-wave-t2675-nqsv-run-membership`、基準 commit = `38353207f`。
一次資料 (前 wave) = `output/insights/2026-09-16/t2622-compute-job-exit-hang/README.md` (D2048)。
目的は**判定方式の分離だけ**で、回収処理・防壁の実装 (T-2676)、subreaper (F973)、`qdel` は scope 外。
実装差分ゼロ (probe は repo へ commit せず job dir へ保全)。

---

## 0. 結論 (先に書く)

**主解析 (事前登録どおり) と事後解析を分ける。** 事前登録は `verbatim/s4-ruling.md` §4〜§5 (実験 1) と §8 (実験 2)。
**正式結論 = 実験 2 を合わせた主解析: (S0′, G0, S30′, G30) = (0, 70, 25, 70) は A 類 (現在の session 所属) だけと一致する。**

**実験 1 (6 条件、子の寿命 75 秒):**

| 条件 | 子の処置 | `E − J` (秒) | 窓 | 適格性 (§4.2) |
|---|---|---|---|---|
| D `no-child` | 子なし (統制) | **−0.001** | 0 | 適格 |
| K `keep` | 所属不変・75 秒 (陽性対照) | **69.546** | 70 | 適格 |
| S0 `setsid-now` | fork 直後に `setsid()` | **−0.473** | 0 | **不適格** (`child-exit` 未記録、最終記録 t0+40.001) |
| G0 `setpgid-now` | fork 直後に `setpgid(0,0)` | **69.757** | 70 | 適格 |
| S30 `setsid-30` | t0+30 で `setsid()` | **24.669** | 25 | **不適格** (`child-exit` 未記録、最終記録 t0+65.001) |
| G30 `setpgid-30` | t0+30 で `setpgid(0,0)` | **69.926** | 70 | 適格 |

- **主解析:** 適格な観測ベクトルは (S0, G0, S30, G30) = **(不明, 70, 不明, 70)**。G0 / G30 は **B 類 (現 pgid 基準) の予測 (0, 25) と不整合**。
  A / C / D 類はこの部分ベクトルでは識別できない (3 類とも G0 = G30 = 70 を予測する)。
- **事後解析 (結果を見た後に適格性を緩めた参考比較、正式結論・台帳追補・T-2676 の確定入力には使わない):**
  S0 / S30 は会計終了 E より明確に後の heartbeat (S0: t0+10〜40 の 7 回、S30: t0+35〜65 の 7 回) を持つので、
  短い `E − J` を「E 時点で子が死んだ」ことで説明はできない。その `E − J` を採ると数値ベクトルは (0, 70, 25, 70) で、
  事前登録した固定予測表では **A 類 (現在の session 所属に応答するモデル) だけと一致**する。

**実験 2 (session 離脱 2 条件の寿命短縮版。段 6 レビュー後・投入前に §8 で事前登録、子の寿命を途絶窓より短くして `child-exit` を記録させる):**

| 条件 | 子の処置 | 寿命 | `E − J` (秒) | 窓 | 適格性 (§8) | 予測 A / C / D |
|---|---|---|---|---|---|---|
| S0′ `setsid-now` | fork 直後に `setsid()` | 35 | **−0.456** | 0 | 適格 (`child-exit` t0+35.001) | A: 0 ○ / C: 30 × / D: 0 ○ |
| S30′ `setsid-30` | t0+30 で `setsid()` | 60 | **25.833** | 25 | 適格 (`child-exit` t0+60.001) | A: 25 ○ / C: 55 × / D: 55 × |

- **事前登録どおりの最終ベクトル (S0′, G0, S30′, G30) = (0, 70, 25, 70) は A 類 (現在の session 所属に応答するモデル) だけと一致する。**
  B 類は G0 / G30、C 類は S0′ / S30′、D 類は S30′ で不適合。実験 1 の不適格走 S0 / S30 の数値 (−0.473 / 24.669) は実験 2 の適格走と同じ窓にある。

**言えること (この観測器具を伴う generic 単一子 probe の条件下で):**
- process group を変えても (session が同じなら) 会計終了は子の寿命まで遅れる (G0 / G30)。**現 pgid 基準は不適合。**
- session を離脱すると、fork 直後なら会計は親終了と同時に (S0′: E = t0+4.6)、t0+30 なら所属変更から 2 秒以内に (S30′: setsid 22:55:56.148 → E 22:55:57) 終わる。
  fork 時に記録され所属変更後も保持される集合 (C 類) と、即時離脱だけが効く走査集合 (D 類) は不適合。
  これは**現在の session 所属に応答するモデルと整合する**が、照会・イベント更新・周期再評価 (< 2 秒) などの内部方式は特定しない。
- **付随観測 (事前登録外):** 寿命 75 秒で session を離脱した 2 走 (実験 1 の S0 / S30) では、会計終了の約 35 秒後まで heartbeat が保存され、
  その次の予定 heartbeat (約 40 秒後) 以降は回収時点まで記録されなかった。寿命を 35 / 60 秒にした実験 2 では子は E の約 30 秒後に自発終了した。
  **記録列の途絶は死亡時刻の区間や残存子の回収成功を示さない。** 原因と主体は未同定 (§5)。

**T-2676 へ渡す 1 行 (事前登録 §5 の A 類の行 + 段 6 B-5 の制約):** この probe では pgid 離脱だけでは短縮せず、**session 離脱に終了遅延の短縮が対応した**
(事前登録どおり)。session 離脱・session を基準とする回収を**検証候補**とし、会計終了と残存子の終了を別々に評価する。
離脱後の記録途絶 (§5) は回収成功の証拠にしない。

---

## 1. 前提 — 前 wave からの継承と、確認した事実

- D2048: 「同じ所属を継承したまま生き残った子孫が存命する間、job の会計終了が遅れる。fd 保持は必要条件ではない。判定方式は未確定」。
  前 wave の全記録は `sid == pgid` で、所属を変える条件が無かった。本 wave はそれを足した。
- job 内 dispatcher の構造 (前 wave M12) は現行コードと一致 (親の読解、段 3 で根拠を添付): `tools/pegasus/dispatch_compute.py` を最後に触った commit は
  `52e8fe7cf` (`git log --oneline -1 -- tools/pegasus/dispatch_compute.py`)、`ac472026c..HEAD` で同 file の変更 0 件。
  L282 `os.fork()` → 子は `unshare(CLONE_NEWUSER)` → uid_map → `setresuid` → L304 `execvpe`、親は L328 正の pid への `waitpid`。
  L1131 の `Popen` に `start_new_session` 指定なし。scheduler 設定・ノード状態の不変性は導けない。
- **probe から見える uid は実 uid (31609) である** (brief の「uid 0 で走る」は誤りで段 3 で訂正)。evidence: `resuid = [31609, 31609, 31609]`、
  `uid_map = "31609 0 1"` (内側 31609 → 外側 0)、`gid_map = "30410 0 1"`。user ns の readlink は 5 走が `user:[4026535834]`、G30 が `user:[4026534700]`、
  pid ns は全走 `pid:[4026531836]` — 別ホスト・別時刻の inode 文字列なので「job ごとに別 / host と同じ」は**本データからは証明しない**。
- generic job の clean env の key は `HOME LC_CTYPE LOGNAME PATH PYTHONDONTWRITEBYTECODE USER` の 6 個 (evidence `env_keys`、値は記録していない)。PBS_* は無い。
  これは「probe 自身の PBS_* を照合する狭い説」に不利なだけで、job 内 dispatcher が起動時に環境から job ID を読む上流登録型は未検証 (段 3 a-8)。
- cgroup は job ごとではなく NQSV service の共有 cgroup (`0::/system.slice/nqs-lchd.service` または `nqs-jsv.service`、ノードで異なる)。D1002 / 前 wave M13 と一致。

## 2. 実験設計 (事前登録は `verbatim/s4-ruling.md` §3〜§5、結果を見る前に固定)

`tools/probe_t2675_run_membership.py` (Codex `role=author`、656 行、30,373 bytes、
sha256 `f781162298f8885bd8d73f9e5d65d0d763fa14cc7e1673dd9961d42f9dc5b3e1`、**repo へは残さず job dir に保全**) を
`--task generic` で 6 条件、**直列・detached**、同一 worktree から投入した (順序 D → K → S0 → G0 → S30 → G30)。
全条件で親 probe は fork の 5 秒後に正常終了し、子を `wait` しない。子は t0+75 で `os._exit(0)`、5 秒周期で `child-alive` を記録、
所属変更は `before-change` → syscall → `after-change` (前後の sid / pgid、syscall 前後の monotonic)。失敗は `child-error` → `os._exit(1)`。
全子条件で fd 1/2 (job の stdout / stderr) を保持 (前 wave C 相当)。実験処置としての fd 解放コードは無く `--release-seconds` は未定義で拒否される。
selftest (login、13 項目 S1・S2・S4〜S14) は author と親の再走でともに 13 passed / 0 failed (親: 32.64 秒、rc=0)。
S6 (`no-child` は `start` / `parent-exit` のみ) は記録からの検査で、fork を呼ばないこと自体は監視しない (静的確認で補う)。S11 の EPERM は
コード内注入で、kernel が実際に EPERM を返す検査ではない (注入後の実子終了は pidfd で観測)。

投入 argv: `--walltime 00:03:00 --queue-wait-timeout 1800 --overall-grace 2100 --accounting-grace 120 --poll-interval 2`。
実験 1 の 6 request すべて `terminal_reason = scheduler-end-state`、`outcome.rc = 0`、`accounting_verified = true`、`qdel.attempted = false`、
`orphan-holds/` に entry なし (現在の一覧であり「一度も立たなかった」の独立証明ではない)。
**「qdel はしない」の扱い:** 6 request はすべて receipt 上 `qdel.attempted = false` で、手動 qdel・hold の手動削除も行っていない。
ただし親は「qdel はしない」を手動操作の禁止と解釈し、dispatcher 既存の QUE/HLD 自動取消経路 (queue-wait-timeout 後、RUN は取消不可) を残した。
この限定はユーザーから明示された例外ではなく、今回その経路が発火しなかったという実績と分けて報告する。

### 判定表 (事前登録、実験 1)

| `E − J` | 読み |
|---|---|
| −1 〜 5 | 待たない (0 窓) |
| 20 〜 30 (≈ 30 − δ) | 所属変更の時刻に会計終了が対応 (25 窓) |
| 65 〜 75 (≈ 75 − δ) | 子の寿命 t0+75 に対応 (70 窓) |
| その他 | 判別保留 |

適格性 (数値を分類する前に全部満たす): D が 0 窓・K が 70 窓、δ ∈ [4.5, 10]、所属変更が予定 ±1 秒で成功、**`child-exit` が t0+75±1 にある**、記録異常なし、J/E の対応。

| 類 | モデル | (S0, G0, S30, G30) |
|---|---|---|
| A | A1 現 session / A2 現 session OR 現 pgid / A3 変更イベントで session 対象を更新 | (0, 70, 25, 70) |
| B | B1 現 pgid / B2 現 session AND 現 pgid / B3 変更イベントで pgid 対象を更新 | (0, 0, 25, 25) |
| C | C1 fork 時登録 / C2 再親化前の親子鎖捕捉 / C3 namespace 残存 / C4 UID 対象集合 / C5 出力参照 / C6 evidence 参照 / C7 保持型走査 | (70, 70, 70, 70) |
| D | D1 最上位 process 終了時の session 集合固定 / D2 特定周期の session 走査 | (0, 70, 70, 70) |

## 3. 結果 — 実験 1 (2026-09-17 22:07〜22:27 JST、`verbatim/s5-measurements.md` に逐語)

`E` = `.e` の `Ended Request Time` (JST、秒精度)、`J` = trace `job-run-returned` の `time_ns`、`t0` = evidence の `t0_realtime_ns`、`δ = J − t0`。

| 条件 | request | node | Created (NQSV) | Elapse | δ | `E − J` | 窓 | 所属変更 (syscall 時刻、成功値) | 子の最終記録 |
|---|---|---|---|---|---|---|---|---|---|
| D | `4006.nqsv` | bnode033 | 22:07:40 | 10S | 5.025 | −0.001 | 0 | — | (子なし) `parent-exit` t0+5.001 |
| K | `4026.nqsv` | bnode028 | 22:15:08 | 79S | 5.022 | 69.546 | 70 | なし | `child-exit` t0+75.001 |
| S0 | `4035.nqsv` | bnode061 | 22:17:21 | 9S | 5.062 | −0.473 | 0 | t0+0.002、sid = pgid = 子 pid | `child-alive` t0+40.001 (次の予定 45 は未記録) |
| G0 | `4051.nqsv` | bnode028 | 22:20:45 | 80S | 5.024 | 69.757 | 70 | t0+0.002、pgid = 子 pid、sid 不変 | `child-exit` t0+75.001 |
| S30 | `4056.nqsv` | bnode033 | 22:22:37 | 34S | 5.022 | 24.669 | 25 | t0+30.001、sid = pgid = 子 pid | `child-alive` t0+65.001 (次の予定 70 は未記録) |
| G30 | `4069.nqsv` | bnode043 | 22:25:49 | 80S | 5.070 | 69.926 | 70 | t0+30.001、pgid = 子 pid、sid 不変 | `child-exit` t0+75.001 |

- 全 96 行が JSON として解析でき、`recording_errors = []`、親・子の seq に欠番なし。trace は全走 `result-dir-fsync-complete` の後に `job-run-returned`。
- 親終了 (t0+5) 後、子の ppid は 1 へ (init へ孤児化)。K / G0 / G30 の sid は job のまま。30 秒条件は `before-change` → `after-change` → `child-alive` の順 (seq 7/8/9)。
- 会計 `E` は秒精度。切捨てなら真の会計時刻は [E, E+1) で、D / S0 の負値はそれと整合するが、秒精度の表示だけで切捨て方式は証明できない。
- heartbeat の件数: K / G0 / G30 は 14 回 (t0+5〜70)。S0 は 8 回 (t0+5〜40) のうち表示 E (t0+4.6) より明確に後は 7 回 (10〜40)。
  S30 は 13 回 (t0+5〜65) で、30 秒未満は 5 回 (5〜25)、E (t0+29.7) より明確に後は 7 回 (35〜65)。

### 3b. 結果 — 実験 2 (寿命短縮版、事前登録は `verbatim/s4-ruling.md` §8)

実験 1 の S0 / S30 が不適格 (`child-exit` 欠落) だったため、段 6 レビュー後・投入前 (22:45) に §8 として事前登録した。
途絶 (§5) は 2 走とも E の 35.3〜40.4 秒後の区間だったので、子の寿命をその区間より短く (S0′ 35 秒 = E+約30、S30′ 60 秒 = E+約30) し、
`child-exit` が t0+`child_seconds`±1 にあることを適格性とした。他の argv は実験 1 と同じ、evidence は `evidence/exp2/`。
§3.3 (6) を今回は守り、S0′ が適格と確認してから S30′ を投入した。予測: S0′ は A / D = 0、C = 30 (≈ 35 − δ)。S30′ は A = 25、C / D = 55 (≈ 60 − δ)。

| 条件 | request | node | Created (NQSV) | Elapse | δ | `E − J` | 窓 | 所属変更 | `child-exit` | 予測との照合 |
|---|---|---|---|---|---|---|---|---|---|---|
| S0′ (寿命 35) | `4108.nqsv` | bnode037 | 22:40:32 | 9S | 5.038 | −0.456 | 0 | t0+0.013、sid = pgid = 子 pid | t0+35.001 (E+約30.4) | A ○ / D ○ / C × |
| S30′ (寿命 60) | `4133.nqsv` | bnode028 | 22:55:12 | 35S | 5.020 | 25.833 | 25 | t0+30.001、sid = pgid = 子 pid | t0+60.001 (E+約29.1) | A ○ / C × / D × |

- S0′ の request は NQSV の Pre-running に 22:40:32 から約 11 分留まった (実行ホスト未割当。同時刻に親の他 session の request 4 本も PRR)。
  原因は不明で、`qdel` はしていない。Started 22:51:40 以降は他の走と同じ経過。
- 2 走とも `recording_errors = []`、seq 欠番なし、`terminal_reason = scheduler-end-state`、`qdel.attempted = false`、orphan hold なし。
- S30′: setsid は 22:55:56.148、E は 22:55:57 (秒精度) → 所属変更から 0.85〜1.85 秒で会計終了。

## 4. 判定

### 4.1 適格性 (事前登録 §4.2) と主解析

| 条件 | D=0 窓・K=70 窓 | δ ∈ [4.5, 10] | 所属変更が予定 ±1 秒で成功 | `child-exit` t0+75±1 | 記録異常なし | 判定 |
|---|---|---|---|---|---|---|
| D | ○ | 5.025 | — | — | ○ | 適格 |
| K | ○ | 5.022 | — | ○ | ○ | 適格 |
| S0 | ○ | 5.062 | ○ (0.002) | **×** | ○ | **不適格** (打切り観測) |
| G0 | ○ | 5.024 | ○ (0.002) | ○ | ○ | 適格 |
| S30 | ○ | 5.022 | ○ (30.001) | **×** | ○ | **不適格** (打切り観測) |
| G30 | ○ | 5.070 | ○ (30.001) | ○ | ○ | 適格 |

**実験 1 の主解析:** S0 / S30 は `child-exit` 欠落により事前登録 §4.2・§5 の適格性を満たさず、機序表への割当てを保留する。
観測ベクトルは (不明, 70, 不明, 70)。G0 / G30 は B 類 (0, 25) と不整合だが、**A / C / D 類はこの部分ベクトルでは識別できない**
(3 類とも G0 = G30 = 70 を予測する)。

**実験 1 の事後解析 (結果を見た後の適格性緩和、事前登録どおりの判定と区別する):** E より明確に後の生存記録があるため、
「E 時点で子が即時に死亡した」ことによる説明は除ける (事前登録 §4.3 の 1 行目)。その上で S0 / S30 の `E − J` を採ると
(0, 70, 25, 70) となり、固定予測表では A 類だけと一致する。

**実験 2 を合わせた主解析 (事前登録 §8):** S0′ / S30′ は §8 の適格性を満たし、(S0′, G0, S30′, G30) = (0, 70, 25, 70) は A 類だけと一致する
(B 類は G0 / G30、C 類は S0′ = 0 ≠ 30 と S30′ = 25 ≠ 55、D 類は S30′ = 25 ≠ 55 で不適合)。
**これが本 wave の正式結論である。** A 類内部 (A1 / A2 / A3) は識別不能、表外モデルも排除しない。

**進行規則からの逸脱 (記録):** 事前登録 §3.3 (6) は「終端記録不足で追加投入を停止」と定めたが、親は S0 の `child-exit` 欠落
(22:19:34、t0+125 まで回収) を確認した後に G0・S30・G30 を投入し、S30 の欠落後にも G30 を投入した。親は当時 `E − J` の分類が
成立していると読んで続行したが、これは規則違反である。後続 3 走は計画どおりの適格走として結果は使えるが、「規則どおりに完遂した検証」ではない。
実験 2 ではこの規則を守った (§3b)。

### 4.2 同値類への対応 (実験 2 の適格走 S0′ / S30′ と実験 1 の適格走 G0 / G30。実験 1 の S0 / S30 も同じ窓)

| 類 | S0′ 予測 / 観測 0 | G0 予測 / 観測 70 | S30′ 予測 / 観測 25 | G30 予測 / 観測 70 |
|---|---|---|---|---|
| A | 0 ○ | 70 ○ | 25 ○ | 70 ○ |
| B | 0 ○ | 0 × | 25 ○ | 25 × |
| C | 30 (≈ 35 − δ) × | 70 ○ | 55 (≈ 60 − δ) × | 70 ○ |
| D | 0 ○ | 70 ○ | 55 (≈ 60 − δ) × | 70 ○ |

## 5. 付随観測 (事前登録外) — session 離脱の 2 走で記録列が途絶した

| 条件 | 表示 E (t0 基準) | 最終生存記録 | 次の予定記録 (未記録) | 最終記録 − E |
|---|---|---|---|---|
| S0 | t0+4.6 | `child-alive` t0+40.001 (state=R) | t0+45 | 約 35.4 秒 |
| S30 | t0+29.7 | `child-alive` t0+65.001 (state=R) | t0+70 | 約 35.3 秒 |

- 2 走とも、会計終了の約 35 秒後まで heartbeat が保存され、その次の予定 heartbeat (約 40 秒後) 以降は回収時点 (S0: t0+125、S30: t0+163) まで記録されなかった。
  別ノード (bnode061 / bnode033)、別の cgroup service。in-session の 3 本は寿命 75 秒で E = t0+75 なので比較にならない。
- 棄却できる説明: 「E 時点で子が即時に死亡した」(明確に E 後の heartbeat と両立しない)、「120 秒の alarm が途絶を起こした」(設定・時刻と整合しない)、
  「最終記録以前に fd 3 が閉じた / 別対象へ変わった」(採取した fd 状態に反する)。
- 区別できない説明: 最終記録後の kill、停止 (SIGSTOP)、I/O 停止、記録失敗。`recording_errors = []` は保存済み行までの事実で、最後の書込み失敗を排除しない。
  「NQSV の後処理が kill した」は主体・signal・実終了を観測しておらず**未支持**。
- 独立した終了観測 (pidfd 等) を本走に置かない設計 (段 4) なので、evidence だけでは死亡と記録障害を分けられない。
- **T-2676 への含意:** 離脱型の対策を採る場合、「離脱後は既存機構が回収してくれる」という期待を根拠にできない。残存子の実終了は独立に検証する。

## 6. 言えないこと

| 項目 | 理由 |
|---|---|
| NQSV 内部実装の一意特定 (A1 / A2 / A3、表外モデル) | 事後解析でも同じ予測ベクトル。イベント通知・常時照会・周期再評価は分かれない。同じ表示秒で対応した 1 走だけでは周期・位相・通知遅延を分離できない |
| session 離脱した子の死亡時刻と主体 | §5。evidence は生存時刻の下限しか与えない |
| 厳密な寿命上限 | alarm はユーザー空間の停止に対する予備で、割込み不能 I/O には効かない |
| 観測者効果の不存在 | 5 秒 heartbeat と fd 3 保持を伴う条件下の観測 (前 wave は 45/60 秒の 2 回)。`now` 前の記録書込みが捕捉窓を作りうる |
| ノード差・順序・時間帯・再現性・発生頻度 | 各条件 1 走 (探索的 1 組)、固定順、別ノード。同一ノードで全条件を反復した比較ではない |
| 他 uid・他 job との相互作用、user namespace / UID mapping の影響 | 全条件が既存の user ns / uid_map を伴い、その有無や NQSV 側からの可視性を独立に変えていない |
| `job-run-returned` と `child-exit` の意味 | 前者は Python process の実終了証拠ではない (前 wave §5)。後者は自発終了処理への到達記録。投入側 poll は 2 秒周期だが、比較に使う E は会計時刻なので poll 周期を E の誤差へ加算しない |
| F853 当時の機序、D1684 の各要素の寄与 | 当時の構造 (FIFO で止まった孫) を再現していない。既存の supersede と D1684 の是正を維持 |
| 受入全走 (pytest / xdist) への外挿 | generic 単一子の構造で測った。D1002 のとおり受入 suite は自ら多数の session を作る |
| 上流登録型の環境変数説 | clean env に PBS_* が無いのは probe 側の事実。job 内 dispatcher 自身の環境は観測していない |

## 7. D2048 への追補 (置換しない、決定は spool fragment)

generic 単一子 probe の事前登録した 2 実験で、(S0′, G0, S30′, G30) = (0, 70, 25, 70) を得た。pgid 変更後も寿命対応の会計遅延が残り (G0 / G30)、
session 離脱では会計が親終了と同時 (S0′) または所属変更から 2 秒以内 (S30′) に終わった。登録した同値類のうち **A 類 (現在の session 所属に応答するモデル)
だけが整合**し、B 類 (現 pgid)、C 類 (fork 時に記録され所属変更後も保持される集合)、D 類 (即時離脱だけが効く走査集合) は不適合。
実験 1 の S0 / S30 は終端記録不足で不適格だが、数値は実験 2 と同じ窓にある。A 類内部 (照会 / イベント更新 / 周期再評価) と表外モデル、
記録途絶の原因・主体、実 workload (pytest / xdist) への適用性は未確定とする。F853 当時の機序・D1684 の要素別寄与は未確定のまま、既存の supersede を維持する。
前 wave の因果の鎖 §7 第 5 段は「限定した命題 (今回の観測器具を伴う generic 単一子条件で、job の session に生きた process がある間 RUN に留まり、
session を離脱すると留まらない) は支持、元の一般命題 (所属一般・実 workload・内部規則) は未支持」に改める。

## 8. F973 の再発検知と変更範囲

F973 の再発検知に従い、既知 consumer として `tools/codex_worker_launch.py` の残存 group 計数、`tools/dev_waves/worker.py` の同型走査、
および probe / selftest の観測を列挙した (網羅探索済みとはしない)。本 wave の所属変更は generic job 内の独立 probe の子に閉じ、
既存 consumer・receipt / result schema・dispatcher は変更対象にしない。非 commit と器具 selftest の成功を、受入全走の免除理由にはしない
(実装差分ゼロによる免除は変異 matrix だけ、`DW-S04`)。

## 9. 次の一手候補 (実装しない、裁定パッケージ候補)

- T-2676 の設計入力: (a) session 離脱・session を基準とする回収を検証候補とし、会計遅延に加えて残存子の実終了・残存資源・別 session の子の扱いを評価項目に含める。
  (b) 元 session の列挙だけでは既に別 session へ移った子を拾えない。(c) 離脱後の記録途絶 (§5) の主体を独立観測 (pidfd / 別 job からの `/proc` 観測) で確かめる。
- 段 3 a-11 の追加介入 (親終了時刻と所属変更時刻の分離、fd / namespace 残存資源と寿命の分離) は本 wave では実施せず、T-2676 の候補選択が残る不確実性に依存する場合に再検討する。
- 受入全走の構造 (xdist、oracle の別 session) での再現は別実験。

## 10. 一次資料の所在

job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2675-nqsv-run-membership/` に保全した。逐語は本 dir の `verbatim/` (下表の sha256 / bytes で原文を同定)。

| file | 中身 |
|---|---|
| `s1-brief.md` | 段 1 brief (P1〜P6、段 3 で 3 点を訂正) |
| `plan-out.md` | 段 2 plan (read-only codex) |
| `consultA-out.md` / `consultB-out.md` | 段 3 敵対相談 (a: 機序帰属と判定表 / b: 設計・安全・期限) |
| `s4-ruling.md` | 段 4 裁定 (判定表・適格性・同値類・完了条件・selftest S1〜S14 の事前登録、§8 に実験 2 の事前登録) |
| `s5-measurements.md` | 段 5 実測 M1〜M10 の逐語 (実験 1 = M1〜M7、実験 2 = M8〜M9、集計 M10) |
| `author-out.md` | 段 5 author の報告 |
| `reviewA-out.md` / `reviewB-out.md` | 段 6 敵対レビュー (a: データ照合 / b: 因果と記録) |
| `probe_t2675_run_membership.py` | probe 本体 (job dir のみ、**repo へは残さない**、sha256 `f781162…`、30,373 bytes) |
| `evidence/probe-<条件>.jsonl` | 実験 1 の生データ 6 本 (本 insight の `evidence/` と byte 同一、`cmp` で確認) |
| `evidence/exp2/probe-<条件>.jsonl` | 実験 2 の生データ (本 insight の `evidence/exp2/` と同一) |

request → submission dir (wave worktree の `output/pegasus-dispatch/<digest>/`、`receipt.json` / `result.json` / `izdw-*.e<request>` に会計と trace):
`4006` → `7dd5d255468e4cfd8b1f21e957facf60`、`4026` → `58197e22c1daa9a36c1eab4197a29bd7`、`4035` → `7b18c319266eeaa03985a653feb82573`、
`4051` → `d45ebf69b352e406846e5c797ad4c9a0`、`4056` → `c3e9dab9db1109cf3805a4d7999e83b1`、`4069` → `69b0893b99c33cf4da15a1a8c197a1d7`、
`4108` (S0′) → `784ddc4ad67a80ec123fd8be601d1446`、`4133` (S30′) → `26c387b8329f0a9f91c6055f269a1977`。
本文の「投入」時刻は親が detach した時計時刻 (`probe-<条件>.started.txt`)、NQSV の `Created Request Time` は表の Created 列。

`verbatim/` の各 file は job dir の原文と byte 同一 (`cmp` で確認、行末空白の正規化は不要だった)。原文の同定:

| `verbatim/` の file | 原文の SHA-256 | 原文の bytes | 複製 |
|---|---|---|---|
| `s1-brief.md` | `a2c281133e8e870f62c2c3f3845979f1389d2e63121c0a933335b9d42f391278` | 5824 | 同一 |
| `plan-out.md` | `ff901175c8b58917a8b27e5d1f275164ed9e75436f1e0576d0f0f07a31ba4f38` | 26527 | 同一 |
| `consultA-out.md` | `1bde996168224afd6d10da5bfc1a67d26eef47bb1be6a2cd70972fd12a79c9ec` | 19241 | 同一 |
| `consultB-out.md` | `a516a84e6682d9a97cd84e23b320c4809f6001b8d2d3eeeb1fe2dc4fe84e24eb` | 13720 | 同一 |
| `s4-ruling.md` | `6f18db173b5ca21c00068e8391a65d4e66a8e7b1d3a47b5c0adfb560c70ca519` | 20753 | 同一 |
| `s5-measurements.md` | `471bae7d84183b85d6b6a2282c91adc76a00e785ca7e37f3816af44b3b82ebbc` | 12435 | 同一 |
| `author-out.md` | `ec7d1c3248922d1553cd64ba14c6384a2ca840d8fd21a6f64f9623bd951d0843` | 3409 | 同一 |
| `reviewA-out.md` | `5bddfc1e9a0d30305588501886ebcd7c6a89ee63631a214f90c7666630bd8f9a` | 14498 | 同一 |
| `reviewB-out.md` | `f26b705848ad53511b4d88d29e76733ba76173947d11c78ad668db6ea15e5c83` | 15331 | 同一 |

## 11. 段 6 の敵対レビューで親が直したこと

**棄却した所見は無い。レンズ 2 本の所見 (A-1〜A-11、B-1〜B-10) はすべて real として採った。**

1. S0 / S30 の「親の読み」による適格化 → 事後変更と認め、主解析 (B 類不適合、A / C / D 未分離) と事後解析 (A 類一致) を分けた (A-1 / B-1)。
2. 後退案の「B / C 類は G0・G30 だけで不適合」→ 誤り。C 類の G0 / G30 も 70 (A-2 / B-2)。
3. §3.3 (6) の「終端記録不足で追加投入停止」からの逸脱を記録した (A-3 / B-1)。
4. 「消えた」「消される」「消失」→ 記録列の途絶へ統一。死亡時刻の区間や回収成功を示さないと明記 (A-4 / B-4)。
5. 「判定は現在の所属」「session 単位の回収が NQSV と同じ粒度」「追加介入は不要」→ 観測の強さに合わせて限定 (A-5 / B-3 / B-5)。
6. heartbeat の件数 (S0 の E 後 8 → 7、S30 の 30 秒未満 6 → 5) を訂正 (A-6)。
7. t0 の定義表記 (`t0_realtime_ns`)、投入時刻の定義と NQSV Created の併記 (A-7 / A-9)。
8. user ns / pid ns の「job ごとに別 / host と同じ」を本データからは証明しないと限定 (A-10)。
9. S6 / S11 の検査範囲の限定 (A-11)。
10. T-2676 へ渡す 1 行を B-5 の形へ、D2048 追補と因果の鎖 §7 第 5 段を B-6 の形へ (B-5 / B-6)。
11. qdel の報告文を「不発火の実績」と「親の限定解釈」に分けた (B-7)。
12. probe 実体・evidence を job dir へ保全し同一性を確認、verbatim/ を配置 (B-8)。
13. 言えないことに標本設計・namespace・終了観測の限界を追加、F973 の consumer 列挙を §8 に (B-9 / B-10)。
14. 事後解析を事前登録済みの結果へ置き換えるため、実験 2 (寿命短縮版) を §8 として**投入前に**事前登録し、2 走とも適格な結果を得た (§3b)。正式結論は実験 2 を合わせた主解析 (§4.1)。
