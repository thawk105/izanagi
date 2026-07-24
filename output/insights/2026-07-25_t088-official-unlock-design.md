# [T-088] official mode 解禁の設計パッケージ (第 1 設計段) — 2026-07-25

**射程**: `orchestrator/campaign/s8b_floor_campaign.py` の `_assert_official_permitted` (S8b floor campaign
の official mode 無条件拒否) を解除するための条件・形・順序を**設計として確定**し、ユーザー裁定へ返す。
**本 wave はコード・テスト・凍結成果物を 1 byte も変更していない** (D75 [T-080] と同じ「第 1 設計段
パッケージ」型)。実装差分がないため変異 matrix と受入全走は対象外である。

**裁定根拠**: worklog 2026-07-24 (6)「(2a) official guard 解除は設計判断として確定する方向を**承認**」
→ [T-088] 採番。「設計は future dev-wave、**実装前に防壁変更として再確認**」。

**検証プロセス**: 親 brief (P1..P8 を攻撃対象として明記 + 前提実測) → codex プラン起草 (read-only, max)
→ 敵対相談 2 本 並列 (read-only, max。レンズ A = 正しさ境界・防壁の破れ / レンズ B = 実在性・scope 肥大・
[T-083] freeze 整合) → 親裁定。**両レンズとも NO-GO** (A: BLOCKER 7 + MUST 5、B: BLOCKER 5 + MUST 4 +
SHOULD 2)。親の provisional 裁定 8 件のうち **4 件が否定された** (P2/P5/P6/P8)。逐語 =
`2026-07-25_t088-official-unlock-verbatim.md`。

---

## 1. 最重要の事実訂正 — R receipt は既に発行済みである

worklog 末尾 (2026-07-25 (1)) の「次の一手」2〜4 は **[T-068]/[T-077]/[T-078] を「R receipt 発行後」
「承認済 (発行待ち)」として繰り越している**。これは stale である。レンズ B が指摘 (B-01) し、親が git で確定した。

| 証拠 | 内容 |
|---|---|
| `8bec195d096f852fd2b47070aa18a3b151613f0a` | **ユーザー本人の commit** (`AI-Agent: none`)。件名「[T-080] activate legacy freeze migration receipt」。変更は `output/t080-migration/legacy-freeze-repin.receipt.json` 1 ファイル (+1 行) のみ |
| ancestry | `8bec195` は /rulings 記録 commit `0c03609` の**祖先**。つまり「発行待ち」と記録した時点で既に発行されていた |
| `c8cbd17` | ユーザーの「[protocol] freeze floor protocol (s8b-floor-protocol/v2)」commit |
| 機械証明 | `freeze_protocol` は T-080 receipt が `state == "active-valid"` かつ refusals 空でなければ **拒否する** (`s8b_floor_campaign.py:537-553`)。protocol 実凍結が成立している事実そのものが receipt 発効の機械証明である |
| worklog 自身 | 2026-07-24 (1) が「**R commit (8bec195) の legacy freeze migration receipt 発効**で赤化した 11 node を復旧」と既に記録している |

**帰結**: [T-068] (superseded 確定)・[T-077] (design_source 再 pin + generator M 化)・[T-078] (S2-4.6 承認
fixture) は **blocker が解消済みで、かつユーザー承認済み**である。次の一手の再編を要する (下記 §6)。

**なぜ見落とされたか (再発防止の材料)**: /rulings の収集が「裁定待ち項目の列挙」だけを行い、
**その項目が既に実行済みでないかを一次資料 (git) で照合しなかった**。承認と実行の状態を別々に追跡する
必要がある。→ `docs/failures.md` 候補 (§8)。

---

## 2. 所見の裁定 (real / refuted・採否・scope)

### レンズ A (正しさ境界・防壁の破れ)

| ID | 判定 | 裁定 |
|---|---|---|
| **A-01** 受理集合は空集合→非空へ厳密拡大。「拒否削除でないから規律 2 を緩めない」は偽 | **real・採用** | 事実として正しい。ただし「規律 2 を文字どおり適用するなら T-088 が NO-GO」という結論は**取らない** — 規律 2 は「verifier が anomaly を検出したら reject」という correctness gate の不可侵性であり、official mode の activation lock は種類が違う。**しかし「この guard を correctness gate ではなく activation lock と再分類する」こと自体が防壁の性格変更であり、ユーザー裁定事項**。→ **U-1** |
| **A-02** private core への `_official_permit` 引数は契約が禁じる「引数 bypass 面」 | **real・採用** | proof object を core へ渡す案を**却下**。core 自身が固定 path の raw bytes と topology を再検証する形にする。AST test は「repo 内の偶発的 constructor 増加の防止」であり security claim に数えない |
| **A-03** `script_sha256` は env 自己申告ゆえ wrapper hash 照合は恒真化可能 | **real・親が独立確認・採用** | `reservation.py:118-126` の `_ENV_FIELDS` が `IZANAGI_RESERVATION_SCRIPT_SHA256` から読み、検証は 64 桁 hex 形式のみ (`:52-53`)。**環境変数同士の一致を authorization gate に数えない**を設計制約とする |
| **A-04** certificate へ permit 内 authorization をコピーし同 permit を expected にするのは自己整合 gate | **real・採用** | 既存 strict certificate が「独立二回目 scan を expected にする」恒真回避を採っている (D80(4)) のと同型の扱いを要求する |
| **A-05** `AI-Agent: none` は人間性を証明しない → `HumanLaunchAuthorization` は名称過大 | **real・採用** | ただし**新事実ではない**。floor protocol 裁定 F6 本文が既に「規約 attestation であり人間性の暗号学的証明ではない。AI が `none` commit を作れば偽装可能」と明記している (`2026-07-16_s8b-floor-protocol-package.md`「代償・限界」)。→ 親の (P8) を**否定**し、命名と防壁計上を改める |
| **A-06** §5-(viii)/B-005 の最終受諾が receipt に未束縛 | **partial (受諾未了は refuted、機械未束縛は real)** | **受諾は済んでいる** — worklog 2026-07-24 (6)「(2b) §5-(viii) 残存限界一覧を**受諾** (floor 実測前 gate クリア)」。A-06 が引いた `2026-07-24_e2e-real-seal.md`「B-005 未裁定」は (6) より前の記述で stale。**残る real 部分** = 「受諾した版を機械束縛していない」→ 設計メモへ (blocker にしない) |
| **A-07** activation に certificate-only commit C が無く、`HEAD==A` 寿命が C 作成で失効 | **real・射程限定して採用** | `s8b_ratified_freeze.py:3047-3053` に `cert C が G の厳密祖先でない` 拒否が実在することを親が確認。ただし receipt は launch 時に消費されるので**初回実行そのものは成立する**。失効が効くのは **C 作成後の retry / resume**。この限定つきで設計へ反映 |
| **A-08** 再利用寿命・path collision・`H` の二義化 | real・採用 | B-02/B-06 と合流 |
| **A-09** `VerifiedFreeze.document` が mutable dict | real・採用 (設計メモ) | 本 wave の scope 外だが real。→ §7 |
| **A-10** certificate v2 一律 bump は既存 resume/ratified の受理集合を狭める | real・採用 | B-05 と合流。**certificate v2 は延期**する裁定により消滅 |
| **A-11** CLI 二重評価は TOCTOU 増、claim 永続化後の失敗が台帳を消費 | real・採用 | 親の (P5) を**否定**。単一 admission predicate へ |
| **A-12** 免除集合 (`scan_exempt`) と束縛集合 (`all_bound`) の混同 | real・採用 (延期先で有効) | selector helper 抽出自体を延期するため、延期先の設計制約として記録 |

### レンズ B (実在性・scope・[T-083] 整合)

| ID | 判定 | 裁定 |
|---|---|---|
| **B-01** R receipt は既発行 | **real・親が git で確定・採用** | §1。本 wave の最重要成果 |
| **B-02** `<artifact_bundle_sha256>.json` は再発行不能 (コード/wrapper 修正で bundle hash 不変なのに内容が変わる) | **real・採用** | 論理的帰結として正しい。filename の preimage 設計は延期先の制約とする |
| **B-03** gate 入力の実在性 — protocol/prediction/journal は実在、wrapper path・実行 revision・authorization・certificate authorization field は**不存在** | **real・採用** | プランの「実在未確認 field はない」を**否定**。DW-O13 違反を回避する |
| **B-04** 不存在 wrapper に依存する機構の同時実装は **DW-G04 違反** | **real・採用 (決定的)** | 「条件付き機能は、発火条件を満たす既存 artifact path または計測 ID を書ける場合だけ実装する。書けなければ設計メモに留める」。floor 専用 wrapper は `tools/pegasus/README.md` が次 wave と明記。→ **wrapper-only wave を先行**させる |
| **B-05** selector helper 抽出・certificate v2・ratified・resume・private permit/AST・完全 negative matrix は初回 cycle 前 blocker でない ([T-083] freeze と lineage 先送りの逆流) | **real・採用 (決定的)** | 規律 5 (盛らない) + DW-G02。**プランの新機構の大半を延期**する |
| **B-06** 提案 receipt は campaign authorization でなく revision activation | real・採用 | 親の (P6) を**否定** |
| **B-07** 「新規 exact schema」が exact でない (literal・canonical preimage・順序・重複・時刻文法が未定義) | real・採用 | schema を書くなら延期先で完全定義する |
| **B-08** `HEAD==A` 一回検査は実行 revision 束縛にならない | real・採用 | 既存 `certify_calibration.sh` が job 開始時に source commit・clean・script bytes を再照合する先例を採る |
| **B-09** `authorization` は repo 内で既に三義 | real・採用 | 専用 namespace を使う。generic な `authorization` を新設しない |
| **B-10** P5 の二重拒否は現実と違い、二重実行に安全上の意味がない | real・採用 | A-11 と合流 |
| **B-11** 文書更新先が誤り (`phase3.md:53` は歴史記述、過去 worklog は凍結) | **real・採用** | 訂正すべきは **phase3 の現行チェックポイント**と **worklog の新規末尾エントリ**。過去エントリは書き換えない |

---

## 3. 親の provisional 裁定の帰結

| | 判定 | 根拠 |
|---|---|---|
| (P1) 本 wave は実装しない | **支持 (両レンズ)** → **確定** | 段 4 で「実装しない」と裁定。`4→7→8→9` |
| (P2) 「§8 未裁定」は古い誤記 → 「発効条件未充足」へ組み替え | **否定 (両レンズ)** | guard は裁定後に**意図して残された dormant 防壁**であり、typo 修正として外せない。さらに floor protocol の裁定 F6 は「**v2 generation の承認方式**」であって launch authorization ではないため、「§8 = 承認束縛 = 裁定済み」への一括置換は**別機構の混同**になる |
| (P3) 実成果物 field への束縛を機械検査する述語 | **原則支持・現案は不充足** | allowlist は関数戻り値、wrapper hash は env 自己申告、wrapper/revision/authorization は不存在 (A-02/A-03/B-03) |
| (P4) 衝突する F 番号を診断文に使わない | **支持 (両レンズ)** | `§8` は 3 系統、`F6` は 2 系統で別義 |
| (P5) core と CLI の二重拒否で同一述語を共有 | **否定 (両レンズ)** | 現行の二重拒否は CLI + public wrapper。二回評価は TOCTOU 面を増やすだけ。**単一 admission predicate + CLI は例外を rc=2 へ翻訳するだけ**へ改める |
| (P6) campaign ごとに条件を再検査 | **否定 (B) / 未達 (A)** | 提案 receipt は campaign 固有 field を持たず、同じ HEAD 上で無制限に再利用できる = revision activation |
| (P7) 循環の疑い (解禁条件を ratified active にすると循環) | **支持 (両レンズ + 一次資料)** → **確定** | 発効順序 (F6 本文 D6″) の step 3 で AI が候補世代を生成し、その入力が floor official 実測。`s8b_ratified_freeze.py:2228-2251` が floor result に `mode=="official"` と `eligible_for_refreeze is True` を要求する |
| (P8) 条件検査 + 人間 receipt の二重 | **否定 (両レンズ)** | `AI-Agent: none` は人間証明でないため第二防壁に数えられない (A-05)。かつ「別 Git launch receipt が必要」という欠陥実例は示されていない (B-08) |

---

## 4. 設計 v2 (最小案) — ユーザー裁定を経てから実装する

**方針**: 大機構を先に建てない。**不存在の前提 (PBS wrapper) を先に実在させ**、その後に最小の
admission 配線だけを行う。lineage 強化は既裁定どおり oracle 結線 wave へ残す。

### 段階
1. **wrapper-only wave (先行、独立)** — `tools/pegasus/` に floor 専用 submit script と job script を、
   既存 `submit_certify.sh` / `certify_calibration.sh` と**同型**で作る。job 冒頭で source commit・
   clean 状態・script blob を再照合し、reservation 環境変数を export する既存作法を踏襲する。
   完了判定 = 実 wrapper path と実 submit artifact ID が 1 度生成・確認できること (DW-G04 の発火条件充足)。
2. **job-scoped submission artifact** — wrapper が create-only で
   `{source_commit, job_script_path, job_script_sha256, job_id, nonce, submitted_at}` を記録する。
   **人間の明示 `qsub` そのものを launch authorization とする**。
3. **単一 admission predicate へ置換** — `_assert_official_permitted` の無条件拒否を、
   **一度だけ実行する** admission predicate へ変える。public wrapper の 13 seam 拒否は順序ごと維持する。
   predicate は既存 `_floor_preflight_freeze_allowlist` の結果 + submission artifact + HEAD/clean +
   **実 wrapper blob** を検証し、検証済み snapshot を同一呼出し内で使う。
4. **CLI** — 固定拒否 (`:3434-3441`) を削除し、public 呼出しから返る admission error を rc=2 へ翻訳するだけ。
   predicate を事前重複実行しない。
5. **不変**: launch certificate v1、ratified verifier、resume schema は**変更しない**。

### 設計制約 (恒真化の禁止 — A-03/A-04 由来)
- **環境変数同士の一致を authorization gate に数えない。** wrapper hash は scheduler が返す job record /
  spool された script bytes / committed blob を独立取得して照合する。
- **expected を自分の出力から作らない。** certificate へ authorization を載せるなら、発行直前に独立再読した
  bytes から expected を構成する (D80(4) の「独立二回 scan」と同型)。
- **gate 入力は実在する field だけ。** 不存在の field に依存する gate は書かない (DW-O13)。
- **`authorization` という generic 名を新設しない。** repo 内で既に三義ある (B-09)。

---

## 5. ユーザー裁定が要る項目

- **U-1 (前提・最重要)**: `_assert_official_permitted` を「正しさゲート」ではなく
  **期限付き activation lock** と再分類してよいか。
  解禁は official 受理集合を**空集合から非空へ厳密に拡大する**行為である (A-01)。
  規律 2 を文字どおり読むなら解禁自体が禁止に見えるため、**再分類の明示承認なしに以降へ進まない**。
  - 影響: 承認しなければ [T-088] 以降は全て停止し、[T-011] floor 実測は発火しない。
- **U-2 (順序)**: 「wrapper-only wave を先行 → 実 artifact 確認 → admission 再裁定」の順序を採るか。
  - (a) **推奨**: 採る (DW-G04・規律 5・[T-083] freeze と整合)。
  - (b) プランどおり wrapper と admission 機構を同時実装する (DW-G04 違反、phantom gate の危険)。
- **U-3 (人間 authorize の形)**:
  - (a) **推奨**: 明示 `qsub` + job-scoped submission artifact を authorization とする (新 Git receipt なし)。
  - (b) 別 Git launch receipt を追加する。`AI-Agent: none` は人間証明でないため防壁増強でなく規約 attestation
    にとどまる (A-05)。採るなら名称を「人間承認」と呼ばず、schema を完全定義する (B-07) 必要がある。
  - (c) allowlist 公開鍵署名。最強だが鍵管理が増える。
- **U-4 (延期の確認)**: selector exact helper 抽出 / launch certificate v2 / ratified verifier 追加 /
  resume authorization / private permit 型 + AST pin / 完全 negative matrix / reason-code 体系一般化 を
  **1 cycle 後または oracle 結線 wave へ延期**してよいか (推奨: 延期)。
- **U-5 (次の一手の再編)**: §1 の R receipt 既発行を受け、[T-068]/[T-077]/[T-078] を
  「発行待ち」から「**着手可能・承認済み**」へ繰り上げてよいか (推奨: 繰り上げ)。

---

## 6. 延期・scope 外だが real な所見

- **A-09**: `VerifiedFreeze.document` は mutable `dict` のまま返る (`s8b_freeze_io.py:30-38`)。
  `RatifiedFreeze` は再帰的に不変化する (`s8b_ratified_freeze.py:717-733`) のと非対称。
  result が正しい v1 SHA を掲げながら異なる cell schedule の計測値を保持し得る。→ **新規 T 番号候補**。
- **A-06 残余**: 受諾済みの §5-(viii) 残存限界一覧の**版**が機械束縛されていない。
- **A-12**: `scan_exempt` と `all_bound` の型分離。延期先 (selector helper 抽出) の設計制約。
- **B-02/B-07**: authorization record を作る場合の filename preimage と exact schema の完全定義。
- **プラン G**: `docs/phase3.md` の現行チェックポイントと worklog 末尾の R 状態が stale (§1 で訂正)。
- **プラン G**: `2026-07-24_e2e-real-seal.md` の受入欄が未反映 placeholder のまま。文書だけを緑の根拠にしない。

---

## 7. 正直な限界

- **実測できなかったこと**: DW-S01 は「コード変更を伴う裁定前提は monkeypatch で代用せず、実際にファイルを
  編集して測り、直後に復元する」と定める。guard の `raise` を実削除する編集自体は成功した
  (`git diff --stat` = 1 file, 1 insertion / 5 deletions、意図した単一変異のみ) が、
  **guard 無効状態でのテスト実行を harness の permission classifier が拒否した**。
  clean tree では同じコマンドが通る (復元後 `-k official` = 29 passed) ため環境不良ではなく、
  「production 拒否を外した状態で実行する」ことに対する安全判断である。DW-O19 手順で即復元し、
  `git status` clean と guard 本文の commit 済み内容一致を確認した。
- **したがって「解除後に実際に何が起きるか」の実測値は本設計の根拠に含まれない。** 根拠は
  (i) 静的読解 と (ii) 既存テスト (= 模擬) である。
- **模擬と実差分の差**: `_official_test_seam` (`test_s8b_floor_campaign.py:612-620`) は guard を潰し
  clean scan digest も固定 stub に差し替える。ただしレンズ A の訂正どおり、real-seal E2E
  (`:3005-3505`) は private core を直接呼びつつ production preflight・二重 clean scan・durable policy は
  実物を通す (`:3282-3339`, `:3384-3403`)。**build と throughput は fake** (`:3355-3372`) で、
  物理 Pegasus attestation でもない。よって「**guard を通る public production 経路は一度も実行されていない**」
  という限定は成立する。
- ベースライン計測: `pytest orchestrator/tests/test_s8b_floor_campaign.py` = 197 passed / 2 skipped (25.03s)。
  本 wave はコード差分がないため、これは前提実測であって受入結果ではない。
- 相談子は read-only sandbox のため pytest を実行していない。子の非実走を緑と記録していない。
