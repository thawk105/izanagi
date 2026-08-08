結論として、段2プランはこのままでは land 不可です。検査自体は恒真ではありませんが、certified reader の迂回、repair 順序、identity の受け渡し、S8b report、D125 の裁定境界に must-fix があります。以下は HEAD `cf90afccf3250493a8ecb35284ecfe6a1e37b3ac` の静的検査です。pytest は実行していません。

### F-01 — 「別 campaign の COMMIT 行だけを複写」は発火証拠にならない

**対象 / 判定:** [s2-plan.md:148–156](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t530-contract-hash-binding/s2-plan.md:148) — **refuted**

**根拠:** COMMIT 行だけを持ち込むと、契約照合より独立に既存 attempt topology が拒否する。

```python
# wal.py:995-1001
if record.stage in {STAGE_BUILD_DONE, STAGE_COMMIT}:
    attempt = global_attempts.get(attempt_id) ...
    if attempt is None or attempt.variant != record.variant:
        raise AttemptTopologyError(
            f"{record.stage}: matching build_start attempt がない")
```

さらに同じ attempt があっても active/receipt/build_done が一致しなければ [wal.py:1002–1020](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/wal.py:1002) で先に落ちる。

**成果物影響:** nit — この例では新検査を除去しても受理集合も certified 値も変わらない。

**修正案:** 例を「別 campaign の完全な BUILD_START→BUILD_DONE→COMMIT attempt 鎖を移植」に置換する。§9 の正当な receipt/attempt を持つ mutation fixture は発火証拠として有効。

### F-02 — 残り4例は先行層を通過し、検査は恒真ではない

**対象 / 判定:** [s2-plan.md:151–156](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t530-contract-hash-binding/s2-plan.md:151)、[wal.py:247–285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/wal.py:247) — **real**

**根拠:** parser は payload が object であることしか保証せず、個別 schema を consumer に委譲する。

```python
# wal.py:250-251
payload object 内の個別 schema は consumer 側の責務。
```

既存 topology が COMMIT で調べるのは attempt ID、receipt SHA、BUILD_DONE の順序だけであり、contract field は読まない。したがって次は検査へ到達する。

- H_A→H_B の field 単独編集
- field 欠落の旧 writer COMMIT
- H だけ異なる campaign の WAL 全体移植
- variant/attempt/receipt を固定した field 単独変更

identity lock も [ident.py:176–182](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/ident.py:176) で「現在 cfg 対 lock」しか比較せず、WAL は比較しない。

**成果物影響:** 検査が無ければこれらの COMMIT は [wal.py:1395–1397](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/wal.py:1395) で `committed=True` となり、terminal skip・選択・報告へ混入する。

**修正案:** §9 fixture を正本にし、helper 単体だけでなく replay、artifact admission、report reader の各入口で同じ変異が赤になることを固定する。

### F-03 — binding error より先に tail repair が成果物を書き換える

**対象 / 判定:** [ident.py:185–202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/ident.py:185)、[s2-plan.md:103–110](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t530-contract-hash-binding/s2-plan.md:103) — **real**

**根拠:** 現行順序は identity lock の照合後、COMMIT topology/recovery 検査より先に tail repair を実行する。

```python
ensure_campaign_identity(...)
repair = wal.repair_truncated_tail(...)
wal.recover_interrupted_attempts(...)
```

repair は receipt を書き、続いて `ftruncate`/`fsync` する。

```python
# wal.py:584-586
receipt_path = _write_receipt(layout, receipt)
os.ftruncate(fd, final_size)
os.fsync(fd)
```

したがって「H mismatch COMMIT＋truncated tail」では、後段で拒否されても WAL bytes と repair 台帳が既に変わる。これはプラン §6 の「WAL bytes を変更しない」と矛盾する。

**成果物影響:** 拒否対象 campaign の WAL hash、tail bytes、repair receipt 台帳が変化し、後続 admission/frozen reference が別 artifact を観測する。

**修正案:** parse 可能な prefix の contract 検査を、tail repair と同じ排他 lock 内で最初の書込みより前に実施する。事前検査と repair を別 lock に分けない。

### F-04 — legacy lane は「parser-only」ではなく production の admitted reader に到達する

**対象 / 判定:** [s2-plan.md:171–189](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t530-contract-hash-binding/s2-plan.md:171)、[artifact_admission.py:95–97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/artifact_admission.py:95) — **real**

**根拠:** pre-policy snapshot の通常 campaign は `"historical-not-reclassified"` となるが、`admitted` は `"legacy-unclassified"` 以外をすべて真にする。

```python
@property
def admitted(self) -> bool:
    return self.admission_status != "legacy-unclassified"
```

```python
# artifact_admission.py:618-635
admission_status=(
    "legacy-unclassified" if _is_legacy_trigger_lock(lock)
    else "historical-not-reclassified"
)
```

その view を [replay.py:120–146](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/replay.py:120) が読み、無束縛 COMMIT を `committed` 集合と `GenomeResult.certified` に射影する。従って「旧 directory を明示すると binding error」というプラン §6 の記述は production admission 経路には成立しない。

**成果物影響:** 既存の無束縛 COMMIT が landscape、既知軸材料、certified 選択入力に残り、「全 certified COMMIT の proof chain 完結」という成果物ラベルが偽になる。

**修正案:** `historical-readable` と `certifying-admitted` を型または状態で分離し、certified selector は後者だけを受け取る。既存 snapshot を引き続き certifying とするなら裁定へ返す。

### F-05 — `admission_policy=None` で post-policy lock を迂回する攻撃は成立しない

**対象 / 判定:** [wal.py:1356–1370](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/wal.py:1356) — **refuted**

**根拠:**

```python
if admission_policy is None and _lock_declares_admission_policy(layout):
    raise AttemptTopologyError(
        "admission-aware campaign replay には current admission_policy が必要")
```

新検査が既存 topology へ AND 条件として加わる限り、post-policy `wal.replay` の受理集合は拡大しない。問題は F-04/F-06 の別 reader と分類であり、集合論上の新規拡大ではない。

**成果物影響:** nit — この特定の迂回では値・参照・受理集合は変わらない。

**修正案:** 「拡大なし」は `post-policy wal.replay` に限定して記述し、全 reader の proof-chain 保証と混同しない。

### F-06 — `read_records` を直接読む production selector が多数残る

**対象 / 判定:** [s2-plan.md:158](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t530-contract-hash-binding/s2-plan.md:158) — **real**

**根拠:** 少なくとも次の選択 reader は、プランの4入口を通らない。

- [screening_driver.py:114–125](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/screening_driver.py:114): `wal.read_records` の BENCH/COMMIT から `baseline_tps` を決定。
- [s1_report.py:339–398](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/s1_report.py:339): `read_records_collected` の COMMIT を `Sample` へ採用。
- [s1_known_axes_freeze.py:221–289](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/s1_known_axes_freeze.py:221): `json.loads` で WAL を独自読取りし、COMMIT fitness を argmax 材料にする。`wal.read_records` caller inventory にすら現れない。
- [s8b_oracle_report.py:1291–1325](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/s8b_oracle_report.py:1291): raw records から oracle window と COMMIT count を構築。

対照的に [layer3_report.py:406–460](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/layer3_report.py:406) は admission 後に lock/WAL hash を再照合しており、この穴には該当しない。

**成果物影響:** H mismatch/missing COMMIT が screening baseline、S1 統計・known-axis winner、S8b oracle の `committed` 判定と bench 値を変え得る。

**修正案:** directory＋lock schema を受ける単一の certified-read API を設け、選択・freeze・report reader を全移行する。caller inventory は関数名検索でなく、`stage=="commit"` を読む独自 JSON reader も検査する。

### F-07 — 正当な resume/report を拒否する未裁定の受理縮小が二つある

**対象 / 判定:** [s2-plan.md:173–176](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t530-contract-hash-binding/s2-plan.md:173)、[replay.py:89–107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/replay.py:89) — **real**

**根拠:**

1. 親 P2 は「無束縛 COMMIT を terminal と数えない」だが、プランは1件の不正 COMMIT で directory 全体を拒否する。ほかの H_A 一致 COMMIT まで resume 不能になる。
2. P3 は旧・新 directory の共存を作る一方、prefix reader は `len(hits) != 1` を無条件拒否する。

```python
if len(hits) != 1:
    raise FileNotFoundError(...)
```

新 ID で同じ slug/tag を再走すれば、旧 WAL と新 WAL の2件が通常状態となり、この拒否は例外事象ではない。

**成果物影響:** 正当な H_A COMMIT の terminal skip、P2 landscape、旧・新 report の参照がまとめて失われる。

**修正案:** directory 全体を taint する粒度を裁定へ返す。report/manifest は prefix でなく、明示 campaign ID または immutable epoch record を保持する。

### F-08 — identity の直接 caller 列挙は合っているが、H の保存・伝播設計がない

**対象 / 判定:** [s2-plan.md:191–223](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t530-contract-hash-binding/s2-plan.md:191) — **real**

**根拠:** 独立検索では §7 の直接 `ident.campaign_id` caller 一覧自体は一致した。しかし以下の consumer は「明示された H」を取得できない。

- [s1_direct_comparison.py:241–244](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/s1_direct_comparison.py:241) の `layout_for(document, role)` は freeze と role しか受け取らない。後日 [s1_report.py:339](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/s1_report.py:339) が同じ関数で ID を再計算する。
- [trial_registry.py:64–65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/trial_registry.py:64) の exact trial schema は `campaign_id` だけで H を持たない。
- [p3_autonomous_workload_trial.py:608–632](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/p3_autonomous_workload_trial.py:608) と [autonomous_trial_completeness.py:1127–1141](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/autonomous_trial_completeness.py:1127) は H 無しで ID を再導出する。
- `s8c_acceptance_receipt.py`、trial registry、S1/S8b freeze は directory 名を文字列として保持する。既存 frozen reference は書換え不要だが、certifying/historical の区別が必要。

**成果物影響:** contract 更新後の report が実走時と別 IDを計算するか、registered launch/completeness が manifest の正当な campaign ID を拒否する。

**修正案:** planning/manifest schema に exact H と確定 campaign ID を版付きで保存し、実走・report・completeness へ同じ値を通す。ambient current-registry lookup はプランどおり禁止する。

### F-09 — D125 supersession は段2で確定してよい裁定ではない

**対象 / 判定:** [s2-plan.md:48–57](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t530-contract-hash-binding/s2-plan.md:48)、[D13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/docs/decisions.md:180)、[D125](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/docs/decisions.md:6081) — **real**

**根拠:** T-530 のユーザー裁定は identity＋COMMIT 束縛と resume 集合変更を認可している。しかし P1 の具体形と P3 は brief 自身が「provisional」と明記する。一方 D125 はユーザー裁定として次を明記する。

> OTHER の campaign_id は 1 bit も変えない

しかも理由は既存最終成果物の resume 互換である。T-530 を lock 隣接 binding、新 certification epoch、Pegasus 限定 split で満たす代案がある以上、広い目的文だけから OTHER invariant の廃止までは一意に導けない。[CLAUDE.md:99–105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/CLAUDE.md:99) も、絶対規律・roadmap・phase docs の変更権限を分けている。

**成果物影響:** D125 が保護した OTHER の最終 campaign ID、loop state、WAL resume、registry/freeze 内の参照が新 ID から到達不能になる。

**修正案:** 「T-530 が D125(2) を supersedeし、OTHERを再測定するか」を明示的に裁定へ返す。承認された場合のみ新 decision として supersession 範囲・旧成果物の格付けを記録する。

### F-10 — guided synthetic COMMIT から certified reader への抜け道は現状ない

**対象 / 判定:** [guided.py:83–137](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/guided.py:83)、[s2-plan.md:59](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t530-contract-hash-binding/s2-plan.md:59) — **refuted**

**根拠:** guided lock は `_NO_BUILD_POLICY` を持つ post-policy lockだが、synthetic `build_start` は attempt ID/receipt を持たない。

```python
wal.log(layout, v, STAGE_BUILD_START, ENV_TAG, {"genome": res.genome})
...
wal.log(layout, v, STAGE_COMMIT, ENV_TAG, {"fitness_tps": res.fitness_tps})
```

この WAL は certified admission に入ると [wal.py:951–954](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/wal.py:951) の `build_attempt_id` 欠落で拒否される。直接読む `_evaluated_canon` は guided 内部の raw 順序用である。

**成果物影響:** nit — 現状、synthetic COMMIT が certified selection/report に入る経路は確認できない。

**修正案:** `require_binding=False` を field 欠落から推論せず、sealed raw-lane marker で指定する。`require_admitted_campaign(guided)` が拒否され続ける負例を追加する。

### F-11 — S8b driver だけ直しても、後日の oracle report が COMMIT binding を検証しない

**対象 / 判定:** [s8b_oracle_driver.py:979–1012](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/s8b_oracle_driver.py:979)、[s8b_oracle_report.py:1275–1407](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/s8b_oracle_report.py:1275) — **real**

**根拠:** プランは private lock と driver の直後読取りだけを変更する。report は `read_records_collected` を直接呼び、campaign-start の execution receipt と manifest H は照合するが、private `campaign.lock` も個々の COMMIT H も読まない。

```python
records, line_issues, truncated_tail = wal.read_records_collected(layout)
...
receipt_matches_contract(start.get("execution_receipt"), ...)
```

COMMIT の新 field だけ H_A→H_B に変えても、stage count と outcome truth tableは変わらない。

**成果物影響:** H_B の COMMIT が H_A manifest の `committed` row と bench_values を成立させ、oracle report の採否・統計へ入る。

**修正案:** report の window 構築前に exact-4 private lock と全 COMMIT H を共有 validator で照合し、driver 書込み後だけでなく後日 report 再生成でも mutation を拒否する。

### F-12 — `env_tag` が一種類という実測から contract identity の安定性は導けない

**対象 / 判定:** [s1-brief.md:31–42](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t530-contract-hash-binding/s1-brief.md:31)、[env_contract.py:90–166](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/env_contract.py:90) — **real**

**根拠:** H は env_tag だけでなく clocks、numactl、attestation、isolation、calibration path/hash の全 field を覆う。

```python
blob = json.dumps(self._canonical_obj(), sort_keys=True, ...)
return hashlib.sha256(blob.encode("utf-8")).hexdigest()
```

実際、同一 `env_tag="pegasus"` に calibration だけ異なる generation 1/2 が既にある [env_contract.py:242–300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/env_contract.py:242)。旧 WAL は H を持たないため、`linux-baremetal` 一種類という観測から過去または将来の H 一意性は検証できない。

**成果物影響:** 同一 env_tag 内の calibration 更新だけでも campaign IDが分裂し、resume・manifest・report 参照が新 rootへ移る。

**修正案:** env_tag 件数ではなく contract generation/churn を影響分析し、その ID 分裂を受容するか裁定へ含める。

### F-13 — 「赤は4件」の10-file subset は全体へ一般化できない

**対象 / 判定:** [s1-brief.md:35–42](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t530-contract-hash-binding/s1-brief.md:35)、[s2-plan.md:247–254](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t530-contract-hash-binding/s2-plan.md:247) — **real**

**根拠:** subset 外に少なくとも次の構造的影響がある。

- [test_p3_s4_loop_trigger_gating.py:562–573](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:562) は `OTHER` の ID 不変を直接 assert。
- `test_s8a_trigger_sweep.py`、`test_autonomous_trial_completeness.py` は複数世代の campaign ID literal を固定。
- `test_s1_direct_comparison.py`、`test_screening_driver.py`、`test_p3_exploration_namespace.py`、`test_s6_sort_sweep.py` は H 無し config から ID/lock を生成。
- `test_artifact_admission.py`、`test_s8b_oracle_driver.py`、`test_s8b_oracle_report.py` は新 lock/COMMIT schema の fixture 更新が必要。
- `test_guided.py` は raw lane と certified lane の分離を維持する必要がある。

**成果物影響:** 未列挙 consumer の ID、registry照合、S1/S8b report acceptance が変わるのに、段2の受入テストでは変化が検出されない。

**修正案:** 実装前に全 test tree の identity/lock/COMMIT fixture inventory を事前登録し、「4件」は subset 内の観測値と明記する。

### F-14 — 親の「32 campaign」は現 checkout で再現しない

**対象 / 判定:** [s1-brief.md:33、79](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t530-contract-hash-binding/s1-brief.md:33) — **real**

**根拠:** 現 HEAD の read-only 集計は次だった。

```text
dirs=30, wals=30, records=3086, commits=459
env_tags=['linux-baremetal'], policy_locks=0, prepolicy_locks=30
```

3086 records は親値と一致する一方、directory 数だけ30対32で食い違う。別 snapshot/root を測ったなら brief に識別情報がない。

**成果物影響:** 旧 campaign 移行・到達不能台帳の母数と参照一覧が2件ずれ、P3 の影響報告が再現不能になる。

**修正案:** 測定 HEAD、root、30/32件の exact basename 一覧または一覧 hash、campaign の数え方を brief に固定する。

## 総括

- **must-fix:** repair より前かつ同一 lock 内で COMMIT binding を検証し、拒否 artifact を変更しない。
- **must-fix:** raw/direct reader、historical admission、S8b report を閉じ、certifying-read 境界を一つにする。
- **must-fix:** H を manifest/registry/report へ永続伝播し、prefix discovery と ambient 再導出を廃止する。
- **must-fix:** subset 外の identity・lock・COMMIT fixture/consumer を受入計画へ追加する。
- **裁定へ返すべき事項:** T-530 が D125 の OTHER-ID 不変を supersedeするか、旧成果物を certifying のまま grandfather するか、directory 全体を taint するか。
- **nit:** 「COMMIT 行だけ複写」は先行 topology に覆われるため発火例から外す。
- **nit:** 32対30の母数差を測定 provenance 付きで訂正する。
