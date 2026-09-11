---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-11
wave: dev-wave-t2397-a1-attempt4
seq: 1
---

## 再発

### F763

- **再発: 2026-09-11** — A-1実装waveのcampaign関連走で46件が/tmp/.gitにより出力先をrepo内と判定して赤になった。directoryは他者所有で非接触とし、Git祖先のない専用TMPDIRとrun_tests.pyの実行場所判定で再実行した。request991839の子は414passed/3skipped。親の取消要求はPRRで見送られinfra終了したため、子の終端・request hash・source cleanを確認してversioned/旧形式の両holdを解除した。記録はoutput/insights/2026-09-11/t2397-a1-attempt4/README.md。

### F764

- **再発: 2026-09-11** — 未commitのloop.pyを含む状態でA-1関連走を始め、30件がcontract-loader-driftで拒否された。検査を緩めずcommit固定後に同じfileを再走し203passed。実装差分の失敗と未固定状態の拒否を区別した。

### F785

- **再発: 2026-09-11** — 変異probeはbaselineと6変異を記録したが、wrapperの共有木事後比較がfalseとなりrc125。同一の判定コードを独立cloneへ移した最終走では全期待nodeが一致し、shared_snapshot_matchesとteardown_completedがtrue、rc0となった。共有木検査を無効化せず、既存の独立clone手順を使った。
