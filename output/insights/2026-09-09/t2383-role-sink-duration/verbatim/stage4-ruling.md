# 段 4 裁定 (確定) — [T-2383]

## 0. 前提の訂正 (親が現物で検算した新事実)

依頼文の前提「受入 63 走で最長残存 node (268〜312 秒)」は **D1795 (2026-09-08、git 62 process → 2 process)
より前の窓の値であり、現在は成り立たない。**

親が `/work/1/SFC/tanab/.izanagi-acceptance-shards/` の junit を直接読んで確認した実測:

- 直近 12 走の当該 node の所要: 171.905 / 103.504 / 60.747 / 49.972 / 68.870 / 75.850 /
  59.234 / 88.618 / 130.621 / 225.640 / 77.351 / 85.035 秒。中央値は約 80 秒
- 最新走 (`ca3fc62c...`、22,147 node) の最長は `test_t080_*` 群の 280〜298 秒。
  当該 node はその走で 171.9 秒で、上位 10 件に入らない
- レンズ B が挙げた 3 走 (88.618 / 75.850 / 68.870) は逐語で一致。
  同 3 走とも当該 node を持つ shard 2 の wall (267.55 / 260.16 / 250.19) より
  shard 0 の wall (319.30 / 325.97 / 440.97) の方が長い

**裁定:** 依頼の本題 (この node を被覆を消さずに短くする) はそのまま実行する。
ただし **「受入 wall を短縮した」とは主張しない。** 成果は「この node の所要を下げた」までである。
D1714 の「床は単独 node でなく帯である」という既裁定はそのまま生きている。

## 1. レンズ A の所見

### A-blocker-1 逐次実行スケジュールの被覆が失われる — **real / 採用 (明示裁定で受ける)**

親の独立確認: 対象 node の**全 assert の意味は実行順に依存しない**。
横断 7 種はすべて集合の要素数、per-iteration 6 種はその反復に閉じた値だけを見る。

**裁定:** この node が被覆する命題は「32 wire の実 trial における wire → role sink bytes の関係」であり、
**逐次という実行スケジュールは被覆対象に含めない。**

**正直に記録する損失:** 「逐次のときだけ wire を混ぜる」形の欠陥は決定的には捕まらなくなる。
docstring と decisions に書く。「等価」と書かない。

### A-blocker-2 集約境界で 32 件収集が保証されない — **real / 採用 (must-fix)**

親の裏取り: `len(set(sink_bytes["planner"])) == 1` は要素 1 個でも真。
`_critic_relation_equivalent` も 1 個で真。auditor だけが `== 32` で件数が守られている。

**must-fix:** 4 role すべてと `trusted_variants` / `secret_records` に件数 32 の明示検査を足す。
これは新設 gate ではなく、逐次 loop が構造から得ていた強さの保存である。

### A-should-fix 失敗 wire の診断 — **real / 採用**
### A-should-fix 「結果順」と「実行順」を分けて書く — **real / 採用 (文言)**

## 2. レンズ B の所見

### B1 対象選定と成功条件が古い — **real / 採用**。§0 のとおり訂正する。

### B2 固定 4 thread は根拠のない負荷増 — **real / 部分採用**

「4 という数に事前の根拠がない」は正しい。**答えは断念ではなく実測である。**

**裁定:** 並行度は決め打ちにせず、実装後に計算ノードで `max_workers` を 1 / 2 / 4 / 8 と
振って solo 所要を測り、**測った値で決める**。1 は「hoist だけ・逐次」の対照でもある。
測定は `DW-O19` の一時変異 (1 行、即時復元) で行う。

### B-S1 計測記述の訂正 — **real / 採用**

「node の 96% が I/O 待ち」は誤り。正しくは
「login の cProfile 付き pytest session 全体で、非 CPU 時間が wall の約 91.5%
(`real 172.912` に対し `user+sys 14.726`)」。
親は `sys` を落として 96% と書いた。insight と worklog はこの訂正形で書く。

### B-S2 thread-safe の名乗りを狭める — **real / 採用**

「現行 CPython 3.10、unregistered exploratory、`do_build=False`、
wire ごとの固有 provider と固有 `run_root` という exact 構成」に限定して書く。
free-threaded runtime へ一般化しない。

### B-S3 timeout の限界を明記する — **real / 採用 (文言)**

### B-別解 fixture binding の前計算 — **real / 採用 (primary の一部)**

親の検算: `orchestrator/tests/campaign_lock_test_support.py` の
`build_v2_campaign_lock(identity_preimage, *, authorization=None, binding=None)` は
**既に binding の注入を受け付ける**。`binding is None` のとき `_binding_from_recorded_head()` が
`_validated_root` + `_head_commit` + `_iter_blobs` で git を 4 回起動する。
これが 32 反復ぶんで 128 回。1 回へ前計算すれば 124 回減る (`_run_git` 640 → 516)。

production の受理集合を変えず、64 回の real admission も 64 回の live closure capture も
1 つも減らさない。**低リスクであり、先に測る。**

### B 由来の親 brief への訂正 — **採用**

「`contract_loader_binding.py` は自身が閉包 member だから変更不能」は過大だった。
正しくは「**pin 追従の費用がある**」であって「変更できない」ではない (D1795 自身が同 file を変更している)。
ただし本 wave では production を変更しないという裁定は維持する — 理由は
D1795 の memo 禁止裁定と、依頼の「本題の短縮だけ」である。

## 3. 実装する変更 (段 5、編集面は test file 2 本)

編集面: `orchestrator/tests/test_p3_autonomous_workload_trial.py` のみ
(`campaign_lock_test_support.py` は既に binding 引数を持つので変更不要)。

- **C1 (hoist):** `_binding_from_recorded_head()` を対象 test の loop 前に 1 回だけ実行し、
  `_write_admitted_rejection_digest` へ optional な `binding` 引数を足して `build_v2_lock` へ渡す。
  既存の他 caller (`:3429`) は引数省略で現行どおり。
- **C2 (並行化):** 32 反復を `ThreadPoolExecutor` + `executor.map(run_wire, range(32))` にする。
  worker は局所値を返し、main thread だけが集約する。`as_completed` は使わない。
  `max_workers` は **module 定数 1 個**で表し、親が `DW-O19` で振れるようにする。
- **C3 (件数検査、A-blocker-2 の must-fix):** 横断 assert の直前に
  4 role と `trusted_variants` / `secret_records` の件数 32 を明示検査する。
- **C4 (診断):** `run_wire` の返り値に wire を含め、失敗時にどの wire か分かるようにする。
- **C5 (docstring):** 被覆する命題と、逐次スケジュールを被覆対象から外した裁定、
  その損失を docstring に 3〜5 行で書く。

**変えないもの:** 反復数 32、全 per-iteration assert 6 種 (`assert do_build is False` を含む)、
全横断 assert 7 種の条件、production file、`_WireRecordingFixture`、
`_critic_relation_equivalent`、`_canonical_without_json_pointers`、
64 回の real admission、64 回の live closure capture。

## 4. 変異事前登録 (段 6、DW-M01 / DW-M08)

**この wave の証明義務は「短縮後も、短縮前と同じ変異を殺す」ことである。**
したがって登録変異は **変更前 HEAD 版と変更後版の双方へ走らせ、KILLED 集合の一致を示す** (DW-M08)。

| # | 変異 | 検出する性質 | 期待赤 node | 新旧両走 |
|---|---|---|---|---|
| M1 | `_WireRecordingFixture` で planner の記録 payload に wire を混入 | planner sink が 1 種 | 対象 node | 両方 KILLED |
| M2 | 同じ seam で coder の記録 payload に wire を混入 | coder sink が 1 種 | 対象 node | 両方 KILLED |
| M3 | `p3_autonomous_workload_trial.py` の auditor `correctness_digest` に `coder.wire` を加える | D pointer 以外の auditor 差異を拒否 | 対象 node | 両方 KILLED |
| M4 | `p3_s4_loop.py` の `diffq_variant_id` を固定値にする | trusted variant と secret variant の 32 種 | 対象 node | 両方 KILLED |
| M5 | critic identity projection を RAW に戻す | raw candidate / build attempt の非混入 | 対象 node + `test_final_generation_critic_rebuilds_projected_digest` | 両方 KILLED |
| M6 | injected drive へ `do_build=True` を渡す | `assert do_build is False` の liveness | 対象 node | 両方 KILLED |
| M7 | `_WireRecordingFixture` で 1 role の `payload_bytes` を二重記録 | 各 role が各 wire で exact 1 回 | 対象 node | 両方 KILLED |
| M8 | **新 collector で critic を先頭 1 件だけ append する** | **C3 の件数検査が効いていること** | 対象 node | **新のみ (旧に collector 無し)** |
| M9 | **`run_wire` で wire 17 だけ例外を送出** | future 例外が吸収されず横断 assert へ進まない | 対象 node | **新のみ** |

M8 と M9 は変更後版にしか存在しない構造への変異なので、旧版走は該当なしと記録する (mask ではない)。

## 5. 採否の事前登録 (結果を見る前に定める、規律 3)

- **C1 (hoist) は無条件で採用する。** 受理集合を変えず、並行性も足さないため。
- **C2 (並行化) の採用条件:** (i) 焦点走と受入全走が緑、(ii) 計算ノード solo で
  `max_workers>1` の所要が `max_workers=1` の 60% 以下、(iii) 実施した走行で新たな flake が出ない。
  **3 つすべてを満たさなければ C2 は採らず、C1 だけを land する。**
- **`max_workers` の決め方:** 測った中で最良値の 10% 以内に収まる**最小の**並行度を選ぶ
  (同じ利得なら並行度は小さい方を採る)。
- **主張してよいこと:** この node の所要が下がったこと。
  **主張してはならないこと:** 受入 wall の短縮、shard wall の改善。
  受入 junit の shard wall は観測値として記録するだけで、本 wave へ帰属させない。

## 6. scope 外 (裁定パッケージ候補、本 wave では実装しない)

1. 対象を現在の床 (`test_t080_*` 群、280〜298 秒) へ移す起票
2. `artifact_admission.py:73` の説明文字列が「exact 62 path」で現物 63 と食い違う
3. `_AUDITOR_D_POINTERS` の exact 集合を pin する assert が無い
4. 対象 test が `report["status"] == "complete"` を検査せず partial report を見逃しうる
5. production の closure capture を同時実行分だけ束ねる single-flight (D1795 の再裁定が要る)
6. free-threaded runtime での replay capability `issued` dict の lock 不在
