# 段 4 裁定 — [T-244] P3 producer 結線

wave: dev-wave-t244-p3-producer-wiring / branch: worktree-dev-wave-t244-p3-producer-wiring
起点 main: 55c2e84 / 受入ベースライン: 5900 passed, 19 skipped (rc=0、計算ノード request 889217、448.90s)

## 裁定

**実装しない。** 段 5・6 を飛ばし `4→7→8→9` とする。実装差分が無いため、変異 matrix と
実装後の受入全走は対象外である (上記ベースラインは実装前の環境健全性確認であって、差分の受入ではない)。

判断は 4 つの独立な情報源が一致したことによる — 親の段 1 前提実測 (M10)、段 2 プラン (codex,
read-only, NO-GO)、段 3 レンズ A (正しさ境界, 実装停止)、段 3 レンズ B (実効性・会計, 実装しない)。

## 実装できない構造的理由 (親が実測または確認した順)

1. **prototype は production では起動できない (M10、親が実測)。** runtime store の genesis は
   private test seam `_fixture_store_for_test` (`reflux_origin_ledger.py:2317-2333`) の
   `_locked(store, create=True)` 1 点だけで、公開 API 3 本 (`read_origin` 2777 / `commit_event` 2784 /
   `read_sealed_batch` 2804) はいずれも `create=False` で入り、`_locked` は create が偽なら
   `O_CREAT` を付けない (同 1392-1399)。親が production 経路で
   `read_origin('0'*64)` を呼び `RefluxOriginLedgerError: cannot open authority lock` を確認した
   (runtime dir は作られないまま)。**「結線」には leaf 側へ production bootstrap を足す必要があり、
   それは誰が・いつ・どの authority 世代で初期化するかという未裁定の設計判断である。**
2. **observed cell を再導出できない (M11、段 2 §2)。** cell key は descriptor SHA / axis semantics /
   verifier policy / environment contract の 4 digest (`reflux_origin_ledger.py:434`) だが、
   `axis_semantics_sha256` と `verifier_policy_sha256` は preimage 規則が repo に存在しない。
   manifest 13 field のうち機械導出できるのは `workload` のみで、`authority_series_id` /
   `recipient_projection_schema_sha256` / `budget_policy` / `stock_certification_ref` /
   `structural_zero_evidence_ref` の 5 件は live campaign に source が無い。preimage を定めることは
   origin 識別を恒久的に固定する行為であり、D121 P10 (origin authority のユーザー裁定) の射程に入る。
3. **予算束縛が成立しない (A-1)。** ledger が `iterations_used` / `queries_used` を増やすのは
   `BatchCommitted` 適用時だけ (`reflux_origin_ledger.py:900,913`)。候補生成後に commit する順序では、
   commit 直前に process を殺して新しい run-root で再実行すれば無課金で候補を引き直せる
   (`run_trial` が拒むのは既存 root の resume だけ、同 `p3_autonomous_workload_trial.py:1786`)。
   予算束縛は P3 の目的そのものであり、これが成立しない結線は名乗りだけになる。
4. **commit-reveal が実効化しない (A-3 / A-4)。** authoritative な Layer-3 admission は
   `_run_workload` の戻り後 (`p3_autonomous_workload_trial.py:1278`) であり、seal はそれより先に
   不可逆に確定する。さらに preview の pass/fail が auditor の skip event と実呼出しを分岐させ
   (同 1533/1541)、実呼出しは `raw_<invocation_id>.txt` を即時 fsync する (同 935)。
   drive 後の outcome/metrics は critic へ直接渡る (同 1647)。seal 前に少なくとも 1 bit が漏れる。
5. **受理集合を変えずには候補を複数にできない (A-11 / B-5)。** completeness consumer は
   `attempt == 1` / `retry == false` を要求し (`autonomous_trial_completeness.py:175-195`)、
   境界テスト `test_autonomous_trial_completeness.py:678-693` が固定している。さらに report は
   role ごとに単一 object で、journal と report の role tuple は Counter の全単射検査を受ける
   (同 916-924)。複数候補は report v3 + consumer 改訂 = D96 手続を要し、本 brief の (P4)
   「consumer に触れない」と両立しない。
6. **DW-G04 の発火 gate を満たさない (A-12 / B-3)。** authority registry は空
   (`reflux_origin_authority_v1.json`) で bootstrap も無いため、実装できるのは拒否側だけである。
   「空 authority を正しく拒否した」は fail-closed の証拠であって、機能の条件節
   (候補を受理し、予算を消費し、seal する) の発火証拠ではない。DW-G04 はこの場合を設計メモに限定する。
7. **規模と順序が DW-G01 に反する (B-9)。** 生きた 1 例が無い段階で generic producer API・
   journal・error taxonomy・変異 14 件を一括設計しており、生死実験先行の要求を満たさない。

## 所見の裁定表

区分: `採用` = 本裁定の根拠に採る / `パッケージ` = scope 外 real、ユーザー裁定へ返す /
`訂正` = 親の記述を直す。**実装差分が無いため、全所見の成果物影響は一律に「certified 選択・
材料レポート・試行台帳・proof chain の現在値は不変」である。**

| # | 判定 | 区分 | 要旨 |
|---|---|---|---|
| plan NO-GO | real | 採用 | 現 brief 不変条件下で実行可能な正の結線案は存在しない |
| A-1 | real | 採用 + パッケージ | commit 前 kill で無課金の候補引き直し。pre-query reservation が要る |
| A-2 | real | パッケージ | cell key 4 digest は full manifest を sink に束縛せず、別 spec/CCBench/role bundle を同一 origin にできる |
| A-3 | real | 採用 + パッケージ | Layer-3 admission 前に不可逆 seal。fixture drive 注入で未検証 outcome を確定できる |
| A-4 | real | 採用 + パッケージ | auditor skip / raw artifact / critic 経由で seal 前に結果が漏れる |
| A-5 | real | パッケージ | producer journal が seal plaintext を先に晒し、消えると prepared operation を復元できず origin が永久停止 |
| A-6 | real | パッケージ | state commitment が全 origin head を含むため別 origin の commit で CAS loser になる。runtime は git-common-dir 共有 |
| A-7 | real | パッケージ | `origin_id` / `batch_id` / `operation_id` / `campaign_id` / `trial_id` の namespace と相互参照が未定義 (D75) |
| A-8 | real | パッケージ | 公開 API は無条件に `_production_store()` を使うため、positive 統合テストは恒真 mock か共有 store 接触の二択 |
| A-9 | real | 訂正 (採用) | 親の代案 (P1') を反証。E 段 proposal file schema は `auditor.verdict` と `diff_digest` を必須にする (`p3_s4_loop_trigger_gating.py:649-681`) ため、2 本を事前に用意するには各候補を materialize して auditor にかけるしかない。**(P1') は撤回する** (親が実ファイルで裏取り) |
| A-10 | 部分 real | 訂正 | M7 の「pin 0 件」は repo 側 pin 台帳としては正しいが、ledger 内部は origin genesis / runtime genesis で authority 全 bytes の SHA を pin する (同 1838 / 1963)。**M7 の結論は本 wave (成果物ゼロ) にのみ妥当で、bootstrap wave へ一般化しない。** authority 世代移行はパッケージへ |
| A-11 | real | 採用 | 複数 coder slot は現 completeness の閉じた role 状態機械で表現不能 |
| A-12 | real | 採用 | DW-G04 の発火 gate を拒否側だけでは満たさない |
| A-13 | 部分 real | 訂正 + パッケージ | M3〜M6 の一般化は「**実候補から**合法 batch を作れる production caller が無い」に限定する。ledger 側は任意 commitment tuple を受け、`commit_event` に role receipt も provider invocation 引数も無い (同 445 / 900 / 2784) — **commitment が実 query 由来かを ledger は検査しない**という別の real 所見であり、パッケージへ |
| B-1 | real | 採用 | 拒否専用 CLI の land は D147 却下案 (b) の再演で、wave 名が会計上虚偽になる |
| B-2 | real | 採用 | 成果に要る 11 層のうち本 wave 内は 4・5 の 2 層のみ。前提層 1〜3 が欠けるため実効 0 層 |
| B-3 | real | 採用 | A-12 と同旨 |
| B-4 | real | パッケージ | production 8c driver の `WORKLOADS` は `ycsb-a/b/c` (pilot) のみ。正式系列の holdout は H1=rr80 / H2=rr20 (`trial_registry.py:46-49`) で driver が回せない。**結線先として 8c を選んでも pilot にしか効かない** (親が実ファイルで裏取り。arm 名は `on/off/swapped`、rr80/rr20 は holdout の workload であり、レンズ B の用語は不正確だが実質は正しい) |
| B-5 | real | 採用 | A-11 と同旨 + D96 の同一変更単位要求 |
| B-6 | real | パッケージ | `SealedBatch` は trial / campaign / report への参照を持たない。durable cross-reference を今出さないと P7 は後からその試行を信用できない |
| B-7 | real | 記録のみ | trial registry は `certifying=False` / `arm_binding="declared-only"` (`trial_registry.py:124-129`)。ここへの結線を certified 選択の前進と数えない |
| B-8 | real | 訂正 | M7 / M8 を発火証拠から外す。M8 (startup gate 緑) は cold-start の健全性確認であって production liveness ではない |
| B-9 | real | 採用 | DW-G01 の生死実験先行に反し、1 wave で安全に閉じない |

## 親の記述の訂正 (段 1 brief に対して)

- **(P1') を撤回する** — A-9 が実ファイルで反証し、親が `load_proposal_file`
  (`p3_s4_loop_trigger_gating.py:649-681`) を読んで確認した。
- **M3〜M6 の一般化を狭める** — 「現行 production caller はどれも合法 batch を作れない」は
  「実候補から合法 batch を作れる production caller が無い」に限定する (A-13)。
- **M7 を限定する** — repo 側 pin 台帳 0 件は本 wave (成果物ゼロ) にのみ妥当で、
  bootstrap 以後の authority 世代移行へ一般化しない (A-10)。
- **M8 を発火証拠から外す** — startup gate の緑は production liveness を示さない (B-8)。

## ユーザー裁定へ返す項目 (裁定パッケージ)

P3 producer 結線を再起票するには、少なくとも次が要る。**下 3 件は互いに独立でなく、
1 の帰結が 2・3 の形を決める。**

1. **origin authority の実体化 (D121 P10 の未充足分)** — authority manifest 13 field の preimage 規則
   (とくに `axis_semantics_sha256` / `verifier_policy_sha256`)、`authority_series_id` の発行主体、
   予算値 (Imax / Qmax / Kmax / batch cardinality / query floor の R・E_min)、
   `stock_certification_ref` と `structural_zero_evidence_ref` に何を選ぶか。
   なお現候補 `output/env/linux-baremetal/calibration/s8a_trigger_gating_coverage.json` は
   clocks 2100 を記録する一方、現 registry の linux-baremetal は 1800 (`env_contract.py:169`) で、
   そのままでは採用できない (段 2 §2 の指摘、未裁定)。
2. **production runtime bootstrap と authority 世代移行の主体・契約** — 誰が genesis するか、
   authority を更新したとき既存 runtime をどうするか (現状は blob mismatch で全拒否、
   削除すれば counter を失った新品になる)。公開 authority reader と、
   `OriginSnapshot` に manifest / cell key / budget policy / open batch を載せるかも同じ単位。
3. **結線先と batch 形状** — 8c は pilot workload しか回せない (B-4)。E 段 loop は proposal file が
   auditor verdict を含む (A-9)。**どちらも今のままでは commit-before-evaluation を満たさない。**
   pre-query reservation event (候補生成前に予算を確定する) を FSM へ足すか、
   caller の制御流を batch 先行へ作り替えるかの択一。
4. **P7 との面の切り方 (B-6)** — origin proof の durable cross-reference (origin_id / authority blob
   hash / batch id / seal commitment) を producer 側で今出すか、P7 wave まで出さないか。
   出さないなら P7 は遡って信用できない。
5. **受理集合の変更手続 (B-5)** — 複数候補を通すなら report v3 + completeness + trial registry +
   新 D + 境界テストを同一変更単位にする D96 手続を踏むか、単一候補のまま batch を諦めるか。

## 本 wave が残す成果物

- 設計メモ = `s2-plan.md` (file:line 粒度)。**未裁定部分を含むため設計確定ではない。**
- 敵対レビュー 2 本 = `s3-lensA.md` / `s3-lensB.md`
- 段 1 brief (実測 M1〜M11 を含む) = `brief.md`
- 本裁定と裁定パッケージ
