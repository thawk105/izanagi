# 段 4 裁定 — [T-2675]

親が段 2 plan と段 3 の敵対 2 レンズ (a=sol 機序帰属と判定表 / b=luna 実験設計・安全・期限) を
real / refuted へ裁定し、plan v2 と事前登録 (判定表・適格性・完了条件) を**結果を見る前に**固定する。
段 4 直前に local main を再読した: `38353207f..main` は 0 commit、spool に関連 fragment なし。

## 1. 親の provisional 裁定の帰結

| # | 親の裁定 | 判定 | 根拠 |
|---|---|---|---|
| P1 | 4 仮説 (現 session / 現 pgid / fork 時記録の集合 / 周期走査の集合) で分離できる | **範囲を狭めて維持。** 4 仮説は網羅的でなく (a-1)、6 条件の結果は個別機序でなく**同値類** A/B/C/D (a-2) に落ちる。結論は「観測ベクトルと整合する同値類」までで、NQSV 内部実装は特定しない | a-1 / a-2 / plan §4 |
| P2 | 判定域 ≤5 / 20〜30 / 65〜75 | **修正。** 「≤5」は下限が無い → **−1〜5** とし、負方向のずれは時刻対応を点検して保留。窓幅 ±5 は事前に選んだ許容幅であって誤差の信頼区間ではないと明記。数値分類の前に**適格性条件** (§3) を置く | a-3 / plan §4 |
| P3 | heartbeat で死亡時刻を上限づける、子は ≤75 秒で自滅 | **誤りを認めて修正。** 最後の heartbeat は**生存時刻の下限**。`child-exit` も `_exit` 直前の記録で実消滅の証拠ではない。「t0+75 で終了処理へ到達 (正常経路)、alarm はユーザー空間の停止に対する予備で、割込み不能 I/O には効かない」と書き直す。E 付近で途切れた走は**打切り観測**として仮説表へ入れない | a-10 / b-4 / plan §6 |
| P4 | walltime 180 / queue-wait 1800 / overall-grace 2100 | **維持。** 期限順序は整合 (QUE 1800 → S+1800、overall は初期 S+2280、RUN 初観測で R+2280 へ更新、accounting grace は END 後 120 秒)。**qdel の境界を確定する (§2)** | b-2 / plan §5 |
| P5 | clean env に PBS_* が無いので環境変数説は弱い | **限定。** allowlist は「probe 自身の PBS_* を直接照合する狭い説」に不利なだけで、job 内 dispatcher が起動時に環境から job ID を読み fork 継承で追跡する上流登録型は未検証。「前 wave で反証済み」とは書かない。env 名採取は存在確認であって因果検証ではない | a-8 |
| P6 | 各条件 1 走で足りる | **限定して維持。** 丸め (≤1 秒) の説明だけを退ける。捕捉位相・ノード差・再現性には答えない → 「探索的 1 組」と明記。判別保留のときだけ同条件を 1 回再走 | a-5 / b-6 / plan §7 |
| brief | probe は uid 0 で走る | **誤り。** bootstrap は外側 `unshare --user --map-root-user` の後、fork 側で更に `unshare(CLONE_NEWUSER)` → uid_map (`real_uid 0 1`) → `setresuid(real_uid…)` → exec。probe から見える uid は実 uid の数値。**probe は `os.getresuid()`、`/proc/self/uid_map`、`/proc/self/ns/user` / `ns/pid` の readlink を `start` と `child-start` で記録する** | a-6 / b-5 |
| brief | dispatch の所属継承は `52e8fe7cf` から不変 | **根拠を添付して維持。** 親の実測: `git log --oneline -1 -- tools/pegasus/dispatch_compute.py` = `52e8fe7cf` (同 file を最後に触った commit)、`git log --oneline ac472026c..HEAD -- tools/pegasus/dispatch_compute.py` = 0 件。現行 L282 `os.fork()`、L304 `execvpe`、L328 正の pid への `waitpid`、L1131 `Popen` に `start_new_session` なし。scheduler 設定・ノード状態の不変性は導けない | a-7 |
| brief | 完了判定 = 判定表の 1 行に落ちる | **修正。** 「適格性を確認した観測ベクトル、整合する同値類、判別不能の理由、T-2676 へ渡せる制約を記録する」を完了条件とし、判別保留・打切り・比較不成立も正式な結果として含む (§5) | a-9 / b-9 |

## 2. 所見の裁定

**棄却した所見は無い。** レンズ a の 1〜11、レンズ b の 1〜10、plan の異議 3 点はすべて real として採る。

### 採用して plan v2 へ反映 (scope 内)

| 出所 | 反映 |
|---|---|
| a-1 / a-2 | §4 の同値類表を事前登録。C 類 (全 70) の内部 7 モデル、D 類 (0,70,70,70) の 2 モデルは本実験で識別不能と明記 |
| a-3 / plan §4 | 判定域 −1〜5 / 20〜30 / 65〜75、`δ = J − t0` を各走で算出し `E − J` の期待値を `30 − δ` / `75 − δ` で読む |
| a-5 | 25 秒 = 「所属変更の時刻に会計終了が対応した」まで、70 秒 = 「変更後も寿命対応の遅延が残った」まで。S0≈70 は fork 時登録の固有証拠ではない (now 前の記録書込みが捕捉窓を作る) |
| a-6 / b-5 | uid 三値・uid_map・ns readlink を記録。selftest (login) は隔離内成功の証明でないと明記し、本走の前後値で確認 |
| a-8 | P5 の限定 (§1) |
| a-9 / b-9 | 完了条件と T-2676 へ渡す 1 行の表 (§5) を事前登録。D2048 は置換せず**追補** |
| a-10 / b-4 / b-7 | heartbeat の解釈表 (§4.3)。記録途絶を「待たない」へ変換しない |
| b-1 | 所属変更失敗は `child-error` (errno・phase・前後所属) → `os._exit(1)`。S11 は mock でなく実子の終了 (pidfd) を観測 |
| b-2 | **qdel の境界 (下記)** |
| b-3 | 異常時手順: 異常 1 件で追加投入停止、receipt・qstat 応答・会計を保存、終端を待つ。手動 qdel も hold の手動削除もしない。hold が立ったら正規解消 (request 終端後の receipt 永続化) を確認するまで停止 |
| b-6 | 進行判定 (§3.3)。再走は「安全・記録異常なしで数値だけ域外」に限り、異常走は機械的に再投入しない |
| b-8 | 「この観測器具 (5 秒 heartbeat、fd 3 保持) を伴う条件下」と限定。fd 3 保持を全子条件で揃えても「比較に効かない」とは書かない |
| b-10 / plan §6 | F973 の再発検知: commit しないことは免除理由でない。既知 consumer (`tools/codex_worker_launch.py` の残存 group 計数、`tools/dev_waves/worker.py` の同型走査) は**本 wave で変更せず**、setsid/setpgid は generic job 内の独立 probe の子に閉じる。receipt / result schema に触れない。網羅探索済みとは書かない |
| plan §1 | `--release-seconds` と fd 解放コードは**削除** (K は fd 1/2 を保持、前 wave C 相当)。旧 S3 は登録しない |

**qdel の境界 (b-2 / plan §5):** ユーザー指示「qdel はしない」を、**親が手動で `qdel` を発行しない・orphan hold を手で消さない**と読む。
既存 dispatcher が queue-wait-timeout 後の fresh-qstat gate で QUE / HLD の request だけを取り消す経路 (RUN は取消不可) は、
ユーザーが指定した generic dispatch の既存挙動であり本 wave は変更しない。前 wave の段 4 裁定 (§3「QUE 状態の取消は許される安全な側」) と同じ読みである。
この読みは親の判断なので最終報告に明記する。発火を避けるため queue-wait-timeout は 1800 秒にしてある。

### 採用するが本 wave では実験しない (記録に留める)

a-1 の代替機序表と a-11 の追加介入候補 (親終了時刻と所属変更時刻の分離、fd / namespace 残存資源と寿命の分離、反復) は
insight の「言えないこと」と「次の一手候補」に置く。実験しない。

### scope 外 (裁定パッケージ候補)

dispatcher の取消政策変更、独立した子孫終了観測の追加、subreaper 再導入 (F973)、`_group_member_count` の Z 除外 ([T-2620])、T-2677。

## 3. plan v2 — 計算ノード実験

### 3.1 条件 (6)、順序 D → K → S0 → G0 → S30 → G30

| 条件 | 子 | 所属変更 | 変更時刻 | 親終了 | 子終了 (正常経路) |
|---|---|---|---|---|---|
| D `no-child` | 作らない | — | — | t0+5 | — |
| K `keep` | 作る (fd 1/2 保持) | なし | — | t0+5 | t0+75 |
| S0 `setsid-now` | 作る | `os.setsid()` | fork 直後 | t0+5 | t0+75 |
| G0 `setpgid-now` | 作る | `os.setpgid(0, 0)` | fork 直後 | t0+5 | t0+75 |
| S30 `setsid-30` | 作る | `os.setsid()` | t0+30 | t0+5 | t0+75 |
| G30 `setpgid-30` | 作る | `os.setpgid(0, 0)` | t0+30 | t0+5 | t0+75 |

子は `t0+5, 10, …, 70` の 14 回 `child-alive` を記録する (30 秒では所属変更を先、heartbeat を後)。
所属変更は `before-change` → syscall (直前・直後の monotonic) → `after-change` (sid/pgid/ppid の前後、errno=null)。
失敗は `child-error` (phase・errno・例外・取得済みの前後所属) → `os._exit(1)`。再試行しない。
`start` と `child-start` で `sorted(os.environ)` の key 名 (値なし)、`/proc/self/cgroup`、`os.getresuid()`、`/proc/self/uid_map`、
`/proc/self/ns/user` と `ns/pid` の readlink を記録する (読取り失敗は失敗として記録、空へ置換しない)。
子の alarm は `ceil(max(0, t0+75−now)) + 45` 秒 (起動遅れで寿命を延ばさない)、SIGALRM は `SIG_DFL`。

### 3.2 投入 argv (1 条件 1 job、直列、detached、この worktree から)

```
python3 tools/pegasus/dispatch_compute.py --task generic --walltime 00:03:00 --queue-wait-timeout 1800
  --overall-grace 2100 --accounting-grace 120 --poll-interval 2
  -- python3 -B tools/probe_t2675_run_membership.py --condition <条件>
  --evidence output/insights/2026-09-17/t2675-nqsv-run-membership/evidence/probe-<条件>.jsonl
```

親は投入前に evidence dir を作る。再走は `evidence/attempt-2/probe-<条件>.jsonl` へ (初走を上書き・追記しない、両方を README に載せる)。

### 3.3 各条件の後に親が確認する項目 (進行判定)

1. receipt `terminal_reason` = `scheduler-end-state` (会計で裏づけられた `request-disappeared-after-visibility` も可)、outcome rc=0、`accounting_verified`、request ID の対応。
2. `output/pegasus-dispatch/orphan-holds/` 0 件 (孤児の不在証明ではない)。
3. `.e` file 末尾の `Ended Request Time` (E) と trace `job-run-returned` (J) の対応、`result-dir-fsync-complete` の後に `job-run-returned`。
4. evidence: D は `parent-exit` が最終、子条件は `child-exit` が最終、変更条件は `after-change` が成功値 (S: sid=pgid=pid、G: pgid=pid かつ sid 不変)。
5. request が早く END しても子条件は t0+75 まで evidence を回収してから次へ (直列)。
6. syscall 失敗・記録破損・終端記録不足・walltime 終了・rc≠0・hold 残存のいずれかで追加投入を停止。

## 4. 事前登録 — 判定表 (結果を見る前に固定)

`J` = job 内 dispatcher の `job-run-returned` の時刻 (`.e` の trace)、`E` = `.e` の `Ended Request Time`、`δ = J − t0` (t0 は probe の `start`/`fork` の realtime)。

### 4.1 窓

| `E − J` | 読み |
|---|---|
| −1 〜 5 | **待たない** (0 窓) |
| 20 〜 30 (`≈ 30 − δ`) | **所属変更の時刻に会計終了が対応** (25 窓) |
| 65 〜 75 (`≈ 75 − δ`) | **子の寿命 (t0+75) に対応** (70 窓) |
| その他 | **判別保留** (同条件を 1 回だけ再走、両 attempt を記録) |

### 4.2 適格性 (数値を分類する前に全部満たす)

- D が 0 窓、K が 70 窓 (満たさなければ「比較不成立」として所属変更の効果を判定しない)。
- `δ` が 4.5〜10 秒 (親 5 秒 + dispatcher の result 公開)。
- 変更条件の `after-change` が成功値で、syscall 時刻が予定 (fork 直後 / t0+30) から 1 秒以内。
- `child-exit` が t0+75±1 秒にある (無ければ打切り観測)。
- `child-error`・必須行の欠落・JSON 破損・`recording_errors` の evidence 失敗が無い。
- J と E の request 対応・timezone が確定し、realtime に不自然な飛びが無い。

### 4.3 記録途絶の解釈

| evidence | 解釈 |
|---|---|
| E より明確に後の heartbeat がある | その時点まで子は生存 (E 時点の即時 kill と両立しない) |
| E 付近で途切れ `child-exit` なし | 打切り観測 (SIGKILL / 停止 / I/O 障害を区別不能)。仮説表へ入れない |
| `child-error` の後に途切れる | 器具の失敗。判定に使わない |
| t0+75 付近に `child-exit` | 自発終了経路への到達 |

### 4.4 観測ベクトル `(S0, G0, S30, G30)` と同値類 (a-2 の 15 モデル)

| 類 | モデル | ベクトル |
|---|---|---|
| A | A1 現 session / A2 現 session OR 現 pgid / A3 所属変更イベントで session 対象を更新 | (0, 70, 25, 70) |
| B | B1 現 pgid / B2 現 session AND 現 pgid / B3 変更イベントで pgid 対象を更新 | (0, 0, 25, 25) |
| C | C1 fork 時登録 / C2 再親化前の親子鎖捕捉 / C3 namespace 残存待ち / C4 UID 対象集合 / C5 全 process の出力参照 / C6 evidence 参照 / C7 即時変更より先に捕捉する保持型走査 | (70, 70, 70, 70) |
| D | D1 最上位 process 終了時の session 集合固定 / D2 特定周期の session 走査 | (0, 70, 70, 70) |

類内の対 (A: 3、B: 3、C: 21、D: 1 = 28 対) は本実験で識別不能。表外のベクトル (窓内だが上のどれでもない) は「既登録モデルでは説明不足、保留」。

## 5. 完了条件と T-2676 へ渡す 1 行 (事前登録)

| 6 条件の結果 | T-2676 へ渡す 1 行 |
|---|---|
| D≈0、K≈70、処置 = A 類 (0,70,25,70) | この probe では **session 離脱**に終了遅延の短縮が対応した → 所属分離 (session) を対策候補として検証する |
| D≈0、K≈70、処置 = B 類 (0,0,25,25) | **pgid 離脱でも**短縮した → group 分離を含む候補の実 workload 適用性を検証する |
| D≈0、K≈70、処置 = C 類 (70,70,70,70) | 今回の所属変更では短縮しなかった → **子の寿命・残存資源を終わらせる方向**を候補とし、追跡対象の同定は保留する |
| D≈0、K≈70、処置 = D 類 (0,70,70,70) | **即時の session 離脱だけ**で短縮した → 捕捉前の離脱を候補とするが有効な時点境界は未確定 |
| D/K 適格、その他の窓内組合せ | 既登録モデルでは説明不足 → 対策選択を保留し観測ベクトルを追加実験へ渡す |
| D 不適格 / K が再現しない | 比較の基準不成立 → 所属変更の効果は判定しない |
| 窓外・時刻対応不良 | 最大 1 回再走、両 attempt を記録。解消しなければ未確定で閉じる |
| 早期死亡・記録不足・投入失敗 | 打切り / 実験不成立。機序表へ割り当てない |

**job が早く終わることと、残存子が適切に終了することは別の評価項目**であり、本 wave は前者の分離だけを扱う。
D2048 は置換せず追補: 「generic 単一子 probe で〈処置〉と〈会計終了応答〉の対応を観測した。〈狭いモデル〉は不適合、〈残る同値モデル〉は識別不能、
NQSV 内部の判定方式は範囲を狭めて未確定」。F853 当時の機序、D1684 の各要素の寄与、pytest/xdist への外挿は未確定のまま。

## 6. 変異事前登録 (DW-M01) と検査

- probe は Codex `role=author` が書き、**commit しない** (job dir へ保全、SHA-256 と bytes で同定)。新規 test file も作らない。
- **commit される実装面の差分は 0 → `DW-S04` により変異 matrix を免除。受入全走は免除しない。**
- probe の fail-closed 挙動は probe 自身の `--selftest` に置き、親が login node で実走して結果を記録する (gate ではなく器具の自己検査)。

| # | 検査 | 確認方法 (`--selftest`、login、全体 ≤ 60 秒) |
|---|---|---|
| S1 | 未知の `--condition` / `--release-seconds` は rc≠0、fork も evidence 生成もしない | subprocess rc と file 不在 |
| S2 | `--child-seconds` > 75、NaN/∞/負、`parent ≥ child`、変更 30 秒 ≥ 寿命 は rc≠0 | 同上 |
| S4 | evidence が `/dev/full` でも子の寿命が延びない (親 1 秒・子 2 秒、pidfd で t0+1.9〜2.5 に終了) | pidfd |
| S5 | 親は子を wait せず子より先に終わる (`keep`、親 1・子 3) | pidfd |
| S6 | `no-child` は `start` / `parent-exit` のみで fork なし | evidence |
| S7 | `setsid-now`: `after-change` と外部 `/proc/<pid>/stat` (field 5=pgid, 6=sid) で sid=pgid=pid、初期値から変化、fd 1/2 保持 | evidence + /proc |
| S8 | `setpgid-now`: pgid=pid、sid 不変、fd 1/2 保持 | 同上 |
| S9 | `setsid-30` (親 0.2・子 32、変更 30): t0+30 未満の heartbeat は初期所属、syscall 直前時刻 ≥ t0+30、成功後 sid=pgid=pid | evidence |
| S10 | `setpgid-30`: 同上、pgid=pid・sid 不変 | evidence (S9 と同時開始) |
| S11 | 故障注入 (selftest 専用 env、公開 CLI にしない) で両 syscall に EPERM → `child-error`、`after-change` 無し、rc=1、失敗後 0.5 秒以内に pidfd ready | pidfd |
| S12 | `os.write` の短書き注入で再試行なし・エラー保持・終了 deadline 不変 | evidence / stdout |
| S13 | S9/S10 の 5〜30 秒 heartbeat の実時刻と事象順 (30 秒は change → alive)、env 値の非記録、cgroup / uid_map / ns 読取り失敗の表現 | evidence |
| S14 | 子が自分の alarm を再設定する (私有 harness で 1 秒 alarm → SIGALRM で終了) | pidfd + wait status |

## 7. 成果物の形

`output/insights/2026-09-17/t2675-nqsv-run-membership/` に (i) 段 1 brief と親の実測、(ii) plan と段 3 レンズ 2 本の逐語、(iii) 本裁定、
(iv) 6 条件の生データ (`evidence/`)、判定 (適格性・窓・同値類)、T-2676 へ渡す 1 行、(v) 言えないこと (内部実装の一意特定、死亡時刻と kill 主体、
厳密な寿命上限、観測者効果の不存在、ノード差・再現性・発生頻度、F853 当時と pytest/xdist への外挿、上流登録型の環境変数説)、
(vi) 次の一手候補 (a-11)。worklog / decisions (D2048 追補) は `docs/spool/` の fragment。failures は新規事故が無ければ触れない。

## 8. 追補 (2026-09-17 22:45、段 6 レビュー後・実験 2 の投入前に固定) — 実験 2: session 離脱 2 条件の寿命短縮版

**経緯:** 実験 1 の S0 / S30 は `child-exit` (t0+75) が記録されず §4.2 の適格性を満たさない (レビュー A-1 / B-1)。
E より後の heartbeat から E − J の分類を救う親の読みは事後変更であり、主解析には使えない。**実験 1 の主解析は
(不明, 70, 不明, 70) = B 類不適合、A / C / D 未分離** (A-2 / B-2)。また §3.3 (6) の「終端記録不足で追加投入停止」に
反して S0 の後に G0・S30・G30 を投入した (A-3)。これは逸脱として記録する。

**設計 (結果を見る前に固定):** 途絶は 2 走とも E の 35.3〜40.4 秒後の区間に入った。子の寿命をその区間より
短くすれば、`child-exit` が記録されうる。

| 条件 | 処置 | `--child-seconds` | 期待 `child-exit` | 予測 (A 類 / D 類) | 予測 (C 類) |
|---|---|---|---|---|---|
| S0′ `setsid-now` | fork 直後に setsid | **35** | t0+35±1 (E+約30) | `E − J` ∈ [−1, 5] (0) | [25, 35] (≈ 35 − δ = 30) |
| S30′ `setsid-30` | t0+30 に setsid | **60** | t0+60±1 (E+約30) | A: [20, 30] (25) / D: [50, 60] | [50, 60] (≈ 60 − δ = 55) |

他の argv は §3.2 と同じ。evidence は `evidence/exp2/probe-<条件>.jsonl` (実験 1 の file を上書きしない)。
順序 S0′ → S30′。**S0′ で `child-exit` が無い・所属変更失敗・記録異常・rc≠0・hold のいずれかなら S30′ を投入しない** (§3.3 (6) を今回は守る)。

**適格性:** §4.2 のうち「`child-exit` が t0+75±1」を「t0+`child_seconds`±1」に読み替える。他は同じ。D / K の適格性は実験 1 の値を用いる。
**分類:** 実験 2 が適格なら、最終ベクトルは (S0′, G0, S30′, G30) で、G0 / G30 は実験 1 の適格走 (寿命 75) を用いる。
寿命が違う (35 / 60 vs 75) ことは同値類の予測に影響しない (各類の予測は「待たない / 所属変更時刻 / 子の寿命」のどれに対応するかで決まる)。
S0′ が 0 かつ S30′ が 25 → A 類。S0′ が 0 かつ S30′ が 55 → D 類。S0′ が 30 かつ S30′ が 55 → C 類。他は保留。
**実験 2 が不適格なら主結論は実験 1 の主解析 (B 類不適合、A / C / D 未分離) のまま**とし、事後解析を併記する。
