### production seal を verifier なしで鋳造できる

`深刻度`: must-fix

`根拠`: [`VerifiedB4AdmissionRecord`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/p3_b4_admission_record.py:115) は任意値で直接構築できる。ところが [`_create_b4_production_context`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/p3_b4_launcher.py:248) は exact type だけを見て production seal を発行し、`verify_b4_admission_record` 由来であることを検査しない。さらに `_bind_b4_campaign` は任意の非空 campaign id を受ける (`p3_b4_launcher.py:268-291`)、sidecar 書込と context activation も module 属性として直接呼べる (`:312-357`)。実際、テスト自身が架空の `VerifiedB4AdmissionRecord` を作り、この経路で production context を得ている (`test_p3_b4_launcher.py:25-35,61-67`)。G4 は sidecar とその context の一致しか見ず、受理記録を再検証しない (`p3_b4_launcher.py:360-404`)。

`到達経路`: `VerifiedB4AdmissionRecord(...)` → `_create_b4_production_context` → 実 `default_cfg(..., b4_reflux_ablation=True)` → `_bind_b4_campaign` → `_write_b4_launch_sidecar` → `_activate_b4_launch_context` → 公開 `p3_s4_loop.main(..., _b4_launch_context=context)` (`p3_s4_loop.py:1562,1655-1660,1707-1717`) → bootstrap `drive_iteration` → `run_campaign` → `pipeline.evaluate` → `wal.append`。この経路は launcher と `verify_b4_admission_record` を一度も通らず、mock や属性書換えも不要である。

`成果物影響`: 架空の受理記録 hash を持つ sidecar の下で bootstrap の certified COMMIT、選択結果、loop digest を生成できる。

`修正案`: production seal の issuer を closure 内へ閉じ、issuer 自身が admission path を実検証する形にする。生の `_create_b4_production_context(VerifiedB4AdmissionRecord, ...)` は module 属性として残さない。テスト用 context は test seal のままとし、production context が必要なテストは実の committed admission fixture を通す。既存 process seal の issuer を閉じるだけでよく、新しい不可逆 token は不要。

### M08〜M10 の副作用 oracle は恒真

`深刻度`: must-fix

`根拠`: 親裁定は G3 を外すと `layout.ensure()` と state 前進が起きることを要求している ([s4-ruling.md:142](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1840-b4-launcher/materials/s4-ruling.md:142>))。しかし M08/M09 は cfg 由来でない tmp layout を渡す (`test_p3_s4_loop.py:2588-2606`, `test_p3_s4_loop_sort.py:975-990`)。G3 を外しても、共有関門が先に authoritative layout 不一致を出す (`p3_s4_loop.py:1241-1243`) ため、root と state file は作られない。M10 は `T.exploration_campaign_layout` だけを差し替える (`test_p3_s4_loop_trigger_gating.py:2840`) が、共有関門が参照するのは未差替えの `L.exploration_campaign_layout` なので同じである。現在のテストは G3 除去時に例外型が変わるため赤にはなるが、実装側と期待例外を一緒に差し替えると副作用 assertion はすべて通る。

M01〜M18 の静的監査結果は次のとおり。

| M | 直接名指しする実体 | mock / stub | 登録関門を外した場合 |
|---|---|---|---|
| M01 | `p3_s4_loop.default_cfg` | 無し | `pytest.raises` が不成立。非恒真 |
| M02 | `p3_s4_loop_sort.default_cfg` | 無し | 同上 |
| M03 | `p3_s4_loop_trigger_gating.default_cfg` | 無し | 同上 |
| M04 | `p3_s4_loop.run_one_iteration` | 無し | root 作成または別処理へ進み赤 |
| M05 | `p3_s4_loop_sort.run_one_iteration` | 無し | 同上 |
| M06 | `p3_s4_loop_trigger_gating._run_one_iteration_resolved` | 無し | `layout.ensure()` 側へ進み赤 |
| M07 | `p3_s4_loop_trigger_gating.run_one_iteration` | `_current_site` を raising Mock | G2 除去で spy 到達、赤 |
| M08 | `p3_s4_loop.drive_iteration` | 無し | 例外差で赤だが、root/state 不在は不変 |
| M09 | `p3_s4_loop_sort.drive_iteration` | 無し | 同上 |
| M10 | `p3_s4_loop_trigger_gating.drive_iteration` | `T.exploration_campaign_layout` を lambda | 同上。共有 `L` 側は未差替え |
| M11 | `wal.append` → `verify_b4_launch_context` | 無し | commit receipt error と空 WAL 作成へ変わり赤 |
| M12 | 同上 | 無し | 後段 context 比較の別 message になり赤 |
| M13 | 同上 | 無し | receipt 検査側へ進み赤 |
| M14 | `create_b4_closed_critic_pair` | 無し。missing admission は入力 sentinel | admission error へ変わり赤。artifact 不在自体は不変 |
| M15 | 同上 | 無し | cfg-kind 検査の別 message になり赤 |
| M16 | 同上 | 無し。test seal の合成入力 | generic production error へ変わり赤 |
| M17 | `p3_b4_closed_critic.main` | `pair_factory` に Mock | exact hard-fail が消えれば赤。factory 未到達だけなら parser でも恒真 |
| M18 | `DRIVER_REGISTRY` と実 `L.main/S.main/T.main` | 無し | 別 callable なら各 `is` が偽。空回り無し |

M18 自体の所見は無し。実装表も実 object を保持し (`p3_b4_launcher.py:407-411`)、bootstrap/continuation はその表を呼ぶ (`:501,:553`)。ただし正例は `REPOSITORY_ROOT`、`ROLE_FILE`、`shutil.which`、controller 初期化、各 layout resolver、snapshot/admission/digest、`ensure_resumable_attempts`、pin/single-tenant、`L.run_one_iteration` を差し替えている (`test_p3_b4_closed_critic.py:2442-2467`)。従って正例は記載どおり routing 証拠であり、科学処理本体の実体証明ではない。

`成果物影響`: G3 回帰時、拒否される B-4 呼出しが campaign root/campaign.lock を残して再開時の参照状態を変え得るが、現テストの副作用 oracle はそれを検出しない。

`修正案`: M08/M09 は共有 `L.exploration_campaign_layout` を対象 tmp layout に差し替える。M10 は `T` と `L` の両方を同じ layout に差し替える。さらに実 `run_one_iteration` を呼ぶ wrapper spy で、G3 mutant 時に渡された state の `iteration == 1` を観測する。永続 state file は G2 例外より後でしか保存されないため、その不在を state 前進の証拠にしない。

### 既存回帰テストは実際に赤

`深刻度`: must-fix

`根拠`: 親の実測は 554 passed / 1 failed ([s5-focus-result.md:15](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1840-b4-launcher/materials/s5-focus-result.md:15>))。テストは `B4LauncherAuthorizationError("marker creation")` を期待する (`test_p3_s4_loop.py:3099-3106`) が、実 `main` は `default_cfg` より前に `B4ProtocolError("fixture run_one_iteration route")` を送出する (`p3_s4_loop.py:1609-1616`)。

`成果物影響`: certified 選択、レポート、台帳の値は変わらないが、焦点検査が常時 1 件赤となり回帰判定を失敗させる。

`修正案`: 既存の `pytest.raises(L.B4ProtocolError, match="fixture run_one_iteration")` を復元する。実装順を G1 到達へ変える必要はない。

### COMMIT 後の lock 書換えは引き続き B-4 へ再分類できる

`深刻度`: backlog

`根拠`: G4 は COMMIT 直前の lock だけを分類する (`wal.py:411-436`)。一方、consumer は現在の lock を decode して generic topology/source を検査するが (`artifact_admission.py:987-1001,1042-1112`)、B-4 sidecar/context を再検証しない。base/sort では directory id と inner identity の照合もなく、この照合は trigger proposal に限定される (`artifact_admission.py:726-752`)。sidecar 自体も意図的に `os.replace` で上書き可能である (`p3_b4_launcher.py:312-339`)。

`到達経路`: 公開 `pipeline.evaluate` (`pipeline.py:705`) を有効な unmarked lock で完走 → `res.certified=True` (`:1453`) → `wal.log`/`wal.append` で COMMIT (`:1483-1489` または `:1551-1557`) → 後から同じ authority を保った marked v2 lock へ置換 → `require_admitted_campaign`。COMMIT 時には marker が無いため G4 未到達で、後段にも sidecar 検査がない。

`成果物影響`: lock marker を B-4 選別に使う将来の report/ledger は、launcher 前の COMMIT を B-4 標本として受理できる。

`修正案`: 親裁定どおり scope 外に残すなら、§7.2 は「COMMIT 時に exact marker が存在した経路だけ閉じた」と限定する。閉じる場合は G4 が検証した `launch_context_sha256` と admission hash を各 COMMIT payload/receiptへ永続化し、artifact admission と B-4 consumer で再検証する。上書き可能な単一 sidecar だけでは過去 COMMITを帰属できない。

### 発火しない入力と marker 定数の複製

`深刻度`: nit

`根拠`: G1 の `require_b4_any_context` は production だけでなく test seal も許可する (`p3_b4_launcher.py:167-194,232-245`) ため、裁定の「G1 は production context 必須」という表現より実装範囲が狭い。G2/G3 の `require_campaign_binding=True` は campaign id が非 `None` かだけを見る (`:197-229`)。arm、現在 cfg の campaign id、lock 上の driver kind との一致は見ない。さらに WAL は marker key/value を正本から import せず文字列で複製し、lock 欠落、読取不能、codec error をすべて `False` に倒す (`wal.py:411-424`)。正本は `p3_s4_loop.py:116-117` である。`loop.run_campaign` が G4 例外を捕捉する箇所は ABORT に倒れるため、そこに certified 化の所見は無し。

`成果物影響`: 現在の sanctioned launcher では値は一致するが、将来の marker drift または誤 binding 時に B-4 gate が黙って外れ、sidecar の arm/driver 参照が lock と食い違い得る。

`修正案`: marker 定数を依存の低い専用 module に移して drivers と WAL から共有する。lock が存在するのに読取/codec が失敗した場合は COMMIT を拒否する。production boundary には `expected_campaign_id` と `expected_arm` を渡して exact 一致を中央 helper で検査する。test seal による G1 通過が意図的なら、§5 は「unsealed marker 作成を閉じた」と書く。

## 総括

must-fix は production seal の無検証鋳造、M08〜M10 の恒真な副作用 oracle、既存回帰テストの赤の 3 件である。  
M18 は実 object identity を直接検査しており、stub 空回りの所見は無し。  
valid な exact-marker lock が COMMIT 時点から存在する経路では、formal WAL COMMIT は `wal.append` に合流している。  
ただし launcher の排他性は raw seal issuer により破れ、後付け lock 再分類も裁定どおり未閉鎖である。  
単一 sidecar は commit-time gate には効くが、上書き後の過去 COMMIT帰属までは閉じない。  
本レビューでは pytest を実走しておらず、実測値は親の 554 passed / 1 failed のみを引用した。