---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-02
wave: dev-wave-t2098-session-job-gap
seq: 3
---

## 再発

### F37

- **再発: 2026-09-02** — 親が local main 取り込み直後の provenance 監査を
  `python3 tools/check_ai_provenance.py 2>&1 | tail -5` で走らせ、報告された rc が `tail` のものだった。
  出力末尾には別 wave の commit message に埋め込まれた dispatch log が写っており、監査の結論行では
  なかった。パイプを外して file へ落とし rc を別に取り直したところ真の rc=0 だった。
  偽緑の実害は無かった (near miss、2026-08-04・2026-08-17 と同型で 4 例目)。
  恒久対応は F37 既存のとおり変わらない。
