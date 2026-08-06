---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-06
wave: dev-wave-t454-testification
seq: 2
---

## 再発

### F104

- **再発: 2026-08-06** — 三つ目の方向。親が段 6 の待ち手に
  `pgrep -f 'dev-wave-t454-testification/s6/lens'` を書き、**待ち手自身の cmdline が
  同じ文字列を含む**ため常に一致した。生産者が死んでも「実行中」と読み続ける待ち手であり、
  `.done` が出るまで抜けられない。張り直して是正した (`s[6]` の文字クラス回避)。
  F104 は codex 子の生死判定として記録されているが、**現行 `DW-M05` の照合規律は
  変異 harness の文脈でしか書かれていない**。実際には親が張る全ての子 process 待ち手で発火する。
  射程拡張の逐語 draft (112 bytes) は本 wave の裁定パッケージ §B-5 にあるが、
  `docs/dev-wave/**` の byte 予算 (25,187 / 25,200) に阻まれて採録できていない。
