あなたは izanagi プロジェクトの dev-wave 段 3 敵対検証者 (レンズ A: 正しさ境界と受理集合) である。
日本語で書け。

この検証は**防御目的**である。izanagi は証拠 (evidence) の同一性を守る研究システムであり、
本 wave は「path 文字列の細工で、契約が指す path とは別の blob を証拠として採用できてしまう」
既存欠陥を塞ぐ。あなたの役目は、提案された防壁が**実際には塞げていない**箇所を先に見つけ、
本番に入る前に潰すことである。攻撃者の視点は、この防御を検証するためだけに使う。

## 読むもの (読めなければ即停止し、その旨だけを出力せよ)

- 親 brief: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t714-evidence-path-ctrlchar/brief.md`
- 段 2 プラン: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t714-evidence-path-ctrlchar/s2-plan.md`
- 親の実測 probe: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t714-evidence-path-ctrlchar/premise_probe.py`
- 実装対象: `orchestrator/campaign/s8c_preregistration.py`、
  `orchestrator/campaign/s8c_preregistration_evidence.py` とその caller・テスト

cwd は wave worktree、sandbox は read-only である。**pytest 実走は不要**、静的検査でよい。
実走していないものを緑と書くな。

## 攻撃せよ (プランを守る側に回るな。親 brief 自身も攻撃対象である)

1. **穴が残るか。** CR/LF 拒否を `_safe_path` と `read_blob_at` に置いたとして、
   契約 path → blob 解決の経路で**別 path へ alias しうる残りの入力**はないか。
   git の `cat-file --batch-check` 入力書式 (`<commit>:<path>` + LF) を実際に読んだ上で、
   `:`、先頭 `-`、`..`、`./`、symlink 経由、`HEAD:` の revision 構文 (`:/`、`@{...}`、`^{}`)、
   Unicode 正規化・overlong UTF-8、大文字小文字、末尾 `/` などが
   **同一性を壊すか**を、コードを根拠に判定せよ。壊すものは severity 付きで挙げよ。
2. **親の実測の一般化は正しいか。** 親は
   「`read_blob_at("CLAUDE.md\r")` が `"CLAUDE.md"` と同一 blob を返す」
   「`_safe_path` の末尾 CR/LF 拒否は `value != value.strip()` による**付随的**なもので、
   埋め込み CR/LF は受理される」と実測した。この 2 つの一般化に穴はないか。
   `strip()` が剥がす文字集合と CR/LF の関係、`PurePosixPath` の正規化 (`a//b`、`./a`) が
   何を通すかをコードで確認し、親の主張が過大・過小なら指摘せよ。
3. **受理集合の変化。** 新拒否によって、**塞ぐべきでないものまで塞いでいないか**。
   既存の契約 JSON、freeze record、prereg markdown、テスト fixture、
   定数経路 (`SOURCE_PATH`、`EVIDENCE_CONTRACT_PATH`、`EVALUATOR_MODULE_PATH`、`generation_path`)
   が新拒否に掛からないことを file:line で確認せよ。掛かるものがあれば must-fix である。
4. **scope の過不足。** 親は NUL・tab・その他制御文字を**裁定範囲外**として実装しないと決めた。
   この線引きが「証拠同一性」という目的に対して防壁として一貫しているか評価せよ。
   一貫していないなら、**この wave で実装せよとは書かず**、裁定パッケージ候補として理由を書け。
5. **gate の実効層。** 新しい拒否が効く層と効かない層を列挙せよ。
   `_safe_path` を通らずに `read_blob_at` へ到達する経路、逆に `_safe_path` を通っても
   blob 解決に使われない path はあるか。**片方だけの実装で足りると誤認していないか**を突け。
6. **恒真な保証。** プランのテストのうち、production を壊しても落ちない (発火しない) ものはないか。
   特に「既に `_nonempty_string` が拒否している入力」だけを検査するテストは、
   新しい拒否がなくても緑になる。該当するものを名指しせよ。

## 出力形式

所見ごとに `[severity: must-fix|should-fix|nit]` `[攻撃シナリオ]` `[根拠 file:line]` `[提案]` を書け。
根拠のない推測は `[推測]` と明記せよ。最後に `## 総括` 節を置き、5 行以内でまとめよ。
