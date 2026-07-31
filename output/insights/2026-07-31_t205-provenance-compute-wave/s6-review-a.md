# 段 6 敵対レビュー A (実装の正しさと防壁の実効) — Claude opus, read-only

判定: **NO-GO** — 防壁 (hook) が同一 commit の `AGENTS.md` が明示許可する形を拒否し、かつ引数順で迂回できる (MF-1)。
checker 本体の A-R1 対策・waiver・bitset・並列化は破れなかった。

静的読解・grep・`git diff`・`python3 -m py_compile`・`guard_bash.decide` の純関数 probe のみ使用。
**pytest・ビルド・qsub は 1 度も実行していない。**

## MF-1 (must-fix) hook の `-m <module>` 分岐が read-only な静的検査を拒否し、しかも引数順・sub-command 形で迂回できる

根拠: `hooks/guard_bash.py:530-532` (`return _invocation_path(script, repo_root), False, module` —
非 provenance module でも script 引数を**積極的な違反**に変える)、`:556-557`、`:570-572`。
対照は同 diff の `AGENTS.md`「許されるのは静的読み取りと `python3 -m py_compile` まで」と
runbook §7「**hook が閉じるのはこの綴り差だけである**」。

実測 (`GB.decide(cmd, site="PEGASUS_LOGIN")`、worktree 版 hook を import して評価):

| command | 実測 |
|---|---|
| `python3 -m py_compile tools/check_ai_provenance.py` | **DENY** |
| `python3 -m json.tool tools/check_ai_provenance.py` | **DENY** |
| `python3 -m flake8 …` / `-m pdb …` | **DENY** |
| `python3 -m py_compile hooks/guard_bash.py tools/check_ai_provenance.py` | **ALLOW** (引数順を変えるだけで迂回) |
| `python3 -m coverage run tools/check_ai_provenance.py --range A..B` | **ALLOW** (実際に重い履歴監査を起動する形) |

失敗シナリオ: land 後、ログインノードの Claude セッションは checker の構文検査を打てなくなる。
段 5 の指示「子は静的検査 (`python3 -m py_compile`) までとし」がこのファイルについてだけ実行不能になり、
hook 迂回は規律で禁止されているため回避手段がない。逆に本当に重い `-m coverage run` は素通る。
現時点で気付かれていないのは、稼働中の hook が `$CLAUDE_PROJECT_DIR` = 本体 repo 側の旧版
(`git show main:hooks/guard_bash.py | grep -c _provenance_violation` = **0**) だからで、
U1 報告の「`python3 -m py_compile` OK」も旧 hook 下の実測である。

成果物影響: 段 5/6 以降の全 Claude セッションで `python3 -m py_compile tools/check_ai_provenance.py` が
機械拒否され、dev-wave の定型 (実装 → 静的検査 → commit) がこのファイルについて実行不能になる。
同時に runbook §7 と `hooks/README.md` の「閉じるのは綴り差だけ」が実装と食い違う (過剰拒否と迂回可能の両方向)。
U2 の受理集合表にこの行が無い = 自己申告と実装の食い違い。

修正案: `-m <非 provenance module>` は「違反」ではなく「**sanctioned 借用の抑止**」として扱う。

- `guard_bash.py:530-533` を `_provenance_entry` から外し、別関数
  `_provenance_script_borrow(head, args) -> bool` (`-m` 形の第 1 非 option 引数が basename 一致) にする。
- `:570-574` を次にする。

      violation = _provenance_violation(raw_head, head, args, repo_root)   # 直接実行形のみ
      if violation: return violation
      if not _provenance_script_borrow(head, args) and _is_sanctioned(...): return None

  `python3 -m pytest tools/check_ai_provenance.py` は既存の `:585-589` が拒否するので M13 の期待赤は保たれ、
  `-m py_compile` / `-m json.tool` は素通る。
- `test_hooks.py:836-848` (`test_bash_login_provenance_branch_does_not_capture_readers`) に
  `python3 -m py_compile tools/check_ai_provenance.py` と
  `python3 -m py_compile hooks/guard_bash.py tools/check_ai_provenance.py` の両方を正例として足し、順序非依存を固定する。

## MF-2 (must-fix) 既存約 100 テストが site 判定を ambient に取り、login 分類ホストでは 1 テストにつき実 qsub を投げる

根拠: `orchestrator/tests/test_check_ai_provenance.py:235-252` (`_run_range` は `provenance.main()` を
`site=` 無しで呼ぶ)、`tools/check_ai_provenance.py:1043-1055` (`site is None` → `current_site()`)、
`:1006-1011` (`_default_dispatch` は本物の `dispatch_compute.dispatch`)。
U1 も自認しているが、**コード側に歯止めが無い**。

失敗シナリオ: `PEGASUS_LOGIN` 分類のホストで suite を回すと、`_run_range` を使う約 100 node が
監査ではなく site gate を測り、**1 node ごとに実 PBS job を投入して poll する** (walltime 30 分)。
`PEGASUS_SUSPECT` なら全 node が rc=16 で赤。共有 queue を数十本占有しうる。

成果物影響: 受入 (D-6 の baseline byte 一致) と回帰検出の意味が実行ホストの hostname 分類に依存し、
login 分類では監査ではなく dispatch を測る別テストに化ける。

修正案: `_run_range` の `provenance.main()` に `site=site_policy.OTHER` を渡す (`main` は既に `site=` seam を持つ)。
`test_message_file_gate_uses_staged_paths` など `provenance.main()` を直接呼ぶ既存 node も同様。
site gate の検出力は専用 5 本 (`:2769-2846`) が持つので落ちない。

## 攻撃したが破れなかった点

1. **A-R1 の別経路探索 (最重要攻撃)**: `normal_findings` が waived の関数であることの消費点を全部辿った。
   `:897` の `target_missing not in target.normal_findings` が見る文字列は `validate_message` 由来の
   「AI-Agent trailer がない」であり、waiver が消せるのは `validate_implementation_author` の 1 finding だけ、
   増やせるのは `_waiver_audit` 由来の別文言だけなので、この判定は 1 bit も動かない。
   `suppressed_missing` は `(commit, finding)` の対で waiver に依存しない。**受理集合が広がる第 2 経路は構成できなかった。**
2. **非遡及**: `_waiver_audit` は epoch 判定の内側でだけ呼ばれ、担い手資格の `correction.waiver.exact` も
   epoch 前は `EMPTY_WAIVER` のまま False。message-file 経路の無条件呼出は既存と同じ非対称で fail-closed 方向にしか効かない。
3. **waiver の 3 重照合を 12 形で攻撃**: folded、divider 越え、block 分割、`reason` 大文字、`;` 後の空白欠落、
   日付ゼロ詰め無し、body 内配置、複数 block、CRLF、key 前後の空白、key の大小、colon 直後の空白欠落。
   **exact を通せた誤形はゼロ。** raw / canonical / final-block の 3 つが互いに補い合う非対称が実際に発火している。
   `role=author` 要求は同一 block 由来の値だけを見ており別 block を借りられない。
4. **bitset 等価性**: 逆順走査で親が先行、反射性は `merge-base --is-ancestor A A` と一致、
   `index.get` の None は shallow/graft のみ、pickaxe は tip 非依存。argv 前置 4 語を保存しているので
   intercept テストは畳んだ 1 本でも発火し rc=2 が保たれる。
5. **逐次 oracle の自己参照検査**: `ancestry=None` は production に残り、等価性テストは `_build_ancestry` を
   `lambda selected: None` へ差し替えて oracle arm を作る。oracle は `merge-base` + per-commit pickaxe の
   **独立実装**なので自己参照ではない。恒真化防止に非空を先に固定している。
6. **thread safety**: `Executor.map` は入力順で yield し `list()` は入力順で最初の例外を送出する。
   index を書きうる `git diff --cached` は message-file 経路 (単一スレッド) だけ。
   **新規の共有可変 module global は無い** (grep 済み)。
7. **site gate の無限ループ**: `PEGASUS_SUSPECT` の rc=16 分岐が login 分岐の**前**にあり、
   計算ノードで `bnodeNNN` 以外に分類されても再 dispatch にならない。`dispatch_compute.py:474-476` が二重の歯止め。
   `--message-f` の接頭辞省略は `parse_args` 後の判定で免除される。
8. **免除件数の意味**: 3 早期 return は全て `False`。出力ループは `if findings:` の**前**なので rc=1 でも出る。
9. **変異事前登録の帰属**: M1〜M7・M9〜M12・M14 は期待 node の assert をコードで追って実 KILL を確認。
   M2 は「canonical multiplicity が同時発火して殺せないのでは」を疑ったが needle が限定されているため一意に落ちる。
   M4 の vector は A-R1 の反例を実際に含み、guard を外すと rc 1→0 で落ちる。
10. **並列度テストの実効性**: `measure(1)` は構造的に peak 1 を強制、`measure(4) >= 2` は
    0.05 秒 × 11 commit に対しフレークしない。ソース文字列 grep 型の恒真ゲートは排除されている。
11. **docs 側の実測**: `wc -c` = **8942** ≤ 9000、`WAIVER_POLICY_LITERAL` と 2 needle の count は各 **1**、
    `_implementation_policy_commit()` = `8c6d3f3…` で pin テストと一致。
12. **`ImplementationWaived.label` 化**: 計上は `waived_applied` が駆動し、`label` は印字行と等価比較にしか現れない。
    「受理集合に影響しない」という U1 の自己申告は正しい。
13. `tools/codex_reasoning_ab.py:97` の sha256 pin は凍結 replay で作業ツリーを hash しないため赤にならない。

## nit / backlog

- 前方訂正の担い手が waiver で失格したとき、**理由を説明する finding が無い**。規律 3 の観点で 1 行足す価値がある。
- M8 の期待 KILL は**確率的**。`audits` が入力順であることを直接 assert する node を足すと帰属が決定的になる。
- `_build_ancestry` の pickaxe は `*commits` を argv に置くため巨大 range では `ARG_MAX` 超過 → rc=2 (現 repo 609 commit ≈ 25 KB では届かない)。
- `hooks/README.md` / runbook §7 の「綴り差だけ」は MF-1 の実測と食い違う。MF-1 を直せば整合する。
- `test_hooks.py` が module 先頭で `import pytest` するようになったため素 runner が pytest 非導入環境で ImportError になる。
  同 `_run()` は parametrize node を skip するので M13 の期待赤も素 runner では走らない。
- `dev_waves/checker.py:339` の 16 分岐は全 spec に効くが、16 を返しうるのは dispatch 経路の 2 spec だけで実害なし。
  `ReasonCode` に infra 専用値が無いので `CHECK_FAILED` の選択自体は妥当。
- `AI-Agent-Waiver` の raw 正規表現は `IGNORECASE` で key 前後の空白も許すが、`_correction_audit` と同じ許容度なので新規の緩みではない。

## 総括

攻撃の主目標だった **A-R1 対策は破れなかった**。`and not correction.waiver.exact` は担い手資格の側で閉じており、
`normal_findings` が waived の関数であることの他の消費点を全部辿っても受理集合が広がる第 2 経路は構成できなかった。
waiver の 3 重照合も 12 形の誤形で 1 つも exact を通せず、bitset 等価性・逐次 oracle の非自己参照性・
`pool.map` の順序と例外伝播・site gate の非ループ性も破れなかった。checker (U1) 側は**設計・実装ともに堅い**。

破れたのは**防壁 (U2) の hook 分岐**である。`-m <module>` 形の判定が「sanctioned を借りさせない」ではなく
「積極的な違反にする」実装になっているため、同一 commit の `AGENTS.md` が明示許可する
`python3 -m py_compile tools/check_ai_provenance.py` を拒否し、`-m json.tool` のような純読み取りまで巻き込む。
同時に引数順の入れ替えと `-m coverage run` で迂回でき、後者は実際に重い履歴監査を起動する。
**過剰拒否と迂回可能が同居しており、防壁としてほぼ無価値なうえ正当な作業だけを止める。**
稼働中の hook が旧版だったため段 5 で顕在化しなかった。

二次的に、`_run_range` が `site=` を渡さないため既存約 100 node が実行ホストの hostname 分類に依存し、
login 分類では実 qsub を投げる。「受入は必ず計算ノードで」という U1 の申告は正しいが、コード側に歯止めが無い。

MF-1 を直せば hook・runbook・`hooks/README.md` の逐語も同時に整合する。MF-2 は 2 行の変更で検出力が上がる。
この 2 点の fix 後は GO でよい。
