# 段 1 brief v2 — [T-1851 前半] + [T-2107] + [T-1946] 試行台帳の配線と proof chain 束縛

**これは brief の差し替え版である。** 初版 (`verbatim-r1/brief-r1.md`) は実測 3 件が誤っており、
段 4 裁定 (`s4-adjudication.md`) で訂正した。初版と、初版に基づく段 2 plan・段 3 検査 2 本は
`verbatim-r1/` に保全してあるが、**前提が違うので結論をそのまま流用しない**。

base = 本 worktree の HEAD (着手時 `2bf9cf387` から local main へ ff 済み)。
branch = `worktree-dev-wave-t1946-t2107-registry-proof-wiring`。

## scope — 3 task の閉包を 1 変更単位で land する

- **T-1851 前半**: 台帳の世代分割、測り直しの別 ordinal 軸 (sealed な理由 authority)、
  terminal 理由の再導出、二台帳の crash 整合。
- **T-2107**: 床値 campaign を試行台帳の書き手 (`launch_floor_attempt`) へ production 配線する。
- **T-1946**: 新規 result 成果物へ台帳を前向きに束縛する (result schema v5)。

**後半 (`verified-registry-recovery` 側) は本 wave の scope 外**である (T-1851 段 4 が別 wave と明記)。
`orchestrator/campaign/trial_registry.py` (8c 層) も scope 外 (D1342)。
本題の実装だけを行い、仮想リスク向けの gate・検査・台帳・一般化は足さない。

## 確定済みユーザー裁定 (与件。再裁定しない)

- **D1341**: 配線と束縛は同じ変更単位で同時 land。片側 land は禁止。
- **D1340**: 予算専用 ledger を作らない。世代別台帳を横断 replay して凍結単位で数える。
- **D1337**: proof identity は `{row_count=N, chain_head_at_N}` の prefix 証明。
  **現 tail との完全一致は禁止。**
- **D1342**: 公式選択表を発行する最終 8c 層は射程外。
- **D1194**: 束縛は新規成果物へ前向きにだけ。既存 v4 の受理面を増減させない。
- **D1193**: 台帳は protocol 世代ごとに分け、予算は凍結単位に残す。
- **D1032 + T-1851 段 4 の承認済み (P1) 読み**: 測り直しは事前登録した別の試行番号軸として同じ
  耐久台帳の中に置く。理由は台帳専用の**閉じた語彙**とし、各値を sealed な session record から
  **機械的に導出**する (呼び手が選べる形にしない)。自由選択が無いので「受理する理由の集合を
  広げる」に当たらない。凍結 protocol の 4 語を再利用しない。
- **D880**: retry trigger は排他二択。**回復権限の pin 集合 (`_FLOOR_RECOVERY_AUTHORITIES`) は
  空のまま変更しない。** 本 wave はこの不整合を増やさない。

## 親裁定 (与件。plan で攻撃してよいが、覆すには実測が要る)

1. **v5 proof に「試行の被覆」を加える。** D1337 の prefix 証明は維持したうえで、
   その result 自身の全 attempt が台帳の lifecycle 行に対応することを検査する。
   根拠 = `{N, head}` だけでは genesis 1 行の台帳でも別 campaign の台帳でも通る (段 3 の 2 レンズが独立に実測)。
   これは D1194 が却下した恒真な保証にあたる。
2. **計測前に除外された試行も台帳へ残す。** campaign の pre-probe 競合による早期終了も、
   計測を開始せず reserve → terminalize する launcher 所有の経路を通す。
   campaign が probe 結果を launcher へ渡して分類させる形は採らない。
3. **live 台帳は shared lock 下で全行 replay し、比較は先頭 N 行だけ。**
   `len(rows) >= N` と `rows[N-1].event_sha256 == 記録 head` を要求する。
   N 行以後が壊れていれば replay が落ちるので受理しない。正当な append は受理する。
4. **不足入力 6 件の解** (段 4 裁定の表に従う)。
   - classification authority = launcher の出力前分類方針を名指しする production 定数を新設し、
     policy digest を方針 bytes から導出する (`s8b_scheduler_accounting.py` の
     `AUTHORITY_POLICY_BYTES` → `AUTHORITY_POLICY_SHA256` と同じ形)。test literal を昇格させない。
   - profile 構築用の recovery authority = `s8b_scheduler_accounting` の既存 authority を渡す。
     admission の pin 集合は空のまま。
   - run-start receipt digest = campaign が既に fsync している session-start bytes の digest。
   - admission claim digest = private `_CellState.measurement_generation_claim_digest` を
     公開 `CellHoldoutAdmission` へ射影する。導出は変えない。
   - retry ordinal 軸 = 上記 D1032 + (P1) 読みに従う。
   - consumption marker = admission 所有の exact validator を通し、adapter は検証済みだけを受ける。
     legacy marker の既存 test 面は維持する。
5. **世代列挙は 64 hex の directory だけを世代とみなす。** freeze 直下の sibling file は明示的に無視する。
6. **共有 root の既存 bytes に触れない** (下記「共有 root の実測」)。

## 不変条件

1. 規律 2 を緩めない。**既存 v4 input の受理面**を増減させない。新規 candidate 発行入口だけを
   v5-only にし、v4 downgrade を拒否する。
2. 予算防壁を世代リセットで緩めない。横断 replay の合計が凍結単位で正しく積算されること。
3. 台帳の不在・空・非 canonical・chain 不連続・別 binding は proof を返す前に拒否する。
   zero SHA を正例にしない。
4. `s8b_attempt_registry` の adapter を `s8b_floor_campaign.py` / `s8b_holdout_admission.py` から
   直接 import しない (meta-test が exact token で赤)。
5. 凍結済み bytes (`output/s8b-freeze/**` の既発行 artifact) を書き換えない。
6. D880 の回復側 pin を変更しない。

## 実アンカー (親が実測。file:line の確定は段 2)

| 面 | アンカー | 現状 |
|---|---|---|
| 台帳 path | `s8b_attempt_profile.py:380-382` | `floor-attempt-registries/{freeze_sha256}/registry.jsonl`。世代次元なし。作成時から不変 (`8d2d7f43d`) |
| path 導出 | `s8b_attempt_registry.py:451-459,462-482,485-491` | `_relative_registry_path` / `_entry_paths` / `registry_path`。内部 call site 11 件、public caller は production 0・test 2 |
| admission 側 raw reader | `s8b_holdout_admission.py:4960-4966,5048` | `_floor_registry_path()` 1 件 |
| 予算 | `attempt_registry_core.py:986-1020,1120-1129` | 単一台帳 replay 内で `(freeze_holdout_key, configuration_id)` 単位に計数 |
| 予算値 | `s8b_holdout_admission.py:1427-1435` + protocol | `n_sessions 8 + retry_slots_per_cell 2 = 10` |
| slot 軸 | `s8b_attempt_profile.py:26-35` | slot = (freeze_holdout_key, configuration_id, repetition, attempt_ordinal)、series = 先頭 3、budget = 先頭 2 |
| retryable | `s8b_attempt_profile.py:395` | `S8B_RETRYABLE_FAILURE_REASONS = frozenset()` (空) |
| ordinal gate | `attempt_registry_core.py:1081-1119` | ordinal>0 は前終端が `retryable-failure` のときだけ |
| 書き手 seam | `s8b_floor_attempt_launcher.py:548-670` | `launch_floor_attempt` の production 呼び手 0 件 |
| campaign 計測点 | `s8b_floor_campaign.py:5995-6122` | `_Runner._run_session()` の `self.measure_fn(...)`。**pre-probe 競合は `:6023` 付近で計測前に早期 return する** |
| campaign retry | `s8b_floor_campaign.py:6169-6187` | `_retry_round` が cell-wide の `_next_retry_ordinal(cell_id)` で採番。`source == "verified-registry-recovery"` 分岐は既に実在 |
| 権限 | `s8b_scheduler_accounting.py:40,102` | `AUTHORITY_ID = "izanagi-s8b-nqsv-qstat-j-f/v1"`、`AUTHORITY_POLICY_SHA256` は方針 bytes から導出 |
| 空の pin | `s8b_holdout_admission.py:105-109` | `_FLOOR_RECOVERY_AUTHORITIES = frozenset()` (理由が直上コメントに明記) |
| marker | `s8b_attempt_registry.py:1458-1460` / `s8b_holdout_admission.py:90` | adapter は `root/"consumed"/…`、admission は `measurement-generation-consumed` dir |
| result schema | `s8b_floor_contract.py:31,34,81-87,157-166` | `PROTOCOL_SCHEMA=s8b-floor-protocol/v2`、`RESULT_SCHEMA=s8b-floor-result/v4` の単一定数 |
| 消費 3 述語 | `s8b_floor_stats.py:734-747` / `s8b_holdout_freeze.py:1429-1439` / `s8b_ratified_freeze.py:2333-2356,2385-2389` | current schema 等値 |
| **見落とされていた消費層** | `s8b_holdout_freeze.py:1813-1840` | `_official_earlier_floor_results()` が earlier `result.json` を読み eligibility を導出する。**D1342 の射程外ではない** (あれは最終 8c 発行層) |
| official 拒否 | `s8b_floor_campaign.py:453-463` | official mode は core で無条件拒否。稼働可能なのは pilot だけ |
| 生成 2 世代 | `s8b_floor_campaign.py:178-179,311` | `floor_protocol.json` (sha256 261cec1c…) と `floor-protocols/e576e9cd…--511c9538….json` (sha256 2c8cf9be…) |

## 共有 root の実測 (初版の誤りを訂正)

台帳の実保存先は worktree 内ではなく **Git common dir 配下の共有 admission root**
(`s8b_holdout_admission.py:510-527` が `git rev-parse --git-common-dir` で解決)。実測:

- `<common>/izanagi/s8b-holdout-admission-v1/floor-attempt-registries/db07b575…/d388477f…/registry.jsonl`
  が **193 行**実在する。genesis の `root_path` は
  `floor-attempt-registries/<freeze>/<protocol>/registry.jsonl` の **2 段構造**である。
- 同じ freeze 直下に `consumption-catalog.jsonl` が **96 行**実在する。
- 両者の mtime は 2026-08-27 19:53:23 で以後不変。
- **この 2 段 path を書ける code は main に存在しない** (`S8B_REGISTRY_LAYOUT` は作成時から 1 段)。
  凍結 hash `db07b575…` は本番の `315b1eb8…` ではない。したがって 2026-08-27 の
  T-1851 実装試行が残した合成データであり、本番の消費者は無い。
- **削除も書換えもしない。** 世代列挙が sibling file で fail-closed しない設計にする。

## 稼働 wave との重なり (初版の誤りを訂正)

exact path 集合 + staged + untracked で再走査した結果 **3 件**。証跡 = `overlap-scan.txt`
(走査時刻・main head・各 worktree の head/base/変更数つき)。

| worktree | 重なる path | 規模 |
|---|---|---|
| `worktree-dev-wave-t2027-root-class2` | `orchestrator/campaign/s8b_floor_campaign.py` | 未 commit 6 行追加 |
| `worktree-dev-wave-t2074-a1-estimand-realign` | `orchestrator/tests/test_s8b_floor_campaign.py` | branch 差分 |
| `impl-dev-wave-t2074-fix2` | `orchestrator/tests/test_s8b_floor_campaign.py` | branch 差分 |

段 5 の実装子 dispatch 直前に再走査し、着地順を考慮する。

## 成果物の形

production code + tests + 変異 matrix + 記録 fragment。4 単位を unlanded workstream として
順に統合し、**統合後に一度だけ commit・land** する (D1341)。

## 分割方針 (provisional)

| 単位 | 編集 path | 内容 |
|---|---|---|
| A | `attempt_registry_core.py`, `s8b_attempt_profile.py`, `s8b_attempt_registry.py`, `test_attempt_registry_core_s8b_profile.py`, `test_s8b_attempt_registry.py` | 世代分割、横断予算 replay、別 ordinal 軸、閉じた理由語彙 |
| B | `s8b_holdout_admission.py`, `s8b_floor_evidence_fixture.py`, `test_s8b_holdout_admission.py` | claim projection、current marker validator、read-only prefix inspector |
| C | `s8b_floor_attempt_launcher.py`, `s8b_floor_campaign.py`, `test_s8b_floor_attempt_launcher.py`, `test_s8b_floor_campaign.py` | 分類権限、pre-probe 経路、配線、二相 crash 整合 |
| D | `s8b_floor_contract.py`, `s8b_floor_stats.py`, `s8b_holdout_freeze.py`, `s8b_ratified_freeze.py` + 対応 test と共有 fixture と `acceptance_duration_ledger.json` | v4/v5 contract、全 consumer、被覆検査 |

**C と D は相互依存するので独立緑を前提にしない。** 依存順 = A → B → (C, D)。

## (P1) 親の provisional 裁定 — 攻撃対象

- (P1-a) 世代識別子は `protocol_sha256` で足りる (段 3 で両レンズが成立と判定済み。再検査は軽くてよい)。
- (P1-f) 親裁定 1 の「被覆」は、result の全 attempt identity を台帳の start / terminal 行へ
  全単射で照合する形で実装できる。新しい成果物を作らずに閉じる。
- (P1-g) 親裁定 2 の pre-probe 経路は、計測を開始しない terminal status を既存の
  4 status (`observed` / `retryable-failure` / `terminal-failure` / `not-consumed`) の中で表現できる。
- (P1-h) 二相 crash 整合は、既存の journal fsync 順序を変えずに、registry terminal を先に
  永続化して再開時に reconcile する形で閉じる。
- (P1-i) 4 単位を 1 commit へ統合できる規模である (前回否定されたので、**行数で再評価すること**)。

## 実測環境

Pegasus。受入全走は親が `tools/dev_wave_wait.py acceptance` で投入する。
性能計測・build・benchmark は本 wave では行わない。

## DW-G05 成果物影響

放置すると、床値 pilot campaign は試行台帳を 1 行も作らないまま結果を発行し続ける。
材料レポートは「測り直しを追跡している」と謳いながら、台帳を削除・不正化しても検証が通る。
official 経路は現在 core で無条件拒否されているので、**現時点の certified 選択集合は変わらない**。
影響は pilot の材料レポートと、休眠中の official / certification 経路である。
同時 land でだけ、この恒真な保証が実効化する。
