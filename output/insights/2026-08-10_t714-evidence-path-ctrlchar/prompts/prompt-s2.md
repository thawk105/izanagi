あなたは izanagi プロジェクトの dev-wave 段 2 プラン起草者である。日本語で書け。

## 読むもの (読めなければ即停止し、その旨だけを出力せよ)

- 親 brief: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t714-evidence-path-ctrlchar/brief.md`
- 実測 probe: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t714-evidence-path-ctrlchar/premise_probe.py`
- 実装対象: `orchestrator/campaign/s8c_preregistration.py` の `read_blob_at` (960 行付近)、
  `orchestrator/campaign/s8c_preregistration_evidence.py` の `_safe_path` / `_nonempty_string`
  (140-190 行付近) と、その caller (`load_contract_bytes`、`EvidenceRef` 構築、376 / 677 行付近)
- 既存テスト: `orchestrator/tests/test_s8c_preregistration_core.py` (`_assert_reason` は 186 行付近、
  `read_blob_at` の既存検査は 974-978 行付近)、
  `orchestrator/tests/test_s8c_preregistration_predicates.py` (契約 loader の検査、60-180 行付近)

cwd は wave worktree である。sandbox は read-only であり書き込み可能な tmp がない。
**pytest を実走する必要はない**。静的検査で足りる。実測は親が行う。実走していない緑を緑と書くな。

## 仕事

親 brief の scope ちょうどを実装するための、**file:line 粒度の実装プラン**を書け。
プランは実装子 (別の codex、sandbox=workspace-write) がそのまま実行できる粒度にせよ。

必ず含めること。

1. **編集ハンクの列挙。** ファイル・関数・挿入位置 (file:line)・追加するコードの意図。
   親の (P1) CR/LF のみ、(P2) 理由語 `path-control-char` / `contract-path-control-char` を
   前提にした案を書き、異論があれば別項に書け (実装案自体は brief どおりにせよ)。
2. **caller 閉包。** `read_blob_at` と `_safe_path` の全 caller を列挙し、
   拒否が新しく発火しうる経路と、発火しないと判断した根拠を書け。
   `EVALUATOR_MODULE_PATH` / `SOURCE_PATH` / `EVIDENCE_CONTRACT_PATH` / `generation_path` の
   定数経路が新拒否で壊れないことを確認せよ。
3. **例外型と reason 語。** `PreregistrationError` / `EvidenceContractError` の既存慣行
   (reason 語の命名・引数・防護的な文字列化) に合わせよ。
   **reason 文字列や例外 message に、拒否対象の生 path をそのまま埋め込むと
   CR/LF がログ行を分断しうる**。既存コードがどうしているかを確認し、必要な扱いを書け。
4. **テスト計画。** 追加する nodeid・ファイル・fixture を具体的に書け。
   - `read_blob_at` が末尾 CR 付き path で **alias せず拒否する** ことの実 git 検査
     (既存 `_init_repo` / `_write` / `_commit` ヘルパを使う)
   - 埋め込み CR / LF の拒否
   - `_safe_path` の CR/LF 拒否が、既存の付随的拒否 (`value != value.strip()`) ではなく
     **新しい明示検査で起きている**ことを区別できる検査 (埋め込み CR/LF を使う等)
   - 正常 path が従来どおり通る正例 (`DW-S04` の「通る正例を 1 つ添える」)
   - 既存の 12 述語・契約 semantic hash・freeze 検証が無変化であることの回帰観点
5. **変異事前登録の候補。** この実装を殺すべき変異 (production を書き換えたときに
   どのテストが落ちるべきか) を 8〜12 件、`file:line` + 変異内容 + 期待して落ちる nodeid で挙げよ。
6. **やらないこと。** NUL・tab・その他制御文字・`ruleops.py` の同型欠陥 (別タスク [T-510])・
   docs 編集・commit は scope 外である。プランに混ぜるな。

## 出力形式

Markdown。最後に `## 総括` 節を置き、プランの核心を 5 行以内でまとめよ。
