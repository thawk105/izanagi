単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg

必読事項の射影: 以下はすべて絶対パスである。**読めなければ即停止**し、読めなかったパスを出力に書け。

- **レビュー対象 (本体)**: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md`
- **レビュー対象 (地図の追記)**: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/README.md`
- 親の段 4 裁定: `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/adjudication.md`
- 段 3 レンズ B の所見 (数値計算つき): `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/consult-b.md`
- 段 3 レンズ A の所見: `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/consult-a.md`
- 第 1 段の一次資料: `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/verbatim/t2418-explore-README.md`
- 実装の現物 (格子・codec・report): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/campaign/backoff_extended_sweep.py`
- report 生成: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/campaign/backoff_extended_sweep_report.py`
- bench の解析: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/calibrator/benchparse.py`
- C++ の hole: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/patches/silo-backoff-fixed.patch`
- CCBench の表示: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/external/ccbench/common/result.cc`
- 投入 script: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/tools/pegasus/b10_backoff_grid.sh`

repo path はすべて上記 worktree のものである。親側 repo は読まない。
本体 file は untracked である。作業ツリー上の現物を読め。
探索走の成果物は `/work/1/SFC/tanab/b10-backoff-grid-t2418-explore/` 以下にある (`jq` か `cat` で読め。
`python3 -c` は guard に拒否されることがある)。

## 依頼 — レンズ B「数値と spec の機械的健全性」

[T-2500] の段 6 敵対レビューである。**親の裁定を守らず攻撃せよ。** 本 wave は docs-only である。

### 1. 数値を自分で再計算して照合せよ

- **格子の再生成。** 本体 §4.1 の規則 `b_k = round(9999 / 2^(k/2))`, `k=6..0`, `b_k > 1000` から
  値を自分で計算し、本体の表・§5 の `formal_tail_values_us` / `analysis_values_us` /
  `encoded_static_points` / `binary_identity.physical_amounts_us` と**全点一致するか**を確かめよ。
  1 点でもずれていれば must-fix である。丸めの端数 (0.5) の扱いが規則どおりかも見よ。
- **符号化。** 各 raw 値について `encode_static_backoff_us` / `decode_static_backoff_us` の往復と、
  C++ 側 hole の商による分岐を突き合わせ、**全点が定数枝を通ること**を確かめよ。
  発行禁止域 `[1000, 2999]` の主張が正しいかも確かめよ。
- **測定順。** 本体が書いた 3 つの順序が、昇順 8 label に
  `random.Random(seed).shuffle` を 1 回適用した結果と一致するかを確かめよ。
  一致を確かめられないなら「確かめられない」と書け。推測で緑にするな。
- **区間の対数比。** 本体 §4.1 が主張する「tail の隣接区間の対数比が 0.3465〜0.3467 で均一」を
  実際に計算して確かめよ。境界参照区間の 0.2231 も確かめよ。
- **検出力。** 本体 §4.4 の `U_flat` の定義に、探索で観測された変動係数を入れて計算し、
  半オクターブ区間が 5% 基準に届くこと、および §6 が書いた概数 (3% と 9% 前後) が正しいかを確かめよ。
  多重度が 24 から 18 に変わったことによる t 分位点の変化も反映せよ。

### 2. spec の内部整合と機械的健全性

- §5 の JSON が**単体で parse できるか**。marker で囲まれた範囲を素直に切り出したときに
  壊れないか (marker 文字列が JSON の中に現れていないか)。
- 散文 (§4、§6、§7) と JSON の値・規則が食い違っていないか。1 件ずつ挙げよ。
- `analysis_input_contract` の field 名が、**実際の成果物・実装の field 名と対応しているか**。
  対応しない名前を要求していれば、後続 driver は満たしようがない。
- `correctness_authority` が指す場所が現物のどこかを特定し、正しいかを判定せよ。
- 失敗条件の列挙に、**起こりうるのに扱われていない状態**が無いか。
  とくに `indeterminate` 区間が生じたときの verdict の決まり方が一意か。
- `preconditions_before_formal_submission` が、現状の実装で満たされていないことを確かめよ
  (満たされているなら本体の記述が誤りである)。

### 3. 時間予算

8 genome × 3 workload の本走が `SWEEP_CAP_S` と PBS の枠に収まるかを、
第 1 段・先例の**実走所要**から見積もれ。推測の所要で議論するな。

## 制約

- 所見は **real / refuted を自分で判定**し、根拠を path と行番号・節番号で示せ。
- 成果物の値・受理集合・参照がどう変わるかを 1 行で書けない所見は must-fix にせず nit と明記せよ。
- **scope 外の real 所見も報告してよいが、実装を要求するな。**「裁定パッケージ候補」と明記せよ。
- 本 wave は docs-only である。コード・test・gate の新設を要求しない。
- sandbox は read-only である。**pytest 緑を要求しない。静的検査でよい。**
- 予算が尽きそうなら途中結論を下記の形式で書いて終われ。無出力が最悪である。
- 出力に結合文字 U+0300〜U+036F を使うな。

## 出力形式

## 再計算の結果
(格子・符号化・測定順・対数比・検出力を、自分で計算した値と本体の値の対照表で)

## 所見
(1 件ずつ。`[real|refuted] [must-fix|nit|裁定パッケージ候補] 見出し` → 根拠 → 成果物影響 1 行 → 提案)

## 総括
(3〜8 行)
