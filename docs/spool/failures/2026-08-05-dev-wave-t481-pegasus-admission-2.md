---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-05
wave: dev-wave-t481-pegasus-admission
seq: 2
---

## 新規

### {{F:pegasus-blanket-rule-porous}}. 一律 prefix 判定の防壁が 6 通りの綴り替えで抜けられていた [防壁の射程誤認] [テスト代表性]

- 事象: `hooks/guard_bash.py` の「`tools/pegasus/` 配下は sanctioned でなければ拒否」という
  一律判定を狭める作業の途中で、**その一律判定自体が既に porous だった**ことが実測で判明した。
  ログインノードで拒否されるはずの綴りのうち、次が実際には通っていた —
  `python3 -m cProfile <pegasus path>` (任意 argv を `os.execv` するトランポリンに到達可能)、
  `python3 -m pytest.__main__` / `-m _pytest.main` (pytest 拒否の迂回)、
  `python3 -W ignore <pegasus path>` と `bash -O extglob <job body>` (interpreter option の値を
  script と誤認)、`cd hooks && python3 ../tools/pegasus/...` (cwd 非追跡)、
  `systemd-run --user --scope -- pytest -q` (未解析 launcher)、`bash -lc` の 3 段ネスト
  (再帰打ち切りが許可へ倒れる)。
- 根本原因: 実行体の同定が「head の後、最初の非 option token」というヒューリスティクスだけで、
  interpreter / shell の実 CLI 文法 (値を取る option、`-m` の意味、startup file) を持っていなかった。
  テストは代表綴りを 1 形ずつしか固定しておらず、綴り差の族を張っていなかった。
- 恒久対応: {{D:pegasus-admission-registry}} 決定 5・6 (実行体の意味規則と単調性)、
  および `orchestrator/tests/test_hooks.py` の `-m` matrix・interpreter prefix・
  script executor の各テスト群。前 4 者は本 wave で閉じた。
  残る cwd/symlink・`env -S` 文法・ネスト深さ・未解析 launcher は
  {{T:guard-bash-residual-bypasses}} として裁定へ返す。
- 再発検知: 上記テスト群に加え、変異 M1 / M4 (executor 閉集合と option 値消費を壊すと赤) と
  親が実 hook subprocess で 69 綴りを照合する probe (`probe_fix.py`)。

### {{F:norm-procedure-barrier-three-way-drift}}. 規範・手順・機械防壁が三者で食い違っていた [誤前提] [ドリフト]

- 事象: `tools/pegasus/README.md` §3 が「ログインノードで実行する」と定める `collect_receipt.py` を
  hook が拒否する、という報告 ([T-481]) を「hook の過剰拒否」として起票していた。実測すると、
  同 CLI は scheduler stderr を全文メモリへ読み (`read_text`)、JSON も全読みし、`rglob` の全件を
  materialize する。`docs/pegasus-runbook.md` §7.0 は「入力サイズに上限が無い」ものを
  `unknown` = `dispatch-required` と定めているので、**拒否している hook の方が規範に忠実で、
  食い違っていたのは手順書の方**だった。
- 根本原因: 規範 (§7.0)、手順 (README §3)、機械防壁 (hook) が別々に更新され、どれが正本かを
  機械検査していなかった。3 者の整合を止める検査は存在しない。
- 恒久対応: {{D:pegasus-admission-registry}} 決定 2・3 (証拠 field と、証拠なき昇格の禁止)。
  registry が `reason` / `primary_gate` / `evidence` を持つことで、hook 側の判定と根拠が
  同じ場所に並ぶ。3 者同期の機械検査は {{T:pegasus-admission-registry-authority}} として
  裁定へ返す (未実装であり、本項の恒久対応は「証拠を registry に持たせる」までである)。
- 再発検知: `test_bash_pegasus_registry_schema_and_fixed_classes` が class と evidence の
  独立 golden を固定し、変異 M3 (class を 1 行変える) で赤になる。

### {{F:classification-bootstrap-deadlock}}. 分類に必要な実測を防壁自身が拒否した [手順漏れ]

- 事象: 段 1 で `collect_receipt.py` の資源を §7.0 の手順で測ろうとしたところ、
  `hooks/guard_bash.py` が rc=2 で拒否した。計算ノードへ逃がす経路も無く
  (PBS ジョブに user systemd session が無いため `systemd-run --user --scope` が rc=1。
  ジョブ自身の cgroup は `nqs-jsv.service` 配下で他テナントと混ざる。2026-08-05 実測)、
  wave 自身の worktree で hook を書き換えても効かなかった
  (Bash 面を支配するのは main checkout の hook。`DW-O19` 準拠で一時変異・即復元して実測)。
  結果として「allowlist に載せるには実測が要る / 実測するには allowlist に載っている必要がある」
  という循環が確定した。
- 根本原因: admission gate が、自分の入力 (資源分類) を作る操作まで対象にしていた。
  測定用の正規経路が設計に無い。
- 恒久対応: {{D:pegasus-admission-registry}} 決定 4 が、現行唯一の正規経路は hook の管轄外
  (ユーザー端末) であることと、迂回禁止を明記する。恒久的な測定経路は
  {{T:pegasus-measurement-surface}} として裁定へ返す。
- 再発検知: `docs/pegasus-runbook.md` §7.0 の該当段落 (測定手順が計算ノードで成立しないことと、
  循環の存在を本文で固定した)。

### {{F:fix-prompt-restore-without-exceptions}}. 「変更前へ戻せ」の指示が例外を落として land 済みテストを赤くした [手順漏れ] [テスト代表性]

- 事象: 段 6 の fix で親が「変更前の判定を復元せよ」と指示したところ、実装子が復元を過大に適用し、
  `python3 -m pytest --collect-only` / `-qm pytest --help` まで拒否して land 済みテスト 2 本
  (`test_bash_login_nonexecuting_forms_allowed` /
  `test_bash_login_python_module_option_boundaries_allowed`) が赤になった。
  変更前の判定は pytest の非実行形を許可する例外を持っていたが、指示がそれを書いていなかった。
- 根本原因: 復元指示が「拒否側の再現」だけを列挙し、「許可側の例外」を同じ粒度で列挙しなかった。
  fix 子は指示の文面に忠実で、誤りは指示側にある。
- 恒久対応: 段 8 で `docs/dev-wave/workers.md` の `DW-S06-B` へ「復元を指示するときは変更前の
  許可側の例外も同じ粒度で列挙する」を追記する (段 8 の自己改善)。
- 再発検知: 上記 2 テストは land 済みで、同型の過大復元は受入で必ず赤になる。

## 再発

### F112

- **再発: 2026-08-05** — fix prompt の「既存テストの期待値を変更しない」を tracked 限定と
  書かなかったため、fix 子が同 wave の段 5 で新設した assert を「既存テスト」と解釈して
  fail-closed で停止し、fix 1 巡がまるごと空振りした ([T-481] 段 6)。
