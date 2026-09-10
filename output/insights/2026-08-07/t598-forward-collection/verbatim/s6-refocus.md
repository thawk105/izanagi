静的再レビューの結論は **NO-GO** です。pytest は実行しておらず、以下の「検出」は assertion failure 条件へ到達するというコード読解上の判定です。

## 新たに確認した退行・残存穴

### N-1 — bare repository を repo 外として受理する — real / must-fix

`_validated_out()` は各祖先の `ancestor / ".git"` だけを探します。[collect_wave_usage.py:150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/collect_wave_usage.py:150)

bare repository は repository root 自身に `HEAD`、`objects/`、`refs/` を持ち、`.git` を持ちません。このため bare repo 配下の出力はそのまま受理されます。

**成果物影響:** repo 外保存契約に違反した artifact が land する。

### N-2 — 読めない `.git/HEAD` は受理側へ倒れる — regressed / must-fix

`.git` directory の判定は `(marker / "HEAD").exists()` に依存します。[collect_wave_usage.py:153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/collect_wave_usage.py:153)

`.git` directory 自体は識別できても、権限不足で `HEAD` を観測できない場合、`exists()` は偽となり repository でないものとして受理されます。marker の `stat` 自体が失敗する場合も `is_file()` / `is_dir()` は拒否を発火させません。これは第2巡が empty directory を受理するために導入した fail-open です。

一方、`path.resolve()` 自体が `OSError` や symlink loop を投げた場合は `_validated_out()` を抜けず、外側の `main()` が rc=0 に変換します。[collect_wave_usage.py:151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/collect_wave_usage.py:151) [collect_wave_usage.py:223](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/collect_wave_usage.py:223) こちらは artifact を公開しない拒否側です。

**成果物影響:** repo 外保存契約違反が land する。

### 共有 site policy の波及 — refuted

`current_site()` の既定値は `require_evidence=False` で、既存 caller は従来どおり `classify_site()` の結果をそのまま受け取ります。[site_policy.py:66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/campaign/site_policy.py:66) [site_policy.py:77](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/campaign/site_policy.py:77)

`_first_label()` の2回目の評価は `require_evidence=True` の新 helper 経路だけです。hostname 取得不能も `PEGASUS_SUSPECT` へ倒れます。既存の `run_tests.py`、`check_ai_provenance.py`、campaign caller の既定挙動を変える経路は見つかりません。

**成果物影響:** なし。

### 非ログイン開発機で収集されない条件 — real、非 must-fix

次では `blocked` artifact となり収集しません。

- `socket.gethostname()` が例外、空文字列、非文字列を返す。
- hostname が `pegasus02` 等だが NQSV 証拠を取得できない。
- hostname が `pegasus-dev` 等 `pegasus` prefix で、既知 login／compute に分類できない。

通常の `developer-box` 等は `OTHER`、`bnodeNNN` は `PEGASUS_COMPUTE` となり収集します。[site_policy.py:30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/campaign/site_policy.py:30) [site_policy.py:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/campaign/site_policy.py:81)

偽の観測値は保存せず、rc=0 の `blocked` へ倒れるため、D205 の prototype 基準では must-fix にしません。

**成果物影響:** なし。

### subprocess テストの不安定性 — real、非 must-fix

hostname は `sitecustomize.py` で固定され、通常環境では site 判定は安定しています。[test_collect_wave_usage.py:63](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_collect_wave_usage.py:63)

ただし次の環境依存があります。

- `tmp_path`／`--basetemp` が repository 配下なら、artifact を期待する subprocess テストは正しい repo 拒否によって artifact を得られない。
- repo 内出力の負例は `tmp_path.name` だけを使った repository-root 直下の名前です。変異・失敗実行が実際にファイルを作ると、同名が後続 run に残って偽赤を作ります。[test_collect_wave_usage.py:504](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_collect_wave_usage.py:504)

実害未観測の test hygiene であり、許された3種の成果物影響には該当しないため must-fix にはしません。

## M1〜M9 の変異事前登録

| 変異 | 静的判定 | 単一理由性・anchor |
|---|---|---|
| M1 | 検出条件へ到達 | `files_scanned=9` の zero fixture が `complete` 側へ変わる。[test:90](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_collect_wave_usage.py:90) 追加された priority fixture も同じ意味理由で反応する。anchor は不変。 |
| M2 | 検出条件へ到達 | limit 以外の理由がない fixture なので分岐削除で `complete` になる。[test:141](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_collect_wave_usage.py:141) |
| M3 | 検出条件へ到達 | `seen.index("--cwd-under")` が成立しなくなる。[test:161](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_collect_wave_usage.py:161) |
| M4 | 検出するが事前登録不適合 | call count、`subprocess` import、`json.loads` の3防壁が独立に反応し得る。[test:221](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_collect_wave_usage.py:221) 過剰決定で単一理由性を欠き、置換も実質複数変更になる。 |
| M5 | 検出条件へ到達 | collector rc=2 の実 process が returncode 0 を直接固定する。[test:512](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_collect_wave_usage.py:512) `_run()` 末尾を対象とする文脈付き anchor が必要。 |
| M6 | 検出条件へ到達 | existing output の bytes が truncate されるため equality が崩れる。[test:283](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_collect_wave_usage.py:283) |
| M7 | 新実装なら検出するが anchor stale | 旧 anchor `is_pegasus_login(site)` 分岐は `refuses_heavy_work(site)` に置換済み。[helper:198](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/collect_wave_usage.py:198) 新しい LOGIN＋SUSPECT 分岐全体へ再登録すれば blocked/call-count fixture が反応する。[test:302](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_collect_wave_usage.py:302) |
| M8 | 検出条件へ到達 | fallback すると status と `calls == 0` が崩れる。同じ「collector が呼ばれた」という意味理由である。[test:380](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_collect_wave_usage.py:380) |
| M9 | 検出条件へ到達 | `<p>-fix` が余分に集計され、期待2件が崩れる。[test:559](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_collect_wave_usage.py:559) anchor は不変。 |

意味どおり注入できた場合に明白な survivor はありません。ただし M4 は単一理由性を欠き、M7 は fix 後 anchor が変わったため、現状の事前登録のまま本走結果を受理できません。これは `DW-M01`／`DW-M07` の違反になります。[mutation.md:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/docs/dev-wave/mutation.md:5) [mutation.md:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/docs/dev-wave/mutation.md:44)

## 総括

### (a) 判定

**NO-GO**

### (b) 対応表

| 所見 | 判定 | 根拠 | 成果物影響 |
|---|---|---|---|
| C-MF1: site fail-closed | **closed** | evidence 必須化と LOGIN/SUSPECT 拒否。[helper:190](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/collect_wave_usage.py:190) [site_policy:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/campaign/site_policy.py:81) | なし |
| C-MF2: import境界＋実process | **partial / real** | subprocess rc fixture は追加済みだが、repo-local import は依然 `main()` より前。[helper:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/collect_wave_usage.py:7) [helper:223](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/collect_wave_usage.py:223) | 非 gate を破って wave が止まる |
| C-MF3: dangling symlink | **partial / real** | lexical destination を `resolve()` 後の target に置換したまま publish。[helper:150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/collect_wave_usage.py:150) [helper:177](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/collect_wave_usage.py:177) | create-only 規約違反が land する |
| C-MF4: M8 fallback | **closed** | status に加え collector call count 0 を直接固定。[test:380](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_collect_wave_usage.py:380) | なし |
| C-MF5: missing優先 | **closed** | zero call＋limit/issues の組合せを固定。[test:110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_collect_wave_usage.py:110) | なし |
| C-MF6: collector rc=2の非gate | **closed** | 実 process returncode 0 と artifact の rc=2 を同時固定。[test:512](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_collect_wave_usage.py:512) | なし |
| D-MF1: READMEへの規範detail逃がし | **partial / real** | 非gate・login記述は削除されたが、「operand と挙動の正本」という規範指定が inventory に残る。[README:69](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/docs/README.md:69) | 規約違反が land する |
| D-MF2: SUSPECT fail-open | **closed** | C-MF1 と同じ fix で collector 非呼出まで固定。[test:309](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_collect_wave_usage.py:309) | なし |
| D-MF3: Codex author trailer | **partial / real** | 現在は未commit。実装面 commit には `role=author` が必須。[ai-provenance.md:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/docs/ai-provenance.md:44) | 欠落したままなら規約違反が land する |
| P-1: worktree基準で本体checkoutを素通り | **closed** | resolved path の全祖先を検査し、`.git` file／HEAD付きdirectoryを拒否。[helper:150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/collect_wave_usage.py:150) | なし |
| P-2: 空 `.git` directoryを拒否 | **closed** | directory は HEAD がある場合だけ拒否し、空directory正例を固定。[test:458](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_collect_wave_usage.py:458) | なし |

### (c) 残る must-fix

1. import 失敗を実 process rc=0 の境界へ入れる。
2. dangling symlink を lexical destination の既存 entry として拒否する。
3. bare repository と `.git/HEAD` 観測時の権限エラーを拒否側へ倒す。
4. `docs/README.md` を純粋な inventory に戻す。
5. M4 を単一理由の変異へ再照準し、M7 の fix 後 anchor を再登録する。
6. commit 前に Codex `role=author` trailer を確定する。