---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-15
wave: dev-wave-t817-epoch
seq: 3
---

## {{D:epoch-purpose-declaration}}. verifier epoch は導出ラベルとし、読み手に受理目的を表明させる

**決定:** `campaign_verifier_epoch` は新しい artifact でも新しい lock field でもなく、
**v2 lock の既存 authority (`contract_loader_blob_sha256s`) からの導出ラベル**とする。
`E1` = 記録された blob map が現在の enforcement source closure と exact 一致、
`E1-stale` = v2 authority を持つが不一致、`E0` = v2 authority を持たない。

除外の適用点は**読み取り側の受理層 1 箇所**に集約し、consumer ごとに散らさない。
各 consumer は `require_admitted_campaign(root, purpose=...)` の `purpose` で、
`CERTIFIED_ACCEPTANCE` (certified を名乗る受理集合として読む) か
`HISTORICAL_RAW` (epoch 表示付きの歴史生値として読む) かを**呼び出し方で表明する**。
`purpose` は既定値を持たず、省略は `TypeError` とする。
certified 側だけが受け取れる view 型を分け、歴史側の view が型境界を越えられないようにする。

**理由:**
- 新しい pin や署名機構を足すと、それ自体が「policy を変えずに受理意味論だけ変える」抜け道に
  なりうる。実 enforcement bytes への束縛だけが、正しさ防壁の書き換えと連動して壊れる。
- 適用点を散らすと、新しい consumer が追加されたときに黙って抜ける。1 箇所へ集約し、かつ
  `purpose` を必須にすると、**新しい呼び出しは表明しない限りコンパイルもテストも通らない**。
  実際、本 wave の取り込みでは、この必須性が別 wave から入った 2 件の未表明呼び出しを露出させた。
- 表明を「呼び出し方」に置くのは、consumer 側の意図を機械が読める形で残すためである。
  同じ campaign を certified として読む経路と歴史生値として読む経路が同居しても、
  どちらの意味で読んだかが呼び出し点に書かれている。

**却下した選択肢:**
- lock へ epoch field を新設する — `IDENTITY_KEYS` / `AUTHORITY_KEYS` は exact key 集合検査なので、
  field 追加は既存 lock を全部不正にする。既存 campaign を引けなくなる。
- consumer ごとに epoch を検査する — 追加漏れが黙って通る。悉皆性を機械で保証できない。
- 受理集合を変えずラベルを表示するだけにする — 「certified を名乗る出力が未検証の証拠に載る」
  という当の問題が残る。裁定 Q1(a) が明示的に除外を選んでいる。
- `purpose` に既定値を与える — 既定が付いた瞬間、新しい呼び出しが黙って片方の意味に倒れる。
  必須にすることが、この設計の実効性を担保している唯一の機構である。
