---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-23
wave: dev-wave-lease-cmd-entry-sync
seq: 2
---

## {{D:pegasus-runbook-lease-optional-followup}}. pegasus-runbook.mdの受入lease規範全面改訂はT-1458着地後の別waveへ送る

**決定:** `docs/pegasus-runbook.md`の受入lease関連記述 (958-961, 980-988, 1045-1051,
1087-1104, 1125-1129行目付近) には、D662 (受入lease待ち行列廃止) およびT-1458の
`--lease-optional`実装と矛盾する「claimが`acquired`/`held-self`の場合だけ投入できる」と
いう無条件の規範が広範囲に残っている。本waveでは`.claude/commands/dev-wave.md`の項6本文と
その機械pin (`tools/check_docs.py`) の整合だけを行い、runbookの改訂はT-1458のmain着地後の
別waveへfollow-upとして送る。

**理由:**
- 958-961行目だけを直しても980行目・1087-1099行目 (FIFO待機・head-of-line blocking)・
  1125-1129行目 (lease残留が他waveを止める前提) との不整合が残る (段3敵対相談レンズBが
  実際に該当箇所を読んで確認した)。全面整合には「optional経路と旧claim経路の分岐を明示する」
  設計が要り、958-961行目の単独修正では成立しない。
- 1045-1051行目のheld-self更新自体や1102-1104行目のrelease責務は、旧来の非optional経路
  ではなお成立し得るため、単純な削除・全面置換も正しくない。
- 段階導入・盛らない (絶対規律5) の下では、本wave (command entry + checker pinの3ファイル)
  とrunbook全面改訂 (5箇所+optional/旧経路の分岐設計) を1つのwaveへ詰め込むべきではない。
  T-1458未着地の現時点では`--lease-optional`の最終仕様 (unclaimed時のTTL・release・receipt
  扱い) を実装から確認できず、正確な改訂もできない。
- 一方でrunbookを放置したままcommandだけ直すと、将来のfresh sessionが詳細なrunbookの記述を
  優先し、flag無しのclaim待ちへ回帰しうる (段3敵対相談レンズBの指摘、real)。D662が解消しようと
  した9wave以上の同時待機・数時間規模の停止が再発するリスクがあるため、本decisionでfollow-up
  として明示的に記録し、見送りのまま忘れられないようにする。

**却下した選択肢:**
- 958-961行目だけを本waveで直す — 他4箇所との不整合が残り、部分的な整合はかえって
  「runbookのどの記述が正しいか」を曖昧にする。
- runbook全体を本waveで改訂する — T-1458未着地でoptional経路の最終仕様を確認できず、
  scopeも規律5に反する。
