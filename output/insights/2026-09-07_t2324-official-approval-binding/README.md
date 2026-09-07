# [T-2324] 床値 official の §8 承認束縛 — 一次資料

wave branch = `worktree-dev-wave-t2324-official-approval-binding`
着手時 main = `f486ff13c` / 記録時に取り込んだ main = `f901221b7`

## 1. 何をしたか

床値 campaign の official 走行を塞いでいた「§8 (承認束縛方式) 未裁定」を理由とする無条件拒否を、
D926 が裁定した承認束縛へ差し替えた。方式は既裁定であり、本 wave は実装だけを行った。

経路は次のとおりである。

```
tools/pegasus/submit_floor.sh --confirm-official-floor-run
  → qsub -v IZANAGI_SUBMISSION_NONCE=<n>,IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN=<n>
  → floor_campaign.sh が <n> == <n> を確認し driver argv 末尾へ承認 flag を 1 個
  → s8b_floor_campaign.py --mode official --protocol <p> --confirm-official-floor-run
  → CLI gate 通過 → run_campaign(confirm_official_floor_run=True) → core gate 通過
```

**実装の着地は測定認可 (D1641) を兼ねない。** 本 wave は走行を認可せず、起動可能にするだけである。
実投入は行っていない。

## 2. 段の成果物

| 段 | 成果物 |
|---|---|
| 1 | `s1-brief.md` (親 brief。§1 の一部は段 4 で自己訂正した) |
| 2 | `verbatim/s2-plan.md` (codex plan、file:line 粒度) |
| 3 | `verbatim/s3-consult-lensA.md` (承認 gate の bypass と恒真化)、`verbatim/s3-consult-lensB.md` (既裁定の禁止事項と pin 閉包) |
| 4 | `s4-adjudication.md` (real 11 件採用 / refuted 9 件 / scope 外 3 件 / 変異事前登録 11 件) |
| 5 | 実装 (Codex author 子。commit `b985d79a6`) |
| 6 | `verbatim/s6-review-A.md` (must-fix 0)、`verbatim/s6-review-B.md` (must-fix 4 → 2 件採用・2 件 nit へ降格) |
| 6 | `mutation-spec-probe.json` / `mutation-ledger-probe.json` / `mutation-spec-final.json` / `mutation-ledger-final.json` |

## 3. 段 3 が反証した親の記述 (段 4 §1 で訂正済み)

1. 不変条件「副作用より前」は誤り。`take_checkpoint_environment` が承認 gate より前に
   `os.environ.pop` を行う。正しくは「build 呼出し・driver 子 process 起動・cell claim 予約・
   一回性 key の消費・filesystem 書き込みより前」。
2. 成果物影響の書き方。「起動と API の受理集合はこの commit で変わる。測定値と freeze / certified の
   選択結果は実投入まで変わらない。nonce 束縛の保証が及ぶのは標準投入経路だけ」。
3. DW-G04 の witness から `output/s8b-freeze-budget-approvals/g1.json` を外した。g1 は投入器・
   job・driver のどこからも読まれず、official result 後の v2 candidate 生成で初めて読まれる。
4. 変更面表は 13 行ではなく 14 行 (実際には 16 ID)。位置を 5 箇所訂正した。
5. (P1) の根拠。`between_run_noise_*.json` 3 件の実在だけでは producer を同定できない
   (JSON に producer identity が無い)。結論を支えるのは
   `orchestrator/campaign/between_run_floor.py` が独立の入口として存在することと、
   production の `.sh` / `.py` に `submit_floor.sh` を起動する consumer が 0 件であること。

## 4. 親が段 3 の合意を反証した 1 件 — 承認 gate の位置は動かさない

段 2 plan が「承認 gate を `take_checkpoint_environment` より前へ動かす」と提案し、段 3 の 2 レンズが
どちらもそれを妥当と認めた。**親は必要性を反証して却下した。**

- 前倒しが解決するのは「未承認 official の直接 API 呼出しで `os.environ` が pop されること」だけで、
  artifact も一回性 key も filesystem も動かない。拒否後は process が終わる。
- この pop は**計測される子 process に診断用 env を継承させない**ための無条件の隔離である。
  `orchestrator/tests/test_pegasus_floor_tools.py` の
  `test_floor_driver_consumes_checkpoint_environment_before_core_dispatch` がその保証を
  `_validate_mode` を番人にした 1 本の無条件テストで押さえている。gate を前倒しすると、
  このテストを承認状態で条件分岐する 2 本に割る必要があり、無条件の保証が条件付きへ弱まる。
- D926 が要求するのは「承認検証を claim 予約より後へ置かないこと」であり、現在位置は
  `campaign_claim.acquire_claim` と holdout observation reservation の両方より前で、
  既存テストが `not out_root.exists()` (書き込み 0 回) を既に固定している。
- **3 者はいずれも親 brief の誤った不変条件を基準に妥当性を判定していた。**
  直すべきは不変条件の書き方であって gate の位置ではない。

## 5. A-1 / B-2 の分割裁定

段 3 の 2 レンズが逆向きの主張を出した。alpha (A-1) は「未設定承認も早期拒否へ強めろ」、
beta (B-2) は「brief を D926 の形へ弱めろ」。**層で分けて両方を成立させた。**

- **投入器は実投入で承認引数を必須にする。** 引数が無い非 dry-run は、submission staging root の
  検査・`SUBMISSION_DIR` の作成・payload staging・claim root 作成・`qsub` のいずれよりも前に
  rc=2 で止まる。実測した行順は
  `argv 検証 (76) → override 検証 (78-82) → 承認 guard (84-87) → staging root 検査 (295-301) →
  SUBMISSION_DIR mkdir (324) → payload staging (524) → claim root (559) → qsub (665)`。
- **job script は D926 の形を literal に保つ。** 未設定 → flag を渡さない / 設定済みで空文字 →
  専用文言で fail-closed / 不一致 → 別の専用文言で fail-closed / 一致 → 1 個 append。
  ここで未設定も止めると標準経路では append が実質無条件になり、D926 が却下した
  「固定 official wrapper が承認を無条件 append する」と静的検査で見分けが付かなくなる。
- raw `qsub` で承認 env を省いた非標準経路だけは build を消費してから driver で止まる。
  これは D461 / D926 が保証範囲外と明言した経路なので機構を足さない。

## 6. 変異 matrix

`mutation-spec-final.json` (sha256 `9202a6c5282555ad2de9f0871265c00b5b7a49acc00c06c710be8aa558bc1598`) を
`tools/mutation_harness.py --runner-mode dispatch --detached` で走らせた。

- **本走: 11/11 KILLED、SURVIVED 0、MISMATCH 0、TIMEOUT 0、PARSE_ERROR 0。baseline PASSED (rc=0)。**
- probe 走 (全件 SURVIVED 期待) は観測 node を集めるための 1 巡で、11 件すべてが MISMATCH =
  実際には赤を出したことを記録している。probe の観測 node をそのまま本走の期待へ焼き込んだ。
- runner argv は
  `python3 tools/run_tests.py --force-dispatch test_pegasus_floor_tools.py test_s8b_floor_campaign.py test_s8b_holdout_freeze.py -q -rf`。
- 走行時の repo HEAD は `805b36f30`。取り込んだ main (`f901221b7`) は `tools/mutation_harness.py` に
  D612 の dispatch timeout 上書きを足しているが、KILLED の判定意味論は変えていないので台帳は有効。

### 挙動 kill と診断感度 pin の分離 (段 6 レビュー B の RB-1)

**11 件のうち挙動 kill は 8 件で、3 件は診断感度 pin である。** 受理集合か fail-closed 挙動が
期待方向へ変わったときだけ kill と数える契約 (DW-M03 / DW-M08) に従って分離した。

| ID | 変異 | 区分 | 理由 |
|---|---|---|---|
| M-1 | 承認 append を無条件化 | 挙動 kill | 未承認 job の受理集合が開く |
| M-2 | 承認 append を 2 回 | **診断感度 pin** | `store_true` が重複を受理し、受理集合も fail-closed 挙動も変わらない |
| M-3 | public gate の呼出しを削除 | 挙動 kill | 先段 authority を通る入力で private core 到達自体を赤にする |
| M-4 | private core gate の呼出しを削除 | 挙動 kill (冗長 gate あり) | 専用負例に加え、呼出し順を逐語で固定するテストも赤になる |
| M-5 | `is not True` を `not` へ緩める | 挙動 kill | truthy な `1` が通る |
| M-6 | 空文字分岐を削除 | **診断感度 pin** | 承認値は 32 桁 hex の nonce と一致しないので不一致分岐が同じ入力を拒否する。変わるのは文言だけ |
| M-7 | nonce 不一致比較を削除 | 挙動 kill | 削除後は downstream に到達する |
| M-8 | 固定 mode を pilot へ戻す | 挙動 kill (冗長 gate あり) | 専用テストに加え実 argv 完全一致 2 本も赤になる |
| M-9 | 投入器の実投入必須 guard を削除 | 挙動 kill | 承認なし実投入が staging と qsub へ進む |
| M-10 | CLI 拒否を削除 | 挙動 kill | protocol loader 未呼出し sentinel が赤になる |
| M-11 | 世代 document 拒否の呼出しを削除 | **診断感度 pin** | 直後の exact top-level schema 拒否に過剰決定される |

M-6 は段 3 の A-5 (「`-z` に独立した歯が無い」) へ対応して文言を分離した結果である。
**文言分離は診断を識別可能にしたが、受理集合の歯にはならない** — 正直にそう記録する。

## 7. 段 6 レビューの裁定

- レビュー A (裁定との一致・bypass・恒真化): must-fix 0 件・nit 0 件。裁定 16 ID すべて実装済み、
  scope 外の混入なし、D926 が不変とした 4 面も不変、既存の拒否・assert の弱体化なし。
  差分 SHA-256 が author patch と一致し、実装面に親が触った痕跡なし。
- レビュー B (変異の単一理由性・テスト弱体化・pin 閉包): must-fix 4 件のうち 2 件を採用。
  - RB-1 (変異の分類) → 採用。§6 の分離表。
  - RB-4 (live 運用文書が旧 pilot interface) → 採用。§8。
  - RB-2 (受入台帳の陳腐化) → **nit へ降格。** 網羅を強制する検査は無く、
    `test_acceptance_schedule_order.py` + `test_plain_runner_coverage.py` は 82 passed。
    正しい更新方法は実受入の記録から再生成することだが、それは受入の後になり
    「検査済み tip 以降は編集不可」の land 契約と衝突する。次の一手として起票した。
  - RB-3 (新設・改名テストの自走 harness) → **nit へ降格。** 該当 2 file は
    `orchestrator/tests/README.md` の pytest 専用許可リストに載っており meta-test は緑。
    追加すると許可リスト側と競合する。証拠は親の実走で足りる。
  - RB-5 (改名した ambient-env テストが部分一致へ) → nit。完全一致は同 file の別テストが維持。

## 8. 更新した運用文書

- `tools/pegasus/README.md` §5 — 投入 command、承認の運び方、D926 の保証範囲と非範囲、
  固定 official argv、失敗文言。
- `docs/phase3-8b-restart-runbook.md` — §2 点検表、§3 順序、W-1 の 3 点、W-2 の見出しと手順、
  §4 決着文。pilot 走行の完走実績は dated history として残した。
- `docs/pegasus-runbook.md` §8 — sanctioned な投入は承認引数付き `submit_floor.sh` だけであり、
  raw `qsub` で承認 env を渡す経路は nonce 束縛の保証外。
- `docs/phase3.md` — 固定 pilot の現況記述を固定 official へ。
- `docs/paper-story/2026-09-05.md` は dated 資料なので書き換えない。

## 9. 親が閉じられなかった課題 (起票する)

1. **official result の repo 相対読取りと走行直後の repo 外退避の順序。**
   `s8b_holdout_freeze._validate_floor_inputs` は `_load_repo_object(root, floor_result_path, …)` で
   repo 相対に解決し、`parse_official_run_path` が official run path を要求する。一方 holdout
   clean-scan の除外は `output/s8b-freeze/` だけなので、result を repo に置いたまま次の official job を
   起動すると起動証明が止まる。**clean-scan は緩めない。** 運用の順序は candidate 生成を実際に
   走らせる wave で決める。
2. **受入台帳の nodeid 再生成。** 旧 nodeid 7 件が残り、新 nodeid 17 件が欠落している。
   実受入の記録から正規の updater で再生成する。
3. **`docs/phase3-8b-restart-runbook.md` W-3 の「candidate producer 不在」は既に偽である。**
   `s8b_holdout_freeze` に `generate-v2-candidate` が実在する。本 wave の変更が原因ではないので
   scope 外とした。
4. **raw `qsub` で承認 env を省いた非標準経路の failure stage 精密化。**
   D926 の保証範囲外なので機構を足さなかった。

## 10. 検査と実測

- 焦点走 (単独走): `test_s8b_floor_campaign.py` 486 passed / 3 skipped、
  `test_pegasus_floor_tools.py` 143 passed、`test_ccbench_spawn_sites.py` 44 passed、
  `test_s8b_holdout_freeze.py` 136 passed / 2 skipped、`test_s8b_ratified_freeze.py` 61 passed。
- consumer 15 file: 1364 passed / 4 skipped。
- 受入台帳・自走 harness の meta-test: 82 passed。
- 変異本走: 11/11 KILLED。
- AI provenance 全史監査: rc=0 (8396 件、新規違反なし)。
- `tools/check_docs.py`: rc=0 (違反なし)。`tools/spool_fold.py --dry-run`: rc=0 (status planned)。
- **受入全走は未実施の時点でこの一次資料を凍結している。** land 対象 tip への最終受入は記録 commit を
  済ませてから投入する契約なので (`DW-O16` 節末)、受入結果をこの節へ追記すると記録 commit が
  tested tip から漏れて land が rc=23 になる。**したがって受入の実測値はここには入らない** —
  session の報告と land の受領証が所在である。次 wave が引くときはそちらを見る。
