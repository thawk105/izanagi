### B-01 / must-fix — `local-ok` 実測は sanctioned 化で開く全入力を覆っていない

- **判定:** **real**。argparse 上の subcommand は表どおり 4 個だけだが、全 subcommand が `--repo-root` / `--cache-root` を受け取る（`tools/pegasus/fetch_third_party.py:672-684`）。前者は別 repo の policy を読む（`:72-95`, `:98-105`）、後者は repo 外の任意絶対 path を受ける（`:108-129`）。一方、実測表は現在の pin 限定と明記される（`docs/pegasus-runbook.md:406-417`）。
- **再現:** `GB.decide("python3 tools/pegasus/fetch_third_party.py fetch --repo-root /work/alternate --cache-root /work/cache", site="PEGASUS_LOGIN")` は静的確認で `(True, "")`。有効な別 repo の policy/CMake を用意すれば、3 名は固定でも GitHub URL/pin は差し替え可能（`orchestrator/campaign/silo_ladder_rung1.py:844-868`）で、`:550-555` が未計測 repo を clone する。runbook は未計測または hard cap のない入力を `unknown`、すなわち `dispatch-required` とする（`docs/pegasus-runbook.md:358-360`）。
- **契約:** CLI は policy/source 異常を rc=1/2 にする点では fail-closed（`fetch_third_party.py:717-725`）だが、site・資源 admission gate は持たない。したがって `hooks/guard_bash.py:180-182` の「全 subcommand が local-ok」は、実際に許可される全 argv/env へ一般化できない。`submit_silo_ladder_rung1.sh` も runbook では `unknown`（`docs/pegasus-runbook.md:393-404`）なので、安全性の先例にはならない。
- **成果物影響:** 未計測 clone/status が login cgroup を圧迫して hydrate/submit を止めると、既存 certified 値は書き換えないが rung1 の試行行・レポート参照が生成されない。
- **scope 判定:** **scope 外**。実効修正には argv/env を含む admission、CLI 自身の site gate、入力 cap、または再裁定が必要。comment の限定だけでは受理集合を閉じない。

### B-02 / backlog — P2 の既存借用穴に、新しい pytest 実行別名が増える

- **判定:** **real**。P2 が「既存の族欠陥」とする分類自体は正しいが、受理集合の増分は実在する。結合形 `-mpytest` は module と認識され（`hooks/guard_bash.py:422-451`）、最初の非 option 引数で sanctioned status を借り（`:479-499`）、`:606-608` の早期許可へ入る。
- **再現:** `GB.decide("python3 -mpytest tools/pegasus/fetch_third_party.py orchestrator/tests", site="PEGASUS_LOGIN")` は `(True, "")`。同じ入力の分離形 `python3 -m pytest ...` は拒否された。前者が実行するのは fetch CLI ではなく pytest である。
- **成果物影響:** login の受理集合に全テストを起動できる別名が 1 個増えるが、既存 sanctioned decoy でも同じ能力があるため certified 選択・レポート・台帳 schema に固有の新差分はない。
- **scope 判定:** **scope 外**。親 brief どおり族修正の裁定パッケージ行き。must-fix には数えない。

### B-03 / backlog — sibling control が、land 済み login 手順の拒否を固定している

- **判定:** **real**。`tools/pegasus/README.md:114-125` は「ジョブ終了後、ログインノード」で `collect_receipt.py` を実行する手順を正本化しているが、新テストは同じ path の拒否を要求する（`orchestrator/tests/test_hooks.py:915-922`）。
- **再現:** README の引数を含む command を `PEGASUS_LOGIN` で `decide()` すると、「非 sanctioned Pegasus 実行体」として拒否された（分岐は `hooks/guard_bash.py:610-612`）。
- **検出力上の補足:** control 自体は恒真ではない。Pegasus directory 全体を sanctioned にする変異なら早期許可へ反転して赤くなる。ただし既存 `exec_calibrate.py` control（`test_hooks.py:976-979`）と冗長であることは事前登録済み。
- **成果物影響:** hooked Bash では canonical 手順から final receipt を作れず、その surface では calibration attempt が受理・レポート化されない（`tools/pegasus/README.md:127-136`）。拒否挙動自体は本 wave 前から存在し、新テストはそれを固定するだけ。
- **scope 判定:** **scope 外**。collector の資源分類と sanctioned 可否を別裁定すべきで、must-fix には数えない。

### B-R1 / docs・module 綴り・README 複製

- **判定:** **refuted**。`python3 -m tools.pegasus.fetch_third_party fetch` は `_python_module_target()` が `tools/pegasus/fetch_third_party.py` へ解決し（`hooks/guard_bash.py:454-466`）、静的確認でも許可された。
- **具体確認:** landed 手順は direct exact path の 4 形（`tools/pegasus/README.md:190-197`）で、いずれも今回の判定を通る。documented wrapper はない。差分は guard と test の 2 file だけで、`hooks/README.md` へ一覧を複製していない。同 README の正本契約（`:78-82`）を維持している。
- **成果物影響:** なし。
- **scope 判定:** 本 wave の実装で充足。

### B-R2 / 追加テストの mutation 検出力

- **判定:** **refuted**。sanction 行をメモリ上で除去すると direct/module とも拒否へ反転した。
- **確実に赤くなる nodeid:**
  - `orchestrator/tests/test_hooks.py::test_bash_login_allows_fetch_third_party_sanctioned_spellings`
  - `orchestrator/tests/test_hooks.py::test_bash_login_fetch_third_party_entry_is_exact`
- **具体確認:** 前者は `(ok, why)` を正しく受け、`site="PEGASUS_LOGIN"` を明示する（`test_hooks.py:901-905`）。後者は membership を直接 pin する（`:908-912`）。置換 anchor は各 1 箇所。skip/xfail/恒真条件・working-tree hash 等の揮発値はない。
- **補足:** compute test（`:925-929`）は sanction 行削除に非感応だが、M1 の期待赤には登録されておらず、上記 2 node が受理集合変化を捕捉する。sibling control も glob 拡大には反応する。
- **成果物影響:** 期待した退行検出力は存在し、欠落なし。
- **scope 判定:** 本 wave の scope 内で充足。

## 親前提 P1 / P2 / P3

- **P1:** exact path・module 解決については成立。ただし「1 行で全受理集合を安全に限定できる」までは B-01/B-02 により不成立。
- **P2:** 既存族欠陥という分類は成立するが、新しい許可別名が増えないという一般化は不成立。
- **P3:** CLI が authoritative evidence でないため certified 受理集合不変という主張は成立する（`tools/pegasus/README.md:210-212`）。ただし資源枯渇による試行行の欠落までは免責しない。

## 総括

- must-fix: **1 件**（B-01、scope 外のため裁定なしでは land 不可）。
- scope 外の real 所見: **3 件**（B-01〜B-03）。
- in-scope のテスト検出力・docs 綴り・module 解決には must-fix なし。
- 残リスクは、未計測 argv/env の全面許可、既知の sanctioned 借用族、collector 手順との既存不整合。
- pytest は実行していない。`decide()` の静的直呼びと source/diff 検査のみであり、緑は主張しない。