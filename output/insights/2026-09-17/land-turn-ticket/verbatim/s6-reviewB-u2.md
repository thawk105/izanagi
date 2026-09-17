## 前提の検算

指定の必読資料を読み、提示された **780 行の diff と現物の `git diff` が完全一致**することを確認した。変更対象は指定の 2 file のみ。ファイル変更・pytest・Git の状態変更は行っていない。

裁定 §3.7、§4.2、DW-G05 に照らし、**must-fix は 1 件**。journal 公開途中の停止で、同じ要求による cleanup 再入が継続的に拒否される。

`131 passed / 8.0 秒` は親から提示された実測値として扱う。author 報告は「機能テスト未実走」であり、本レビュー自身の実測ではない。M10 の KILLED も未確認。

以下の `tools/…`、`orchestrator/…` は指定 repo root 相対。

## 最小性

**中核機構が過大という指摘は refuted / nit。全 file の生 bytes 保存は簡素化余地あり、real / nit。**

各機構が塞ぐ反例は次のとおり。

| 機構・位置 | 塞ぐ反例 |
|---|---|
| journal：`tools/dev_wave_cleanup.py:950` | HEAD／gitdir 消失後、通常の porcelain／backpointer だけでは自 admin と撤去前の安全検査結果を復元できない。 |
| 再帰 snapshot：`:770`、subset 検査 `:882` | 部分撤去後、残存 entry が差し替わった、増えた、内容が変わった状態を「自分の削除の続き」と誤認する。 |
| admin directory の flock：`:816` | 同じ admin を束縛した協調 cleanup 2 件が同時に撤去へ進む。Git 一般との排他を保証するものではない。 |
| `AdminBinding`：`:726` | 再入時の path 文字列だけを信頼し、別の common／registry／admin を撤去する。FD 3 個と name／identity が対象を固定し、backpointer／commondir／bindings が対応関係を、tip が HEAD を、journal／recovery が再入証拠を保持する。 |

11 field という個数だけでは過大とは判定できない。`AdminBinding` を辞書に置き換えても保証や分岐は減らない。

一方、`:789` は index 等も含めて全 file を hex 化し、`:956` で journal に保存する。**復元処理は存在せず、多くの file に必要なのは同一性比較だけ**である。

具体的な縮小案は、再帰構造・inode・種類・nofollow・subset 検査を維持し、通常 file の内容を長さ＋SHA-256 にすること。削除後にも意味検査が必要な gitdir／commondir／HEAD／HEAD reflog の証拠だけ別途保持する。`:939` の比較も同じ digest にする。これなら SHA-256 の衝突耐性を前提に、他 admin 非削除と残存物改変時の再入拒否を維持し、journal の容量を減らせる。

ただし、容量が成果物や受入上限を実際に破った証拠はないため、簡素化を must-fix にはしない。

## journal の運用影響

**real / must-fix：journal の公開が原子的でない。**

[tools/dev_wave_cleanup.py:960](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-turn-ticket/tools/dev_wave_cleanup.py:960) は最終名を `O_CREAT|O_EXCL` で作り、その後 write／flush／fsync する。

反例は次の順序で成立する。

1. wave directory は `:1243` で撤去済み。
2. journal 作成直後、または書込み途中で停止する。
3. admin はまだ残っているが、最終名の journal は空または不完全。
4. 再入は `:1051` → `:858` の `json.loads` で失敗し、preflight の rc=20 になる。
5. 同じ要求を再実行しても、その journal を読み続ける。

**成果物影響：本来再入で完了できる cleanup が恒常的な rejected となり、自 wave の admin と branch が残り、§3.7 の partial 再入契約を満たさない。**

修正は局所的でよい。完全な journal を一時名へ書いて fsync し、既存 final を上書きしない原子的公開と親 directory の fsync を完了してから admin 削除へ進む。公開前停止の残骸は有効 journal として読まない設計にする。この停止点の再入 test が必要。

他 tool への影響は以下。

| consumer | 判定 |
|---|---|
| land `_verify_history_modifiers`：`tools/dev_wave_land.py:1426` | shallow／grafts／replace refs の検査。未知の `.git` 直下 file を列挙・拒否しない。衝突懸念は **refuted / nit**。 |
| land `_verify_effective_config`：`:1450` | Git config の特定 key を検査。journal は読まない。**refuted / nit**。 |
| `check_wave_startup.py:132,239,255` | grafts、操作中 marker、worktree status 等の検査。journal を直接検査する経路は見当たらない。**refuted / nit**。 |
| `git worktree prune`／`git gc` | ローカル Git man は admin を `$GIT_DIR/worktrees` 配下とし、gc から worktree prune が呼ばれることを記載。直下の独自 journal を回収する契約はない。journal の自動回収に依存できない。実機での共存挙動は **未確認 / nit**。 |
| U1 の `<common>/dev-wave-land-turn/` | 指定の置き場と cleanup journal の名前は衝突しない。U1 との結合実走は **未確認 / nit**。 |

正常終了時と正常な再入時には `tools/dev_wave_cleanup.py:990` が journal を消す。**再入されない残骸や破損 journal の回収主体はない**。`.claude/commands/cleanup-branches.md:53` の手順にも記載がない。

破損 journal は上記 must-fix に含める。放棄された journal 全般の棚卸し・回収運用は **real / nit、裁定パッケージ候補**とし、この wave に汎用掃除機構を追加させない。

## 波及

**指定 consumer の破壊は refuted / nit。実走による確認は未了。**

- `docs/dev-wave/operations.md:215` の CLI literal は不変。`tools/check_docs.py:626` の literal と `:662` の exact pin を緩めていない。
- `test_check_docs.py:192,920` の literal／helper 存在参照は維持。
- `test_branch_rescue_ledger.py:340` の DW-O28 helper 文書参照は維持。
- `test_pytest_collection_config.py:51,389,484` の file path と指定 node は維持。`test_real_occupancy_scan_rejects_live_process_cwd` は現物 `test_dev_wave_cleanup.py:900` に残っている。
- `orchestrator/test_selection_contract.py:41` の canonical file path は不変。自走入口も `test_dev_wave_cleanup.py:1521` に残る。
- 廃止 private symbol の production caller は、検索範囲内で残っていない。

前提を訂正すると、**`/cleanup-branches` は `dev_wave_cleanup.py` を呼んでいない**。`.claude/commands/cleanup-branches.md:60` は自分で `git worktree prune --dry-run --verbose` の候補を確認する手順である。今回削除する `_dry_run_candidates` の戻り値や出力には依存しない。

## test の検出力と M10

**実 registry による保持・再入検査は real / nit（肯定所見）。**

`test_dev_wave_cleanup.py:1072` は実際に `git worktree add` で他 wave を作る。live／stale の両 parameter で自 wave の cleanup 成功を要求し、`:1089` の比較は他 admin の root と全子孫について dev／inode／file bytes を確認する。branch は SHA の保持を確認する。

したがって旧 test の反転は、単なる期待 rc の変更ではない。**他 wave の directory が実在する live ケースでも、自 wave の cleanup が成功する**ことを検査している。ただし live ケース自体は、全体 prune の誤使用を検出する負例にはならない。

partial test `:1097` も実物を削除している。`:1112`／`:1118` は本物の unlink／rmdir を先に呼び、その後割り込む。`:1128` で消失を確認し、branch と foreign admin の保持を確認してから再入する。これは要求された HEAD／gitdir 消失後の再入を覆う。

限界は次のとおり。

- 同一 process の例外注入であり、SIGKILL／電源断ではない。
- journal 作成・書込み中断を覆わない。
- `removed="admin-directory"` の tamper 3 種は、いずれも `admin.mkdir()` になるため、この組合せでは別々の lock／bytes／inode 攻撃ではない。

M10 は exact 置換を区別する必要がある。

**author の anchor `tools/dev_wave_cleanup.py:1249` の 4 行を次に置換した場合：**

```python
phase = "admin-remove"
_must_git(args.main_worktree, "worktree", "prune", "--expire=now")
```

静的予測は次のとおり。

| node | 赤になる理由 |
|---|---|
| `test_cleanup_preserves_foreign_stale_admin[live]` | `_validate_git_argv` が prune を拒否し、成功期待に対して rc=30。 |
| 同 `[stale]` | 同じ理由。foreign admin 保持比較には到達しない。 |
| `test_forbidden_git_verbs_absent_from_source_calls_and_runtime_allowlist` | `:1248` の AST 検査が `_must_git(..., "worktree", "prune", ...)` を検出。 |

この赤は **他 wave admin 保持の検出力を証明しない**。原因は先行する argv gate である。

専属の挙動検出を確認する変異としては、同じ 4 行を、変異版限定で以下へ置換できる。

```python
phase = "admin-remove"
subprocess.run(
    ["git", "-C", os.fspath(args.main_worktree),
     "worktree", "prune", "--expire=now"],
    check=True, stdin=subprocess.DEVNULL,
    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
)
```

この場合の予測は、`[live]` は保持され成功、`[stale]` は実 prune が foreign admin を削除し、`:1085` の `_admin_tree_state(admin)` が不在 root の `lstat` で赤になる。AST 禁止 test は `_git`／`_must_git` のみを対象にするため、この置換を先行検出しない。

**M10 の専属帰属は未確認 / nit。** 親の段 6 で exact diff と node 単独結果を記録すべきであり、本レビューでは KILLED と数えない。

## 既存 test の期待値変更

**裁定外の期待値緩和という指摘は refuted / nit。**

提示 diff の既存変更は以下に収まる。

- `:270`：全体 prune 呼出しの期待を廃止し、自 admin 消失を確認。
- `:1072`：他候補による全体停止から、他 wave 保持と自己 cleanup 成功へ反転。
- `:1235,1258,1310`：prune の禁止追加と許可形削除。
- `:1360,1417`：失敗注入点を新しい admin 撤去 phase へ移動。
- `:1478`：`_preflight` の追加引数に合わせて mock を変更。KeyboardInterrupt の期待は維持。

いずれも §1 #12、#22、#38 と §3.7 に対応する。無関係な安全検査の削除・期待値緩和は見つからなかった。

## 所要

`git diff --stat` は次のとおり。

| file | 追加 | 削除 | 純増 |
|---|---:|---:|---:|
| `tools/dev_wave_cleanup.py` | 315 | 43 | 272 行 |
| `orchestrator/tests/test_dev_wave_cleanup.py` | 170 | 34 | 136 行 |

parameter の差分から test case は純増 27 と読める。現在の 131 件を基準にすると変更前相当は 104 件だが、**変更前の実行時間は資料にない**。速度の改善・悪化は判定できない。

`_admin_snapshot` は hex 化だけでなく、`:926` → `:979` により **各 entry の削除前に残存 tree 全体を再読込**する。entry 数を N、総 bytes を B とすると、読込み量は配置次第で O(NB) に近づく。小さい fixture の 8 秒は、大きい index／reflog／admin tree の上限を示さない。これは **構造上 real / nit、実時間への影響は未確認**。

8 秒は 300 秒の約 2.7%。ただし受入全走の総時間は不明で、canonical cleanup exclusion の適用有無でも寄与は変わる。**5 分上限への適合も、時間回帰なしも、この値だけでは認定しない。**

## 所見一覧 (must-fix / nit、real / refuted / 未確認、file:line)

| ID | 分類 | 位置 | 所見 |
|---|---|---|---|
| B1 | **must-fix / real** | `tools/dev_wave_cleanup.py:960,858` | journal の途中公開が同一要求の再入を恒常拒否にする。**成果物影響：cleanup が完了せず自 admin／branch が残り、partial 再入の受理集合が欠ける。** |
| B2 | nit / real | `tools/dev_wave_cleanup.py:789,956,979` | 全 bytes の hex 保存と残存 tree の反復読込みに縮小余地。性能上限超過は未確認。 |
| B3 | nit / real | `tools/dev_wave_cleanup.py:990`、`.claude/commands/cleanup-branches.md:53` | 放棄 journal の回収主体がない。一般回収運用は裁定パッケージ候補。 |
| B4 | nit / 未確認 | `tools/dev_wave_cleanup.py:1249`、`orchestrator/tests/test_dev_wave_cleanup.py:1081,1235` | M10 の現 anchor だけでは argv 拒否に遮られる。保持検査への専属帰属は未実測。 |
| B5 | nit / refuted | `tools/dev_wave_cleanup.py:726,770,816,950` | binding／再帰比較／協調排他／再入証拠の中核を一律に過大とは判断しない。 |
| B6 | nit / refuted | `tools/check_docs.py:626,662`、`.claude/commands/cleanup-branches.md:60` | CLI pin 破壊や cleanup-branches への helper 呼出し破壊はない。 |
| B7 | nit / refuted | `orchestrator/tests/test_dev_wave_cleanup.py:270,1072,1360,1478` | 既存期待値変更は裁定範囲内。 |
| B8 | nit / 未確認 | `tools/dev_wave_cleanup.py:979`、`orchestrator/test_selection_contract.py:41` | 変更前後の時間差、受入全走への実寄与、Git gc／U1 との実走共存は未確認。 |

## 総括

**B1 の修正が必要。** journal を完全な状態で原子的に公開し、公開途中の停止から再入できることを検査してほしい。

対象限定撤去、実 registry による他 wave 保持、HEAD／gitdir 消失後の再入 test は裁定に沿っている。M10 は argv 拒否による赤と、foreign admin 消失による赤を分離して記録する必要がある。性能・結合実走・変異 KILLED は本レビューでは認定していない。
