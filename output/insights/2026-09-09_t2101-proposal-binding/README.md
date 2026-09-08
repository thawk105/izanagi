# [T-2101] 提案の束縛を実行ループ側で閉じた — 閉じられたのは bootstrap だけで、continuation は登録値が別の対象を指す

2026-09-09。branch `worktree-dev-wave-t2101-proposal-binding`。base `2143a49c0`。
実装 commit `cd47c4651`、fix commit `f6655fa89`、main 取り込み `56dd4b65d` (固定 SHA `d106bebd0`)。
裁定の正本は `docs/decisions.md` の D1343 (ユーザー裁定、2026-09-01)。

## 0. この wave が主張すること・しないこと

**主張する:**

1. formal B-4 の **bootstrap** 実行で、3 driver (base / sort / trigger) の proposal loader が
   提案の canonical hash を再導出し、封印済み prerun publication の registry 行にある
   `initial_proposal_sha256` と一致しなければ、campaign 実行の副作用より前に拒否する。
2. この検査は恒真ではない。同じ publication root と同じ attempt id を固定したまま提案だけを
   別の schema-valid な提案へ差し替えると拒否される。**「registry に attempt があること」と
   「登録された hash と一致すること」は別の述語であり、後者は前者に含意されない。**
3. 事前登録した 10 変異が全件 KILLED で、期待 node と完全一致した (`matching: 10`)。
4. **登録値が指す対象は block 共有の初期 (bootstrap) proposal であって、continuation で
   driver へ渡る次の synthesis ではない。** これは事前登録の一次資料から確定した。

**主張しない:**

- **continuation の提案は内容束縛されない。** §2 の理由により、この wave では閉じていない。
- **どの publication が権威かは強制されない。** publication root は呼び手が実行時に選び、
  issuer は別 root での再発行を防がない。任意の提案 B に対して `H(B)` を持つ registry を
  別 root へ発行すれば通る。本検査が拒否するのは「指定された組の不一致」であって、
  「事前固定した集合であること」ではない。
- **束縛の成功は耐久証拠に残らない。** 実行後に別の attempt へ付け替える経路は塞いでいない。
- **manifest membership を検査していない。** manifest の 201 行の外にある registry 行でも、
  hash が一致すれば実行できる。
- **束縛されるのは実行される提案 (parse 結果の canonical 形) であって file の raw bytes ではない。**
  duplicate key を持つ file は最後の値が採られ、その canonical hash で照合される。
- **今日この gate が発火する formal 実行は無い。** 事前登録 §5 が `未記入` で、launcher が
  要求する admission record 3 件も HEAD に存在しないため、formal B-4 は開始できない。
  本 wave は「実走開始前に束縛を閉じる」作業である。

## 1. 中核の発見 — 登録値はどの提案を指すか

親 brief と段 2 プランは、launcher の `--proposal` を `initial_proposal_sha256` と比較する設計を
置いていた。段 3 の敵対相談 (sol の S9 / S14) がこれを割り、**親が一次資料で独立に検算した。**

- 事前登録 §5.1 の適格性述語:
  「**初期 proposal が、事前に固定した bootstrap 集合に属する。実走開始後に足さない。**」
  (`docs/phase3-b4-reflux-ablation-preregistration.md:377`)
- 同 §:「`precursor_hash_mismatch` — 同じ block の両アームの `precursor_hash` が一致しない」(`:547`)
  → **1 block の on / off は同じ `precursor_hash` を持つ。**
- raw producer は `precursor_hash` を `registry_attempt.initial_proposal_sha256` から出す
  (`orchestrator/campaign/p3_b4_raw_record_producer.py:2033`, `:2328`)。

一方 launcher の `--proposal` は、continuation では critic pair を実行した**後**に
main session が書く**アームごとに異なる次の synthesis** である
(`orchestrator/campaign/p3_b4_launcher.py:574-609`)。

**帰結:** continuation の `--proposal` を `initial_proposal_sha256` と比較してはならない。
比較すれば 1 block の on / off に同一の提案を強制することになり、測ろうとしている treatment 効果を
構成的にゼロにする。これは正しさ防壁ではなく実験そのものの破壊である。

## 2. continuation を閉じられなかった理由 (親の実測)

continuation で登録値を強制する唯一の筋は「この campaign を種付けした初期 proposal が
登録値と一致する」の検査である。ループがそれを再導出できるかを実測した。

**再導出できない。** checkpoint へ焼く辞書 (`orchestrator/campaign/p3_s4_loop.py` の
`state_to_dict`) は whiteboard の 5 field (`iteration` / `direction` / `magnitude` / `result` /
`delta_pct`) だけで、**提案の `value` も `implementation` も意図的に落としている**
(D39 決定 3 の構造的リーク遮断、絶対規律 2 / 6)。初期 proposal を復元する経路はループ内に無い。

閉じるには新しい耐久 carrier (受領証・台帳) の新設か、リーク遮断の設計変更が要る。
どちらも本 wave の scope 外であり、**親は発明せず裁定へ返した** (§6)。

## 3. 実装

### 3.1 適用範囲と関門の位置

`b4_reflux_ablation=True` かつ bootstrap (terminal receipt 束縛なし) の経路だけ。3 driver すべて。
照合は各 driver の proposal loader 内、既存の receipt gate と closed schema 検査の**後**に置く。

- base: `orchestrator/campaign/p3_s4_loop.py` の `load_proposal_file`
- sort: `orchestrator/campaign/p3_s4_loop_sort.py` の同名 loader
- trigger: `orchestrator/campaign/p3_s4_loop_trigger_gating.py` の同名 loader

launcher で先に読む案は**採らなかった**。段 3 luna の L5 が決定的で、launcher が読んで driver が
再度開けば、その間に `os.replace` で差し替えられる二重 open の窓ができる。
**proposal file を開くのは各 loader で 1 回だけとし、同じ buffer から parse と hash の両方を導く。**

### 3.2 canonical hash

`attempt_registry_core.canonical_json_bytes` に parse 結果を渡した bytes の sha256。
key 順・空白・非 ASCII escape の表記差は同じ hash になり、`1` と `1.0` は別の提案として扱う。
後者は意図した選択である — 登録値は事前に固定された「その提案」を指し、実行 genome が
同じになることは同一性の根拠にならない。

### 3.3 行の選択

`p3_b4_prerun_issuer.load_b4_prerun_publication` が返す封印 registry から、`attempt_id` が
exact に 1 件一致する行を選び、**その行の `driver` が実行中の driver と一致することも検査する。**
これは追加 gate ではなく、正しい登録値を引くための行選択の一部である
(段 3 luna の L9 が、attempt_id だけでは sort の実行が base の行を引けることを示した)。

### 3.4 fail-closed の範囲

束縛引数の欠落 (片方だけ・両方なし・空文字)、publication root が相対 path・不在・load 失敗、
attempt_id が registry に無い / 複数一致、登録値が 64 hex でない、行の `driver` 不一致、
canonical hash 不一致 — すべて拒否する。素通しの分岐は無い。
**continuation と非 B-4 経路で束縛引数が渡された場合も拒否する。**

## 4. 変異 (10 件、全件 KILLED、期待 node 完全一致)

spec は `mutation/mutation-spec.json`、結果は `mutation/mutation-report.json`。
runner は `python3 tools/run_tests.py orchestrator/tests/test_p3_b4_proposal_binding.py -q -rf --force-dispatch`。
repo head `f6655fa89762bfb688a0a2b931711eb2cb5dd2b8`。

| ID | 変異 | 期待した受理集合の変化 |
|---|---|---|
| m01 | 再導出 hash と登録値の等式比較を外す | 登録値と異なる bootstrap 提案が実行される |
| m02 | expected を registry でなく再導出した observed から取る | 自己比較になり、どの提案でも通る (恒真化) |
| m03 | publication root 不在時に素通しする | 束縛を持たない実行が通る (fail-open) |
| m05 | 行選択から `driver` 一致検査を外す | 別 driver の登録行の hash と比較して通る |
| m06 | canonical 化を非 canonical な `json.dumps` に変える | key 順・空白だけ違う正当な提案が拒否される (過剰拒否) |
| m08 | attempt_id lookup を registry の先頭行に変える | 指定した attempt と別の行の hash と比較する |
| m09 | publication load の例外を握り潰す | 壊れた publication が束縛なしで通る |
| m10 | sort driver の照合呼出しを外す | sort の formal bootstrap が素通しする |
| m11 | trigger driver の照合呼出しを外す | trigger の formal bootstrap が素通しする |
| m12 | continuation でも等式比較を強制する | **過剰拒否。**両アームに同一提案を強制し treatment を消す |

**m01 と m02 は、不一致の拒否だけでなく「実行より前に拒否すること」も同時に kill した** —
期待 node に `test_mismatch_is_single_read_and_precedes_all_campaign_effects` の 3 driver 分が入る。
**m06 と m12 は過剰拒否の検出変異**で、正当な入力を拒否する向きの変化を正例が捕まえることを示す。

### 4.1 事前登録からの変更 (erratum)

段 4 で登録した 13 件のうち 3 件を、**単一理由性 (DW-M01) が成立しないため登録しなかった。**

- **M04 (launcher argparse の `required=True` を外す)** — 実装は `required=True` を使わず
  bootstrap 分岐の手動条件で必須化しており、登録した位置が実装に存在しなかった (段 6 レビュー A2)。
  さらに attempt_id 欠落の経路は内側の gate が二重に塞ぐため、外側だけを外しても拒否は残り、
  赤理由が診断文字列の差にしか帰属しない。実効 gate へ再照準できなかったので登録から外した。
- **M07 (照合を `drive_iteration` の後ろへ移す)** — m01 / m02 の期待 node に
  実行前性の 3 node が入ったため、独立の変異として登録すると同じ理由の重複になる。
- **M13 (正例)** — m06 と m12 が過剰拒否検出の役割を担うため、独立登録をやめた。
  正例そのものは `test_matching_bootstrap_accepts_reordered_spaced_unicode_spelling` と
  `test_continuation_and_non_b4_reject_bootstrap_binding_arguments` の受理側として残っている。

### 4.2 期待 node の確定手順 (probe)

期待 node を推測で書かず、**全件 SURVIVED 登録の probe を先に走らせて観測 node を集めた**
(DW-M08)。probe 1 (`mutation/mutation-probe1-*.json`) が 7 件、probe 2
(`mutation/mutation-probe2-*.json`) が残り 3 件を返し、その完全集合を本走の spec に焼いた。

probe 2 の初回投入は、spec の `timeout_seconds` を 300 に置いたために queue 待ち (実測 8 分) を
待ちきれず harness 自身の per-run timeout が先に発火し、dispatcher を落として orphan hold を
作った。job 自体は走り切っており (`result.json` の `child_rc=1`)、**hold は誤検知だった。**
時間予算を実測 max の 3 倍超 (1800 秒) へ上げて解消した。詳細は §5。

## 5. 運用で判明したこと

- **`output/pegasus-dispatch/orphan-holds/` に 1 件でも残っていると、以後の dispatch が
  すべて起動前に止まる** (`tools/pegasus/dispatch_compute.py` の hold gate は live file の
  実在と archive directory の非空を同じ条件で見る)。live の `orphan-hold.json` を消しても
  archive を消さない限り解けない。復旧は (1) qstat で対象 job の終端を確認、
  (2) dirty source を `git checkout --` で復元して bytes を HEAD と照合、
  (3) live hold と archive の両方を削除、の順で行った。手動 qdel はしていない
  (F47 のラッチを武装させるため)。証拠は `orphan-hold-evidence/` に退避した。
- **変異 spec の `timeout_seconds` は queue 待ちを含む。** 計算ノードが混んでいる時間帯は
  per-run 300 秒では足りず、harness が dispatcher を落として orphan hold を作る。
- **sandbox の Codex 子は `tools/run_tests.py` を走らせられない** (`qstat -Q preflight rc=1`、
  `Unknown user-id`、`child_started=false`)。本 wave の実装子は pytest を 1 件も実走できず、
  実走はすべて親が行った。子の自走 harness (`PYTHONPATH=.` で test file を直接実行) は動く。

## 6. ユーザーへ返す裁定パッケージ (この wave では実装しない)

1. **continuation の提案束縛をどう閉じるか。** §1 / §2 のとおり、登録値は block 共有の初期
   proposal を指し、ループは checkpoint から初期 proposal を再導出できない。閉じるには
   耐久 carrier の新設か、リーク遮断の設計変更が要る。
2. **どの publication が権威かを誰が決めるか。** publication root は呼び手が実行時に選び、
   issuer は別 root での再発行を防がない。
3. **formal B-4 の母集合は manifest の 201 行か、registry の全行か。** 現在は manifest 外の
   registry 行でも実行でき、raw producer が後から拒否するまで build と WAL は進む。
4. **保証の境界は formal launcher 限定か、B-4 marked config を受ける全 sink か。**
   D1343 の文言は「実行ループ側」だが、束縛は loader 内に閉じ `drive_iteration` の型には載らない。

## 7. 一次資料

- 段 1 brief `verbatim/s1-brief.md` (訂正は `verbatim/s4-ruling.md` §0)
- 段 2 プラン `verbatim/s2-plan.md`
- 段 3 敵対相談 `verbatim/s3-consult-sol.md`、`verbatim/s3-consult-luna.md`
- 段 4 裁定 `verbatim/s4-ruling.md`
- 段 5 実装報告 `verbatim/s5-author.md`
- 段 6 敵対レビュー `verbatim/s6-review-a.md`、`verbatim/s6-review-b.md`、fix `verbatim/s6-fix.md`
- D1343 の逐語 `verbatim/d1343-verbatim.md`
