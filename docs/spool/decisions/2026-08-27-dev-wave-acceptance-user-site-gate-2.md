---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-27
wave: dev-wave-acceptance-user-site-gate
seq: 2
---

## {{D:bound-runner-user-site-gate}}. 束縛 runner の dependency は外側で検証した path を argv で渡して開ける

**決定:** 計算ノードの束縛 runner (`tools/pegasus/dispatch_compute.py` の
`_run_bound_tests_child`) が `-I` によって user site を失い `pytest-xdist` を見失う障害を、
次の形で直す。**`-I` は維持する。**

1. **外側の `_job_run()`** (非隔離、既に import probe 済み) で
   `importlib.metadata.distribution("pytest-xdist").locate_file("")` から root を解決する。
2. 外側で **絶対 path** ・ **実在 directory** ・ **import 済み `xdist.__file__` の包含**を検査し、
   どれかを満たさなければ `DispatchError` で **fail-closed** に止める。
3. 検証済みの root を **positional argv** で隔離子へ渡す。**環境変数では渡さない。**
4. `_BOUND_RUNNER_BOOTSTRAP` は source を compile する前に **`sys.path.append()`** するだけとし、
   **子の中で `site` にも `os.environ` にも問い合わせない。**
5. 注入した root を result payload の `bound_xdist_distribution_root` へ記録する。

**先頭挿入 (`sys.path.insert(0, ...)`) と `site.addsitedir()` は禁止する。**

**理由:**

- **`site.getusersitepackages()` は使えない。倒れ方が逆である。**
  `PYTHONUSERBASE` を差し替えると `site` 経路は攻撃者の path を黙って返し (fail-open)、
  `importlib.metadata` 経路は `PackageNotFoundError` で止まる (fail-closed)。
  `-I` は startup の環境解釈を止めるが `site._getuserbase()` の `os.environ` 読取りは止めない。
  子の中で `site` に問い合わせると **`-I` が閉じた注入面を開き直す**。
- **テストの受理集合は広がらない。** 実 pytest 子は元から `-I` 無しで起動されており
  (`tools/run_tests.py` の `cmd = [python_executable, "-m", "pytest"]`)、
  テスト本体は user site を既に見えていた。壊れていたのは**可用性を判定する gate が
  隔離側にあった**点だけである。広がるのは control runner 自身の import 面であり、
  そこを guardrail で狭める。
- **末尾 `append` に限れば `.pth` と `usercustomize` は実行されない。**
  先頭挿入は system site を shadow して**従来通っていた入力を新規拒否**しうる
  (受理集合を狭める方向の害)。`addsitedir` は `.pth` を実行してしまう。
- **`-s` を落とすこと自体が必須防護だという契約は一次資料に存在しない。**
  `-I` を入れた commit の message は「候補外 launcher が受領証を作る / blob bytes を stdin で渡す /
  pathname から import しない / 実行後に blob を再取得して照合」を明記するが、
  `-E` と `-s` の個別の脅威モデルは message にも diff の負例にも無い。
  同 commit のテストも pathname 側を毒化するだけで user site を毒化していない。

**却下した選択肢:**

- **`PYTHONPATH` で復元** — `-I` が `-E` を含むため無効。`PYTHONPATH` は tests の
  env allowlist にも無い。
- **`-I` を廃止 / `-E` だけにする** — user site に加え `.pth` が追加する任意 directory、
  `.pth` 内 `import` 行によるコード実行、`usercustomize` などの startup hook、
  `-c` の cwd まで受理される。本決定より実質的に広く、隔離境界を実際に壊す。
- **xdist を system site へ導入** — repo 外の環境変更。全 node への展開漏れと version drift を
  repo の検査で固定できない。
- **gate を実 pytest 子へ移す** — 設計としては最良だが `tools/run_tests.py` の変更を要し、
  land が main と tip の blob 一致を要求するため wave branch で land できない。
  **land 契約側の課題として別途起票した。**
- **`runner_binding` 経路の機能撤退** — launcher が K 件の binding report を必須とするため
  receipt が発行されない。診断には使えるが land 用の修理にならない。

**この決定が保証しないこと:**

- 末尾 `append` では user site の `.pth` が追加する path は復元されない。
  **`.pth` 経由でしか入らない依存が将来要求されたとき、同じ無言 rc=16 が再発する。**
- `tools/run_tests.py` は repository root 挿入より前に `packaging.version` を import するため、
  **root 挿入前に import される module だけは user site から来うる。**
