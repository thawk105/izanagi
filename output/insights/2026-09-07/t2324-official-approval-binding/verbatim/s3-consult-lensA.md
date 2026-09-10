## 所見 (real)

**A-1 [real] 承認 env 未設定の標準投入は、承認拒否より先に reservation と build を通る。**

発火手順は、実装後に承認 flag を付けず通常投入すること。

```bash
tools/pegasus/submit_floor.sh
```

plan は未指定を許し、承認 env を export しない (`s2-plan.md:114-145`)。job 側も未設定なら `OFFICIAL_APPROVAL_BOUND=0` のまま継続する (`:151-163`)。その結果、現在の `floor_campaign.sh` の順序では次を通る。

1. submission directory 作成: `submit_floor.sh:291-316`
2. payload staging と claim root provisioning: `:396-548`
3. `qsub`: `:633-652`
4. job scratch / attempt directory 作成: `floor_campaign.sh:267-366`
5. receipt copy・検証: `:552-695`
6. allocation reservation と `reservation.json`: `:774-972`
7. gflags / glog build: `:986-1123`
8. fixed official driver を承認 flag 無しで起動
9. driver CLI が rc=2 で拒否

したがって brief の「未設定も build・claim・副作用より前に拒否」(`s1-brief.md:54-55`) と、plan の「全副作用は gate より後」(`s2-plan.md:60`) は標準投入全体について成立しない。

ただし driver の `run_campaign` には入らないため、`campaign_claim.acquire_claim` (`s8b_floor_campaign.py:7482`) と holdout observation reservation (`:7879`) は消費しない。session attempt や一回性 observation key も消費しない。一方、submission nonce、PBS request、job attempt directory、reservation artifact、依存 build は消費する。

**A-2 [real] 未承認投入の job-result と failure stage が誤分類される。**

A-1 の手順では driver の stdout にだけ `status=refused` と承認不足理由が残る。job 側は以下を生成する予定である。

- `job-result.json`: `driver_rc=2`, `"mode":"official"`
- `failure.json`: stage=`floor_driver`, message=`official floor driver returned nonzero`

本当の停止点は `submit_binding` の承認不足なのに、一般的な driver 障害として記録される。plan の golden 更新 (`s2-plan.md:336-346`) もこの誤分類を固定する向きである。

**A-3 [real] 拒否文言が条件を区別しない。**

具体的な発火状態は次のとおり。

- env 未設定: job は拒否せず、最後に generic `floor_driver` failure
- env が空文字: `submit_binding / must exactly match`
- env が別 nonce: 空文字と同じ `submit_binding / must exactly match`
- Python API の `False`、`None`、`1`: すべて「明示承認がない」

特に plan の shell 条件 (`s2-plan.md:153-158`) は空と不一致を同じ文言にまとめている。これでは輸送欠落、空値輸送、別 nonce 輸送を failure artifact から判別できない。

**A-4 [real] public gate の独立した歯を mutation で証明できない。**

具体的な変異は `run_campaign` の次の呼出しだけを削除すること。

```python
_assert_official_permitted(mode, confirm_official_floor_run)
```

提案中の public 未承認負例は、削除後も次のどちらかで赤になる。

- `_require_supplied_protocol_authority` が先に別理由で拒否する。
- authority が通れば private core の同じ `_assert_official_permitted` が拒否する。

したがって「テストが赤」でも public gate 自身の歯とは帰属できない。逆に private core の呼出しを削る変異も、CLI/public の負例では先段の拒否に隠れる。新設 private test は exact な承認拒否理由または downstream 未到達 sentinel を要求すると plan に書かれておらず、無効な protocol/freeze による後段拒否で通る余地がある。

**A-5 [real] 空文字用の `-z` は独立した mutation tooth を持たない。**

具体的な変異は次から `-z` 節だけを削ること。

```bash
[[ -z "$IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN" \
   || "$IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN" != "$IZANAGI_SUBMISSION_NONCE" ]]
```

submission nonce は先に 32 桁 lowercase hex を要求されるため、空 approval は必ず後半の `!=` でも拒否される。よって `test_floor_job_official_approval_binding_rejects_empty_before_build_and_driver` は変異後も緑になり、`-z` の歯を証明しない。A-3 のように空専用文言へ分ければ、この変異を帰属可能にできる。

**A-6 [real] 親の producer 根拠は結論より弱い。**

現物 3 件はすべて存在し、schema と構造は `between_run_floor.py:179-193,196-256` の出力と一致する。履歴も次を示す。

- rr5 / rr50: commit `4e5e555a`、T-1942
- rr95: commit `e5a0dba4`、T-1477

したがって「別 driver の成果物」という結論には強い補助証拠がある。しかし JSON 自体には producer、source commit、script hash がなく、`run_cmd` も測定 binary しか記録しない。発火手順として JSON の top-level key を確認すると、producer identity が存在しない。ゆえに「3 JSON が実在することだけから `floor_campaign.sh` が producer でない」と一般化するのは不成立である。

P1 の「生きた pilot consumer は見つからない」という結論自体は、production `.py` / `.sh` の検索と `between_run_floor.py` の独立入口により支持される。

また N4 の g1 実在も確認したが、`g1.json` は v2 budget approval であり、official submission nonce 承認そのものではない。発火経路が書ける根拠は予定する submitter→job→driver 経路であって、g1 の存在ではない。

**A-7 [real] brief の実アンカー表には件数と位置のずれがある。**

表は「13 行」ではなく A1〜E1 の 14 行ある。全行の照合結果は次のとおり。

| 行 | 判定 | 実物との照合 |
|---|---|---|
| A1 | 合致 | gate は `465-475`、`:476` は空行 |
| A2 | 合致 | public gate は `7207-7208` |
| A3 | 合致 | private gate は `7304` |
| A4 | 不一致 | `_parser` は `8393-8406`。`:8435` は別 parser の `--confirm-user-freeze` |
| A5 | 部分合致 | block は `8599-8608`。表は return の `8608` を落とす |
| B1 | 不完全 | usage `7-11`、初期値 `31-34`、parser `36-70`、export `621`。`:35-60` では閉じない |
| B2 | 合致 | bootstrap `41-43`、runtime nonce gate `547-551` |
| B3 | 合致 | fixed pilot は `1202` |
| B4 | 合致 | `1329`, `1360`, `1377` |
| C1 | 部分合致 |関数と docstring は `932-933`、挙動は `934-941` |
| C2 | 合致 | `944-957` |
| D1 | 不完全 | 最初の範囲は `7081-7131`。`:7131` の `§8` assertion が表から漏れる |
| D2 | line 無し | 後段 plan では `2196-2309` 等を特定している |
| E1 | line 無し | 現物は README `217-257`、restart runbook `49`, `165-197`, `229-241` |

## 所見 (refuted)

**A-8 [refuted] plan の既定値だけで承認 gate が恒真になる形はない。**

- submitter local state は `0`
- job local state は `0`
- public/private keyword default は `False`
- `argparse action="store_true"` の既定は `False`
- ambient 承認 env は submitter option 無しでは `qsub -v` に追加されない
- `${VAR+x}` は未設定と空文字を区別し、`set -u` 下でも安全
- job の append 箇所は 1 個だけ
- submitterまたは driverへ flag を複数回渡しても bool が True になるだけで、env export と job append は各 1 回のまま

複数 `store_true` が黙って受理されること自体は事実だが、単発 flag と権限が同じであり、恒真化や追加 bypass にはならない。

**A-9 [refuted] 標準 job 内で approval nonce と検証済み receipt nonce がすり替わる経路は、現 plan からは構成できない。**

予定する approval check は raw submission nonce と比較するが、その同じ shell 変数が後で copied receipt の nonce と exact 比較される (`floor_campaign.sh:606-648`)。さらに同じ値が reservation nonce へ写される (`:938-945`)。途中に `IZANAGI_SUBMISSION_NONCE` の再代入はない。receipt 検証が失敗すれば driver へ到達しないため、D1628 型の「別々の raw env を別 authority として使う」穴にはならない。

ただし検査を receipt validation 後へ置く方が、拒否文言を「検証済み receipt nonce との不一致」と正確にできる。

**A-10 [refuted] CLI・API・resume・sub-command・mode 省略記法から、承認値無しで core へ到達する経路はない。**

- public/private API は省略時 False で拒否する。
- CLI official は flag 無しで CLI gate が拒否する。
- `--mod official` のような argparse 省略は同じ `mode="official"` になり、gate を迂回しない。
- mode value は choices により exact `pilot|official` に閉じる。
- `reseal-protocol`、`check-protocol-index`、`resolve-current-protocol`、`freeze-protocol` は first-token exact branch であり campaign を走らせない。
- `freeze-protocol` の `--confirm-user-freeze` は別 parser・別処理で、official run 承認へ流れない。
- job script は `--resume` を渡さず、mode env・argv・`eval` の受け口もない。

driver CLI や API に直接 `--confirm-official-floor-run` / `True` を渡せば nonce 無しで official を起動できるが、これは gate を通過した direct path であり、D926 が明示的に保証外とした経路である。brief の「標準投入経路でだけ」は、D926 の保証範囲についての文言として限定して読む必要がある。

**A-11 [refuted] N1〜N5 の主要な現物認識は成立する。**

- N1: floor submit/job/driver に D461 nonce binding 実装はない。既存同名 pilot flag は oracle N 系だけで、env は固定 literal `1`。
- N2: submitter の nonce export は `submit_floor.sh:621`、job の形式検査は `floor_campaign.sh:41-43,547-551`。
- N3: seam classifier は明示した 18 kwargs だけを受け、承認 bool を渡さなければ集合は不変。
- N4: 実装後の発火経路は構成可能。ただし g1 は run approval authority ではない。
- N5: `s8b_holdout_freeze.py:932-955` は v1 verifier に流れた generation document の拒否であり、official submission approval とは別命題。

**A-12 [refuted] U1/U2 の file ownership 衝突と、絶対規律 2 の明示的な弱化はない。**

U1 は `orchestrator/campaign/`、U2 は shell と `orchestrator/tests/` で、同一 file の編集は不要である。driver signature と U2 tests の意味論 handshake はあるが、plan が記す「U1 適用後に U2」を守れば file conflict ではない。

18 seam 集合、eligibility 式、receipt schema、admission key を緩める変更もなく、`is not True`、未承認負例、flag 1 個性は強い向きである。絶対規律 2 に触れる実害は、検証条件を甘くする変更ではなく、A-1 の「未設定承認を build 後まで流す」順序欠陥である。

## 順序の検算

予定する job の approval check は、現在の `floor_campaign.sh:547-551` 直後に入る。したがって次の順になる。

```text
bootstrap checkpoint / static admission
→ scratch・job attempt 作成
→ policy
→ approval env 検査
→ receipt copy・strict validation
→ source/script identity
→ allocation reservation
→ gflags/glog build
→ driver
```

- mismatch / empty: reservation・build・driver より前に停止するが、checkpoint、scratch、attempt directory はすでに作成済み。
- unset: approval check を通過し、reservation・build 後の driver CLI で停止する。
- exact match: receipt/source/reservation/build を経て driver へ flag 1 個を渡す。

driver 内の予定順序は妥当である。

```text
_validate_mode
→ seam classification
→ eligibility 導出
→ official seam/materializer 拒否
→ approval gate
→ checkpoint env 消費
→ protocol/freeze/reservation
→ campaign claim
→ run directory・build
→ holdout observation reservation
→ runner
```

plan が `cell claim :7879` とだけ記すのは不完全で、durable な `campaign_claim.acquire_claim` が `:7482` にもある。ただし移動後の core gate は両者より前なので、driver 単体の順序は成立する。

現存 test で関連するものは以下だが、新しい順序を現時点で保証するものではない。

- `test_main_official_mode_always_refused`
- `test_run_campaign_core_rejects_official_with_zero_side_effects`。名前に反して public wrapper 呼出し
- `test_core_derives_refreeze_eligibility_at_entry_and_finalizes_without_args`
- `test_floor_driver_consumes_checkpoint_environment_before_core_dispatch`。現在は変更後と逆順を要求
- `test_floor_job_has_no_confirmation_dataflow_and_keeps_admission_order`
- `test_floor_job_invokes_fixed_pilot_cli_without_bypass`

テストは実走していない。

## plan へ入れるべき最小の修正

1. 実投入の `submit_floor.sh` は `--confirm-official-floor-run` 無しなら、submission directory、payload staging、claim-root provisioning、`qsub` より前に rc=2 で拒否する。dry-run の扱いは別にできる。

2. job 側も approval env 未設定を継続させず、`submit_binding` で停止する。unset・empty・mismatch を別 branch・別文言にする。receipt nonce との意味を明確にするなら、copied receipt の strict validation 直後、source identity・reservation・build より前に置く。

3. 未承認 job は `job-result.json` を作らず、`failure.json` の stage=`submit_binding` とすることを test で固定する。reservation、gflags/glog marker、driver marker、campaign claim、holdout claim が無いことも確認する。

4. public gate test は protocol authority と private core を sentinel 化し、public gate 削除変異で「別 gate が赤」ではなく private core 到達が直接赤になる形にする。private core test も exact approval reason と downstream sentinel を要求する。

5. mutation matrix では、空文字 test を同一 mismatch 文言のまま `-z` の歯として数えない。空専用 branch・文言へ分けるか、`-z` 削除を同値変異として対象外にする。

6. brief の実アンカー表を 14 行として直し、少なくとも A4、B1、D1、D2、E1 の位置を plan 本文の実アンカーへ揃える。

## 総括

最大の破断は、固定 official 化と「承認 env 未設定なら flag を渡さない」を組み合わせた結果、通常の無承認投入が receipt・reservation・gflags/glog build を消費してから driver で拒否され、failure stage まで誤る点である。mismatch/empty の early rejection、standard path の nonce→receipt 束縛、CLI/public/private の既定 False は成立している。

repo file は変更しておらず、pytest も実走していない。以上は指定 worktree のコード、成果物、git 履歴を用いた静的検査である。