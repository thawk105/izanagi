結論は must-fix 1 件、既存族として scope 外 4 件です。pytest・実 command は走らせず、差分と分岐の静的検査だけで判定しました。

## MF-A1 / sanctioned path が未計測の policy・pin まで許可する

- **判定: real / must-fix。** `_SANCTIONED_PATHS` 一致後は全 argv を無条件に早期許可します（[guard_bash.py:479](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t455-guard-bash-sanction-fetch/hooks/guard_bash.py:479)、[guard_bash.py:606](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t455-guard-bash-sanction-fetch/hooks/guard_bash.py:606)）。

- **具体 command:**
  ```bash
  python3 tools/pegasus/fetch_third_party.py fetch --repo-root /tmp/large-policy-repo --cache-root /tmp/t455-cache
  ```

  差分前は `_script_target()` が非 sanctioned Pegasus path を返し、[guard_bash.py:610](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t455-guard-bash-sanction-fetch/hooks/guard_bash.py:610) で拒否。差分後は exact path 一致により 606–608 行で許可されます。

  しかし実体は任意の実在 directory を `--repo-root` に受け入れ（[fetch_third_party.py:98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t455-guard-bash-sanction-fetch/tools/pegasus/fetch_third_party.py:98)、[fetch_third_party.py:677](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t455-guard-bash-sanction-fetch/tools/pegasus/fetch_third_party.py:677)）、そこから URL・pin を読み、3 repository を clone します（[silo_ladder_rung1.py:844](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t455-guard-bash-sanction-fetch/orchestrator/campaign/silo_ladder_rung1.py:844)、[fetch_third_party.py:518](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t455-guard-bash-sanction-fetch/tools/pegasus/fetch_third_party.py:518)）。

  Runbook は入力上限なしを `unknown = dispatch-required` とし（[pegasus-runbook.md:358](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t455-guard-bash-sanction-fetch/docs/pegasus-runbook.md:358)）、測定値を現在の pin に限定し、pin 変更時は再分類を要求しています（[pegasus-runbook.md:406](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t455-guard-bash-sanction-fetch/docs/pegasus-runbook.md:406)、[pegasus-runbook.md:416](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t455-guard-bash-sanction-fetch/docs/pegasus-runbook.md:416)）。したがって「全 subcommand local-ok」は「現 policy・現 pin・測定 argv」にしか一般化できません。

- **成果物影響:** 未計測 clone/検査が login の共有資源を圧迫すると rung1 試行が失敗・欠落し、certified 選択へ供給される測定行と台帳材料が変わります。
- **scope 判定:** scope 内。新 entry 固有の公開 argv が、裁定根拠となった測定集合より広く新規受理されています。
- **テスト穴:** 新テストは既定 argv 4 本だけです（[test_hooks.py:893](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t455-guard-bash-sanction-fetch/orchestrator/tests/test_hooks.py:893)）。`--repo-root`、policy/pin binding、将来の pin drift は緑のままです。

## SO-A2 / `-m <他 module>` が新 path の sanctioned status を借用する

- **判定: real / scope 外。** 指定例は通ります。
- **具体 command:**
  ```bash
  python3 -mpytest tools/pegasus/fetch_third_party.py
  ```

  `_script_target()` が Python の最初の非 option 引数を候補にして exact path を返します（[guard_bash.py:479](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t455-guard-bash-sanction-fetch/hooks/guard_bash.py:479)）。`_provenance_script_borrow()` は basename が `check_ai_provenance.py` の場合だけ発火するため（[guard_bash.py:560](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t455-guard-bash-sanction-fetch/hooks/guard_bash.py:560)）、606–608 行で早期許可され、pytest 拒否の [guard_bash.py:619](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t455-guard-bash-sanction-fetch/hooks/guard_bash.py:619) へ届きません。

  この具体 command の受理 bit は本差分で新しくなりますが、`submit_certify.sh` 等でも成立済みの同一族です。
- **成果物影響:** login で pytest を起動できる既存受理穴が新 path にも増えますが、certified/report/台帳に対する新しい欠陥類型ではありません。
- **scope 判定:** 明示された基準どおり scope 外の裁定パッケージ。P2 の分類は支持します。

## SO-A3 / path identity は実 file ではなく字面に束縛される

- **判定: real / scope 外。** `_invocation_path()` は `expanduser` と `normpath` のみで、候補の `realpath` や segment 間の cwd を追いません（[guard_bash.py:411](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t455-guard-bash-sanction-fetch/hooks/guard_bash.py:411)）。

| command | 静的判定 |
|---|---|
| `python3 ./tools/pegasus/fetch_third_party.py fetch` | 通る。repo 内同一 file |
| `python3 /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t455-guard-bash-sanction-fetch/tools/pegasus/fetch_third_party.py fetch` | 通る。repo 内絶対 path は相対化 |
| `python3 tools/pegasus/../pegasus/fetch_third_party.py fetch` | 通る。`normpath` 後は exact path |
| `python3 /tmp/copy/tools/pegasus/fetch_third_party.py fetch` | 差分前後とも通る。repo 外絶対 path は Pegasus target と認識されない |
| `python3 ~/copy/tools/pegasus/fetch_third_party.py fetch` | repo 外なら差分前後とも通る |
| `python3 ../copy/tools/pegasus/fetch_third_party.py fetch` | 差分前後とも通る |
| `cd /tmp/copy && python3 tools/pegasus/fetch_third_party.py fetch` | 差分後は通る。heavy 層が先行 `cd` を追わず、実際には repo 外 copy |
| repo 内の別名 symlink `tools/pegasus/fetch-link.py` | 非 sanctioned Pegasus path として拒否 |
| symlink と `..` を組み合わせ、字面だけ exact に正規化される path | 通り得る。candidate を `realpath` していない |

- **成果物影響:** repo 外 copy 実行は既に絶対・`~`・`..` 綴りで許可済みで、certified/report/台帳の新しい受理集合類型ではありません。
- **scope 判定:** generic sanctioned/path-resolution 族として scope 外。ただし `cd … && exact-relative-path` の具体受理 bit は本差分で増えます。

## SO-A4 / `xargs` は新 path 追加と無関係に素通りする

- **判定: real / scope 外。**
- **具体 command:**
  ```bash
  printf 'fetch\n' | xargs -n1 tools/pegasus/fetch_third_party.py
  ```

  `xargs` は `_WRAPPERS` に含まれず（[guard_bash.py:119](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t455-guard-bash-sanction-fetch/hooks/guard_bash.py:119)）、heavy head は `xargs` のままです。後続 path を `_script_target()` が見ないため、差分前から許可です。通常層の `_OPAQUE_RE` には `xargs` がありますが（[guard_bash.py:108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t455-guard-bash-sanction-fetch/hooks/guard_bash.py:108)）、proof-chain path がなく fast path で終わります（[guard_bash.py:957](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t455-guard-bash-sanction-fetch/hooks/guard_bash.py:957)）。
- **成果物影響:** script-file 越しという既知限界であり、本差分による certified/report/台帳の新規受理差はありません。
- **scope 判定:** scope 外。

## SO-A5 / sanctioned segment は quoted command substitution・here-doc 展開を覆い隠す

- **判定: real / scope 外。**
- **具体 command:**
  ```bash
  python3 tools/pegasus/fetch_third_party.py fetch --cache-root "$(pytest -q)"
  ```

  quoted `$()` は shlex 上で同一 argv token に残り、exact script による早期許可が先行します。heavy 層は `_OPAQUE_RE` を適用せず、通常層も保護 path がないため fast path です。実 shell は script 起動前に pytest を実行します。

  同型の here-doc は次です。
  ```bash
  python3 tools/pegasus/fetch_third_party.py verify --cache-root /tmp/t455-cache <<EOF
  `cmake --build build`
  EOF
  ```
  unquoted here-doc の backtick 展開は実行されますが、heavy parser は backtick 内容を再帰検査しません。

  これは既存のどの sanctioned path でも成立します。対照的に通常の `;` / `&&` / `|` / 改行は `_tokenize()` と `_segments()` で分割されます（[guard_bash.py:677](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t455-guard-bash-sanction-fetch/hooks/guard_bash.py:677)、[guard_bash.py:696](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t455-guard-bash-sanction-fetch/hooks/guard_bash.py:696)）。
- **成果物影響:** login 重量処理を隠せる既存 sanctioned 族の穴が新 path にも増えますが、新しい成果物受理類型ではありません。
- **scope 判定:** generic sanctioned/opaque 構文族として scope 外。

## RF-A6 / 通常 wrapper・明示的な複数 segment は別の重い head を通さない

- **判定: refuted。**
- `bash -c 'python3 tools/pegasus/fetch_third_party.py fetch'`、`sh -lc '…'`、`env …`、`nohup …`、`timeout 5 …` は通りますが、いずれも最終 head は exact script です。wrapper 展開は [guard_bash.py:302](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t455-guard-bash-sanction-fetch/hooks/guard_bash.py:302)、shell 再帰は [guard_bash.py:652](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t455-guard-bash-sanction-fetch/hooks/guard_bash.py:652)。
- 次はすべて拒否されます。
  ```bash
  python3 tools/pegasus/fetch_third_party.py fetch ; pytest -q
  python3 tools/pegasus/fetch_third_party.py fetch && cmake --build build
  python3 tools/pegasus/fetch_third_party.py fetch | make -j48
  python3 tools/pegasus/fetch_third_party.py fetch
  ninja -C build
  ```
  pytest/cmake/make/ninja の各分岐は [guard_bash.py:614](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t455-guard-bash-sanction-fetch/hooks/guard_bash.py:614)–650。
- **成果物影響:** なし。
- **scope 判定:** scope 内攻撃を実施し refuted。

## RF-A7 / 通常 argv で別 Pegasus 実行体を起動する形は通らない

- **判定: refuted。**
- 次は非 sanctioned module target が先に解決され、拒否されます。
  ```bash
  python3 -m tools.pegasus.exec_calibrate tools/pegasus/fetch_third_party.py
  ```
- 次は hook 自体は exact script として通りますが、fetch parser が余分な位置引数を拒否し、別実行体は起動しません。
  ```bash
  python3 tools/pegasus/fetch_third_party.py fetch tools/pegasus/exec_calibrate.py
  ```
  parser の閉じた subcommand/option 集合は [fetch_third_party.py:672](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t455-guard-bash-sanction-fetch/tools/pegasus/fetch_third_party.py:672)。
- **成果物影響:** なし。
- **scope 判定:** scope 内攻撃を実施し refuted。

## RF-A8 / 1 行削除の検出力と README 契約

- **判定: refuted。** sanctioned entry 1 行を消すと、少なくとも membership assert（[test_hooks.py:908](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t455-guard-bash-sanction-fetch/orchestrator/tests/test_hooks.py:908)）と LOGIN 正例（[test_hooks.py:901](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t455-guard-bash-sanction-fetch/orchestrator/tests/test_hooks.py:901)）が赤になります。
- `GB` は実 worktree の hook を直接ロードし（[test_hooks.py:32](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t455-guard-bash-sanction-fetch/orchestrator/tests/test_hooks.py:32)）、`site="PEGASUS_LOGIN"` と `(ok, why)` の受け取りも正しいため恒真ではありません。
- COMPUTE 正例は当該 1 行を消しても緑ですが、上記 2 test が kill するので変異検出は成立します。
- brief 指定の `exec_calibrate.py` は新 test にないものの、既存 positive control が拒否を固定しています（[test_hooks.py:976](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t455-guard-bash-sanction-fetch/orchestrator/tests/test_hooks.py:976)）。
- `hooks/README.md` は一覧を写しておらず、正本を `guard_bash.py` とする契約を維持しています（[hooks/README.md:78](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t455-guard-bash-sanction-fetch/hooks/README.md:78)）。
- **成果物影響:** 1 行削除の見逃し、および docs 二重管理による参照 drift はありません。
- **scope 判定:** scope 内検査、refuted。

## 親 provisional 裁定

- **P1:** refuted。正例を通すだけなら 1 行で足りますが、path-only sanction は `--repo-root` と将来 pin を測定 tuple に束縛しません。
- **P2:** 支持。借用は real だが既存 sanctioned 族であり、指定どおり scope 外です。
- **P3:** 「正しさ防壁ではない」は [hooks/README.md:78](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t455-guard-bash-sanction-fetch/hooks/README.md:78) と整合します。しかし「測定した4 subcommandだから新受理集合全体も local-ok」という根拠は refuted。軽量 wave か否かとは別に MF-A1 は閉じる必要があります。
- 親の rc=2 / rc=0 実測は、それぞれ「既定綴りが従来拒否」「借用族が既存」を示すだけで、任意 `--repo-root`・将来 pin・opaque 展開への一般化根拠にはなりません。

## 総括

- must-fix: **1 件** — sanctioned path と local-ok 測定 tuple が未束縛。
- scope 外: **4 件** — module 借用、path/CWD identity、xargs、opaque 展開。
- P1 は refuted、P2 は支持、P3 は local-ok 一般化部分を refuted。
- 1 行削除は新テストが確実に検出し、README 契約違反はない。
- 残リスクは sanctioned 族共通の lexical/opaque/script-file 限界。
- pytest・hook subprocess は未実走であり、緑は主張しない。