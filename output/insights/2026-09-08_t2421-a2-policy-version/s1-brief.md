# 段 1 brief — [T-2421] A-2 consumer の policy 版選択

基準: local main `cc9bba523ac7804aadb7891d686bf4c925789a3f`。
worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2421-a2-policy-version`。

## 研究前進

論文 A-2 の結果図 `docs/paper-story/figures/fig6_a2_certification_observed_positive.{png,pdf}` は
生成器 `tools/plotting/plot_a2_certification.py` が凍結 `certification.json` から作る。
producer の policy 文法が締まるたびにこの図が再生成不能になる。完了判定は
「t2364 成果物 (`output/insights/2026-09-07_t2364-paper-story-a2-certification/certification.json`) を、
当時の文法の**全体**で読んで figure data を構成できること」。土台側の最小差分は consumer の
版選択 1 点であり、測定のやり直しも producer 出力の変更も要らない。

## scope

- `orchestrator/campaign/paper_story_a2_certification.py`: `load_policy` の文法定数を
  **世代 (generation) で選べる**形にする。既定は現行世代で、既定経路の挙動と producer 出力 bytes は不変。
- `tools/plotting/plot_a2_certification.py`: `_historical_policy_view` の手書き再構成をやめ、
  選択表が**世代 id** を指し、その世代の完全な文法で読む形にする。
- `orchestrator/tests/test_plot_a2_certification.py`: 上記の正例・負例。新規 test file は作らない
  (共有台帳 `acceptance_duration_ledger.json` を t2417 と競合させないため)。

scope 外: producer が世代 id を成果物へ書き込む改修 (成果物 schema と凍結 pin が動く)。
仮想リスク向けの gate・検査・台帳・一般化の追加。A-6 系への波及。

## 確定済みユーザー裁定

- D1754: 歴史読みの主 key は `(認証 bytes sha256, 埋め込み policy bytes sha256)` の組。
  未知 hash への fallback は設けない。**この裁定は維持する。**
- D95: 実装面は Codex author が書く。親は直接編集しない。
- 絶対規律 7: 現行コードとの差だけを理由に記録された測定を無効にしない。
  ただし**過去成果物を読めるようにすることは、当時の測定を現行の正しさ主張へ昇格させることではない** —
  この一文を成果物 (insight README と decisions) に明記する (ユーザー明示要求)。

## 不変条件

- 未知 hash への fallback を作らない。受理集合を 1 件も増やさない (規律 2)。
- 既定 (`generation` 無指定) の `load_policy` は現行文法のまま。producer の書き出し経路・出力 bytes・
  shipped policy bytes を 1 byte も変えない。
- 図の bytes・provenance・`CANONICAL_SHA256`・凍結成果物を変更しない。
- cell の exact shape、順序と identity、`source_binding_status`、受領証 / raw / WAL / effect の照合は
  historical 側でも 1 つも外さない。

## (P1) 親の provisional 裁定 — 攻撃対象

**(P1-a)** 現行 `_historical_policy_view` は当時の文法ではなく 3 assert の近似を当てている。
ただし entry key が bytes を完全に固定するため**受理集合は緩んでいない**。よって欠陥は「緩い」ではなく
**「再利用できない」**であり、直す動機は正しさではなく再現性である。
根拠: `tools/plotting/plot_a2_certification.py:194-250`、同 `256-290`、`_expected_hashes:124-142`。

**(P1-b)** 文法差分は `trace0_cmake_argv.configure` の key 集合 1 点だけ
(現行 7 key、当時 6 key、増えたのは `fetchcontent_path_argument_prefixes`)。
したがって世代は「文法定数の差分」で表現でき、検証本体は共有できる。
根拠: `orchestrator/campaign/paper_story_a2_certification.py:129-134` と t2364 の埋め込み policy 実測。

**(P1-c)** 選択表の key は `(cert sha, policy sha)` の組のまま据え置き、値だけを世代 id にする。
成果物が記録する `source_commit` (両成果物に実在) を選択入力に格上げする案は、
今回の本題に必要でないので採らない。

## 成果物の形

- `orchestrator/campaign/paper_story_a2_certification.py` と
  `tools/plotting/plot_a2_certification.py` の差分、`orchestrator/tests/test_plot_a2_certification.py` の
  正例 1・負例 2 以上。
- `output/insights/2026-09-08_t2421-a2-policy-version/` に brief・plan・敵対相談・裁定・変異台帳・逐語。
- worklog / decisions / failures は `docs/spool/` の fragment。

## 分割方針

実装単位は 1 つ (loader の世代化 + consumer の選択 + test)。Codex author 1 本。
設計択一が割れる (P1-c の選択入力) ので軽量版にせず、段 2 plan 1 本 + 段 3 敵対相談 2 本 +
段 6 review 2 本を置く。
