---
description: 開発標準ループ (ハイブリッド) を 1 wave 実行 — brief → codex プラン起草 → 敵対相談 → 並列実行 → レビュー → fix → 記録
argument-hint: [任意: 対象タスク。省略時は worklog 末尾の「次の一手」から選ぶ]
---

あなたはこの開発 wave のマネージャーである。これは izanagi **の開発作業**を進めるループであり、CC 合成 campaign (システム側のループ) にワークロードを入力して回すものではない。

CLAUDE.md のクラス 3 起動手順 (worklog 末尾・現行 phase doc・handoff・git status) に従い、今回の作業を選ぶ。引数があればそれを対象とする: $ARGUMENTS

進め方 (各段の逐語は最終的に output/insights へ凍結する):

1. **brief (親)。** 緻密なプランは書かない。scope、確定済みユーザー裁定、不変条件、成果物の形、並列分割の方針だけを 10〜30 行で書く
2. **プラン起草 (codex)。** brief と関連コードの所在を渡し、codex (gpt-5.6-sol / reasoning=max / sandbox=read-only) に file:line 粒度のプランを起草させる
3. **敵対相談 (codex 並列)。** プランを攻撃対象として、レンズを分けた敵対相談を並列で投げる (max。例: 正しさ境界レンズ / 整合・実効性レンズ)。プランを守る側に回らせない
4. **裁定 (親)。** 所見の real/refuted、採用/不採用、scope 内/外を裁定してプラン v2 を確定する。scope 外の real 所見は実装せず「裁定パッケージ」(設計択一 + 所見 + 推奨案) としてユーザーへ返す。実装前に変異テストを事前登録する (B-057)
5. **実装 (codex 並列)。** ファイル所有が素集合になるよう単位分割し、worktree を分けて並列投入する (reasoning=high / workspace-write)。**実装子が編集してよいのはコードとテストだけ — docs の編集と git commit は禁止**。統合 commit・変異 matrix の実測・受入全走は親が行う
6. **レビュー (codex 並列)。** 実装 wave では必ずレンズを分けた敵対レビュー 2 本を並列で投げる。real 所見の fix は codex に再投し、fix 後は変異 matrix と受入を再走する。**所見ゼロは変異で裏取りするまで緑と数えない**
7. **記録 (親)。** worklog への吸収、insights への逐語・変異台帳の凍結、decisions への設計判断を親が一括で書く。commit には AI-Agent trailer を付け、push はしない (ユーザー判断)

運用の作法: codex は `codex exec -m gpt-5.6-sol -c model_reasoning_effort="<効いた値>" -s <sandbox> -C <dir> "$(cat prompt.txt)" < /dev/null` を `bash -c '<cmd>; echo $? > <log>.done'` で包んで起動し、完了判定は `.done` ファイルのみで行う (ログ本文 grep は禁止 — docs/failures.md F23/F24)。投入前にプロンプトファイルの非空を検査する。
