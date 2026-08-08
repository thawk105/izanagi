# [T-316] 意味 gate 設計択一 — 裁定パッケージ (ユーザー返し)

- 生成 wave: `worktree-dev-wave-t316-semantic-gate` (2026-08-09)
- 種別: 設計択一の裁定パッケージ。**実装差分ゼロ** (dev-wave 4→7→8→9、`DW-S04` の「実装しない」)。
- 逐語: `verbatim/` (段 1 brief、段 2 プラン sol、段 3 敵対 sol/luna、各プロンプト)
- 段 3 の敵対 2 レンズは**いずれも NO-GO**。ただし「設計の方向」への NO-GO ではなく
  「この前提のまま実装 wave を起票するな」への NO-GO。方向は生存し、レビューがそれを硬化させた。

---

## 0. 何を裁定するか

`tools=[]` + JSON schema では 2 脅威を止められない。

- **脅威 α (coder injection):** hole 内 1 行の `std::system`/`execl`/`std::ofstream`/無限ループが
  `DiffQuarantine` を通り build/run される (D127 背景で実測済み、`util.hh` 経由で追加 include 不要)。
- **脅威 β (auditor echo):** `auditor_gate.py` は `diff_digest` が実 working_diff と一致することしか
  照合しない。auditor が実 diff の digest を計算し `verdict="pass"` + `violations=[]` を返せば全検査を
  通る (`auditor_gate.py:148-243` を精読)。「この diff を見たか」は証明するが「安全か」は証明しない。
  = **fail-open by construction**。

起票時の 3 案: (i) coder 出力を許可識別子・enum・論理演算だけの boolean-expression AST/DSL へ落とす、
(ii) build/run を credentialless・network 無し sandbox へ置く、(iii) 両方。

**注意:** [T-316] は D127 で一度 land 済みだが、意味 gate 本体 (a)/(b)/(c) は D127 決定(1) が明示的に
「別 wave へ分離」。現状の gate = `build_admission.py` の「未分類 source を build 拒否」opt-in だけで、
D127 決定(4) が「検出器でも意味 gate でもない」と自認している。本 wave がその分離された別 wave。

---

## R1. 推奨 = 非対称 (iii)。ただし「両方」の意味を厳密化する

**全軸一律に (i)+(ii) ではない。** coder.md と各 producer role 契約から、正しい構成は次の非対称:

| 軸 | hole 文法 | 採る封じ込め | 根拠 |
|---|---|---|---|
| backoff | スカラー値 | **(i) value-IR + trusted compiler** + (ii) sandbox | 値の自力合成 (D39) は IR でも維持。α を**消す** |
| trigger-gating | 5-bit wire | **(i) 既存 `reflux_ir.py` の wire IR を最終 admission まで延長** + (ii) | 既に exact 5-bit parser + 固定 emitter が実在 (`reflux_ir.py:113-141`)。α を**消す** |
| sort-strategy | comparator コード片 (raw C++、複数行を契約上許可) | **(ii) sandbox のみ** (raw 合成を維持) | DSL 化は「合成 → 事前 allowlist 選択」に化け、Phase3 の合成能力実証 (D39) を別実験に変える |

- **(i) 全軸一律は却下。** sort 軸の comparator を typed IR に落とすと、`coder-v4-autonomous-sort` が
  研究対象にしている「複数行 comparator コードの独立合成」(role 定義 §58-134) が消え、実証点が縮む。
- **(ii) を全軸の host-security boundary** とする。ただし `run_campaign` 全体を包むのではなく
  (WAL/cache/repo/認証情報の書込み mount で境界が広がる)、untrusted source/binary を消費する
  **子 process だけ**を包む: `buildcache._run`、`pipeline._run_trace`、`calibrator.run_once`、
  preprocess (`source_digest.py:320-352`)、post-build `nm` (`buildcache.py:1026-1049`)。
- **auditor は deny-only (脅威 β の非 load-bearing 化)。** `pass` は build/sandbox/semantic の
  capability を一切発行しない。`reject`/`uncertain` のみ保守的 veto に使える。`diff_digest` は
  attribution/provenance 専用。これで echo された `pass` は独立 gate を迂回できない。
  **文言は「advisory」ではなく「mandatory deny-only veto; affirmative security credit なし」**で固定する
  (Lens A F2: 「advisory」は「任意実行」と誤読されうる)。

**脅威被覆の要約 (3 軸 × 3 案の全表は `verbatim/s2-plan.md` R5):**
- α: (i) は source で**消す**、(ii) は run-time blast radius を**絞る** (任意 C++ は残る)、非対称 (iii) は
  backoff/trigger で消し sort で絞る。
- β: どの案でも auditor 自体は直さない。deny-only 化で**非 load-bearing** にする (安全性が auditor
  判定に依存しなくなる)。
- **reward hack (規律2 本体) はどの案も塞がない。** sandbox は host 被害の話、reward hack は
  certification 整合の話。混同しない (R2 が本質)。

---

## R2. 【ユーザー裁定が要る核心の分岐】sort の reward hack を意味 gate は塞がない

段 3 の**両レンズが独立に**突いた最深の所見 (Lens A R3 = Lens B #6、いずれも blocker、親裁定 = real)。

- raw sort comparator は、たとえ sandbox 内でも、**候補が制御する trace dir / stdout** に偏った
  abort count・性能値を書ける (`pipeline.py:260-288`, `calibrator/runner.py:360-391`)。pipeline は
  その trace を検証して `verify_done.certified=true` を記録し、全 pass 後に `COMMIT` と `fitness_tps` を
  発行する (`pipeline.py:856-1087`)。
- 現行 sort runbook は非 SWO・fairness の reward hack 防壁を **auditor の静的目視に依存**している
  (`phase3-s5-sort-runbook.md:182-193`)。auditor echo (β) はこの目視を fail-open にする。
- したがって **sort 軸では (i) 却下 [synthesis 毀損] と (ii) [host 封じ込めのみ] のどちらも
  reward hack を塞がない。** これは α/β とは別レイヤの、規律2 本体の穴。

**ユーザーに択一を返す (親は非同値な択一を勝手に決めない、`DW-S04`):**

- **(R2-a) sort に typed comparator IR / effect gate を置く** — reward hack を source で構造的に狭める。
  代償: sort の raw 合成実証 (D39) を別実験 (typed-program synthesis) に変える。= 実質 sort も (i)。
- **(R2-b) 候補出力に依存しない独立 oracle を実装する** — SWO/liveness/fairness を candidate-controlled
  trace/stdout の外側で機械観測する。raw 合成は維持。代償: 新規 oracle の設計・実装コスト、
  fairness の機械観測点は現在未実装。
- **(R2-c) 残余として明示し、raw sort を「certified 対象から外す」か「reward hack 既知」と台帳に刻む** —
  実装最小。代償: sort 軸の certified 選択の信頼性に恒久的な但し書きが付く。

推奨は **(R2-b)**。理由: (R2-a) は D39 の実証点を削り、(R2-c) は成果物 (certified 選択・レポート・台帳) の
信頼境界に恒久的な穴を残す。ただし (R2-b) のコストが [T-664]/[T-184] の前提を大きく超えるなら
(R2-c) を暫定にして (R2-b) を後続 ID に切る順序もありうる。**ここは設計択一なのでユーザー裁定へ返す。**

---

## R3. 実装 wave の前提条件 (段 3 が real と裁定した blocker/must-fix)

方向は生存するが、次が揃うまで**実装 wave を起票しない** (親 provisional 裁定、攻撃を通過)。

1. **計算ノード backend の決定的計測 (blocker、Lens B #1)。** login node で bwrap/unshare/
   `--unshare-net` を実測したが (brief 既測)、build/run は qsub で計算ノードに走る。login の実測を
   計算ノードへ**転用してはならない** (F29 型)。qsub 計測 ID を作り、user/net/pid namespace 起動可、
   network connect と credential/home/agent socket が失敗、source RO・scratch 限定 write、
   process-tree timeout が子孫を残さない、CMake build/trace/`perf stat`/numactl/48-thread run が成功、
   stock/variant 双方で性能差と floor 再較正要否、を確認する (`DW-G04` の発火 artifact)。
2. **実発火する正負制御 (blocker、Lens B #2)。** `system`/network/file-write/infinite-loop の 4 種で
   DSL reject または sandbox containment を区別して期待値化し、**通る正例と落ちる負例**を fixture で
   示す。「consumer の存在は発火証拠でない」(worklog 既記録) を再演しない。恒真な gate を作らない。
3. **`DW-O13` の exact field mapping (blocker、Lens A R4)。** 現状、gate 入力に canonical field が無く
   識別子が二義化している (D75 型): `build_admission` が policy preimage と per-attempt receipt の
   二義、`hole の working_diff` と `full tracked diff` が別 domain (`source_digest.py:800-821`)、
   `CampaignSummary.execution_receipt` は環境 attestation で sandbox 実行証明ではない (`loop.py:61-134`)。
   `build_admission_policy`/`build_admission_receipt`、`hole_working_diff_sha256`/
   `full_tracked_diff_sha256`、`environment_execution_receipt`/`sandbox_stage_receipt` に分離する。
4. **policy ≠ 実行封じ込めの証明 (blocker、Lens A R1)。** `SandboxProfile` を admission/cache identity に
   入れても、cache hit 後の各 `exec` が実際にその profile で走った証明にならない。特に
   `calibrator/runner.py:440-450` は非 certify mode で injected runner を下流に渡さない (実確認済み) →
   同一 admission/cache/campaign ID のまま unsandboxed run が `certified=true` になりうる。
   **stage/binary SHA/profile/backend/attempt を束縛した sandbox execution receipt** と、
   **receipt 欠落時に `COMMIT` を拒否する WAL topology** が要る。
5. **全 untrusted materializer の閉包 (must-fix、Lens B #5)。** 「全軸 sandbox」は pipeline 外の直接
   materializer を取り残す: `s5_permutation_coverage.py` の `_build_broken` は buildcache 非経由で
   直接 build し (実確認済み)、`materializer_admission.py` は shell materializer と任意 binary path を
   **意図的に admission 外**に残している (docstring 明記)。admission 外を「非認証成果物」として明示隔離
   しない限り certified 選択・proof chain に入りうる。
6. **安全な sandbox build output copy-out (must-fix、Lens A R5)。** 現行 v2 は staging binary を
   `os.path.isfile`/通常 open で検査後、staging directory 全体を `os.rename` する。symlink 拒否が無い
   (`buildcache.py:740-783`)。untrusted build に staging を書かせるなら、allowlisted regular file だけを
   `O_NOFOLLOW`/beneath-only で読み clean host directory へ再構築する。
7. **backoff の producer/consumer 移行 (blocker、Lens B #3)。** coder 契約と loader が
   `value + implementation` を要求する (`p3_s4_loop.py:115-121,939-960`)。consumer だけ IR に狭めると
   有効な自律 backoff 候補を全拒否し、producer も raw を残すと injection 経路が残る。producer 契約と
   同時に移行する。
8. **trigger は既存機構を再利用、新 receipt を増やさない (must-fix、Lens B #7)。** canonical IR/emitter
   (`reflux_ir.py`)、source-bound binding + nonce/commitment (`trigger_gate_binding.py:136-202`)、
   pipeline 再検証 (`pipeline.py:691-715`) が既にある。並列 receipt/schema を足すと emitter・WAL・
   source binding が分岐し、valid trigger の拒否や identity 不一致を招き、[T-664] の docs 予算だけ消費する。
9. **SemanticReceipt / sandbox token は issuer 認証ではない (must-fix、Lens B #4)。** 同一 process の
   issuer を認証しない限界 (D127 決定(4)、`build_admission.py:4-13`) を DSL receipt・sandbox token にも
   docstring で明記する。receipt を「安全性の証明」として扱わない。

---

## R4. 順序の裁定 — 予算捻出を先に置く (blocker、Lens B #8)

- 現況 (実測): dev-wave reference aggregate `25,199 / 25,200 bytes`、dispatcher `9,457 / 9,500 bytes`
  (`tools/check_docs.py:247-258`)。backend 契約・stage 別 profile・失敗時規則・field mapping・deny-only
  規則を恒久文書へ置く余地が**ほぼゼロ**。
- **実装順:** [T-664] で docs 記録領域を確保 → [T-184] で対象 stage/owner を確定 (sandbox profile を
  T-316 独自 matrix に新設せず [T-184] 所有の stage policy に追加) → 計算ノード backend を実測 (R3-1) →
  正負制御 (R3-2) → 実装。順序を誤ると実装 wave が `check_docs.py` で止まる。

---

## R5. やってはいけないこと (段 3 refuted + 却下)

- **全軸一律 DSL** (R1)。sort の raw 合成実証を別実験に変える。
- **trigger に新しい汎用 receipt を新設** (R3-8)。既存 `reflux_ir.py`/`trigger_gate_binding.py` を再利用。
- **sandbox policy を identity に入れただけで「実行を封じ込めた」と主張** (R3-4)。policy ≠ enforcement。
- **SemanticReceipt/sandbox token を in-process issuer への認証境界と称する** (R3-9)。
- **auditor を「advisory」と書く** (R1)。「mandatory deny-only veto」と固定する。
- **[refuted] 「D127 決定(5) の class-cross cache hole が現存」** (Lens A F1)。後続 D136 が直接経路の
  cache/replay/選択 identity 束縛を閉じたと明記、legacy key は admission receipt SHA を含む (実確認済み)。
  ただし R3-4 の「同一 profile identity で unsandboxed run」は別問題で未閉鎖。
- **[refuted] 「login で測れたので計算ノードでも使える」** (Lens B refuted-1)。brief/plan は明示的に
  未計測とし計算ノード計測 ID を実装条件にしている。この誤りは犯していない。R3-1 は必須のまま。
- **[refuted] 「有限 DSL は必ず allowlist で合成を失う」** (Lens B refuted-2)。backoff 値も trigger の
  wire も有限だが合成は成立する。D127 の懸念は「有限性」でなく「sort の raw C++ synthesis という
  実験対象を typed-program synthesis に変える点」に限る。

---

## 総括 (ユーザーへ)

1. **推奨は非対称 (iii):** 全軸 sandbox (host boundary) + backoff/trigger 限定 DSL、sort は raw 合成維持、
   auditor は mandatory deny-only veto。全軸一律 DSL は却下 (sort の合成実証を毀損)。
2. **要ユーザー裁定 = R2 の分岐:** 意味 gate は sort の reward hack (候補が trace/stdout を偽装して
   certified/fitness を作る) を**塞がない**。(R2-a) sort に typed IR、(R2-b) 独立 oracle [推奨]、
   (R2-c) 残余として台帳明示、の択一。これは規律2 と規律5/D39 が衝突する非同値な設計択一。
3. **実装 wave は起票しない。** 前提 = 計算ノード backend 実測 ID (R3-1) + 正負制御 (R3-2) +
   D75 field mapping (R3-3) + sandbox receipt & WAL topology (R3-4) が揃うまで設計メモに留める (`DW-G04`)。
4. **順序:** [T-664] 予算捻出 → [T-184] stage matrix → 計算ノード計測 → 実装 (R4)。
