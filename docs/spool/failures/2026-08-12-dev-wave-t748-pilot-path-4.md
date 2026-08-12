---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-12
wave: dev-wave-t748-pilot-path
seq: 4
---

## 再発

### F8

- **再発: 2026-08-12** — 生成文書の定量ではなく、**敵対相談子が根拠として挙げた file path が
  実在しなかった**形。段 3 の子が `experiments/phase3-benchmark/scripts/floor_campaign.sh` を
  2 箇所で行番号つきに引用したが、repo 内に同名 script は `tools/pegasus/floor_campaign.sh` の
  1 本しか無い (親が `find` で実測)。**引用先が実在しないだけで、主張の内容は実体側で裏が取れた**ため
  結論は維持したが、突き合わせをしなければ捏造を根拠に採用していた。
  **恒久対応は F8 と同じで足りる** — 採用前に一次資料と突き合わせる規律が、
  定量値だけでなく**子が挙げた file:line 引用にも同じく効く**。
  本 wave の追加事実は、**正しい結論に誤った引用が付く**ため引用の実在検査を
  結論の妥当性判定と分けて行う必要がある点である。
