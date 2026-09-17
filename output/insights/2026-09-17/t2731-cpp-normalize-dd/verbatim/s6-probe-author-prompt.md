単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/s4-ruling.md

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する。これは射影 file 限定の
停止規則であり、自分が推測して探した path が不在でも停止理由にしない。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/s4-ruling.md`
  — 親の段 4 裁定 (§1 の B-2 が本作業の根拠)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2731-probe/orchestrator/tests/test_t2630_scan_boundary_reach.py`
  — 編集対象 (probe branch にだけ存在する runner test。`EVIDENCE_ROOT` :25-27)

## 所有と権限

- 編集してよい file は `orchestrator/tests/test_t2630_scan_boundary_reach.py` の 1 つだけ。他の file・docs に書かない。
  commit・push・stash をしない。親が commit する。
- 既存 test の期待値・node・観測の意味を変えない。

## この段の仕事

`EVIDENCE_ROOT` の定数値を旧 job dir から今回の job dir へ変える。変更は次の 1 箇所だけ。

```python
EVIDENCE_ROOT = Path(
    "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/evidence"
)
```

理由: 段 3 レンズ B の B-2 — 旧値のままだと再走の `observations.json`・compiler 記録・TU 差分が T-2630 の job dir に混ざる。
親は `mkdir -p` で directory を用意済み。変更後に `python3 -m pytest orchestrator/tests/test_t2630_scan_boundary_reach.py
--collect-only -q -p no:cacheprovider` で 4 node が collect されること (実走はしない。計算ノード dispatch でしか走らない test) を確認する。

## 出力形式

Markdown。次の H2 節をこの順で必ず置く。

## 変更した file と差分
## collect-only の結果
## 総括

予算が尽きそうなら、途中までの結論をこの出力形式どおりに書いて終える。**無出力が最悪である。**
