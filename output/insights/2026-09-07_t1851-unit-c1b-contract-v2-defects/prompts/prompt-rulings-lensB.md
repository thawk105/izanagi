単独段 dispatch: stage=consult; lane=luna; sandbox=read-only; task=[T-1851] C1b 未裁定 4 件の裁定

# レンズ B: 前提そのものを疑ってから決める

## 必読事項の射影

作業 repository は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a`、
HEAD は `68573078e` である。コードも文書もすべてこの worktree の中を読む。
**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `output/insights/2026-09-07_t1851-unit-c1b-contract-v2-defects/s4-adjudication.md`
   — **本件の正本。** 1 節が実測で確定した契約 v2 の欠陥 7 件 + 偽造 2 件、2 節が親が確定させた
   訂正、**3 節が本相談の対象である未裁定 4 件**、5 節が段 3 所見の裁定表
2. `output/insights/2026-09-07_t1851-unit-c1b-contract-v2-defects/verbatim/s3-lensA.md`
   — 正しさ境界レンズの所見 (A-01〜A-12)。**A-06 / A-07 / A-08 / A-09 / A-10 が本相談に直結**
3. `output/insights/2026-09-07_t1851-unit-c1b-contract-v2-defects/verbatim/s3-lensB.md`
   — 整合と実効性レンズの所見 (B01〜B13、S01〜S04、M1〜M18)
4. `output/insights/2026-09-07_t1851-unit-c1b-contract-v2-defects/parent-verification.md`
   — 親の独立検算 V1〜V6 と、誤りだった V3 の撤回
5. `output/insights/2026-09-07_t1851-unit-c-launcher-raw-facts/s4-adjudication.md`
   — **前 wave が固定した契約 v2 の原文。** 3 節が exact な field 表・cross-field 不変条件・
   再導出 6 枝・E2 の 4 語・crash 後の権威、5 節が C1b / C2 / D2 の境界
6. `output/insights/2026-09-07_t1851-unit-c1b-contract-v2-defects/verbatim/s2-plan.md`
   — 段 2 の実装プラン (判定は「実装不可」)

主要な現物 (自分で開いて確かめる。行番号は引用でなく現物から取る):

- `orchestrator/campaign/attempt_registry_core.py` — 台帳 core。terminal の検査順序、
  `terminal_row_validator`、`record_attempt_terminal`、genesis の `retryable_failure_reasons`
- `orchestrator/campaign/s8b_attempt_profile.py` — v1 / v2 の profile、`S8B_V2_RETRYABLE_FAILURE_REASONS`、
  `_reject_unsealed_s8b_v2_terminal`、`make_s8b_v2_domain_profile`
- `orchestrator/campaign/s8b_floor_attempt_launcher.py` — 起動層。分類語彙の定数、
  `_pre_observation_failure_reason`、`_CLASSIFICATION_POLICY` と authority digest
- `orchestrator/campaign/s8b_floor_campaign.py` — `_finish_session` と、その手前の理由 precedence
- `orchestrator/calibrator/runner.py` — 計測 runner。`notes` と rep 記録の生成元
- `orchestrator/campaign/s8b_floor_stats.py` — `assess_session`、`_derive_rep_integrity`
- `orchestrator/campaign/s8b_attempt_registry.py` — adapter。handle、claim、create-only publish

## 絶対に守る制約 (この repo の憲法。緩める提案は却下される)

- **規律 2: 正しさゲートを緩める変異を許さない。** anomaly を検出した対象は即 reject。
  性能や利便のためにゲートを緩めない。
- **規律 3: 正しさシグナルを後付けにしない。** 検査は pass/fail でなく「なぜ壊れたか」を構造化して返す。
- **D1113: 呼び手は証拠の値を選べない。**
- **規律 7: 過去の判定は追記でのみ訂正する。** 遡って無効化しない。

## 共通の制約

- 読取専用である。実装しない。書込可能な tmp が無いので pytest を走らせない (走らせられない)。
  テストの実測は親が行う。子の非実走を緑と数えない。
- **選択肢を並べるのではなく決めろ。** 各項目に**ちょうど 1 つの推奨**を出し、
  採らなかった案を却下理由付きで書く。「どちらもありうる」は回答として不受理である。
- 主張には **[実測] / [推測]** を付ける。行番号・件数・key 集合・値域は必ず [実測] にする。
  文書に書かれた行番号を転記せず自分で現物に当たる。
- 出力へ結合文字 U+0300〜U+036F を使わない。
- 三軸語 (`ycsb_rratio` / `ycsb_zipf_skew` / `ycsb_rmw`) の**値**を出力に書かない。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。無出力が最悪である。
- 出力の最後に `## 総括` 節を置き、4 項目の推奨を各 1 行 + 全体の実装可否を 8 行以内で書け。

## このレンズの依頼 — 前提そのものを疑ってから決める

未裁定 4 件に答える前に、**そもそもこの機構が必要かどうか**を疑え。そのうえで 4 件を決めよ。
「決められない」「ユーザー次第」は不受理である。

### (0) 前提の再検査 — これは必ず最初にやる

契約 v2 は「v2 台帳の terminal 行に封印証拠を要求する」機構である。前 wave の裁定で固定され、
本 wave で実体化不能と判明した。**その機構が本当に必要かを、下流の成果物から逆算して確かめよ。**

- **v2 台帳の terminal 行を誰が読むのか**を現物で追え。読み手 (consumer) を全列挙し、
  各読み手が terminal 行の**どの field を実際に使うか**を書け。
- **封印証拠が無い場合に、具体的に何が偽装できるのか**を、攻撃者が実際に取れる手順として書け。
  「呼び手が値を選べてしまう」だけでは不十分で、**その値が下流の certified な選択・レポート・
  proof chain のどこに、どう伝播するか**を追え。伝播しないなら、その機構は要らない。
- 既存の防壁 (classification receipt、observation-start event、`raw_output_sha256` の
  deferred reader 再計算、admission の claim、freeze / ratified の検査) が**すでに何を塞いでいるか**を
  列挙し、封印証拠が**追加で**塞ぐものだけを残せ。

この (0) の結論が「機構は過剰である」なら、そう書いてよい。その場合は (1)〜(4) を
「縮小した機構」に対して答えよ。**結論が「必要である」なら、その必要性を上の伝播経路で示せ。**

### (1)〜(4)

`output/insights/2026-09-07_t1851-unit-c1b-contract-v2-defects/s4-adjudication.md` の 3 節に
(1) core の等値検査と E2 語彙の衝突、(2) `exec_failures` の出所、(3) 封印の信頼境界、
(4) C1b の単位、として書かれている 4 件である。原文を読んで答えよ。

各項目で必ず次を含めること。

- **(1)** 変更する関数と変更後の signature。v1 の受理集合が変わらないことの根拠。
  **「そもそも E2 の 4 語を台帳の `failure_reason` に載せる必要があるのか」も疑え。**
  観測後に導出された理由を台帳の別 field へ置き、`failure_reason` は観測前分類のままにする案が
  成立するか、成立するなら null matrix と retryable 集合をどう扱うかを現物で確かめよ。
- **(2)** 「証拠が何を証明するのか」から逆算して決めよ。契約と campaign のどちらが誤っているかを
  値の使われ方で判定する。**両方が正しくてよい (別の量である) 可能性**も検査せよ
  — `exec_failures` と `rep_integrity_failures` が別々に存在する理由を現物で確かめること。
- **(3)** 脅威モデルを攻撃者の能力で定義せよ。この repo は **AI が生成した variant と外部 CCBench を
  取り込むのが本質**である (規律 6)。同一 process 内の module 改変を脅威に含めるかは、
  「その module を書けるのは誰か」で決まる。**誰が repo へ書けるのかを実際の運用から特定してから**
  決めよ。
- **(4)** (0) の結論を反映した規模で決めよ。機構を縮小したなら、その縮小後の見積りを出せ。

## 出力形式

`## (0)` 〜 `## (4)` の 5 節をこの順で置き、各節に次を書く。

- `**決定:**` 1 段落。
- `**根拠:**` file:line と実行結果。[実測] / [推測] を付ける。
- `**却下した案:**` 各 1 行で理由付き。

`## (0)` では `**決定:**` の代わりに `**判定:**` (機構は必要 / 過剰) と、
封印が無いときの**具体的な偽装手順と伝播経路**を書く。
