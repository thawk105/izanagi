---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-10
wave: dev-wave-t139-addendum-b2
seq: 2
---

## 再発

### F32

- **再発: 2026-08-10** ([T-139] 追補 B wave)。恒久対応 4 の自己一致が、変異ハーネスではなく
  **dev-wave の汎用待ち手**で再現した。`wait.sh <done> <artifact> <pattern>` が producer 消滅を
  `until ! pgrep -f "$PAT"` で判定し、`$PAT` が待ち手自身の argv に載るため常に自己マッチする。
  `.done` も成果物も揃った後に 2 本 (段 2 用 20 時間 23 分、段 6 用 7 時間 36 分) 滞留し、
  親 session は通知待ちのまま 7 時間 36 分停止して wave が無音で死んだ。別 session が引き取って
  完遂した。同 wave の `wait2.sh` / `wait6.sh` は pattern を script 内へ埋め込んでおり正常終了
  しているため、正例と失敗例が同一 wave 内に揃っている。
  恒久対応: **producer の生死は pid で直接見る** (`kill -0`)。pattern 照合を使うなら
  待ち手自身の argv に pattern を載せない。`DW-M05` の自己マッチ禁止は変異 harness の節にあり
  汎用待ち手には掛からなかったため、`DW-C00` の待ち手条項へ同じ禁止を入れた。
