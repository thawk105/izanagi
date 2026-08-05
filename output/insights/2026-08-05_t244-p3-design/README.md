# [T-244] P3 (1)(2)(3) 設計裁定パッケージ

**この文書が裁定の正本である。** §9 が択一の一覧で、ここだけ読めば裁定できる。
逐語は `brief.md` (段 1 実測)、`s2-plan.md` (設計案)、`s3-lensA.md` / `s3-lensB.md` (敵対 2 レンズ)、
`s4-adjudication.md` (段 4 裁定)。

- wave: `dev-wave-t244-p3-design` / 起点 main `3075a8fd` / **実装差分なし (docs のみ)**
- 依頼 = worklog (200) のユーザー裁定で設計 wave へ委任された (1)(2)(3) の起草 +
  「prototype が production で起動できない件」((198) / D163) の解消案
- 前提として使った裁定済み事項 = **(4)** origin proof の durable cross-reference を producer 側で今出す /
  **(5)** 複数候補を通すなら D96 手続

### 行番号の基準と再確認 (erratum、land 直前に実測)

本パッケージと逐語の file:line は**すべて起点 main `3075a8fd` 時点**のものである。land までに
local main が `6d6cd095` まで進んだため、**設計の根拠にしている実装事実が生きているかを取り込み後に
再確認した。結論は「事実はすべて不変、行番号だけが動いた」である。**

- `orchestrator/campaign/reflux_origin_ledger.py` と `reflux_origin_authority_v2.json` は
  **差分ゼロ**。§1 の事実 (b)(c)(d) と §3・§4 の根拠はそのまま有効である。
- 8c driver の `WORKLOADS` は `ycsb-a/b/c` のまま (171 → 173 行)、`MAX_APPROVED_GENERATIONS = 1`
  も不変 (143 → 145 行)。
- 完全性 consumer の `attempt` 厳密 1 / `retry` false の pin も不変 (192-195 → 200-202 行)。
- `trial_registry` の `certifying=False` / `arm_binding="declared-only"` (124-129 → 199-200 行) と
  H1=rr80 / H2=rr20 の束縛 (46-49 → 52-55 行) も不変。

**したがって §9 の択一 10 件はいずれも影響を受けない。** ただし (198) の前パッケージが
行番号 stale で使えなくなった前例 (§1 の事実 (a)) があるため、実装 wave を起票するときは
その時点の main に対して file:line を取り直すこと。

---

## 1. 先に読むべき 4 つの事実 (本 wave の実測。前提が動いている)

**(a) ledger は v1 から v2 へ移行済み。** (198) / D163 が見たのは v1 で、間に P4 wave (`61fc5202`、
D166) が land した。**(198) の裁定パッケージが引く file:line はすべて stale** である。

**(b) production の runtime 初期化は「入口が無い」のではなく明示的に禁止されている。**
`_initialize_locked` の冒頭が `if not store.fixture: _fail("production runtime initialization is
forbidden")` である。したがって D163 の起動不能の解消は、入口を足すだけでは済まず
**「誰が・何を根拠に禁止を解除できるか」という受理契約**を伴う。

**(c) 最初の genesis が、その runtime で今後存在しうる origin 集合を永久に固定する。**
genesis は authority registry の全 entry をその場で焼き込み、読み出し側は authority blob の
完全一致と entry 件数の一致を要求する。origin を後から足す event 型は存在しない。
**すなわち bootstrap と世代移行は不可分**であり、世代移行を決めずに最初の genesis を打つと
後戻りできない。

**(d) batch の distinct 制約は「候補平文」でなく「commitment」に掛かる。**
commitment の preimage が (wire, query ordinal, replicate ordinal) を含むため、
**同一候補 1 点の R 回反復でも合法な batch になる**。(198) の「複数候補にしないと batch を
作れない」という閉塞は、この意味では崩れている。**ただしそれは予算束縛の実現を意味しない** —
下記 §5 を参照。

---

## 2. 本パッケージの結論 (一文)

**(1)(2)(3) の設計は起草できたが、そのまま実装 wave として起票してはならない。** 段 3 の敵対
2 レンズが独立に NO-GO を返し、(i) DW-G04 の発火 gate を満たす正の artifact path が書けない、
(ii) DW-G01 の生死実験が先行していない、(iii) 受理集合の変更が 4 面同時で 1 wave に収まらない、
(iv) 予算 root の同一性が repo 内の検査だけでは原理的に閉じない、を挙げた。
**先に §9 の択一を裁定し、その後で「生死実験だけの小さい wave」から始めるのが本パッケージの推奨である。**

---

## 3. (1) origin authority の実体化 — 推奨

### 3.1 preimage の trust root = 捕捉 commit の名前付き artifact の raw blob bytes

**推奨。** authority generation が捕捉した full 40-hex commit `H` に対し、`H:<path>` の blob bytes
全体 (末尾 LF 込み、再直列化なし) を SHA-256 する。freeze 族 (`s8b_ratified_freeze.py`) が
既に採っている型であり、reviewer が意味内容を artifact 単位で承認できる。

**却下: コードから導出する案** (`inspect.getsource()`、module source hash、runtime 定数の JSON 化)。
import closure を漏らしやすく、Python / serialization 実装差に依存し、
**「実装を実装自身で証明する」自己参照**になりやすい。補助 provenance としては持ってよいが
trust root にはしない。

**必須の追加条件 (レンズ A の指摘)。** 捕捉 commit `H` は **authority record 自身を含まない**
commit でなければならない (非自己参照 topology)。これを書かないと hash の自己参照が成立する。

**成果物影響:** 採らないと `origin_id` は作れても後日同じ preimage を再構成できず、proof chain が閉じない。

### 3.2 manifest 13 field の割り当て (親 brief の N6 を訂正済み)

| 分類 | 件数 | field |
|---|---|---|
| 既存規則をそのまま使える | 2 | `environment_contract_sha256` (env contract の canonical JSON)、`workload.descriptor_sha256` |
| 部品はあるが集約・解決規則が無い | 2 | `ccbench_commit_oid`、`role_bundle_sha256` |
| preimage 規則が無い (新規 artifact が要る) | 5 | `spec_content_sha256` / `axis_semantics_sha256` / `verifier_policy_sha256` / `candidate_ir.schema_ref` / `candidate_ir.canonical_emitter_sha256` / `recipient_projection_schema_sha256` (`schema_ref` は「値規則あり・内容参照なし」として細分) |
| authority が値を入れる | 4 | `authority_series_id` / `budget_policy` / `stock_certification_ref` / `structural_zero_evidence_ref` |

**訂正の要点:** `ccbench_commit_oid` は manifest が full 40-hex を要求するのに対し
`pin.CURRENT_PIN` は 7 文字 prefix であり、**そのままでは使えない**。推奨は
「authority generation が捕捉した superproject `H` の `external/ccbench` gitlink が指す full OID」
とし、実行時の submodule HEAD との完全一致と dirty 無しを要求する。short pin は不受理。

**成果物影響:** 訂正しないと authority 登録が形式検査で通らず、bootstrap が最初の 1 歩で止まる。

### 3.3 `authority_series_id` の発行主体 = 人間

**推奨。** CLI は generation の作成・検証を行えるが、series や予算値を推測・自動採番してはならない。
driver と test に発行権限を与えない。

### 3.4 予算値 — **本 wave では決めない**

D147 決定 4 に従い、値は authority record から immutable な制約として受け取り、caller に literal を
置かない。値を決めるのに要る入力は 12 項目 (科学的 cell の同一性 / `Imax` / `Qmax` / `Kmax` /
`Bmin` / 1 round の物理 replicate 数 / 自動再測定 round 上限 / early stop・失敗・tombstone の
no-refund 規則 / floor tuple の `B0`・`q_round`・`R`・`E_min` / 各種失敗をどこまで課金するか /
物理 query と evidence row の完全性規則 / codec・storage 上限)。floor 制約の形は
`F = B0 + q_round × R + E_min` と `max(2, Bmin) ≤ F ≤ Qmax` ほかを `s2-plan.md` §1.3 に置いた。

### 3.5 evidence artifact — 現候補は不採用

**現 `output/env/linux-baremetal/calibration/s8a_trigger_gating_coverage.json` は採用できない。**
根本原因は artifact の破損ではなく **producer の hardcode** (`s8a_trigger_coverage.py:63-64` が
`ENV_TAG = "linux-baremetal"` と `CLK = 2100` を literal 保持)。registry の linux-baremetal は 1800、
2100 は「TSC を実測できないときの CCBench default」と同じ値である。
**さらに clocks だけの問題ではない** — 同 artifact は short pin を保持し、登録済み `numactl` を
run command に付けず、現 producer が出す `build_admissions` を持たず、**workload cell が 8c の
ycsb-a/b/c と別 cell**である。

**推奨:** producer が `ExecutionEnvironmentContract` を引数で受け取る形へ直し、origin ごとに
stock certification と structural-zero evidence を**再測定して commit する**。authority loader は
`{path, sha256}` の形式検査だけでなく**内容を dereference して manifest と照合**する。

**未確定 (裁定が要る):** linux-baremetal での再測定が現に可能かは repo から判断できない。
可用な host も予約状態も記録されていない。**不可能なら evidence を別に選ぶか、pegasus 側で
新規に測ることになり、authority bootstrap は測定タスク待ちになる。**

---

## 4. (2) bootstrap と世代移行 — 推奨

### 4.1 D163 の起動不能の解消 (依頼の明示要求)

**推奨する形:**

- 公開 API 3 本は `create=False` のまま据え置く。**lazy-create は採らない** — runtime root は
  git-common-dir 配下で全 worktree に共有されるため、迷い込んだ 1 呼出しが共有状態を無音で作る。
- `_initialize_locked` の禁止は **boolean で解除しない**。admin loader だけが生成できる
  authorization 型を要求し、公開 API から到達可能な `create=True` / bypass を作らない。
- 解除の成立条件 = (i) authority generation と approval が捕捉 commit に exact blob として存在、
  (ii) active / revocation 連鎖が一意で未取消、(iii) authority registry が非空、
  (iv) 全 preimage / evidence closure が検証済み、(v) hash が command 引数と一致、
  (vi) successor なら親 runtime が terminal かつ state commitment 一致、
  (vii) runtime active pointer が未作成または完全一致。
- **provisioning は二相・crash-idempotent にする** — staging へ完全構築 → fsync → atomic rename。
  現行初期化は origin file を先に `O_EXCL` で作り最後に head を作るため、中途 crash 後の
  単純再試行は既存 file で失敗し冪等でない。
- `--runtime-root` / `--fixture` / `--force` / `--reset` は設けない。
- **`absent ⇒ genesis` の素朴な実装を禁じる** — 現在は runtime を消すと単に起動不能になるが、
  素朴な provisioning を入れた瞬間に「消せば新品予算」が成立する。

**成果物影響:** 解かなければ producer 結線は永久に起票できず P3 は FAIL のまま。
素朴に解くと予算束縛が最初から無効になる。

### 4.2 世代移行 = epoch router

**推奨。** authority generation ごとに runtime epoch を分け、新世代は `added_origins` だけを持ち、
origin は誕生 epoch へ恒久 route する。旧 epoch と counter は保持し、新 authority blob へ
コピー genesis しない。successor activation は親 epoch の全 origin が terminal seal であることと
state commitment の一致を要求し、open / prepared batch があれば移行を拒否する。

**却下: 累積 authority 全体を毎世代 genesis し直す案。** 旧 origin の counter reset か、
現行 event / hash model に無い imported-terminal genesis を必要とする。

**s8b からそのまま流用できるもの** = 捕捉 commit に対する純関数解決 / exact schema・path・sha /
generation と `supersedes` / 人間 approval / active pointer 連鎖 / revocation tombstone /
transition allowlist / no-active・fork・gap・revoked の fail-closed。
**origin 固有に作り直すもの** = epoch route / 世代跨ぎの cell 一意性 / 累積予算 /
runtime epoch の health を active 連鎖に含めること。
(親 brief の「新機構を発明しない」は言い過ぎだった。上記の後半は新規である。)

**必須の追加条件:** transition table は **exact な JSON Pointer 表**として書く。散文の箇条書きでは
不足である (s8b の allowlist は subtree ごと許すため、列挙を誤ると既存 origin・budget・cell identity
の改変を許してしまう)。

### 4.3 「seal-and-succeed」の解釈

**推奨:** predecessor origin は `certifiable` でも `aborted` でもよく、いずれも terminal seal と
no-refund を要求する。"succeed" は科学的成功ではなく**移行 transaction の成功**を指す。
科学的成功に限定すると、正当な abort が 1 つあるだけで authority 列全体が永久停止する。

### 4.4 公開 authority reader

**推奨:** `read_authority_binding(origin_id) -> AuthorityBinding` を足す (manifest / cell key /
budget policy / authority blob hash / generation hash / active pointer hash / birth epoch)。
authority は commit 済みの公開情報なので reader 自体は秘密を増やさない。
**`OriginSnapshot` は mutable state に限定**し、open batch は別の opaque handle
(batch id / phase / cardinality / 次の query ordinal だけ) とする。
seal 前に member commitment・候補 wire・replicate ordinal 配列・結果・constraint hash 数を返さない。
**role projection へ渡すことは schema で拒否する** (D166 決定 2 の境界)。

---

## 5. (3) 結線先と batch 形状 — 推奨

### 5.1 単一候補 × R replicate をどう扱うか (**親の暫定裁定を撤回した点**)

親は段 1 で「第 1 段として単一候補 × R replicate を結線すれば予算束縛が実体化する」と暫定裁定した。
**これは撤回する。** 予算 counter が動くのは `BatchCommitted` 受理時だけで、それを呼ぶ production
caller は存在しない。N3 が示したのは「ledger の受理規則上そういう batch が作れる」ことに留まる。

**さらにレンズ A が重要な誤導 risk を指摘した (採用)。** ledger の `cardinality` は **member row 数**
であって候補数ではない。単一候補 × R をそのまま記録すると、将来の P4 consumer が
`batch_cardinality >= 2` を見て**候補 1 点を候補 2 点以上と誤認できる**。散文で
「反 oracle 性は満たさない」と断るだけでは機械的な誤認を防げない。

**推奨:** `member_row_count` と `distinct_candidate_count` を**別 field**として記録し、
後者が 1 の記録を P4 / 軸 (iii) の証拠として**受理不能**にする。記録してよい名乗りは
**「ledger transaction batch」**までで、**「候補 batch を作った」とは記録しない。**

### 5.2 予算束縛 = pre-query reservation event (FSM 追加)

**推奨 (案 B)。** 候補に影響する最初の role 呼出しより**前に** iteration / query 予算を durable に
消費する。予約後の provider 失敗・candidate 不成立・process kill でも refund しない。
event path は `BATCH_RESERVED → CANDIDATES_COMMITTED → RESULTS_PREPARED → BATCH_SEALED`。

**却下 (単独案として): 案 A = caller の制御流だけを batch 先行にする。** coder 出力後・commit 直前に
process を kill し新しい run-root で引き直す無課金経路を塞げない (D163 決定 3(a) の反例が残る)。
**ただし案 A は案 B の補完として併用する** (代替ではない)。

**これは ledger の event 集合と受理集合を変え、D166 の現行 3-event uniform path も変えるため、
D96 の同一変更単位 (新 D + 境界テスト + consumer) の対象である。**

**未設計 (裁定が要る):** 予約後に候補が作られなかった行の terminal 表現。stock wire を偽装して
埋めてはならない。reservation 後の crash recovery と namespace も未設計である。

### 5.3 結線先

**wiring host の推奨 = 8c 自律 trial。** coder の単一 wire・workload 実行・journal・report・
completeness・Layer 3 admission が同じ driver にあり、**非認定 pilot と明示されている**ため
境界が明確である。制限を名乗りに書き込む — ycsb-a/b/c のみ、**正式 holdout H1/H2 は回せない**、
trial registry の `certifying=False` / `arm_binding="declared-only"` を変えない、cap=1 を維持。

**却下: E 段 loop を wiring host にする案。** proposal loader が auditor verdict と diff digest を
要求するため、pre-query reservation と commit-before-evaluation を実現するには proposal topology
自体の作り直しが要る。最初の production caller としては変更面が広い。

**ただし生死実験の宿主は E 段 loop が最安 (レンズ B、採用)** — E には実走可能な既存 CLI がある。
§8 の手順を参照。

### 5.4 commit-reveal

単一候補にすると「複数候補のどれを選んだか」は漏れなくなるが、**漏洩はゼロにならない** —
(i) その候補が preview / pre-audit を通過し auditor 呼出しまで進んだかの 1 bit、
(ii) critic payload が seal 前に受け取る連続値 metrics。

**推奨:** machine preview は correctness gate として維持 / auditor は常に同じ shape で呼ぶか
seal まで隔離 staging に置く / **critic を Layer 3 admission・ledger seal・proof 書き込みの後へ移す** /
proposal と raw response の公開も seal 後 / reservation で oracle query の反復回数を no-refund で束縛。

### 5.5 (4) の durable cross-reference の置き場

**推奨: producer 側の create-only sidecar** (`<run-root>/origin-proofs/<workload>.g<generation>.json`)。
ledger event に trial / report field を足す必要はない。field 案と書き込み位置 (Layer 3 admission
finalize の後、ledger seal → sidecar fsync → report 構築の順) は `s2-plan.md` §3.5。
report は既存 v2 を暗黙拡張せず **v3** にする。

**名乗りの限定 (両レンズ):** これは「必要な cross-reference」であって **proof chain ではない**。
crash recovery と namespace を閉じるまで「durable」とも名乗らない。

---

## 6. 実装しても閉じない残余 (正直な会計)

全案を実装しても、11 層のうち埋まるのは**機構面で最大 6 層**であり、第 1 層 (authority 値・発行) が
空で正の artifact path も無いため、**成果として閉じる層は 0** である。空のまま残るのは
trial registry の origin 束縛 / P7 formal consumer / Layer 3・WAL・正式材料レポート /
正の runbook・監査・crash recovery。

さらに次は**この設計では原理的に閉じない**。

- **予算 root の同一性** — 別 clone、pointer ごと全削除、履歴書換えで予算 root を作り直せる。
  git-common-dir 束縛が塞ぐのは**同一 clone 内の worktree 回避だけ**である。
  外部の append-only anchor が無い限り、同一 UID の協調削除は防げない。
- **同一 cell の再発行** — `derive_cell_key` は 4 digest だけで、blob hash 由来のため
  意味を変えない空白変更でも別 cell を作れる。世代を跨ぐ重複拒否が無い。
- **物理 query との一対一** — ledger の sealed query counter は evidence 付き member row 数であり、
  物理実行回数の証明ではない (D166 決定 5)。producer 側 `rep_evidence` は自己申告である。

---

## 7. 名乗りの上限

本設計を**実装しても**名乗ってよいのは
**「承認済み authority 世代に対する production provisioning と、非認定 8c における
single-candidate × reserved-replicate の producer liveness / 配線」**までである。

名乗ってはならない — P3 充足・部分 P3 / P4・軸 (iii) の anti-oracle / P7 formal consumer /
ledger 単体による物理 query floor の証明 / 規律 3 の還流完了 / 多世代開放 / certified 選択 /
cap 引上げ / 正式 H1・H2 通過。**D114 の cap=1 と D166 の P4 FAIL は不変。**

---

## 8. 推奨する次の一手 (段取り)

**DW-G01 に従い、一括実装ではなく最安の生死実験から始める。**

1. **有効な authority entry を 1 件と、最小の明示 provisioning だけを先に成立させる。**
   (これは §9 の (1)(2) の裁定が先に要る。)
2. **100 行以内の使い捨て wrapper**で、同一 wire・R=2 を現行 batch API へ commit し、
   既存 E driver を呼び、prepare / seal receipt を 1 個保存する。既存 CLI:
   `python3 -m campaign.p3_s4_loop_trigger_gating --preview-wire 11111` /
   `--run-iteration <scratch>/prop.json --allow-coder-derived-build`。
3. この実験が証明するのは**受理・counter 更新・seal の生死だけ**である。kill-before-commit 対策も
   科学的有効性も名乗らない。
4. 生死が取れてから、reservation FSM / report v3 / completeness / sidecar を **D96 の同一変更単位**で
   分割 wave として起票する。**1 wave にまとめない。**

---

## 9. ユーザー裁定へ返す択一 (**ここだけ読めば裁定できる**)

推奨は各項の先頭に置いた。**U-1〜U-4 は互いに独立でない** — U-1 の帰結が U-2・U-3 の形を決める。

| # | 択一 | 推奨 | 成果物影響 (採らない場合) |
|---|---|---|---|
| **U-1** | preimage の trust root を「捕捉 commit の名前付き artifact の blob bytes」にするか、コード導出にするか | **artifact bytes**。非自己参照 topology (捕捉 commit は authority record を含まない) を必須条件に付ける | コード導出は自己参照 hash になり、build / runtime 差で authority hash が揺れる |
| **U-2** | 予算 root の同一性が repo 内検査で閉じない問題をどうするか。(a) 外部 append-only anchor を導入 (b) 予算束縛を「同一 clone 内の honest caller に対する保証」と明示的に弱めて名乗る (c) 閉じるまで production provisioning を解禁しない | **(b) を推奨** — (a) は外部依存を新設し scope が跳ね上がる。(c) は P3 が永久に FAIL のままになる。(b) なら名乗りの限定という形で正直に閉じられる | 決めないと provisioning を解禁した瞬間に「予算 root を作り直せる」が成立し、D147 が止めた穴の再演になる |
| **U-3** | 世代を跨ぐ同一 cell の再発行をどう禁じるか。(a) 「ever-issued cell」台帳を series 全体で持ち全世代で重複拒否 (b) 単一 authority blob 内の重複拒否のまま (現状) | **(a)**。ただし意味等価性の裁定は人間 gate に残す (blob hash は空白変更で別 cell になるため機械だけでは閉じない) | (b) のままだと successor 世代が意味等価な cell を byte-different に再発行して使用量 0 の予算を得る |
| **U-4** | 単一候補 × R replicate の記録形。(a) `member_row_count` と `distinct_candidate_count` を別 field にし後者=1 を P4 証拠として受理不能にする (b) 現行 `cardinality` のまま散文で断る | **(a)** | (b) だと将来の P4 consumer が候補 1 点を候補 2 点以上と誤認する。D121 決定 2 が警告した恒真化そのもの |
| **U-5** | 予算束縛の実現形。(a) pre-query reservation event を FSM へ追加 (受理集合変更、D96) (b) caller の制御流だけを batch 先行に (c) 両方 | **(c)**。(b) 単独では kill-before-commit を塞げない | (b) 単独だと候補引き直しの上限が実効化しない |
| **U-6** | 結線先。(a) wiring host = 8c、生死実験の宿主 = E 段 loop の既存 CLI (b) 両方 8c (c) 両方 E | **(a)** | (b) は生死確認が全機構実装後になり DW-G01 に反する。(c) は proposal topology の作り直しを最初に背負う |
| **U-7** | evidence artifact の再測定。現候補は不採用が確定。**linux-baremetal で再測定できるか** (repo からは判断できなかった) | ユーザーの情報が要る。不可能なら (i) 別 evidence を選ぶ (ii) pegasus で新規に測る のいずれか | 決まらないと authority bootstrap が測定タスク待ちで止まる |
| **U-8** | critic を Layer 3 admission・seal の後へ移すか | **移す**。現行は seal 前に連続値 metrics を受け取っており、単一候補でも 1 bit では済まない | 移さないと commit-reveal が名乗りだけになる |
| **U-9** | 段取り。(a) §8 の生死実験を先行させ、本体は D96 の分割 wave (b) 一括実装 wave を起票 | **(a)** | (b) は受理集合変更 4 面同時で 1 wave に収まらず、両レンズが独立に NO-GO と判定した |
| **U-10** | 予算値 (Imax / Qmax / Kmax / Bmin / floor tuple) を誰がいつ決めるか。本 wave は入力 12 項目と制約の形だけを起草し**値は決めなかった** | 別途、authority 発行の裁定として決める | 値が無いと authority entry を 1 件も作れず、生死実験にも入れない |

### 併せて返す scope 外 real 所見 (実装 wave の入力)

- **A-5 相当**: full manifest が実 execution sink まで束縛されない (既知 A-2 の未処理)。
- **A-7 相当**: producer 側 `rep_evidence` は自己申告で、ledger 側から検証できない。
- **A-8 / B-8**: reservation / seal / sidecar の crash recovery と namespace が未設計。
- **A-10**: recipient schema validation は D164 型の恒真 tripwire になりうる。
- **A-11**: 既知 A-6 (別 origin の event が global CAS で post-query commit を妨害する) が未処理。
- **B-9 (疑い)**: epoch router と全 origin CAS の並行性契約が無い。

### 前 wave (198) から引き継いだ scope 外 real 所見の現状

(198) が返した 8 件 (A-2 / A-5 / A-6 / A-7 / A-8 / A-13 / B-4 / B-6) は本 wave の入力とした。
このうち **B-6 (durable cross-reference)** は裁定済みの (4) として §5.5 に取り込み、
**B-4 (8c は pilot のみ)** は §5.3 の名乗り限定に取り込んだ。残る 6 件は依然 open で、
上記の A-5 相当 / A-11 に再掲したものを含む。
