結論は **NO-GO**。静的検査のみで、pytest は実行していない。現 worktree に本 wave の実装差分はなく、`GIT_TIMEOUT_SECONDS` も 15 秒のままである。

## 1. 計測 probe の代表性

### B-01 — Major: 48 本同時実行から本番全走を代表できない

[probe_git_batch_budget.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/probe_git_batch_budget.py:315) は、同じ `cat-file` コマンドを K 本、barrier で同時開始する。実際の pytest は、48 worker のうち 1 worker が対象処理を行い、残りは異なるテスト・異なる Git 操作・CPU/IO 負荷を持つ。

同種処理の同期競合については probe の方が厳しい可能性があるが、異種処理、他ユーザー負荷、NFS/Lustre メタデータ競合、scheduler 遅延を含む全走の方が厳しい可能性もある。厳しさの向きは確定できない。

probe は cache drop を行わず、K=1/K=16/K=48 の順で同一 workload を測るため、K=48 は既に暖まっている。さらに他ユーザーの外乱や filesystem 競合を測定・記録していない。

影響（未実装）: `RATE` が過小または過大に較正され、producer/pilot の有効な選択が再び `git-timeout` で落ちるか、不要に長い時間予算で受理集合が広がる。

### B-02 — Major: workload と request 数が本番と一致していない

probe の大きな R は履歴中の任意の tracked path を補充して作るだけで、実際の `SOURCE_PATH`、evidence、generation path の組合せを厳密には再現しない。また blob probe は現状 4 OID 程度で、合法な 16 MiB/64 MiB 近傍の fixture を自動生成していない。

現行 HEAD の `validate_condition_freeze_at` は 7002 request ではなく、候補 commit を 1 件追加した invariant test では 2335 commits × 3 paths = **7005 requests** になる。

影響（未実装）: 実際の producer/pilot 入力の I/O 量と異なる値で較正され、特に高 blob サイズ・高 generation 数の試行だけが赤のまま残る。

### B-03 — Major: 測定失敗を成功として記録できる

[probe_git_batch_budget.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/probe_git_batch_budget.py:756) は、timeout、非ゼロ return code、barrier 欠損 worker があっても `payload["completed"] = True` を無条件に設定する。`_summaries` は成功した観測だけで分布を作るため、失敗・打ち切りを除いた biased なデータになり得る。

影響（未実装）: 不完全な測定を完成済みとして `RATE`/`CAP` に採用し、certified 選択の時間 gate と受理集合を誤って変更する。

## 2. RATE の過適合

### B-04 — Major: `max U(c)/R(c)` は一機体・2反復の最大値に過ぎない

段 2 の手続きは測定したセルの最大値を取るだけで、半年後の 5,000 commit、別ノード、別混雑度、cache 状態の上限保証にはならない。現 probe の contended 測定は実施されておらず、得られたのは login node の単一実行 smoke 値だけである。

必要なのは、実際の 7005 request と 50,000 request、混合負荷、複数ノード・複数混雑度、cold-ish/warm cache を分けた反復測定、p99 または上側信頼限界、安全係数、repo 規模増加時の再較正条件である。

影響（未実装）: 将来環境で本番全走の timeout が再発するか、逆に一時的な遅さを許容して長時間の壊れた試行を通す。

## 3. 受理集合の広がり

### B-05 — Major: 時間 gate は実際に広がる

段 2 の式を `r = RATE` とすると、

`B(R) = min(15 + Rr, 15 + 50000r)`

である。smoke 値 `r = 0.136293 / 7002 ≈ 0.000019465 s/request` を機械的に代入すると、7005 request で約 15.136 秒、15,000 request で約 15.292 秒、cap は約 15.973 秒になる。しかしこれは warm/single-node 値であり、全走を代表する実測範囲ではない。

感度例は次の通り。

| 想定 rate | B(7005) | B(15000) | cap |
|---:|---:|---:|---:|
| 0.001 s/request | 22.0 s | 30 s | 65 s |
| 0.01 s/request | 85.1 s | 165 s | 515 s |
| 0.02 s/request | 155.1 s | 315 s | 1015 s |

具体的には、病的な NFS/pack 配置または共有負荷で合法な 50,000-request repository の `cat-file` が 100 秒かかる場合、現行 15 秒では operational failure として落ちるが、`r=0.01` なら cap 515 秒内で通る。

意味論的に壊れた repo が、timeout を伸ばしただけで通るシナリオは、後続の `path-not-blob`、blob byte limit、record schema 等の reject を維持する限り構成できない。したがって R2 は守られるが、「時間上の受理集合」は確実に広がる。

影響（未実装）: 時間超過を false reject として除外する代わりに、resource-wise に本当に運用不能な repository を長時間受理する可能性が残る。

### B-06 — Critical: cap 自体が RATE に無制限に従属している

`CAP = BASE + 50000*RATE` は独立した wall-clock 上限ではない。rate の過大推定がそのまま cap の増大になり、`r=0.02` なら約 1015 秒、`r=0.05` なら約 2515 秒になる。

cap は acceptance 全走の許容時間、PBS walltime、CPU/IO 資源上限など別の根拠で独立に置き、RATE には安全係数または上側信頼限界を適用すべきである。

影響（未実装）: 受理集合が実質的に「数十分かかる壊れた試行」まで含み、suite の安定性・資源可用性を損なう。

## 4. 下流波及と literal pin の全数確認

### B-07 — Major: literal golden はないが、activation digest の下流値は変わる

`CORE_MODULE_PATH` は編集対象自身である [s8c_preregistration.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/campaign/s8c_preregistration.py:41)。そのため本 wave で bytes が変われば `core_module_blob_sha256`、activation report digest が変わる。

下流では次を確認した。

- [trial_registry.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/campaign/trial_registry.py:1244) の launch admission。
- 同ファイル :1572 の lifecycle start row。
- 同ファイル :2412 の acceptance receipt。
- launch admission record 自体の SHA は :1561 で再計算される。
- [`FROZEN_MANIFEST`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/test_frozen_artifacts.py:38) は 23 key のままで、s8c artifact は存在しない。
- 現在の durable freeze は `condition-freeze.v1.g1.json` 1 件のみで、実 SHA の外部 literal pin は見つからない。
- trial registry の出力 artifact も現 tree には存在しない。

したがって g1 の再発行や FROZEN_MANIFEST の更新は不要。ただし既存の activation report/admission/lifecycle/receipt を新しい module bytes のものとして再利用することはできず、新しい launch 時に再生成が必要である。

影響（未実装）: frozen contract bytes は変わらなくても、古い activation digest 参照を持つ launch admission・lifecycle・acceptance receipt が不一致となり、下流受理が失敗する。

## 5. DW-O09 / DW-O10 の閉包

### B-08 — Minor: 親の「pin なし」は結論として保つが、path literal だけでは証明不足

親の literal path 検索 2 件は確認できた。ただし閉包検索では以下も見つかる。

- `FREEZE_DIR`/`FREEZE_BASENAME` の symbolic consumer: [test_s8c_preregistration_invariant.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/test_s8c_preregistration_invariant.py:109)。
- activation digest の key consumer: `trial_registry.py`、`s8c_acceptance_receipt.py`、`autonomous_trial_completeness.py`。
- 実 SHA 値（現 production SHA、g1 raw SHA、g1 内 `protected_sha256`）の repository 外 literal pin はなし。
- `prepare_revision` の永続的な named output は [gN.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/campaign/s8c_preregistration.py:1713) 1 種。ただし Git subprocess の `TemporaryFile()` と親 directory 作成は存在するため、「全 filesystem write が 1 種」という意味ではない。

判定は「byte-level golden pin なし、structural consumer は多数」である。

影響（未実装）: g1 の再発行は不要だが、symbolic consumer や将来の generation path を pin と誤認・見落としし、再発行範囲または digest 更新範囲を誤る。

## 6. 親の実測値・一般化の再検証

### B-09 — Major: provenance の現在 rc=0 は再現できない

`python3 tools/check_ai_provenance.py` は read-only sandbox で実行したところ、監査結果ではなく Pegasus dispatch setup failure の **rc=16** になった。

したがって親の rc=0 は、この環境からは独立確認できない。ただし rc=16 は repository violation の rc=1 ではなく、監査未実施を意味するため、現在の tree が赤だとも断定しない。

影響（未実装）: provenance を実際に監査できていないまま、certified 選択や acceptance 全走を緑として確定できない。

### B-10 — Minor: `prepare_revision` の永続成果物は gN.json 1 種という主張は限定付きで正しい

`prepare_revision` は generation path に `condition-freeze.v1.gN.json` を exclusive-create するだけで、永続的な成果物種は 1 種である。ただし前述の temporary Git file と directory creation を含めれば、関数全体の filesystem effect を「1 種」と一般化するのは不正確である。

影響（未実装）: 永続 artifact の再発行判断は変わらないが、監査対象の write surface を狭く記録して一時ファイル・directory effect を見落とす。

### B-11 — Major: 要求数 7,002 は実際の failing path の値ではない

`HEAD` は 2334 commits。候補 commit helper が HEAD の child を 1 件作るため、実際の invariant test の graph は 2335 commits。現行 generation path は g1、source/evidence/generation の 3 path なので、

`2335 × 3 = 7005`

である。7002 は候補を作らない HEAD 直下の値に過ぎない。

影響（未実装）: 7002 を calibration/golden として使うと実際の invocation を 3 request 過小評価し、境界付近の RATE、予算、timeout 原因判定を誤る。

## 7. 依頼の達成度

### B-12 — Critical: 本 wave の scope だけでは依頼を達成していない

worklog/failures には、s8c の `git-timeout` が複数回継続しており、同時負荷時には ruleops 側の timeout も記録されている。

- `docs/failures.md` F57: s8c candidate timeout、1 failed/7569 passed/20 skipped。
- 同 F57: ruleops `git log` timeout の別 failure。
- F167: PBS walltime SIGKILL の別問題。
- worklog T-697: xdist 下の s8c invariant timeout。
- T-698: external-root/global-state 系の別候補。

本 wave は s8c の Git 予算変更だけで、実装差分もなく、全走も実行していない。したがって producer/pilot の受入が suite 上で安定して緑になったとは言えない。

影響（未実装）: 新しい certified 選択、report、trial ledger の green receipt は確定できず、「直したふり」で終了する。

## 総括

NO-GO。  
probe は本番全走の代表性、cold cache、外乱、合法な大 blob を測れていない。  
`completed=True` の誤記録経路があり、RATE の統計的保証もない。  
時間 gate は広がり、cap は RATE に従属するため、resource-wise な受理集合が拡大する。  
s8c の literal frozen pin はないが、activation digest は launch/lifecycle/receipt へ波及する。  
実際の failing request 数は 7002 ではなく 7005。  
provenance は現環境では rc=16 で監査未実施。  
s8c/ruleops/PBS の残存 failure があり、依頼達成は未確認・未達成。