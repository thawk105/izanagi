結論は **NO-GO**。親実測の 4 赤は最初に踏む旧 late 成果物 assertion と整合するが、期待値更新後に現れる追加回帰が静的に確認できる。私は pytest を実行していない。

## 所見

### C-01 / 期待値更新は現状のままでは許可条件を満たさない

- **1 行要約:** 早期化と両立する `tolerance_pct`、完全な評価 sample、exact reason 集合が失われ、metamorphic test には隠れた次段 failure がある。
- **根拠:** 旧テストは profile 全 sample、`tolerance_pct == 2.0`、成果物不在まで固定する（[test_calibrator_certify.py:740](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:740)）。しかし新 `rejection.json` は reason、reservation、diagnostics、not-evaluated しか持たず（[cli.py:512](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:512)）、diagnostics に tolerance や全 sample はない（[execution_guard.py:214](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/execution_guard.py:214)）。
- **さらに:** clock-only rejection の実 reason は、直接 reason を追加してから aggregate error を再追加するため（[cli.py:630](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:630)、[cli.py:742](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:742)）、次の 2 件になる。

  ```text
  effective-clock-self-comparison-failed
  acquisition-invalid: effective-clock-self-comparison-failed
  ```

  metamorphic test が固定する exact list は 1 件だけである（[test_calibrator_certify.py:929](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:929)）。現在はそれ以前の call-count assertion で停止するため、この回帰が親実測では見えていない。
- **判定:** real
- **成果物影響:** rejection proof から「どの tolerance と全 sample を実際に評価したか」が消え、reason 集合と成果物 SHA も不要に変わる。
- **重要度:** must-fix
- **推奨対応:** rejection に評価済み `samples_mhz` と `tolerance_pct` を明示し、clock-only reason を exact 1 件にする。旧 test は削除せず、artifact 種別だけ更新して全 compatible assertion を移植する。

4 赤が固定していた性質の分解は次のとおり。

| 赤 node | 早期化と両立しない性質 | 早期化と両立し、落としてはならない性質 |
|---|---|---|
| outlier `[0]` | probe 3 回、late `calibration.json`、`calibration.md`、`window-probes.json` の存在、`rejection.json` 不在 | 3 profile の区別、canonical `[True,False,True]`、rc≠0、rejected status/reason、全 48 sample と index 0 の `3079.456`、tolerance 2.0、candidate/publish/registered 不在 |
| outlier `[24]` | 同上 | 同上。ただし帯外位置 24 |
| outlier `[47]` | 同上 | 同上。ただし帯外位置 47 |
| metamorphic | policy=2 側の probe 3 回、late calibration/v2 成果物 | policy=3 の producer→loader→issuer→consumer→self 全 pass、policy=2 の rc≠0・exact reason、direct self/consumer/receipt reject、policy 再束縛後の loader reject（[test_calibrator_certify.py:838](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:838)） |

したがって、call count と artifact 種別の期待値更新自体は正当だが、現在の実装に対する無条件の更新許可は正当ではない。

### C-02 / canonical 抽出は挙動同値ではない

- **1 行要約:** 通常境界の真偽値は保たれるが、policy 不一致でも band math を先行評価し、旧 `all()` の短絡も失ったため、旧 `False` が `OverflowError` に変わる。
- **根拠:** 新 public は shape/policy rejection 前に evaluator 全体を呼ぶ（[execution_guard.py:183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/execution_guard.py:183)）。evaluator は policy mismatch でも `float(tolerance)` と全 observed sample を評価し（[execution_guard.py:224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/execution_guard.py:224)）、`OverflowError` を捕捉しない（[execution_guard.py:276](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/execution_guard.py:276)）。
- **具体的反例:**
  - `tolerance_pct = 10**400`：旧 public は policy mismatch で `False`、新 public は `float(10**400)` で `OverflowError`。
  - expected `[100.0]`、observed `[200.0, 10**400]`、tolerance 2.0：旧 public/private は先頭帯外で `all()` が短絡して `False`、新 evaluator は 2 番目まで走査して `OverflowError`。
- **到達性:** receipt validator は任意精度 `int` を JSON value として許す（[execution_guard.py:296](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/execution_guard.py:296)）。consumer 側 catch にも `OverflowError` がない（[execution_guard.py:159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/execution_guard.py:159)）。したがって不正 receipt が「reject」ではなく例外送出へ変わり得る。
- **判定:** real
- **成果物影響:** execution receipt consumer の fail-closed 性が壊れ、malformed receipt が campaign admission 呼出しを例外終了させ得る。
- **重要度:** must-fix
- **推奨対応:** public の shape/policy precheck を evaluator 前に保持し、legacy short-circuit と全件 diagnostics を分離する。少なくとも consumer 境界では `OverflowError` を reject に変換する。

指定された通常境界の旧→新比較は以下。`T/F` は戻り値、中心値は 100、policy は 2.0。

| 入力 | canonical 旧→新 | private math 旧→新 |
|---|---:|---:|
| 非 Mapping | F→F | F→F |
| 余分な key、他は正常 | F→F | T→T |
| key 不足 | F→F | F→F |
| `samples_mhz` が非 list | F→F | F→F |
| 空列 | F→F | F→F |
| tolerance `bool` / `"2.0"` | F→F | F→F |
| tolerance `2` / `2.0` | T→T | T→T |
| tolerance `0`、完全一致 | F→F | T→T |
| tolerance `100`、`[0,200]` | F→F | T→T |
| tolerance `inf`、有限 sample | F→F | T→T |
| NaN / ±inf sample | F→F | F→F |
| numeric string `"100"` | T→T | T→T |
| bool sample `True`、中心 1 | T→T | T→T |
| observed 長不一致、全て帯内 | T→T | T→T |
| 上下境界ちょうど | T→T | T→T |
| 上下 1 ulp 外側 | F→F | F→F |
| tolerance `10**400` | F→`OverflowError` | `OverflowError`→`OverflowError` |
| 先頭帯外＋後続 `10**400` | F→`OverflowError` | F→`OverflowError` |

基本ベクトルの bit drift は反証できなかったが、全 object/JSON 数値領域での「1 bit も不変」は反証された。

### C-03 / publish temporary の掃除は保証されていない

- **1 行要約:** policy mismatch の通常経路では削除されるが、temp 書込み失敗と unlink 失敗では orphan が残る。
- **根拠:** `_write_exclusive(temporary, artifact)` は cleanup 用 `try` の外（[cli.py:709](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:709)）。同関数は create 後の write/fsync 失敗時に unlink しない（[cli.py:283](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:283)）。後段 cleanup も `OSError` を無記録で捨てる（[cli.py:725](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:725)）。
- **補足:** primary policy mismatch は `CertificationError` として reasons に載る。cleanup failure 自体は載らない。`attempt_tolerance_pct is None` のまま publish に達する通常経路は、代入と schema preflight が先行するため反証できなかった（[cli.py:611](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:611)）。
- **判定:** real
- **成果物影響:** `registered/` に完全または部分的な `.publish-*.tmp` が残り、producer inventory と cleanup 主張が偽になる。
- **重要度:** must-fix
- **推奨対応:** temp write 自体を cleanup 範囲へ入れ、`lexists()` 再確認を行う。削除不能は少なくとも構造化 reason に残す。

### C-04 / M1・M2・M5・M8 の変異帰属は同列に扱えない

- **1 行要約:** M1/M2 は受理集合変異ではなく時点・reason pin、M5/M8 は現在コードに事前登録どおりの単一 mutation anchor がない。
- **根拠:**
  - **M1:** early 削除後も late gate が残る。赤くなるべきなのは publish ではなく `calls == [0,1]` と `calibrate_calls == []`（[test_calibrator_certify.py:594](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:594)）。診断・費用時点 pin である。
  - **M2:** late 削除後も publish policy gate が同じ入力を拒否する（[cli.py:713](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:713)）。赤は accepted-set ではなく reason が self-failure から policy-changed へ変わる assertion（[test_calibrator_certify.py:677](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:677)）。
  - **M5:** 現実装には変異対象の `all` がなく、loop と `band_pass = not violations` である（[execution_guard.py:244](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/execution_guard.py:244)）。
  - **M8:** bytes checker は test helper にしか存在せず（[test_calibrator_certify.py:268](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:268)）、CLI internal profile を読む単一 production replacement anchor がない。test oracle 自体を変異して得た KILL は product gate の保証ではない。
- **判定:** real
- **成果物影響:** mutation ledger が KILLED でも「publish 受理防壁が load-bearing」と誤記録し得る。
- **重要度:** must-fix
- **推奨対応:** M1/M2 を diagnostic/timing sensitivity に分類し、M5/M8 は具体的な一置換 anchor を再登録する。M3/M4/M6/M7/M9には静的な mask を見つけられなかった。

### C-05 / 新規 test に自己参照 oracle と旧保証の未固定がある

- **1 行要約:** `not_evaluated` の期待値が production constant 自身から作られ、reason exactness・status・tolerance・publish 不在も十分固定されていない。
- **根拠:** `assert rejection["not_evaluated"] == list(cli._EARLY_CLOCK_REJECTION_NOT_EVALUATED)` は実装定数を期待値へ差し込むため、定数から `"publish"` や late gate 名を削っても緑になる（[test_calibrator_certify.py:597](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:597)）。reason も membership のみで二重 reason を許す（同:598）。新 early test は rejected status、literal tolerance、candidate/publish 不在を固定していない（[test_calibrator_certify.py:594](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:594)）。
- **境界不足:** 新 evaluator vectors には extra/missing key、tolerance string/int 極値、inf、OverflowError/短絡反例がない（[test_execution_guard.py:558](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_execution_guard.py:558)）。
- **判定:** real
- **成果物影響:** 必須 stage 名や exact reason/evidence が消えても test が通り、期待値更新が防壁弱体化を隠せる。
- **重要度:** must-fix
- **推奨対応:** `not_evaluated` を literal list で比較し、quality object と全禁止成果物を exact assert する。C-02 の反例を unit vector に加える。

## 反証できなかった点

- diagnostics が admission に使われる経路は見つからない。early/late admission は canonical predicate（[cli.py:483](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:483)、[cli.py:683](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:683)）、diagnostics は拒否確定後の serialization のみである。
- `input_valid=False` の値は一意でない。非 Mapping・missing・非 list・空列・変換失敗では `band_pass=False / out_of_band_count=None`。extra key だけなら math は続行され、`band_pass=True / count=0` にもなる（[execution_guard.py:203](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/execution_guard.py:203)）。これを合格と読む production caller は見つからない。
- schema-valid な通常 CLI 経路で、追加 check が `KeyError/TypeError/ValueError` を新たに `receipt-invalid` へ変える反例は見つからない。schema preflight が先行する（[cli.py:618](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:618)）。ただし clock-bad の compound reason 集合・順序は C-01 のとおり変わる。
- bytes self-comparison は実際に fresh bytes を読む（[test_calibrator_certify.py:268](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:268)）。改竄後に同 path を再読している（[test_calibrator_certify.py:733](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:733)）。CLI profile 参照はなく、expected/observed の list alias も predicate が非破壊なので反証できなかった。
- clock-good inputについて、early gate 自体が最終 publish 受理集合を変える反例は見つからない。late gate は残っている。

## 総括

- 最重要 C-01: 期待値更新後に exact reason 回帰が露出し、rejection には literal tolerance と全評価 sample が残らない。
- 最重要 C-02: evaluator 抽出は短絡を失い、旧 `False` を `OverflowError` に変えて receipt consumer の fail-closed 性を破る。
- 最重要 C-03: publish temp の書込みと削除失敗で orphan が残り、cleanup は保証されない。
- 親実測の 4 赤は「最初の failure が予告どおり」までしか証明せず、許可条件充足を証明しない。
- pytest は実行しておらず、緑は主張しない。

**NO-GO**