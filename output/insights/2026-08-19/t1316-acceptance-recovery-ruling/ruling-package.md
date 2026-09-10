# 裁定パッケージ草稿 — 受入 lease 取得後・受入 command 投入前に落ちる型からの回復経路 ([T-1316])

2026-08-19 00:11 JST 作成。wave `dev-wave-t1316-acceptance-recovery-ruling`、
base main `a31832d9`。本 wave は**実装しない** — 択一整理と推奨案の提示だけが scope。
一次資料は同 directory `verbatim/` (brief・段 2 plan・段 3 レンズ A/B)。
段 3 の 2 レンズ (正しさ境界 / 実効性・網羅性) が計 11 件の所見を出し、親はそのうち
9 件を real、2 件を refuted と裁定した (内訳は各節)。refuted はいずれも
「P1 が既存の正当な fail-closed 経路を壊す」という懸念で、コード・テストで反証されている。

---

## R-A. `merge_message_file` 供給経路の欠落 (核心問題)

### 事実

- **F365 は claim 前の経路 (`preclaim-behind-count`) だけを塞いだ。** main が既に進んでいて
  `--merge-message-file` 未指定なら claim せず拒否する (`tools/dev_wave_wait.py:3734-3747`)。
  これは有効な恒久対応で、t1180 が実際に踏んだ「省略に気づかず lease を消費する」型は
  この修正**後**は claim 前に止まる。
- **claim 後 (queue 待ちの間に main が進む場合) の再計測には回復経路が無い。**
  `behind` を postclaim で再測定し (`tools/dev_wave_wait.py:3789`)、`behind > 0` かつ
  `merge_message_file is None` (または検証失敗) なら `_StageFailure("merge-message")`
  (`3793-3797`)。**これが T-1316 の未解決点。**
- **この失敗は D486 の再試行条件を構造的に満たせない。** 再試行は「受入 command (pytest) が
  判定を 1 つも産まずに戻った」ことの 6 条件肯定的証拠が揃ったときだけ発火する
  (`docs/decisions.md:20259-20272`)。`merge-message` 失敗は受入 command 自体を 1 度も
  起動していないため `retry_evidence_reason` が設定されず (`tools/dev_wave_wait.py:4186-4192`)、
  `retry=False` のまま `_cleanup_lifecycle` が lease を解放する (`4255-4261`)。
  既存 pin テスト `test_postclaim_merge_message_requirement_still_catches_main_race`
  (`orchestrator/tests/test_dev_wave_wait.py:6736-6745`) が
  `(claims, submissions, releases) == (1, 0, 1)` として、この「claim はしたが受入 command は
  1 度も投入されず lease だけ失う」挙動を現状の意図された仕様として固定している。
  待ち札は release 後の再 claim で新しい到着時刻になり先着順を失う
  (`docs/decisions.md:20297-20299`、F365 実測 = t1180 で 52 分喪失)。
- **queue 待ちは長い。** `docs/pegasus-runbook.md:944-947` の実測では `--max-wait-seconds`
  既定 7,200 秒を使い切って `claim-timeout` になった例がある。D253 は
  「待ち時間の上界を保証しない」(`docs/decisions.md:11668-11670`)。**race window の長さは
  数十分〜2 時間規模になりうる。**
- **既存 runbook には近い規約が既にあるが、対象が狭い。**
  `docs/pegasus-runbook.md:921-922`「`--merge-message-file` は待機を始める前に用意しておく。
  behind が判明した時点で必須になり」は**投入時点で behind が判明している場合**の
  preclaim 相当の規約であり、**postclaim で新たに behind になる race を対象にしていない**。
  対話 manager 向けの同種規約があってもなお t1180 で省略が発生した実績がある
  (`docs/failures.md:9277-9280`)。**運用規約は prompt 規律であり機械強制されない**
  (`CLAUDE.md` 冒頭の hooks 非強制の明記、`docs/failures.md:9307-9312` — F365 自身が
  「prompt 規律では 1 セッションしか直らない」ため受入経路へ機械関門を入れたと記録している)。
- **message 内容は「main に完全非依存」ではない。** `_message_has_ai_agent` /
  `_validated_message_copy` 自体は非空 + `AI-Agent:` 行の存在しか見ない
  (`tools/dev_wave_wait.py:2891-2909`) が、merge 実行後に走る
  `check_ai_provenance.py --message-file` (`tools/dev_wave_wait.py:3816-3825`) は
  prospective merge parents から**両親と結果が異なる path** (3 方向結合が実際に起きた path、
  `tools/check_ai_provenance.py:1344-1349`) を計算し、そこに実装面 path があれば
  Codex `role=author` trailer (または有効な waiver) を要求する
  (`validate_implementation_author`, `tools/check_ai_provenance.py:1231-1261`)。
  この経路は過去に実際に発火し known-violation として登録済みである
  (`_DW8C_ACCEPTANCE_MERGE_NOTE`, `tools/check_ai_provenance.py:213-219`)。
  **ただしこれは message 供給の有無とは独立した別リスクであり、R-B へ切り出す
  (常時供給でも条件付き供給でも同じ経路を通るため、P1/P2 いずれを採っても増減しない)。**
- **`--merge-message-file` は現在 optional で、attempt 間で再取得されない。**
  CLI 定義 (`tools/dev_wave_wait.py:1607-1614`)、`run_acceptance` の attempt ループ
  (`4323-4338`) は同じ `Path | None` を使い回す。

### 効き

直さない場合、この型を踏むたびに certified 選択・材料レポート・台帳の確定が観測範囲で
40〜70 分遅れ続ける (task 引数の記述、F365 実測の待ち直しコストに基づく)。
queue 待ちが数十分〜2 時間に及びうる現状の運用では、**「投入時点で behind かどうか」で
message file の要否を決める設計は、待ち時間が長いほど当たらなくなる。**

### 択一

構造上 2 つの軸があるが、本 wave (T-1316) は軸 1 だけを scope とする。軸 2 は R-B で
scope 外として明記する。

- 軸 1 (本 wave の scope): message input の供給方法 — P1 / P2 / P3 / 現状維持
- 軸 2 (scope 外、R-B): pre-command failure 全般の lease 処理 (D486 の fail-closed 境界を
  拡張するか否か)

1. **P1 — 運用規約のみ (コード変更ゼロ)**

   manager は `tools/dev_wave_wait.py acceptance` を投入する前に、**投入時点で main が
   behind かどうかに関わらず**、有効な merge-message-file (完全な `AI-Agent:` trailer 付き、
   `docs/ai-provenance.md:9-31` 準拠) を repo 外へ用意し、`--merge-message-file` を
   常時渡す。process 終了まで削除・書換えしない。
   `docs/dev-wave/operations.md` と `docs/pegasus-runbook.md:921-922` の規約を
   「behind の有無に関わらず全 invocation で」に是正する。

   **効き:** 有効な message file が process 終了まで保持されて全 invocation に渡るなら、
   `merge_message_file is None` による `merge-message` 分岐 (`3789-3798`) は到達不能になる
   (段 3 の 2 レンズが独立に検証し反証できなかった)。`behind == 0` なら file は使われず
   余計な merge も発生しない。

   **限界 (段 3 で確定):** (i) 遵守されて初めて効く運用規約であり、機械強制されない —
   既存の近い規約があっても omission は再発した実績がある (最も深刻な所見、レンズ B #1)。
   (ii) D486 の retry (attempt 2) が発火した後、attempt 2 の self-claim 前に main が
   **さらに**進む複合レースは閉じない — self-claim は新しく測った main_sha と lease 記録の
   不一致で `claim-self-unverified` になりうる (`tools/dev_wave_wait.py:2875-2881`,
   `tools/wave_land_window.py:733-761`)。これは T-1316 が対象にする attempt 1 の
   単純欠落レースとは別の失敗コードであり、R-B へ残す。(iii) `docs/dev-wave/operations.md`
   への追記は段 7 の直接編集ではなく段 8 self-improvement routing が必要
   (`docs/skill-self-improvement.md:9-19, 57-60`)。かつ **予算がほぼ満杯**
   (`.claude/commands/dev-wave.md` 9,492/9,500 bytes、`docs/skill-self-improvement.md`
   5,963/6,000 bytes、実測で確認済み) — 意味のある追記は圧縮または独立の予算審査なしには
   収まらない可能性が高い。

   **条件付き推奨。** 即時 (P2 の実装を待たずに) 効かせられる唯一の選択肢だが、
   単独の恒久策としては採用しない。

2. **P2 — `--merge-message-file` を必須化し、claim 前に検証済み snapshot を取る**

   `tools/dev_wave_wait.py:1613` (argparse) を `required=True` にし、`run_acceptance`
   (`4297-4311`) も `None` を拒否する。`_validated_message_copy` (`2897-2909`) の呼び出しを
   queue 待ち開始前 (`_wait_until_acquired` 呼び出しより前) へ移し、postclaim では元の
   `--merge-message-file` path ではなく queue 待ち前に取った検証済み temp copy を使う。
   既存の `merge`・`merge-history-provenance`・`merge-message-provenance`・
   `owned-path-overlap` の各 fail-closed 検査、D253 の待ち札意味論、D486 の retry 6 条件は
   変更しない。既存 pin テスト (`orchestrator/tests/test_dev_wave_wait.py:6680-6746`) は
   「claim 前に必須化で拒否される」形へ更新するが、削除・弱化はしない。

   **効き:** omission が CLI/API レベルで構造的に不可能になり、レンズ B #1 が指摘した
   「運用規約は守られなければ効かない」問題を機械で閉じる。queue 待ち中の file 削除・
   書換えにも影響されない (snapshot 済み)。

   **限界:** attempt 2 の複合レース、merge-message-provenance の実装面著作 classifier は
   P1 と同様に閉じない (R-B)。API 変更に伴い呼び手 (今のところ manager 本人の直接 CLI
   呼び出しのみ、production wrapper 追加は repo 全体検索で見つからず) と既存テストの更新が要る。
   実装規模は 1 wave 相当 (argparse・`run_acceptance` 引数検証・snapshot 経路の移動・
   pin テスト更新)。

   **推奨 (恒久策)。**

3. **P3 — message 未指定時に待ち手がデフォルト trailer を自動生成する**

   **非推奨。** `validate_implementation_author` は実装面 path の 3 方向結合結果に対し
   Codex `role=author` または有効な waiver を要求する (`tools/check_ai_provenance.py:1231-1261`)。
   固定・自動生成の trailer では、実際にそれが必要になる稀なケース (R-B) で
   虚偽の provenance 記録を作りかねない。誤った固定 trailer は規律 6 (信頼境界) が
   守ろうとしている「正しさシグナルを後付けにしない」の対偶に近い失敗様式になる。

4. **現状維持**

   **非推奨。** D253 の fail-closed 自体は守るが、queue 待ちが長いほど発火率が上がる
   40〜70 分の待ち直しを再発させ続ける (`docs/archive/worklog-phase3-0817-630-631.md:583-587`)。

### 親の推奨

**P2 を恒久策として裁定へ提出する。** 効果が確認でき (段 3 で反証できず)、D253/D486/
受領証 schema/rc 意味論のいずれも変えない範囲で omission を機械的に閉じられるため。
**P1 は P2 の実装が決まるまでの間、または P2 を採らない場合の暫定 mitigation** として
別途採用可否を裁定してよいが、(a) 段 8 self-improvement routing を経由すること、
(b) 現行の docs 予算では追記が収まらない可能性が高く、圧縮または独立予算審査が要ることを
明記して提出する。P3 は却下、現状維持は非推奨。

---

## R-B. 本 wave が閉じない、構造が同型の残余 (scope 外・記録のみ)

T-1316 の task 引数は `--merge-message-file` の供給協調点に scope を絞っている
(`絶対規律5 段階導入 / 盛らない`)。段 3 の敵対レビューが検出した次の 3 件は、
いずれも「lease 取得後・受入 command 投入前に落ちて retry せず release する」という
**同じ構造**を持つが、引き金が異なる別問題であり、本 wave では設計しない。
DW-G03 (族一般化には独立 2 例) の基準にはまだ届いていない (2 件目は R-D の 1 件のみ実測)。

1. **同型の兄弟 failure 経路の一覧 (レンズ B が構造化):**
   `owned-path-overlap` (`3791-3792`)、`merge` / `merge-history-provenance` /
   `merge-message-provenance` (`3799-3825`)、`commit-message-postcheck` / `postcheck` /
   `commit-head-postcheck` / `prerun-clean` (`3841-3868`) はいずれも claim 後に発生し
   retry せず release する。`preflight-index-flags` / `preflight-submodule-ready` は
   claim **前** (`3717-3718`) なので実は該当しない (段 3 レンズ B が反証)。
   `prerun-fingerprint` / `restart-required` 等は `held-self` のときだけ release されず
   保持される例外がある。**判断:** 個別の発生頻度・実害が未計測であり、本 wave では
   「同じ構造を持つ」という指摘の記録に留め、対策 (D486 の retry 境界拡張など) は
   別裁定へ送る。

2. **D486 attempt 2 の複合レース (`claim-self-unverified`):**
   attempt 1 が `retryable-no-verdict-infra` で再試行された後、attempt 2 の self-claim
   前に main がさらに進むと、self-claim が新しく測った main_sha と lease 記録の不一致で
   失敗しうる (`tools/dev_wave_wait.py:2875-2881`、`tools/wave_land_window.py:733-761`,
   `390-398`。既存テストは `claim-self-unverified` / command 1 回 / release 1 回を
   `orchestrator/tests/test_dev_wave_wait.py:10125-10138` に固定)。P1/P2 いずれも
   閉じない。**判断:** T-1316 の主対象 (attempt 1 の単純欠落) より狭い複合条件であり、
   実測された実害はまだ無い。将来 ticket 化の候補として記録する。

3. **`merge-message-provenance` の実装面著作 classifier (R-A で先出し):**
   3 方向結合で実装面 path が両親と異なる結果になると、固定 trailer では
   `merge-message-provenance` 自体が rc=70 で落ちる。過去に 1 度実際に発生し
   known-violation registry で事後救済された実績がある
   (`_DW8C_ACCEPTANCE_MERGE_NOTE`, `tools/check_ai_provenance.py:213-219`)。
   既存の `owned-path-overlap` (`--owned-path` 指定時のみ有効、任意指定) は
   **部分的な緩和**に留まる — `_DW8C_ACCEPTANCE_MERGE_NOTE` の対象 file は
   その wave の owned-path 宣言に無かったと推測される (overlap 検査を通過して実際に
   発生しているため)。**判断:** P1/P2 いずれを採っても増減しない既存リスクであり、
   本 wave では触らない。将来 ticket 化の候補として記録する。

### 親の推奨

R-B の 3 件はいずれも「実装しない・起票のみ」。次の /rulings で R-A (P2 推奨、P1 は
暫定可否を別途判断) を裁定した後、R-B は独立の起票 (新しい T-ID) として扱う。

## 総括

- 核心問題 (R-A): `merge_message_file` を postclaim で持たない race は F365 で未解決のまま
  T-1316 として残された。段 3 の 2 レンズが独立に「有効な message file を全 invocation に
  常時渡せばこの特定 race は閉じる」ことを検証し反証できなかった。
- 推奨は **P2 (CLI/API 必須化 + claim 前 snapshot) を恒久策**、**P1 (運用規約の即時是正) を
  暫定 mitigation** とする二段構え。P1 単独は「守られなければ効かない」という、
  この問題を生んだのと同じ弱点を持つ (既存の近い規約があっても t1180 は発生した)。
  P1 の docs 追記は段 8 routing 必須かつ予算がほぼ満杯であることも明記した。
- P1/P2 いずれも、attempt 2 の複合レースと実装面著作 classifier の残余 (R-B) は閉じない。
  これらは同じ構造を持つが引き金が異なる別問題であり、DW-G03 の基準 (独立 2 例) に
  届いていないため本 wave では設計せず、将来の独立起票として記録するに留める。
- D253 の FIFO・待ち札意味論、D486 の retry 6 条件、受領証 schema、rc の意味論は
  いずれの択一でも変更しない。
