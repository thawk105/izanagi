# [T-529] 契約世代の活性化権限 — 段 1〜4 の逐語と親実測

wave branch: `worktree-dev-wave-t529-activation-authority`
基準 commit: 616ef5db (段 1〜4 を通じて worktree は clean)

段 4 で **本 wave では実装しないと裁定した**。理由と裁定パッケージは下記「段 4 裁定」に置く。
実装差分がないため変異 matrix と受入全走は対象外である。

## ファイル

| ファイル | 中身 |
|---|---|
| `s1-brief.md` | 親 brief (scope、不変条件、暫定裁定 P1〜P4、pin 閉包候補) |
| `s2-plan.md` | 段 2 codex プラン起草 (`gpt-5.6-sol`、`reasoning=max`、`sandbox=read-only`、rc=0) |
| `s3-lens-a-invariant-check.md` | 段 3 レンズ A — 不変条件と検査の対応づけ (must-fix 7) |
| `s3-lens-b-scope-coverage.md` | 段 3 レンズ B — scope 被覆・整合・実装可能性 (must-fix 8 / should-fix 6 / nit 1) |

段 3 レンズ A は初回投入が上流分類器に拒否され `rc=1` で出力ゼロだった (F102 の再発)。
言い換えて再投入したものが `s3-lens-a-invariant-check.md` である。詳細は failures 台帳。

## 親が独立に裏取りした実測

### 実測 1 — D176 の fuse が塞いでいる窓は実在する (段 1、DW-G01 生死確認)

`_build_registry()` の pegasus へ `generation=2` を**実編集**で追加し、`git checkout --` で復元した
(復元後 `git status --porcelain` 空、`git diff HEAD --stat` 空、HEAD blob `abe103e5` と一致)。

- 現状の fuse は import 時に発火する:
  `EnvContractError: 活性化権限 (activation record / activation receipt) が未実装のため、2 世代目の登録を fail-closed で拒否する`
- fuse を外した反実仮想 (module 複製で `validate_generations` を
  `_validate_generations_without_bootstrap_fuse` へ差し替え) では import が成功し、
  `lookup("pegasus")` が g2 を返した。g2 の `calibration_ref.path` は**実在しないファイル**を
  指していたが current になった。存在検査も bytes 検査も publish 証拠検査もない。

**射程の限定 (段 2・段 3 の指摘を親が受け入れたもの):** 言えるのは
「structural validation を通る g2 が末尾にあり `REGISTRY` が `sequence[-1]` のままなら
`lookup()` は g2 を current とする」までである。実行受理までは示していない。
floor (`s8b_floor_campaign.py:2758-2785`) と oracle (`s8b_oracle_driver.py:781-803`) は
claim より前に calibration bytes を読むため、非実在 path の g2 は両入口では write 前に落ちる。
一方 scoping・T-126・silo は最初の write の後にしか calibration を検査せず、
selector と P3 は同等の calibration admission を持たない。**この非対称性こそが
共通 activation receipt を足す実際の理由である。**

### 実測 2 — g2 を活性化すると既存 frozen proof chain が壊れる (段 4 の裏取り)

```
output/s8b-freeze/floor_protocol.json : env_tag=pegasus
  contract_sha256 = e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01
env_contract.lookup("pegasus").contract_sha256 = 同値 (一致: True)
```

`s8b_floor_contract.validate_protocol` は
`protocol.contract_sha256 != contract_sha256_lookup(env_tag)` を fail-closed で拒否し
(`s8b_floor_contract.py:137-151`)、`s8b_ratified_freeze.py:2876-2882` はその lookup に
**current** `_env_contract.lookup` を渡す。したがって g2 を current にした瞬間、
committed floor protocol は `floor-artifact-invalid` で拒否される。
同型の current 比較は `s8b_ratified_freeze.py:1795,2285` と `s8b_oracle_report.py:1189` にもある。

**帰結: D176 の fuse を外しても U-2 は進まない。** blocker が「fuse」から
「historical / versioned contract resolution が production consumer に配線されていない」へ移る。
D176 自身が「履歴 resolver は production の消費者を持たない data 層の準備である」と限定していた。

### 実測 3 — certified writer に env 契約認可の迂回が現存する (段 4 の裏取り)

`loop._authorize_measurement` は `env_contract is None` で即 `return None` する
(`loop.py:66-70`)。その直後 `loop.py:139-145` が `layout.ensure()` で書き始める。
`s8a_trigger_sweep.py:457` は `env_contract` を渡さずに `run_campaign()` を呼ぶ。
すなわち **activation 以前に、そもそも env 契約の認可を通らずに書き始める certified 経路が
現存する。** これは T-529 が入っても塞がらない独立の欠陥である。

## 段 4 裁定 — 本 wave では実装しない

### 裁定した所見 (すべて real)

親が独立に裏取りしたのは実測 2 (レンズ B 所見 5 / レンズ A 所見 5) と
実測 3 (レンズ A 所見 6 / レンズ B 所見 9) の 2 件。残りは 2 レンズが独立に、
または file:line 付きで示したものを real として採る。refuted はゼロ。

### 実装しない理由

1. **`DW-G04` (条件付き機能の発火 gate) に抵触する。** 活性化機構の発火条件は
   「正規 publish 証拠を持つ 2 世代目が存在すること」である。その artifact path も計測 ID も
   brief に書けない — 2 世代目の取得は [T-564] (pin 済み依存 source の消失で certify job が
   11 秒で停止)、[T-443]/[T-444] (source proof) で塞がれている。`DW-G04` は
   「書けなければ設計メモに留める」と定めている。
2. **実測 2 により、fuse を外しても目的が達成されない。** 活性化権限を入れて fuse を外しても、
   g2 を実際に current にした瞬間に既存 certified floor / freeze / selector / oracle report が
   読めなくなる。historical resolver と versioned predicate dispatch を先に配線しない限り、
   「較正を再取得できる」状態にはならない。
3. **レンズ A 所見 7 が示すとおり、実装可能な部分集合は「永久 fuse」実装と区別できない。**
   プランの positive control は valid な active g2 を一度も成功させない。
   `generation > 1` を無条件拒否する実装でも全テストが通る。
   その状態で land すると、後続の読み手は活性化権限が実在すると誤読する
   — D176 が型分離を却下した理由 (「名ばかりの保証」) と同型の失敗になる。
4. **権威の trust root がユーザー裁定事項である。** レンズ A 所見 1 と レンズ B 所見 2 が
   独立に示したとおり、`AcquisitionReceipt` は自己申告値の schema であって publisher の実行を
   証明しない (`schema_v2.py:345,521,555-567,611-627`、`make_acquisition_receipt.py:36`)。
   「レビュー済み git commit を authority と定義する」か「外部 trust root を持つ署名済み
   evidence を導入する」かは D176 級の設計択一であり、親が独断で選ぶべきものではない。

`DW-S04` に従い、scope 外の real 所見は実装せず裁定パッケージで返す。

### 裁定パッケージ — ユーザーに諮る 6 択一

| # | 択一 | 親の推奨 | 決めないと何が起きるか |
|---|---|---|---|
| 1 | 活性化の trust root を「レビュー済み git commit」と明示して非偽造性の主張を弱めるか、外部 trust root を持つ署名済み publish evidence を導入するか | 前者 (主張を実態へ合わせる)。後者は repo 外の鍵管理を伴い規模が別次元 | 「非偽造」と書かれた名ばかりの保証が台帳へ入る |
| 2 | 入口 receipt を process-local な制御フロー gate に限定して保証を縮めるか、activation serial / state hash を新規 run の versioned identity へ durable に残すか | 前者を今 wave の範囲、後者を別 wave。ただし前者だけでは「全入口が同じ状態」を成果物から監査できない | 6 入口の同一状態性が事後に検証できない |
| 3 | fuse 解除の前に historical resolver + versioned predicate dispatch を consumer へ配線するか、g2 後の旧 artifact 拒否を明示的な受理縮小として承認するか | 前者。後者は certified 成果物の参照鎖を切る | 較正を再取得した瞬間に既存 certified evidence が読めなくなる |
| 4 | `linux-baremetal` g1 を exact contract hash で grandfather するか、legacy bytes 用の detached acquisition evidence を新設するか | 前者 (現 registry に対して必要十分な狭さ) | 初期 activation record 自体が import 時に拒否される |
| 5 | `loop.run_campaign` を含む全 certified writer を活性化対象にするか、legacy producer を機械的に非 production 化するか | 実測 3 の迂回は T-529 と独立に塞ぐべきなので別タスクへ切る | env 契約認可を通らない certified 成果物が残り続ける |
| 6 | silo は ability probe writers を対象と呼ぶか、真の promotion consumer が同定されるまで「silo 昇格入口は未実装」とするか | 後者。ability probe を結線して「昇格入口を守った」と報告してはならない | 入口被覆率の過大報告になる |

### 採用した設計上の結論 (実装しないが記録する)

- 命名は `activation_serial` / `activation_state_sha256` / `previous_activation_state_sha256` を採る。
  `migration_epoch` は repo 内で `epoch` が unix 時刻の一義 (`submit_epoch` /
  `deadline_epoch` / `completed_epoch` / `scheduler_started_epoch`) を壊し、
  `migration_*` は T080 の `migration_id` と近い。`bundle_hash` は `role_bundle_sha256` /
  `raw_bundle` と別義で衝突する (D75)。両レンズが親の暫定命名 (P2) を否定し、この案を支持した。
- 入口の同定は brief の暫定案から次のとおり訂正される。
  - floor の正式入口は `s8b_floor_campaign.py` (`pegasus_floor_scoping.py` は自ら
    「certified consumer へ配線しない調査値」と宣言している)
  - oracle は driver だけでなく `s8b_oracle_report.py` の独立 observations writer も入口
  - selector の実 producer は `s8b_prediction_runner.seal()` であって `s8b_selector_freeze.main()` ではない
  - 適格性の最初の書込みは `t126_driver.py:899` の `QualificationRoot.issue()`
  - silo は昇格入口として実在しない
  - 7 種目以降として `p3_s4_loop.py` / `p3_s4_loop_sort.py` / `p3_kickoff.py` /
    `loop.py` の `env_contract=None` 経路、`t419_probe_causality.pbs` の Python 起動前 write、
    floor protocol authoring utility がある
- brief が挙げた pin 8 箇所は**すべて byte 固定でなく実行時再計算**である
  (`qualification/contract.py:62` は path 集合で digest は run 時に working bytes と
  `HEAD:<path>` blob から再計算、`test_env_contract.py:83,559,1195` は AST 検査、
  `t419_probe_causality.py:3495,3533` は dirty scope と記録)。
  一方でレンズ B は閉包の漏れを指摘した — `test_s8b_protocol_builder.py:47-63,91-105`、
  `test_s8b_floor_campaign.py:3240-3252`、`test_silo_ladder_rung1_evidence.py:1252-1262`、
  `s8c_preregistration_evidence_contract.v1.json:431-468`、
  `env_attestation.py:28-30,1119-1133` (SHA 定数 pin)、`qualification/contract.py:140-149`。
- evidence 検査を設計するときは、既存 loader が行う
  `calibration.env_tag == contract.env_tag` / clock / effective-clock policy の照合
  (`env_attestation.py:1091-1111`) を必ず含める。プランの 7 条件はこれを欠いていた。
