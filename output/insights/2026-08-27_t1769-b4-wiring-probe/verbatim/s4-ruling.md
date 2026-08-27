# 段 4 裁定 — [T-1769] B-4 §5.1 (ii) 非標本 probe

親が段 2 プラン (`s2-plan.md`)、段 3 レンズ A (`s3-consult-sol.md`)、レンズ B (`s3-consult-luna.md`)
を読み、親自身の実測 (`parent-measurements.md`) と突き合わせて裁定した。

## 0. 総括裁定

**プランは条件付き採用。** レンズ B の総括は「現プランは不採用、B1 だけで違反確定、停止」だが、
**この停止は refuted する** (理由は 1-B1)。ただし A2・A3/B4・B5・B8 は real であり、
**この 4 件を直さない限り段 5 へ進まない**。

## 1. 所見別裁定

### A2 — 保証が本番の入口へ配線されている検査が無い → real / 採用 / must-fix (最優先)

負例は遮断機構を子 process で組み立てて発火を見るだけで、`main()` が実際にその機構を
装着することを検査しない。`main()` から装着を消して証拠 boolean を `true` のまま出せば
全検査が通る。**これは恒真の典型である。**

**採用する修正:**
1. 証拠の `profile_hook_active` / `audit_hook_active` / window 4 boolean を**literal にしない。**
   実際に設置された hook の identity (`sys.getprofile()` が seal した callable と同一 object か、
   audit hook が installed か) を観測した結果から導出する。観測できなければ publish しない。
2. **実 `main(argv)` を通る負例**を置く。子 process で probe module を import し、
   private の検査表の 1 要素を「実 `pipeline.evaluate` を呼ぶ」ものへ差し替えてから
   実 `main(argv)` を呼ぶ。`OutcomeGenerationError` で落ち、証拠 file が 0 件であることを確認する。
   **production 側に負例起動口 (`--negative-control` 相当) を公開してはならない。**
   `DW-O14` に従い正規の注入 seam を先に探したが、production に seam は無く、
   **作るべきでもない** (作れば防壁に穴を開ける)。子 process 内の private 属性差し替えに限る。
3. 変異 M-01 (下記) がこの配線検査を殺すことを実走で示す。

### A3 / B4 — 遮断集合は producer/viewer の完全目録ではない → real / **限定採用**

親の実測 (`parent-measurements.md` M-P5/M-P6) で逆閉包が `run_one_iteration` を捕まえることは
確認済みであり、**恒真ではない**。しかし「新 producer は自動的に全部入る」という
**完全性主張は成立しない**。実測した反例:

- `p3_s4_loop.py:1021` `_resolve_duplicate` は WAL の terminal record から `fitness_tps` を
  読んで返す (**閲覧側の反例**)。anchor を通らない。
- `p3_s4_loop.py:593` `project_whiteboard` は結果を state へ append する (**生成側の反例**)。
  anchor を通らない。
- `p3_s4_loop.py:370` `record_diff_reject` は anchor を通らず WAL へ 2 record 書く。
  **しかもこれは probe が正例で必ず呼ぶ** (B4 の指摘どおり)。

**採用する修正 (無制限の census はしない。3 点に限定する):**
1. **種を 2 つ足す。** `save_loop_state` (`p3_s4_loop.py:802`、checkpoint 永続化) と
   `project_whiteboard` (`:593`、結果射影) を anchor と並ぶ独立の種として逆閉包を取る。
   親実測で両者は anchor を通らず、かつ probe は呼ばない。したがって足しても probe は動く。
2. **`record_diff_reject` は遮断しない。束縛する。** probe が呼ぶときの layout root が
   発行済み workspace であることを実行時に要求する。protected root を渡す負例で拒否を示す。
   (遮断すると probe が自分の正例を実行できない。束縛なら発火する述語になる。)
3. **役割分担を証拠と docs に明記する。**
   - **生成**は遮断集合が受け持つ (種は 3 つ: certified-writer anchor / `save_loop_state` /
     `project_whiteboard`)。種へ到達しない producer は**この層では覆わないと書く。**
   - **閲覧**は隔離層が受け持つ (protected root の read/write を audit hook が拒否)。
   - 「新 producer は自動的に全部入る」とは**書かない**。書けるのは
     「3 種のいずれかへ到達する producer は自動的に入る」までである。

### B1 — 承認経路が実 campaign 3 件の台帳を読む → real / **停止は refuted** / 開示 + 束縛で採用

**実測 (親):** `orchestrator/campaign/legacy_admission_overlay_v1.json` は
`deny-only-admission-overlay` であり、legacy campaign 3 件の path・campaign_id・
lock/WAL sha256・`build_start_count`・`verification_status: historically-certified` を持つ。
`require_admitted_campaign` はこれを読む。レンズ B の事実認定は正しい。

**しかし停止は採らない。理由:**
1. `p3_s4_loop.py:568-573` が `type(view) is not CertifiedCampaignView` を拒否する。
   `CertifiedCampaignView` を発行するのは `require_admitted_campaign` だけである。
   **迂回は正しさゲートを緩めることに等しく、規律 2 に反する。**
   レンズ B 自身も「public admission gate を緩めず」と書いており、両立する解は迂回ではない。
2. この台帳が持つのは legacy campaign 3 件の**承認 metadata** であって、
   B-4 の primary / secondary outcome ではない。B-4 の outcome はまだ 1 件も存在しない。
3. そこに載る 3 campaign の既知性は、事前登録 §9 (HARKing 境界) が
   **既に閲覧済みとして開示している**範囲に収まる。

**採用する修正:**
1. 証拠 JSON に `admission_reads` 節を置き、読んだ overlay の repo 相対 path と sha256、
   および「deny-only の承認台帳であり B-4 の outcome ではない」旨の分類を記録する。
2. audit ledger が「この overlay 以外の実 campaign artifact を 1 件も読まなかった」ことを
   `protected_read_attempts == 0` で示し、テストで固定する。
3. 事前登録 §10 へ**名前付きの未閉鎖**として書く —
   「非標本 probe は承認経路の deny-only legacy overlay を読む。これは outcome ではないが、
   実 campaign 3 件の識別子と歴史的検証状態を閲覧することは事実である」。
   **黙らせず、開示する** (規律 3)。

### B8 — 親の一般化は誤り。かつ**事前登録文書の記述が sort について偽** → real / 採用 / 訂正

**親の実測で確認した:**

|driver|`--no-build` で切替点へ到達するか|根拠|
|---|---|---|
|base|**到達しない**|`p3_s4_loop.py:1508` `if do_build and out["outcome"] != "dry-pass":` の内側|
|trigger|**到達しない**|`p3_s4_loop_trigger_gating.py:1031` 同型。1049 の `else` が digest を明示的に飛ばす|
|**sort**|**到達する**|`p3_s4_loop_sort.py:502-513` は `drive_iteration` (423) の中で**無条件**。`main` は 642-643 で `do_build=not a.no_build` を渡すだけ|

したがって:
1. **親 brief の一般化を撤回する。** 検査 2・3 が共有関数の性質である点は正しいが、
   「`--no-build` は切替点を通らない」は driver 非依存ではない。
2. **事前登録 §10 の記述 (`--no-build` 経路は §3.1 の切替点を通らない) は sort について偽である。**
   docs 修正で driver 別に書き分け、sort の `--no-build` が probe にならない本当の理由 —
   iteration を実走して checkpoint と whiteboard 結果を書く、すなわち synthesis 記録を生成する —
   を書く。
3. 検査 1 は driver ごとに条件付き edge の guard 式まで証拠へ記録する (B6 と同じ修正で足りる)。
4. trigger の identity は site projection 後の cfg から作られる
   (`p3_s4_loop_trigger_gating.py:423-437, 806-822`)。検査 4 は raw `default_cfg` だけでなく
   **その driver の sanctioned 経路が実際に使う cfg** で測る。

### A5 / B6 / P2 — 静的到達性は runtime 通過の証明ではない → real / 採用 (文言と証拠形式)

1. 証拠と docs に「静的 candidate-main path + probe による実切替点 direct call の composite」と
   逐語で限定する。「driver が runtime に切替点を通る」とは書かない。
2. 条件付き edge は `conditional_edges` として guard 式の逐語つきで証拠へ残す。
   分岐の実行可能性は主張しない。
3. 解決不能な束縛 (非 literal `getattr`、star import、動的 import、`sys.modules` 経由) が
   証明 path に入ったら `StaticInventoryError` で fail-closed。静かに「到達」と答えない。

### B5 — `sys.modules` 差替え・新 code object は未閉鎖 → real / 採用 (限定)

publish 直前に、目録の全 entry について
(a) `sys.modules[module]` が seal 時と**同一 object**、
(b) 関数の `__code__` が seal 時と**同一 object**
であることを再検証する。窓の中の `exec` / `compile` は audit で拒否する。
実 swap を行う負例を置く。**任意の native code や同権限 process による interpreter 改変までは
主張しない**と証拠へ書く。

### B3 — ambient temporary root が実 campaign tree に入りうる → real / 採用 (安価)

発行 workspace の realpath が (a) repo 外、(b) 解決済みの全 campaign root の外、
の両方であることを要求する。`TMPDIR` が campaign tree 内を指す場合は拒否する。負例を置く。

### B2 — fixture の非派生性が未証明 → real / **縮約して採用**

無制限の provenance schema は作らない。次の 3 点に限る。
1. fixture payload は**型から機械生成**する。実 campaign の payload を転記しない。
2. probe 専用の予約 marker を使う。
3. fixture schema が、性能値・receipt・実 campaign id を運ぶ field を**拒否**する。
   拒否が発火する負例を置く。

### A6 — 受入検査の漏れ → real / 採用 (安価)

受入列へ追加する:
- `orchestrator/tests/test_ccbench_spawn_sites.py`
- `orchestrator/tests/test_check_subprocess_bytecode_guard.py`
子 process runner は `-I -B` と clean env で固定する。

### B9 — 生の campaign_id が実 root の locator になる → real / 採用 (安価)

証拠から `on_campaign_id` / `off_campaign_id` の**生値を削り**、
domain separated な preimage hash と `different: true` だけにする。

### A7 / B10 — 文言 → 採用

- 親 brief の「唯一の blocker を外す」を「**CLI 不在という blocker を 1 つ外す**」へ訂正する。
  §5.1 (i) の先行 freeze と人間の指名が残る。
- 「既存受理集合は変更しない」を
  「**既存 driver の runtime 受理集合と campaign identity は不変。repository 全体を走査する
  開発 gate の対象集合は拡張される**」へ訂正する。

### B7 / B11 — nit / 採用

- import 時の `atexit` / signal / finalizer / thread 起動を拒否する regression と
  seal 時の thread census を足す。
- `_make_probe_view()` は zero-argument・exact return type を保つ。
  test のための token/path constructor を足さない。

### A8 — 正式採用層 → **scope 外 / 裁定パッケージへ**

§5.1 (i) の先行 freeze commit、人間の記入者・レビュー者の指名、その版での正式 (ii) 実走、
§5 欄の記入は**本 wave の scope 外**である。人間の指名を含むため AI が確定できない。
最終報告で裁定パッケージとしてユーザーへ返す。

### P1〜P7 の最終裁定

|P|裁定|
|---|---|
|P1 (新規 module + `--driver`)|**採用**|
|P2 (静的 + 動的の 2 本立て)|**限定採用** — composite と明記。runtime 通過とは書かない|
|P3 (interdiction 窓)|**修正のうえ採用** — A2 の配線検査と A3 の種 2 追加、完全性主張の撤回が条件|
|P4 (実体名指しの負例)|**修正のうえ採用** — 実 `main()` を通る負例の追加が条件|
|P5 (実 campaign 非接触)|**修正のうえ採用** — B3 の ambient root 拒否、B1 の開示が条件|
|P6 (§5 の欄を埋めない)|**採用** — レンズ A も独立に支持|
|P7 (docs 改訂)|**修正のうえ採用** — B1・B8 の訂正を含め、未発効の理由を両節に残す|

## 2. 変異の事前登録 (DW-M01)

実装前に登録する。各変異は 1 つの検査だけを殺し、前後に同じ入力を拒否する層が無いことを
実装子が確認する。確認できない変異は登録から外し、実効 gate へ再照準する。

|ID|変異位置|狙う検査|単一理由性の確認事項|
|---|---|---|---|
|M-01|probe `main()` から guard 装着呼出しを削除|A2 の配線検査|証拠 boolean が観測由来であること。literal なら M-01 は死なない|
|M-02|証拠の `profile_hook_active` を観測でなく literal `True` にする|A2 の観測由来性|M-01 と別理由 (装着はするが報告が偽) であること|
|M-03|遮断集合の種から certified-writer anchor を外す|生成遮断 (anchor 経路)|`pipeline.evaluate` の負例だけが落ちること|
|M-04|種から `save_loop_state` を外す|生成遮断 (anchor 非経由)|A3 で足した種の実効性。M-03 と独立に落ちること|
|M-05|種から `project_whiteboard` を外す|同上|M-04 と別 node が落ちること|
|M-06|`record_diff_reject` の layout 束縛検査を外す|B4 の束縛|protected root を渡す負例だけが落ちること|
|M-07|静的解決で非 literal `getattr` を fail-closed でなく「未到達」にする|B6 の fail-closed|`StaticInventoryError` の負例が落ちること|
|M-08|off 経路で loader を 1 本だけ reflux 分岐前へ移す|検査 3 の loader 0 件|off count が 1 になることだけで落ちること|
|M-09|off の戻り値に 1 byte 足す|検査 3 の byte 一致|hash 不一致だけで落ちること|
|M-10|`default_cfg` の on/off を同じ reflux 値にする|検査 4 の identity 分離|preimage 一致だけで落ちること|
|M-11|workspace 検査から「campaign root の外」条件を外す|B3|ambient root 負例だけが落ちること|
|M-12|publish 前の `sys.modules` / `__code__` 同一性再検証を外す|B5|swap 負例だけが落ちること|
|M-13|fixture schema の性能値 field 拒否を外す|B2|拒否負例だけが落ちること|
|M-14|検査失敗時にも証拠を publish する|publish gate|失敗時 0 件の検査だけが落ちること|
|M-15|sort の条件付き edge 記録を base と同じ「条件なし」にする|B8 の driver 別記録|sort の `conditional_edges` 検査だけが落ちること|

**正例 (過剰拒否の検出、DW-M01):** 変異を入れない baseline で 3 driver すべてが
`passed=true` で証拠を publish すること。遮断が過剰なら probe 自身が動かず、これが落ちる。

## 3. 段 5 へ渡す確定事項

- 実装面は Codex `role=author` が書く (D95)。親は直接編集しない。
- 編集面: `orchestrator/campaign/p3_b4_wiring_probe.py` (新規)、
  `orchestrator/tests/test_p3_b4_wiring_probe.py` (新規)。
  **docs と証拠 JSON は段 5 の編集面に含めない** (親と dogfood 走が担う)。
- 既存 3 driver、`pipeline.py`、`loop.py`、`test_p3_s4_loop.py` は編集しない。
- source に exact 文字列 `--build` を置かない。`exploration_campaign_layout()` を呼ばない。
- 子は commit しない。
