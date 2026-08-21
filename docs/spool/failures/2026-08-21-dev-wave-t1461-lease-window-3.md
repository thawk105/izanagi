---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-21
wave: dev-wave-t1461-lease-window
seq: 3
---

## 再発

### F1

- **再発: 2026-08-21** (受入lease排他区間短縮waveの段1 brief)。依頼文が引用した具体的な数値
  (「受入投入〜land完了7時間中、実テスト8分44秒・残り98%超」) を、引用元として名指しされた
  `output/insights/2026-08-20_t870-congestion-nproc/README.md` の実際の文字列と照合せず brief
  へ転記した。段3敵対レンズ (luna) が独立に grep で該当数値の不在を検出し、親が追認した。
  転写対象が日付・機構の実在状態・推測の確度に続き、**依頼文中の引用数値**へ広がった顕在化。
  問題の定性的な結論 (lease順番待ちが実テスト時間を大きく上回る) 自体は別の一次資料
  (`output/insights/2026-08-20_t870-acceptance-lease-timing/README.md`) が独立に支持しており
  誤りではなかったが、具体的な数値の出典は未確認のまま記録した。実害は段4裁定で
  「実装しない」に転じたため無し。恒久対応は memory から変更なし — 依頼文自身が引用する数値も、
  他の docs 引用と同様に一次資料の文字列と照合してから根拠にする。
