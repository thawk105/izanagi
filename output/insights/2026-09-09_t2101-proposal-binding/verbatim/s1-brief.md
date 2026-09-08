# [T-2101] 段 1 brief — 提案の束縛を実行ループ側で閉じる

wave: dev-wave-t2101-proposal-binding / branch: worktree-dev-wave-t2101-proposal-binding
起点 main: 2143a49c0 / 投入先 worktree (子はここを読み書きする):
`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding`

## 研究前進

B-4 の材料レポートは「事前固定した 201 試行」を主張する。現状その主張は成り立たず、raw 記録は
「registry のラベルを付けた 201 の**選択可能な**証拠」に留まる (D1343 理由節、s4-ruling §4 項 1)。
実行ループが実行直前に提案の canonical hash を再導出して封印 registry の登録値と照合し、
不一致なら実行前に拒否すれば、この主張の前提が閉じる。
**完了判定:** 不一致の提案が build・campaign lock 取得・WAL 書込みより前に拒否され、
その拒否が候補集合に含意されて恒真になっていないことを変異で示せること。

## 確定済みユーザー裁定 (覆さない)

- **D1343 (2026-09-01 ユーザー裁定):** 束縛は**実行ループ側で閉じる。** ループが提案の canonical hash を
  再計算し、封印済み registry と一致しなければ**実行前に拒否する。**
  却下済み: (a) issuer 側だけで閉じる、(b) 束縛を閉じないまま実走する。
- **D302:** 承認済み spec への束縛は hash の転記でなく**内容の再導出**で行う。
- 依頼本文: 本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。

## 段 1 前の実測 (親が実施済み。推測ではない)

1. 実行経路: `p3_b4_launcher.main` → `launch_bootstrap_impl` / `launch_continuation_impl` →
   `DRIVER_REGISTRY[driver_kind](argv)` = `p3_s4_loop.main` 等 → argv は `_driver_argv` が組む
   `--run-iteration <proposal_path>` → `load_proposal_file(path)` が JSON を読む。
2. **launcher も 3 driver も封印 registry / prerun publication を一切知らない。** launcher の argparse は
   `mode` `--driver` `--arm` `--admission-record` `--proposal` `--artifact-root` だけ。
3. `initial_proposal_sha256` は `B4ScheduledAttemptInput` の field として存在し、64 hex であることだけが
   検査される (`p3_b4_analysis_ledgers.py:339`)。**canonical 化の規約は repo のどこにも無い。**
   raw producer は非保証 `:63` に「計算・記録する経路が repo に無い」と明記している。
4. 読み手は既に在る: `p3_b4_prerun_issuer.load_b4_prerun_publication(publication_root)` が
   registry・manifest・receipt を厳密に再検証して返す。**gate の入力は新設でなく既存 loader の消費である。**
5. `output/` に既存の prerun publication artifact は無い (find 0 件)。したがって発火条件は
   「今日以降の B-4 formal 実行の**すべて**」であり、休眠する条件付き機能ではない (DW-G04)。
6. pin 閉包 (DW-O09): `p3_s4_loop.py` は 63 path enforcement closure 外、whole-file sha256 も
   projection digest も凍結 literal に pin されていない (repo hit 0 件)。`p3_b4_launcher.py` は
   63 path closure 内だが、その blob sha を pin する凍結成果物は repo/output に 0 件。
   **凍結 bytes を動かす変更ではない。** 未 commit の間 contract-loader-drift で焦点走が赤になるのは既知。

## scope

- `orchestrator/campaign/p3_s4_loop.py` に (a) 提案 document の canonical hash 再導出、
  (b) 封印 registry の登録値との照合、(c) 不一致・不在時の**実行前**拒否 を実装する。
- `p3_s4_loop_sort.py` / `p3_s4_loop_trigger_gating.py` も同じ関門を通す。3 driver とも
  `DRIVER_REGISTRY` に載っていて launcher から今日実行できるため、1 つでも素通しなら保証に穴が開く。
  これは族一般化 (DW-G03) ではなく、**実在する受理集合の境界を全部覆うこと**である。
- `p3_b4_launcher.py` は束縛引数を argv へ通す。formal B-4 の唯一の入口だから。
- 負例・正例・恒真でないことの証拠テスト。

## scope 外 (実装しない)

- issuer 側で `initial_proposal_sha256` を生成・記録する経路 (T-2050 / T-2051 の領域)。
- 汎用の束縛 framework、新しい台帳・受領証・署名・一回性状態機械。
- 非 B-4 経路 (`--b4-reflux-ablation` 無し) への適用。
- 凍結 closure 5 file と `_SOURCE_CLOSURE_PATHS` の変更。

## 不変条件

1. **規律 2:** 受理集合は狭める向きにだけ動かす。既存テストの期待値を緩めない・反転しない・skip しない。
2. **規律 6:** proposal は未信頼の外部データである。document 内の自称 hash を登録値の出所にしない。
   登録値は封印 registry からのみ取る。
3. **単一読取り (D162 決定 5):** proposal file は 1 度だけ開き、同一 buffer から hash と parse を導く。
   2 度開いて hash と parse を別 buffer にする形は ABA 差し替えを通すので禁止。
4. **実行前性:** 拒否は build・campaign lock 取得・WAL 書込み・campaign 実行のいずれよりも前に起きる。
5. **恒真化禁止:** 登録値が不在・読めない・attempt が registry に無いときは fail-closed で拒否する。
   fail-open (束縛が無ければ素通し) にしない。
6. 凍結 bytes を動かさない (実測済み: 該当 pin なし)。

## 親の provisional 裁定・攻撃対象 (P1)

- **(P1-1)** 束縛の入力は launcher 経由の新 argv (`--b4-prerun-publication <root>` と
  `--b4-attempt-id <id>` 相当) で loop へ渡す。campaign layout から暗黙に探す案は採らない
  (identity が二義化するため、D75)。
- **(P1-2)** B-4 mode (`--b4-reflux-ablation`) では束縛引数を**必須**とし、不在は実行前拒否とする。
  これが無いと検査は恒真になる。既存 B-4 テストはこの必須化に合わせて**束縛を与える**方向で更新し、
  期待値を緩める方向では更新しない。
- **(P1-3)** canonical 化の対象は `load_proposal_file` が schema 検査に使う document、すなわち
  `b4_closed_critic_receipt_sha256` key を除いた proposal document とする。canonical JSON は
  `sort_keys=True` / `separators=(",",":")` / `ensure_ascii=False` / `allow_nan=False` (repo 既存規約)。
  **理由:** その receipt hash は run 中に `launch_continuation_impl` が鋳造する値であり、
  registry を封印する時点では存在しない。含めると登録値が原理的に計算できない。
- **(P1-4)** 3 driver すべてを対象にする (base / sort / trigger)。共通実装は `p3_s4_loop.py` に置き、
  sort / trigger は既に `L.B4_PROPOSAL_RECEIPT_SHA256_KEY` を参照しているのと同じ形で呼ぶ。

## 成果物の形

- `p3_s4_loop.py` の public 関数 2 つ: 提案 document → canonical hash、および
  (publication root, attempt id, proposal bytes) → 一致/拒否。
- 3 driver の proposal 読取り経路が同関数を必ず通る。
- launcher が束縛引数を通す。
- テスト: 負例 (不一致 → 実行前拒否)、不在負例 (束縛引数なし → 拒否)、
  正例 (一致 → 通過し過剰拒否しない)、単一読取りの正例、実行前性の正例。

## 変更面 実アンカー表

| path:line | 内容 |
|---|---|
| `orchestrator/campaign/p3_s4_loop.py:169` | `B4_PROPOSAL_RECEIPT_SHA256_KEY` 定義 |
| `orchestrator/campaign/p3_s4_loop.py:2007`〜`2105` | `load_proposal_file` (読取り・schema 検査の本体) |
| `orchestrator/campaign/p3_s4_loop.py:2452`〜`2500` | `main` の段 4b 駆動口 (`--run-iteration` の消費点) |
| `orchestrator/campaign/p3_s4_loop_sort.py:465`〜`481` | sort driver の同型読取り |
| `orchestrator/campaign/p3_s4_loop_trigger_gating.py:944`〜`960` | trigger driver の同型読取り |
| `orchestrator/campaign/p3_b4_launcher.py:177`〜`195` | `_driver_argv` |
| `orchestrator/campaign/p3_b4_launcher.py:531`〜`555` | `launch_bootstrap_impl` |
| `orchestrator/campaign/p3_b4_launcher.py:557`〜`605` | `launch_continuation_impl` |
| `orchestrator/campaign/p3_b4_launcher.py:632`〜`660` | launcher `main` の argparse |
| `orchestrator/campaign/p3_b4_prerun_issuer.py:1009` | `load_b4_prerun_publication` (既存の読み手) |
| `orchestrator/campaign/p3_b4_analysis_ledgers.py:137`, `:339` | `initial_proposal_sha256` の field と検査 |
| `orchestrator/campaign/p3_b4_raw_record_producer.py:63` | 非保証。この wave で 1 項が閉じる |

## 成果物影響 (DW-G05)

放置すると B-4 の材料レポートと raw 台帳は、事前固定した試行集合ではなく事後に選択可能な証拠集合を
指し続ける。すなわち報告される 201 試行の**参照**が、事前登録が意味するものと別物になる。

## 受入・実測環境

login node の python テストのみ。計算ノードへの dispatch と性能計測は不要。

## 並列分割方針

編集面が相互依存 (loop 共通関数 → 3 driver → launcher) のため実装は Codex `role=author` 1 単位。
段 2 は plan 子 1 本。段 3 は敵対相談 2 本 (レンズ ① 恒真化・受理集合の実効性、
② 信頼境界・単一読取り・実行前性)。段 6 はレビュー 2 本 + fix + 焦点 1 本。
