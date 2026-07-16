# 8b freeze v2 設計素材 (2026-07-16) — strict v2 verifier / R3 runner / R6 強化

**本文書は設計素材 (非正本・未承認)。裁定パッケージの裁定結果によって改訂される。正本化は
裁定後に §8 の再凍結手続き (`docs/phase3-8b-descriptor-design.md:255-267`) で行う。**

- 読者: 裁定後に strict v2 verifier / trusted prediction runner (R3) / resume 強化 (R6) を
  実装する次セッション
- 出典: 敵対相談 4 本の逐語 + 親裁定表 = `output/insights/2026-07-16_s8b-ruling-prep-consultations.md`
  (親裁定表が採用済み修正の正本)。裁定パッケージ (裁定 2/5 の提示本体・工数 U3) =
  `output/insights/2026-07-16_s8b-ruling-package.md`。第 3 波監査 A3-3〜A3-6 =
  `output/insights/2026-07-16_s8b-third-wave-audit.md`。承認状態と再開手順の正本 =
  `docs/phase3-8b-descriptor-design.md` §9 と `docs/worklog.md` 2026-07-16 (9) 追記 (再掲しない)
- 用語: 「裁定 2」= 裁定パッケージの §9 項 8 / 再走ポリシー裁定 (択 (a)/(b))、「裁定 5」=
  R5 量化の裁定 (裁定パッケージは rationale の扱いを第 5 項目に含めた 5 項目で提示 — R5 層の
  placeholder 表に対応)。本文書内の file:line はすべて worktree 現物 (基準 50b499b) と突合済み
- 前提 (絶対規律 2/3): 本文書のどの設計も correctness gate・凍結契約を緩めない。曖昧・欠測・
  検証不能は常に判定不能 (fail-closed) へ倒す

---

## T 層 — 実行トポロジー・予算台帳

### 設計

1. **manifest 単一 block 化。** schema で「blocks は正確に 1 件 + その block に予定全行
   (n=1 なら 12 行) を含有」を明記し、build/verify の双方で `len(blocks)==1` を強制する。
   現行は campaign_ids ↔ block の一対一のみ
   (`orchestrator/campaign/s8b_oracle_manifest.py:484-485`) で、schedule は複数 block を正式に
   許しテストも early/late 2 block を正例にしている
   (`orchestrator/tests/test_s8b_oracle_manifest.py:45`)。これで A3-3 の両破綻経路 (共有台帳
   path では 2 block 目が BudgetError 焼失 / block 別 path では総枠 B_total_seconds が block
   数倍に fail-open) を構造的に閉じる。
2. **台帳 identity = v2 freeze byte hash 由来。** ledger/marker の identity を freeze bytes の
   sha256 から導出し、header に generation hash・budget-policy hash・schedule hash・limits を
   固定する。open 時に検証済み freeze と完全一致を要求する。現行 header は
   schema_version/manifest_sha256/limits/spent/entries のみで freeze への束縛がなく
   (`orchestrator/campaign/s8b_budget.py:14-16`)、read の照合も manifest hash + entries 再集計
   に限られる (`orchestrator/campaign/s8b_budget.py:212-221`)。別 worktree・別 host の同名 path
   は別台帳になるため、共有不能なら実行 site を一台へ固定する。
3. **freeze-wide lease 下の事前一括 reservation → terminal 後精算。** attempt 開始前に全予定行の
   最大 bench 枠 (`extime × reps × 行数` 由来) を一括予約し、terminal 後に実測へ精算する。
   crash 時は予約を解放しない。`actual_bench_s` (実測) と `charged_bench_s / reserved_bench_s`
   (gate 用) を分離して記録する。現行は行単位 preflight
   (`orchestrator/campaign/s8b_oracle_driver.py:441-448`) → evaluate → 完了後 debit の順で、
   `completed += 1` (`orchestrator/campaign/s8b_oracle_driver.py:546`) が debit
   (`orchestrator/campaign/s8b_oracle_driver.py:561`) より先にあり、debit 拒否時も実測値が台帳に
   残らないことをテストが正例化している
   (`orchestrator/tests/test_s8b_oracle_driver.py:358-382`、台帳空 assert は `:379-382`)。
   物理消費の捕捉が debit 順序に依存する
   現行構造を、予約先行で置換する。
4. **並行 campaign は禁止、または reservation まで直列化。** 現行の排他は append_entry の
   exclusive lock 区間のみ (`orchestrator/campaign/s8b_budget.py:291-298`) で、preflight を双方が
   通過して同時消費できる。
5. **予算枯渇 = `budget_exhausted_before_attempt` で全体判定不能。** 一括予約が確保できなければ
   一行も走らせない。§5.2 は予算不足を未実施 arm ごと対称に判定不能へ倒す契約
   (`docs/phase3-8b-descriptor-design.md:209-212`) であり、行単位 skip での途中停止
   (`orchestrator/campaign/s8b_oracle_driver.py:576-583`) を再走の前提にしない。緊急増枠は
   結果閲覧後の予算変更であり禁止。
6. **CLI `--budget` override (`orchestrator/campaign/s8b_oracle_driver.py:618`) は廃止、または
   freeze が凍結した canonical path/URI との一致を要求する。**
7. **再走ポリシーは裁定 2 の択に従属する (両方の設計を下に書く)。**

### 却下対案と理由

- **「1 campaign = 1 block」制約のみ:** 現行 invariant の言い換えで A3-3 を直さない (C-C #1)。
- **台帳継続 API (block 別 path + 共有計上):** `oracle_shared=true` はリテラル検査のみで共有計上
  経路が存在せず (`orchestrator/campaign/s8b_oracle_manifest.py:430`)、cross-path 集計の正本が
  ないまま総枠 gate が fail-open する。単一 block 化の方が小さく閉じる。
- **全 attempt 報告 + 経済的拘束だけで cherry-pick 抑止:** 全件公開は透明性であって選択規則では
  ない (C-C #3)。report は block ごとに manifest 所有 campaign しか射影せず
  (`orchestrator/campaign/s8b_oracle_report.py:583-586`)、judge は追加・重複行を不一致にする
  (`orchestrator/campaign/s8b_oracle_judge.py:193-196`) ため、「悪い途中結果なら crash して新 ID
  で再走」が予算内で繰り返せる。
- **crash 消費を B_total に数えない:** 実 bench 消費の算入は §5.2 と整合する (C-C #12
  攻撃失敗欄)。数えない案は物理消費の過少計上。

### 裁定依存点

- **裁定 2 択 (a) — marker 後再走なし:** 実走前 marker 生成以後の crash は当該 freeze の実験
  全体を判定不能とする。便益 = reservation 非解放と整合し実装が最小。代償 = bench 前の初期化
  失敗 (台帳生成前 crash 等) でも全体が焼失する (C-A #6: 現行の拒否境界も既に「最初の有効 WAL
  record 以後」であり、campaign-start が台帳生成より先に書かれる —
  `orchestrator/campaign/s8b_oracle_driver.py:391` → `:396`)。さらに単一 block 化 (本層項 1)
  の下では crash 1 回 = 12 行実験全体の焼失であり、**救済経路は存在しない** — holdout 実走後は
  未既知性検索が恒久に fail する (計測開始前にのみ成立する性質、
  `orchestrator/campaign/s8b_holdout_freeze.py:595-597` の意図した fails-closed) ため、同一
  holdout での再凍結やり直しも不能。S 層は世代間で変わってよい field を floor/budget 系に
  限定するので、freeze 新世代も同一 holdout を保持し verify を通らない (裁定パッケージ裁定 2
  択 (a) と同一の帰結)。
- **裁定 2 択 (b) — §9 項 8 改訂 + 事前割当 attempt registry:** 便益 = crash 1 回で承認済み
  freeze 全体が恒久判定不能になる事態を回避する。負担 = §9 項 8
  (`docs/phase3-8b-descriptor-design.md:311-313`) の再凍結 + 承認を要し、freeze-wide の
  registry に (i) 最大再走数 K を実走前に凍結、(ii) 再走は人手判断なしの自動発火のみ、
  (iii) 最初の authorized completed attempt だけを採用、(iv) correctness-red は全 attempt 横断で
  吸収的に disqualify、(v) 複数 completed attempt = protocol violation、(vi) 実走後に失効する
  未既知性 verifier を代替する launch certificate (事前発行の再走許可証拠)、を固定する。
  両択は中立に並置し、複数 block 運用の破綻 (A3-3) と合わせた実行トポロジーの設計裁定として
  提示する (C-C #2 修正案・worklog 2026-07-16 (9) 追記の裁定順序)。
- 単一 block 化・reservation ポリシー・crash charge・contingency budget は §8 の再凍結事項
  (schedule / 予算構造の変更) であり、裁定なしに発効しない。

### 実装既定でよい部分 (C-C #11 の D2 切り分け)

reservation 機構の実装形、台帳 atomic create (`orchestrator/campaign/s8b_budget.py:153-165` の
create-only 契約は維持)、actual/charged 分離の記録形式、header hash の検証コード、改竄検出。
いずれも既承認規則を弱めない方向のみ。

---

## C 層 — status / rc 契約

### 設計

- **completed の強い定義:** 「全予定行に、report が受理できる一意の terminal outcome と、対応する
  budget terminal record (精算済み) が耐久化済み」。現行は evaluate 到達で `completed_trials` が
  debit より先に増え (`orchestrator/campaign/s8b_oracle_driver.py:546` → `:561`)、run 到達後の
  終端 status は error / budget-refused / completed の三値
  (`orchestrator/campaign/s8b_oracle_driver.py:592-593`)、gate 拒否時はこれと別に
  `status="refused"` を返す (`orchestrator/campaign/s8b_oracle_driver.py:369-370`) — 計四値の
  語彙であり、binding-refused 行は status に影響しない (A3-4: 全行 binding-refused +
  evaluate 0 回でも completed / rc 0)。新契約の全数性 (refused の扱い・rc 割当) はこの四値を
  母集合として定義する。
- **rc 優先順位の固定:** `internal-error (rc 1) > protocol_violation (rc 3) >
  budget-refused (rc 2) > completed (rc 0)`。gate-refused の rc も別途明記する。現行 CLI は
  completed 以外を一括 rc 2 (`orchestrator/campaign/s8b_oracle_driver.py:637`)、例外を rc 1
  (`:642`)、gate-check 拒否を rc 2 (`:630`) にしている。
- **全行 binding-refused → `protocol_violation` / rc 3。**
- **JSON schema の凍結 + CLI subprocess テスト:** status/rc/events の出力 schema を固定し、
  in-process テストだけでなく subprocess 起動で rc を検査する。現行の binding mismatch テストは
  events と evaluate 呼数のみ検査し campaign status を見ない
  (`orchestrator/tests/test_s8b_oracle_driver.py:322-336`)。

### 却下対案と理由

- **契約の文書化のみ (killed 所見の framing):** 下流 report/judge は fail-closed でも、rc 0 を
  成功と読む自動化が黙って前進し、当該 campaign は WAL 汚染 + resume 拒否で再実行不能のまま
  「成功」表示になる (A3-4 親裁定)。

### 裁定依存点

- protocol_violation の適用範囲 (全行 binding-refused のみか、部分 refused を含むか) は C 層
  裁定。rc の数値割当・schema・テストは既承認規則を弱めないため実装既定でよい。

---

## S 層 — freeze v2 schema・R1・A3-6

### 設計

- **世代別不変 filename + supersedes 連鎖:** 各世代を不変 filename (例:
  `holdout_freeze.v2.g<N>.json`) で保存し、`supersedes_sha256` (旧世代 bytes hash)・変更理由・
  承認者・承認時刻・承認対象を header に記録する。世代間で変わってよい field は列挙済みの
  floor/budget 系に限定し、それ以外の差分は verifier が拒否する。
- **旧世代の source verify は `frozen_at_head` の git blob へ束縛:** 現行 `_verify_source` は
  現行 worktree path の bytes を hash する
  (`orchestrator/campaign/s8b_holdout_freeze.py:550-560`、実体は `:556` の
  `_sha256(root / rel)`) ため、設計本文の更新後に旧世代を独立再検証できない。v2 では
  `git cat-file` で `frozen_at_head` 時点の blob bytes と照合する。
- **現行 generate() 契約との整合と代償:** 現行 generate は既存出力があれば raise し「再凍結は
  明示削除 + 再承認」という人手介在を機械的に強制する
  (`orchestrator/campaign/s8b_holdout_freeze.py:521-524`)。v2 の世代別 filename では path 衝突が
  起きないため、**この機械的障壁は消える** — これは代償であり隠さない。代替の「supersedes 連鎖 +
  承認記録 + 旧世代の削除しない保持」のうち、header の承認記録 (承認者・承認時刻・承認対象) は
  自己申告にすぎず、承認と世代を束縛する機械検証を設計しない限り F14 型 (宣言のみの遮断、
  `docs/failures.md:125`) になる。特に floor/budget は §8 が再凍結 + ユーザー承認を要求する
  field (`docs/phase3-8b-descriptor-design.md:265-266`) なので、「世代間で floor/budget 系の
  差分を許す」verifier が承認証拠と照合しなければ、未承認の floor/budget 差し替え世代が通る
  (fail-open)。v2 verifier は承認束縛を検証できない世代を invalid に倒す (fail-closed)。
  create-only (`open("x")`) は各世代 file にも適用。
- **selector_basis の versioned preimage 拡張:** 現行 basis は workload 条件・variant_binding・
  derangement・choice mapping の部分 hash のみ
  (`orchestrator/campaign/s8b_selector_freeze.py:306-315`)。v2 では versioned preimage として
  「4 agent cell の実送信 payload bytes/hash + catalog bytes + descriptor projection・schema +
  role + resolved model・effort + parser + execution policy + choice mapping + target binding」
  を含める。sources verifier は現在ラベル付き任意 path/hash を受理する
  (`orchestrator/campaign/s8b_selector_freeze.py:381-390`) ため、正本 path をコードまたは freeze
  で逐語固定する。世代差分として許すのは列挙済み floor/budget field だけ。
- **rep 採否規則の凍結項目化:** `unstable` / `high_variance` / 部分欠測 rep / expected reps との
  束縛を、v2 freeze の凍結項目 (数値・規則) に含める。現行は report が `tps` だけを射影し
  (`orchestrator/campaign/s8b_oracle_report.py:383-390`、row 更新 `:437-441` にも
  unstable/rep_notes なし)、judge の eligibility は bench_values 非空・有限のみ
  (`orchestrator/campaign/s8b_oracle_judge.py:90-99`)、pipeline は unstable を「呼び手が除外する」
  前提で WAL に残し (`orchestrator/campaign/pipeline.py:601-603`)、manifest は reps を正整数と
  しか制限しない (`orchestrator/campaign/s8b_oracle_manifest.py:298-300`)。この経路のままでは
  既知の不安定測定・2/5 rep 成功の trial が完全 trial と同重みで winner を決め得る (C-A #1)。
- **A3-6 = 単一 object 使い回し:** `load_verified_freeze(path, expected_hash)` を新設し、hash
  検証した bytes の strict parse 結果を単一 object として全 consumer (gate・driver・manifest・
  budget limits・perf 三軸) へ渡す。現行は driver の gate_check
  (`orchestrator/campaign/s8b_oracle_driver.py:366-370`) と run_block の再読込 (`:376`) が独立
  read で、manifest verify も freeze を再読込する
  (`orchestrator/campaign/s8b_oracle_manifest.py:592-596`) — verify-use 間の差替え窓 (TOCTOU)。

### 却下対案と理由

- **同一 filename 上書き + 旧 freeze の別所コピー:** generate の上書き禁止契約と衝突し、identity
  (どの bytes が発効中か) が曖昧になる。
- **basis の hash 強度対策 (SHA-256 衝突):** 現実的攻撃ではなく、問題は preimage の投影漏れ
  (C-C #12 攻撃失敗欄)。
- **A3-5 (verify-inconclusive の build_done 束縛) の即時修正:** 現状 judge が必ず unknown に
  倒すため実害経路なし (`orchestrator/campaign/s8b_oracle_judge.py:64-67`)。v2 実走前の強化候補
  (受理域の証拠束縛) として保持し、本設計の必須要件にはしない。

### 裁定依存点

- rep 採否規則の本体と数値、floor/budget の数値、expected reps は選択規則 = §8 の再凍結 +
  ユーザー承認事項。
- 世代 schema の field 列挙 (何が世代間可変か) も再凍結事項。
- 世代生成と承認の束縛方式 (承認記録を何と照合して「承認済み世代」と機械判定するか) は §8 の
  承認手続きに関わるため裁定依存。束縛方式が設計・裁定されるまで新世代は発効しない。

### 実装既定でよい部分

schema 骨格、単一 read object 化、atomic create、strict parse、git blob 照合コード、改竄検出。

---

## R3 層 — trusted prediction runner

### 設計

- **契約 = at-most-once + 結果不明 crash は missing 固定。** exactly-once はローカル台帳では
  実現不能: claim を call 前に書けば「claim 後・call 前 crash」でゼロ回、call 後に書けば
  「call 後・記帳前 crash」で再走時の二重呼出になる。宣言だけの遮断は F14 型
  (`docs/failures.md:125`)。現行 module は selector を実行せず
  (`orchestrator/campaign/s8b_selector_freeze.py:2-5`)、実行規律は定数宣言
  (`orchestrator/campaign/s8b_selector_freeze.py:64-70`)、provenance verifier は自己申告値の
  検査のみ (`orchestrator/campaign/s8b_selector_freeze.py:221-228`)。
- **journal 束縛:** durable claim を先行させ、canonical payload (byte 固定)・実 invocation
  receipt・raw 応答 bytes を同一 append-only journal に束縛する。claim なき応答・応答なき
  二重 claim はどちらも protocol violation。
- **claim 後 crash = 当該セル missing で恒久確定。** 再呼出しない (救済再試行は §9 項 4 の
  cherry-pick 禁止に反する)。missing セルは §9 項 5 により `choice_id=null` で凍結され、§6 の
  該当条件が判定不能へ倒れる。
- **off arm (2 セル) は invocation record を持たない static terminal record。** §9 項 1 の
  `static_default` (`docs/phase3-8b-descriptor-design.md:281-284`) を journal 上も agent 呼出と
  構造的に区別する。
- **strict parser 接続:** §9 項 5 (`docs/phase3-8b-descriptor-design.md:298-300`) の parser
  (`orchestrator/campaign/s8b_selector_output.py` 系) を runner の唯一の応答受理経路にする。
- **`selector_predictions.json` は exclusive-create + 内容 hash + commit pin + selector_basis
  束縛** (§9 項 6、`docs/phase3-8b-descriptor-design.md:301-307`)。swapped 追従の期待値
  (`on[derangement[target]].choice_id`) もこの時点で固定する。

### 却下対案と理由

- **exactly-once 保証:** 上記のとおりローカル台帳では実現不能。provider の idempotency
  key/receipt が将来使えるなら別途再設計。
- **台帳記録だけで fresh・一回を「検証済み」と主張:** F14 型の恒真ゲート。
- **missing セルの再試行・fallback:** §9 項 4/5 (承認済み) に反する。

### 裁定依存点

- 「結果不明 crash = missing 固定 (再呼出なし)」は §9 項 4 の「各独立 1 回・再試行しない」の
  解釈確定として裁定パッケージで明文化する (承認済み規則の適用確認であり新規緩和ではない)。

### 実装既定でよい部分

journal の形式、claim 機構 (O_EXCL 等)、receipt の記録項目、off arm record の schema。

---

## R6 層 — resume 強化

### 設計

- **原子的 one-shot lock の新設:** `O_CREAT|O_EXCL` による獲得のみを正とする。現行
  `campaign.lock` は identity ファイルで、`exists` 確認後に通常の `"w"` で書く非原子的実装
  (`orchestrator/campaign/wal.py:146-151`) であり、WAL 空確認から最初の `campaign-start` append
  までを覆う排他区間もない (`orchestrator/campaign/s8b_oracle_driver.py:352-359`)。
- **output-root 非依存マーカー:** 実走済みマーカーを `--output-root` の外 (freeze 正本側、例:
  `output/s8b-freeze/` 配下) に置き、identity は v2 freeze byte hash から導出する。これで
  `--output-root` 変更による resume 拒否迂回 (R6) を閉じる。マーカーのキーと scope は裁定 3 の
  トポロジーで確定し (freeze-identity 束縛 — T 層項 2)、再走可否が裁定 2 に従属: 択 (a) =
  マーカーが存在すれば当該 freeze の再走を全拒否、択 (b) = attempt registry が発行した launch
  certificate を伴う起動だけを許可。なお新世代 freeze (別 bytes) は marker では阻まれないが、
  同一 holdout の未既知性検索が恒久 fail するため救済経路にはならない (T 層裁定依存点)。
- **順序: マーカー生成 → WAL `campaign-start`。** マーカー生成直後の crash は、択 (a) では
  「実走ゼロでも再走不可 = 全体判定不能」、択 (b) では「attempt 1 消費」として registry に
  記録される。現行でも拒否境界は「最初の有効 WAL record 以後」であり、`campaign-start` が台帳
  生成より先に書かれる (`orchestrator/campaign/s8b_oracle_driver.py:391` → `:396`) ため、
  「実走後から拒否」より安全側に広いことを提示・実装の双方で明示する (C-A #6)。
- **truncated WAL 迂回の閉鎖:** 現行 `_ensure_campaign` は parse 済み record が空なら resume を
  許す (`orchestrator/campaign/s8b_oracle_driver.py:358-359`) ため、campaign-start 1 行だけの
  途中切断 WAL で迂回できる。強化 = 「WAL ファイル bytes の存在 / lock の存在 / マーカーの存在」
  の三重判定とし、parse 可能 record がゼロでも bytes が存在すれば拒否する (fail-closed)。

### 却下対案と理由

- **campaign_id 単位マーカー:** 新 `campaign_id` を名乗るだけで迂回できる (C-C #2)。
- **lock 強化のみ (マーカーなし):** 同時起動は防げても `--output-root` 変更の逐次迂回が残る。
- **holdout 条件が WAL に現れてからの拒否 (文言どおりの「実走後」):** 判定に WAL 内容の解釈を
  要し、truncated/汚染 WAL で誤許可し得る。存在ベースの拒否の方が安全側。

### 裁定依存点

- マーカーの identity/scope は裁定 3 のトポロジーで確定し、再走可否の全体は裁定 2 の択に従属。
  択 (b) は §9 項 8 の再凍結 + 承認が前提。

### 実装既定でよい部分

原子的 lock の実装、マーカー生成順序、truncated 判定、拒否時の構造化 refusal 出力。

---

## R5 層 — 結合 judge (prediction × oracle)

### 設計

- **入力:** (1) verify 済み `selector_predictions.json` (selector_basis 束縛、§9 項 6)、
  (2) oracle 観測 (report → `judge_oracle` 出力)、(3) v2 freeze の `floor_<holdout>`。
- **§6 判定表 3 条件 + 結論 (`docs/phase3-8b-descriptor-design.md:225-230`) を機械判定する:**
  1. *on/off 予測差* — choice ID のカテゴリ比較。floor は使わない (C-A #8)。
  2. *swapped 追従* — 予測凍結時に固定済みの期待値 (`on[derangement[target]].choice_id`) との
     family ID 一致 (§9 項 3)。oracle winner を見てから整合性を定義しない。
  3. *oracle floor 超* — on の予測構成と off の予測構成の oracle 実測差が当該 holdout の floor を
     超えるか。floor を使うのはこの条件のみ。
  結論 = 三条件の連言。
- **tie / indeterminate の判定不能への写像:** oracle judge の exact tie は
  `verdict="tie", winner=None` のまま overall `determinate`
  (`orchestrator/campaign/s8b_oracle_judge.py:226-234`, `:243-245`) — これは「データとして確定した
  tie」であり、§6 の「oracle 非一意 → 判定不能」への写像は結合 judge が担う (oracle judge 側は
  変更しない)。indeterminate・missing prediction (`choice_id=null`)・excluded も同様に該当条件を
  判定不能へ倒す。floor を oracle judge へ tie-break として持ち込まない
  (`orchestrator/campaign/s8b_oracle_judge.py:110-115` の契約を維持)。
- **truth table は裁定 5 の結果を埋める placeholder として構造だけ規定する:**

  | 未規定点 | 択 | 裁定 5 で充填 |
  |---|---|---|
  | swapped 成立の量化 | 両 holdout 必須 / いずれか 1 つ | (placeholder) |
  | floor 差の規則 | `oracle(on) − oracle(off) > floor` (符号付き) / 絶対差 | (placeholder — 性能改善主張なら符号付き) |
  | 同一 holdout 束縛 | on/off 予測差と floor 超を同一 holdout に要求 / 独立 | (placeholder) |
  | invalid・tie・excluded の三値伝播 | 各条件ごとの成立/不成立/判定不能への写像規則 | (placeholder) |
  | rationale の扱い | 診断材料に限定 (裁定パッケージの代替 = なし) | (placeholder — 推奨は下記の診断限定) |

- **rationale は診断材料に限定する。** 成立を真へ昇格させる証拠に使わない。parser の受理条件は
  非空文字列 + 長さ上限のみで証拠力がない
  (`orchestrator/campaign/s8b_selector_output.py:110-115`)。候補 ID の列挙は「descriptor を消費
  した証明」にならない (C-C #10)。
- **代償の明示 (承認資料に含める):** practical tie band は置かないため、floor 内の微小差でも
  point-estimate の oracle winner は一意になり得る。§6 第 3 条件が別途 floor で締める (C-A #9)。

### 却下対案と理由

- **rationale を swapped 消費証拠に数える:** free-text は検証不能で恒真化する。
- **oracle judge へ floor を注入して tie-break:** §9 項 7 の「floor は argmax の tie-break に
  使わない」に反する。

### 裁定依存点

- 裁定 5 の 5 項目全部 (上表 — rationale の扱いを含む)。truth table の充填は §8 の再凍結 +
  承認を経て発効する。

### 実装既定でよい部分

純関数 judge + JSON 出力 schema、各条件への evidence pointer (prediction hash / observations
pointer / floor 出典) の記録、三値伝播の実装 (規則自体は裁定 5 に従属)。

---

## 付録 1 — campaign lifecycle 状態遷移表

状態: S0 = 未着手 / S1 = claimed (one-shot lock + 実走済みマーカー生成済み、WAL なし) /
S2 = reserved (freeze-wide lease 下で全行一括 reservation 済み) / S3 = 実走中 (WAL 蓄積、
terminal record 未完) / S4 = terminal (completed / budget_exhausted_before_attempt /
protocol_violation / error のいずれかが耐久化済み)。

| 遷移 | 条件 | crash 時の状態 | 再起動時挙動 (択 a) | 再起動時挙動 (択 b) |
|---|---|---|---|---|
| S0 → S1 | gate 許可 + lock 原子獲得 + マーカー生成 | S1 | マーカー存在 → 再走全拒否 = 実験全体判定不能 | registry が attempt 消費を記録。K 未満なら launch certificate 発行で新 attempt |
| S1 → S2 | 全行の最大 bench 枠を一括予約成功 | S1 (予約前) / S2 (予約後、非解放) | 同上 (予約は解放しない) | 同上。残枠 < 全行最大費用なら `budget_exhausted_before_attempt` で全体判定不能 |
| S2 → S3 | `campaign-start` append (マーカー・予約より後) | S3 | WAL bytes 存在 → 拒否 (truncated でも) | 同上 + registry 記帳。再走は新 attempt としてのみ |
| S3 → S4 | 全行の一意 terminal outcome + budget terminal record 耐久化 | S3 | 拒否 (部分結果は採用しない) | 同上。correctness-red は attempt 横断で吸収 disqualify |
| S4 | — | — | 完了済み。再実行要求は拒否 | first-authorized-completed のみ採用。二つ目の completed = protocol violation |

- どの状態でも: 予約済み `reserved_bench_s` は crash で解放されない。`actual_bench_s` は
  terminal 精算でのみ確定する。
- R3 の予測セルは本表と独立の journal で管理する (claim → invocation → receipt。claim 後
  crash = missing 恒久確定)。

## 付録 2 — 受入ベクトル (実装時に通すべき検証シナリオ)

production 実装は裁定後だが、以下を通していない実装を「完成」と評価してはならない (C-D #9)。

1. **V1 — 2 block manifest 拒否:** blocks 2 件 (early/late) の manifest が build と verify の
   双方で reject される。共有台帳 path でも block 別 path でも実行に到達しない (A3-3 の再現形を
   閉じたことの確認)。
2. **V2 — 各境界 crash:** S1/S2/S3 の各境界直後を模擬 crash させ、択 (a) では再起動が全拒否 +
   全体判定不能の構造化出力、択 (b) では registry 経由の attempt 2 だけが許可され K 超過で
   拒否されること。
3. **V3 — 全行 binding-refused:** evaluate 0 回で `protocol_violation` / rc 3 になる
   (現行の completed / rc 0 — `orchestrator/campaign/s8b_oracle_driver.py:592-593`, `:637` —
   からの契約変更を subprocess テストで固定)。
4. **V4 — `--output-root` 変更拒否:** 実走済みマーカーが output-root 非依存に発火し、別
   output-root での再走が拒否される。
5. **V5 — truncated WAL 拒否:** `campaign-start` 1 行だけの途中切断 WAL (parse 可能 record 0 件)
   でも bytes 存在で resume が拒否される。
6. **V6 — verify-use 間差替え検出:** gate 検証後・使用前に freeze bytes を差し替えても、単一
   object 使い回し (`load_verified_freeze`) により差替え後の値が一切使われない (budget limits・
   perf 三軸を含む)。
7. **V7 — R3 二重呼出拒否 + claim 後 crash = missing:** 同一セルへの二度目の claim が拒否され、
   claim 後 crash からの再起動が当該セルを missing のまま恒久確定して再呼出しない (journal に
   invocation record が 1 件も増えないこと)。
8. **V8 — 一括予約不能:** 残枠が全行最大費用未満のとき、一行も走らず
   `budget_exhausted_before_attempt` の terminal record が耐久化される。
9. **V9 — R5 集約統計の変異 kill (C-A #3):** 非対称 fixture (median と mean が乖離する
   rep/trial 値配置) で trial_medians・最終集約値・winner を数値 assert し、median→mean 変異で
   FAIL することを確認する。現行の対称 fixture では mean 置換でも unique-best / exact-tie の
   両テストが PASS する false-green を親が in-process 変異で再現済み (親裁定表 C-A #3)。

## 付録 3 — F3 admission 強化 (binary path 非依存の競合検知)

floor 実測の前提作業であり、env 選択 (cygnus / Pegasus) に関わらず必要 (C-B #6 親裁定)。

- **現行の穴:** 競合検知 `competing_bench_pids`
  (`orchestrator/calibrator/runner.py:60-75`) の pgrep パターンは
  `r"build-variants/.*ycsb_.*\.exe"` (`orchestrator/calibrator/runner.py:71`) で従来ビルド木に
  固定されている。8b oracle は build cache を `output_root / "s8b-build-cache"` に置く
  (`orchestrator/campaign/s8b_oracle_driver.py:466`) ため、8b 由来の孤児 bench はこのゲートを
  素通りする。between-run floor driver の per-session admission も同関数
  (`orchestrator/campaign/between_run_floor.py:85-91` の `_assert_single_tenant`) に依存して
  おり、同じ穴を共有する。F3 の恒久対応 (`docs/failures.md:36-40`、memory
  `verify-single-tenant-before-measuring`) が現行コードで満たされていない。
- **強化案 (実装既定でよい — 検知を広げる方向のみ):**
  1. パターンを binary path 非依存へ: `ycsb_.*\.exe` をパス接頭辞なしで検索し、自プロセスの
     子孫 PID を除外して「他者/孤児」だけを残す。
  2. 検知結果は fails-closed: 競合 PID が非空なら計測に入らない (現行契約の維持・強化)。
  3. C-B #6 採用分の併設: scheduler 上の同居確認 (ノード上での実施)、load/frequency の記録、
     `settled=False` の測定値を採用しない、block 単位の破棄・再投入規則。
- **裁定依存点:** なし (正しさ・単独性ゲートを強める方向のみ。数値閾値は floor protocol の
  再凍結と同時に固定)。

## 付録 4 — 対象別 floor 専用 driver と budget 数値の再凍結手順 (C-B #2 / #4)

親裁定表 C-B #2 / #4 の処置「設計素材へ」を本付録が受ける。数値そのものは §8 の再凍結 +
ユーザー承認事項であり、ここでは手順だけを固定する。工数比較 (U3) は裁定パッケージ側が正本。

- **対象別 floor 専用 driver (C-B #2):** 8b の対象別 floor は rr80 / rr20 の 2 holdout 分
  (`output/s8b-freeze/holdout_freeze.json:40`, `:307`)。既存 between-run 資産と現行 driver の
  `POINTS` は rr5 / rr50 / rr95 の 3 点固定
  (`orchestrator/campaign/between_run_floor.py:57-60`) で、8b の対象を一つも測っていない —
  既存資産は動作点の参考まで。v2 では **holdout freeze から target manifest を生成する専用
  driver** を実装する。`POINTS` の手編集と既存 3 点値のコピー (流用) は禁止。floor protocol
  (対象集合・n・reps・時間分離 block・別 process/build の扱い・算出式・cross-block 統合 —
  C-B #3) の凍結が実測に先行する。
- **budget 数値の再凍結手順 (C-B #4):** budget は floor から自動では出ない。§5.2 の予算契約
  (`docs/phase3-8b-descriptor-design.md:209-212`) が要求する `B_arm_seconds` /
  `B_total_seconds` は、(i) bench 上限の事前導出式 (`n × reps × extime × max_rounds` 由来) で
  導出し、(ii) 既知 workload の full-pipeline pilot (build/verify/bench/timeout を含む wall
  time) で校正して数値化する。T 層項 3 の一括 reservation 枠 (`extime × reps × 行数`) はこの
  導出値を消費する機構であり、導出手順の代替ではない。
- **裁定依存点:** floor protocol の本体・数値、`B_arm_seconds` / `B_total_seconds` の数値、
  pilot の対象 workload は §8 の再凍結 + ユーザー承認事項。driver の実装形・manifest 生成
  コードは実装既定でよい。
