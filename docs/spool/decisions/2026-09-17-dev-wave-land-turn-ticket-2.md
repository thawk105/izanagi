---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-17
wave: dev-wave-land-turn-ticket
seq: 2
---

## {{D:land-turn-ticket}}. land に受入 lease と別の順番票を入れ、lock-busy で監査・fold gate の証拠を捨てず、control-plane 観測を protected child と自 wave の admin に限る

**決定:** `tools/dev_wave_land.py` の land に、受入 lease (D662 / D691) と独立した **land 順番票** を入れる。

1. **順番票。** `<common git-dir>/dev-wave-land-turn/` に `registry.lock` (固定 inode、短い `LOCK_EX`)・`registry.json` (連番と request key の対応、現在の grant、一時 file → fsync → rename) ・ticket `<seq:08d>-<holder12>.jsonl` (phase を追記) を置く。登録できるのは、現行 `_verify_acceptance_receipt` の lock 非依存部分 (schema・authority kind・holder・tested main/tip・argv・scheduler・env projection・verdict と rc/nodeids の整合・fingerprint・固定 object の blob/bytes・raw digest) を通した request だけで、`non-attributable-only` 旧互換分岐は保持する。lock 内の完全検証は不変で、登録時 digest との一致を要求する。request key は `(acceptance_wave, tested_tip, receipt raw sha256)` + main path / wave path / common / tested_main の一致で、landing_tip は key に含めない (前進 merge 後の再試行を許す)。
2. **生存と先頭。** 生存は待ち手が ticket file に保持する `LOCK_EX` で判定し、pid・mtime・TTL は使わない。grant は非横取りで、grant 不在時に「登録済み・生存・最小 seq」を選ぶ。先頭だけが initial → 監査 → fold gate → ff/fold を通り、新規到着は追い越せない。terminal outcome では grant を放す registry 更新と同じ更新で次の待ち手へ渡す。同一 key の二重起動は第二の ticket を作らず `lock-busy` (別文面、retryable) で降りる。先頭は各 mutation 直前 (ff-only 前・`apply_fold` 前・shape B の mark/finalize 前) に grant 保持・FD 生存・binding 不変を再確認する。
3. **rc 別の seq 処理と order。** `landed` / `already-landed` は seq 削除。`stale-main`・順番期限の `lock-busy`・retryable な拒否・rollback 成功は seq (identity) を保持し、同 key の再入で新規登録しない。非 retryable の拒否 (provenance の violation rc・監査赤・dirt・control-plane・fold gate 赤・receipt 不一致) は seq 削除。rollback 不完全・recovery 失敗・postcondition 失敗は `mutating` のまま通常 grant を止める。選出は seq と別の `order` で行う: 初回登録で `order = seq`、**grant を得る前の終端** (順番期限・registry busy) では order を保持し、**grant を消費して終端した request** (stale-main・retryable 拒否・rollback 成功) は order をその時点で登録済みの全 ticket の後ろ (発行済み最大 seq) へ回す。着地できない request は待ち手全員に 1 巡ずつ譲り、新規到着よりは前に戻る。
4. **死亡 `mutating` 票の完了照合。** `mutating` record は main_before・landing_tip・wave_ref・trusted_main_cutoff・audited_digest・expected_fold を束縛し、後続は common flock 内で (1) fold state 実在 → 同 key の元 request だけが既存 recovery へ、他は通常 grant 停止 (2) state 不在かつ main == main_before → rolled-back、seq 保持 (3) state 不在かつ main == landing_tip かつ fold なし → done (4) state 不在かつ main の first-parent が landing_tip でその commit が `verify_declared_fold_commit` を通る → done (5) それ以外 → fail-closed、と判定する。main は変えない。
5. **証拠保持と二層予算。** `_LAND_TURN_WAIT_SECONDS = 3600.0` を 1 invocation の絶対期限とし (`_verify_repository` 直後に 1 本)、`_LAND_LOCK_WAIT_SECONDS = 180.0` は累積競合待機枠として据え置く (補充しない、各枠の deadline は順番期限で切る)。180 秒を使い切った後も順番期限まで短い sleep + 非 blocking 取得を反復する。`_run_outside_land_lock` は runner を 1 回だけ呼び、成功 payload (provenance receipt / fold gate receipt) を順番期限まで保持して再取得し、取得後に既存の全再検査 (control 比較・fingerprint・完全 preflight・receipt 再照合・active state・closure) を通す。provenance の非ゼロ payload は再取得を待たず `RC_PROVENANCE` で即終端する。期限到達時だけ `lock-busy` を返し、reason に順番待ち実績を出す。結果 JSON の key 集合は変えない。**これにより 180 秒は総競合待機の上限ではなくなる。** D432 の「上限内に terminal outcome へ至る」は順番期限 3600 秒が引き継ぐ。
6. **registry の I/O。** `_turn_registry` は内容が変わったときだけ保存する (読取りだけの poll で fsync を出さない)。実測: `/tmp` (xfs、load 55) で 1 保存 37 ms、poll ごと保存では 8 本の正例 node が runner 外で 270 秒 (runner 内は数秒)。
7. **非接触。** `_worktree_snapshot` は wave 自身と `protected_paths` に重なる child だけを open して admin binding を検証し、無関係 child は名前を列挙するが実体・identity・admin binding を読まない (`observed_worktree_identities` は protected child だけ)。`_CONTROL_CONTAINERS` 自体の保護、handoff 名前集合と directory identity、自 wave の再 open と binding、`protected_after != protected_before` は維持する。
8. **cleanup。** `tools/dev_wave_cleanup.py` の全体 `git worktree prune --expire=now` をやめ、preflight で束縛した自 wave の admin gitdir (一意、複数一致は拒否) だけを registry 親 FD からの相対操作で撤去し、`_verify_record_state(absent=True)` で確認する。`_dry_run_candidates` と prune の argv 許可形は廃止する。主張は「他 wave の admin を削除しない」までで、resolver が他 admin の backpointer を読む点は残る。

**本決定は D432 と D1996 を supersede し、D109 と D702 を部分改訂する。** D432 の再束縛 (取得後の inode 照合)・knob 禁止・`lock-busy` の rc 不変、D1996 の「取得ごとに満額補充しない」「lock 外の作業時間を差し引かない」は維持する。D109 の「拒否は衝突軸へ一本化」はそのままで、無関係 child の実体・admin 観測と同名差替え拒否だけを外す。D702 の自己撤去義務は維持し、prune の範囲だけを自 admin に限る。D254 (監査は lock 外、receipt 束縛、480 秒)・D1393 (plan 作成は lock 内)・D662 / D689 / D731 / D987 (receipt 再利用条件) は変えない。

**進行保証の前提 (主張の範囲):** 成功可能な候補が存在し、先頭の検査・I/O が有限時間で応答し、順番票を持つ driver 同士が同じ規約に従い、順番票を知らない旧 driver の common flock 保持が終息し、fold 途中 state を残した元 request が再入するとき、競合だけを理由に全員が永久再試行しない。registry lock の取得公平性は OS の flock に依存し、理論上の無期限飢餓は排除しない。生存したまま hang した先頭は TTL で追い越さず、止める主体は本決定の外にある。受入 lease の TTL 2400 秒は順番期限 3600 秒より短く、待機中の lease 保持は保証しない (renew loop は足さない)。

**理由:**
- 2026-09-16 21:09〜22:25 に 8〜13 本の land が共通 flock を 3 回 (initial / post-provenance / post-fold-gate) 取り直す競走で全員 `lock-busy` になり 76 分着地ゼロだった ({{F:land-storm-lock-busy}})。manager session が手で 1 本ずつ GO を渡すと 2 波 30 本が失敗 0・5〜6 分/本で流れた。人手の直列化を道具に入れるのが最小差分である。
- 旧 tree (abc7085ae) に新 harness だけを重ねた決定的 schedule probe (13 本、20 秒間隔到着、in-lock 240 秒、監査 430 秒、gate 130 秒、rc=11 は 120 秒後に再投入、fake 76 分) は着地 0・main 不変・監査 18 回・終端 151 回 (全 rc=11、最終 initial 12 / post-provenance 1) を再現し、in-lock 30〜200 秒では 1 本着地する。嵐の本体は「lock 内作業が 180 秒の累積予算を超える + 到着率 > 処理率」で、D1996 が直した混同とは別の穴である。同 policy の新 tree は着地 1・監査 1。
- order の回転は、新 tree の同 probe で独立 branch の stale-main request 2 本が保持 seq のまま先頭を交互に占め、後続 10 本が 3600 秒の順番期限で `lock-busy` になった実測から入れた。
- 現行は再取得に負けた時点で 480 秒の監査結果と fold gate 結果を捨て、fresh context で全部やり直す。証拠を保持して待つだけで、同じ入力への同じ検査の反復が消える。
- 3600 秒は実測分布から取った: 成功 land の窓 `window_elapsed_s` は n=34 で median 272 / p90 543 / max 1,180 秒 (dev-wave-jobs 配下の land 結果 468 件、窓付き 113 件、2026-08〜09-17)。3600 ≈ 13 × median ≈ 6.6 × p90 ≈ 3 × max であり、13 本が median regime で並ぶとき 1 invocation で捌ける上限。p90 以上の regime では期限到達 → seq 保持の再投入に頼る。有限 N 本の全完了を導く数値ではない。
- 無関係 child の `.git` を開いてから読む race (`_open_container` → child open → `_validate_admin_binding` → `.git` read) は、cleanup が他 wave を撤去する瞬間に `RC_CONTROL_PLANE` を出していた。対象外 child を開かなければ race そのものが消える。`ENOENT` を握り潰す方法では部分撤去の別の失敗箇所が残る。
- D432 が「ticket file による FIFO」を却下したのは stale ticket・owner crash・別の直列化 lock を要する crash protocol が scope より大きかったからで、本決定はその crash protocol (FD lock 生存・rc 別 seq 処理・死亡票の完了照合) を明示的に持つ。

**却下した選択肢:**
- 180 秒の単純延長、jitter 強化 — D1996 の増幅の懸念どおり同時流入を増やすだけで、公平性も証拠保持も得られない。
- TTL 切れによる owner 追越し — 生存 owner を追い越して mutation を二重化する経路になる。
- 監査を lock 内に置く、plan 作成を lock 外へ出す — D254 / D1393 の反転。本件の原因は再取得競走であり、lock 区間の移動では直らない。
- file 交差で受入結果を流用する、lease を land 待機まで広げる、汎用 read-set 解析 — scope 外 (別裁定)。
- 他 wave が死亡 owner の fold 途中 state を自動復旧する — 元 wave の cwd・binding・receipt・起動主体・結果帰属が要り、origin 照合を緩めて代替できない。裁定パッケージへ返す。
- ticket dir を `IZANAGI_WAVE_LEASE_DIR` 配下に置く — 別 root の identity 検証と未設定時の分裂が要る。common git-dir なら既存 lock と同じ inode に束縛できる。
