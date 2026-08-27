# [T-1974] 段階 P — 計算ノードの受入子を tested main の blob へ束縛する

- 依頼 (ユーザー): 段階 P を実装する。計算ノード側の子の実行 bytes を tested main の blob へ束縛し、
  **実行器を 1 byte も変えずに**通常の受入・land で着地させる。
- wave branch: `worktree-dev-wave-t1974-runner-main-blob-binding`。統合 commit `b93861570`。
- 確定済み裁定: **D1151** (受入の実行器束縛 D838 は外さない。材料を運ぶ変更を先に着地させる)。
  設計 6 点の正本は `docs/archive/worklog-phase3-0827-1028.md` の [T-1974] 項。
- 関連: D838 / D440 / D387 / D388 / D397 / D859 / D987 / D1103。前 wave の実測は
  `output/insights/2026-08-27_runner-tip-equality-dispatch/`。
- 逐語は `verbatim/`。変異台帳は `mutation-final-out.json`、spec は `mutation-spec-final.json`
  (probe は `mutation-spec-probe.json`、観測 node は `observed-nodes.json`)。

## 結論

計算ノードで dispatch された `tests` 子の実行 bytes を tested main の blob へ束縛した。
`tools/run_tests.py` の差分は **0 byte** である。

- **執行は launcher。** main 束縛の launcher が session nonce と exact K を所有し、
  継承 write-fd で全 shard の申告を無条件に要求する。受領証を書く前に fail-closed する。
- **機構は dispatcher。** launcher 所有の manifest がある走行にだけ束縛を適用する。
  manifest が 1 key も無ければ現行の pathname 起動を維持するので、
  **段階 P 自身の受入 (main の旧 launcher が動く) は落ちない。**
- **同一 buffer 束縛。** 計算ノード側は `git cat-file blob <tested_main>:tools/run_tests.py` を
  1 回読んで単一 buffer を作り、同じ buffer を hash と子の stdin に使う。
  期待 digest を子へ転記しない。

## 親が実測して設計を変えた点

段 2 のプランを段 4・段 6 で 6 点覆した。いずれも実測または敵対レビューの所見が根拠である。

| # | プランの案 | 覆した理由 (実測) | 確定した形 |
|---|---|---|---|
| 1 | manifest の path を環境変数で運び、repo 外 directory へ申告 file を書く | **環境変数は実行器の子孫すべてに継承される。** login collect-only 子、bounded local の pytest、計算ノードの pytest = 被検査テストコードが manifest から nonce・digest・K を読み、`0..K-1` の申告を丸ごと偽造できる。同一 uid なので mode 0700 は隔離にならない | launcher 所有の**継承 write-fd**。`subprocess` の既定 `close_fds=True` で exec された子孫は fd を失う |
| 2 | request payload へ runner の base64 source を載せる | `tools/run_tests.py` は 96,988 bytes、base64 で 129,320 bytes。K=3 で 387,960 bytes になり、size 上限も境界試験も未定だった | source を運ばず **revision だけ**運ぶ。計算ノード側が blob を読む |
| 3 | 未設定時に launcher が `IZANAGI_ACCEPTANCE_SHARDS="2"` を明示注入する | 明示値は `explicit_shard_mode` を立て、**login admission と queue 可用性の判定を飛ばす** (`tools/run_tests.py:2495-2545`)。待ち手は queue を確認できないと注入しないので実運用で到達する | launcher は**注入も書き換えもしない**。未設定・空・不正は runner 起動前に fail-closed |
| 4 | 申告検査を outcome 書き込みの前に置く | 待ち手は先に outcome pipe を読む (`tools/dev_wave_wait.py:3810-3819`)。EOF は即 `acceptance-command` 失敗になり、**queue timeout の再試行分類が消える** | outcome の後・受領証の前 |
| 5 | `result.json` を `O_EXCL` から atomic replace へ変える | 現行の `O_EXCL` は先行作成を**妨害 (fail-closed)** にしており偽造にはならない。replace 化はむしろ新しい risk を作る | 書き込み意味論は変えない。申告は既存 result payload の optional field |
| 6 | 発火条件を `task == "tests" かつ argv_policy == passthrough かつ child_script == (...)` の 3 項にする | 後 2 項は `TASKS` の固定表から**恒真**。単独で発火する入力が存在しない | gate 述語は 2 項 (`task == "tests"` と manifest 完全)。残りは assert に留め、変異にも登録しない |

## 親が実測した blast radius (設計 (iv) の代償)

**「queue 停止 + login に空きメモリあり」の受入は、段階 P 着地後に受領証を作れなくなる。**

連鎖はすべて親が本 wave 中に実測した。

1. 待ち手は Pegasus LOGIN かつ queue が `ENA=ENA` / `STS=ACT` のときだけ
   `IZANAGI_ACCEPTANCE_SHARDS=3` を注入する (`tools/dev_wave_wait.py:821-845`)。
2. 注入されないと `explicit_shard_mode=False` になり、実行器は login admission へ入る。
3. `admission_outcome is None` (memory headroom あり) なら
   `_launch_local_scope` で **suite をログインノードで local 実行**し、rc 0/1 を返す
   (`tools/run_tests.py:2495-2545`)。今日はこの経路が v5 受領証を出している。
4. 段階 P 着地後、この走行は申告 0 件で fail-closed になる。

これは確定済み設計 (iv)「dispatch しない authoritative 受入は R まで fail-closed」そのものであり、
親は不採用にしていない。逃がし道 (flag・環境変数・「manifest 無しなら要求しない」) は作っていない。
**復旧は段階 R ([T-1976]) が bounded local を main blob 実行へ移すまで待つ。**
`docs/pegasus-runbook.md` に明記した。

## 束縛が及ばない層 (過大主張をしないための列挙)

束縛されるのは **dispatch された `tests` 子 1 層だけ**である。次は束縛外に残る。

- login 側の tip dispatcher import (`tools/run_tests.py:1307` の `from tools.pegasus import dispatch_compute`)
- 計算ノードの job script が tip の dispatcher を pathname 起動する経路
- login の collect-only pytest、bounded local の pathname runner
- 計算ノードの pytest controller と xdist worker、テストが起こす孫 process

さらに **shard worker は `multiprocessing.get_context("fork")` で起動される**
(`tools/acceptance_shards.py:1201, 1243-1255`)。fork は `close_fds` / `FD_CLOEXEC` と無関係に
開いている fd を複製するので、shard worker は申告用 write-fd を継承する。
そもそも dispatcher はその fork worker から呼ばれるため、**段階 P の制約下 (実行器も
`tools/acceptance_shards.py` も編集できない) では、この継承を閉じられない。**

したがって残余の正確な形は次である。

> **`tools/pegasus/dispatch_compute.py` または `tools/acceptance_shards.py` を編集した wave は、
> 段階 P では捕まらない。**

それでも file 経路より厳密に強い。file 案では exec された任意の子孫 (被検査テストコードそのもの) が
偽造できた。fd 案ではそれらは fd を失うため偽造できない。
閉じるのは段階 R が外側 dispatcher import を main 側へ束縛したときである。

**「dispatcher 導入以降、実行器を触った 24 commit のうち 6 件が同じ commit で dispatcher も触っている」**
は観測事実として記録するが、申告の必要性や将来の確率の根拠としては使わない。

## 受理集合の差

**受理集合は狭まる。** 「一切変えない」は誤りだった (段 6 レビュー A が訂正)。
次を新たに拒否する。

- 申告が出ない authoritative 受入 (dispatch しない走行を含む)
- `IZANAGI_ACCEPTANCE_SHARDS` の未設定・空・不正値
- manifest 環境 3 key の部分設定
- 申告の件数不一致・index の multiset 不一致・nonce / tested_main / digest の不一致

受領証 (`dev-wave-acceptance-receipt/v5`) の field 集合・値の意味、`_ENV_PROJECTION_FIELDS`、
`TASKS[*].env_allowlist`、`result.json` の `O_EXCL` はいずれも不変である。
`tools/run_tests.py` / `tools/dev_wave_land.py` / `tools/dev_wave_wait.py` /
`tools/acceptance_shards.py` に差分は無い。

## 変異 matrix

`--runner-mode dispatch`、使い捨て worktree (`/work/1/SFC/tanab/mutation-scratch-t1974`)。

**baseline PASSED / KILLED 13 / SURVIVED 0 / MISMATCH 0 / TIMEOUT 0。**

本走は 2 回ある。1 回目は統合 commit `b93861570` で、受入全走の後に bytecode guard の回帰を
1 行で直したため、DW-M07 に従い**最終 commit `17d42cdf6` で再走した**。
再走前にアンカー 13 件の一意性を再検証し、spec の内容 hash が不変であることを確かめている
(`58655ae2e8d554929dd0b239c14c5cbec788baaec37aaba0a8c61b03071df45b`)。
両走とも結果は同一で、台帳 (`mutation-final-out.json`) は再走 (`repo_head` = `17d42cdf6...`) の分である。

対象テストは 5 file
(`test_acceptance_launcher.py`、`test_pegasus_dispatch_compute.py`、`test_dev_wave_land.py`、
`test_resume_gate_acceptance_boundary.py`、`test_dev_wave_wait.py`)。
`test_dev_wave_land.py::test_exploration_external_root_keeps_wave_clean` は F57 系の既知非帰属赤
(所有 [T-1079]) なので DW-C01 / D690 の既定手順で `--deselect` した。

### 事前登録を本走前に訂正した 4 件 (erratum)

段 4 で登録した変異のうち 4 件は、実装が確定した後に見ると殺せない型だった。
DW-M03 / DW-M04 に従い**本走前に**実効 gate へ再照準した。初回登録は捨てていない。

| # | 旧登録 | 問題 | 新登録 |
|---|---|---|---|
| M4 | index の multiset 比較を `set` 比較へ緩める | **同値変異。** 件数が exact K で固定されているため `set` 一致は multiset 一致と同値になる | index 検査を丸ごと削除する |
| M7 | 未設定・空の fail-closed を落とす | **診断だけの赤。** guard を消すと `int(None)` の `TypeError` になり runner は起動しない | 未設定時に既定 K=2 を返す (受理集合が実際に広がる) |
| M9 | 申告 digest を manifest 期待値の転記にする | **構成不能。** manifest に期待 digest を載せていないので転記元が存在しない | hash 対象を pathname から読み直した bytes にする |
| M11 | manifest 一部欠落の fail-closed を落とす | **診断だけの赤。** 欠落 key の添字参照が `KeyError` になり scheduler へ到達しない | 部分 manifest を unbound として通す |

さらに段 6 レビュー A が見つけた実バグ (下記) に対応する M13 を新設した。

### probe を挟んだ効果

DW-M07 に従い、まず全件 SURVIVED 期待の probe を走らせて観測 node を集めた。
**13 変異のうち 5 件 (M1 / M2 / M5 / M7 / M10) は、意図した node に加えてもう 1 本を落としていた。**
期待 node は完全集合でなければならないので、勘で書いていれば本走を 1 回捨てていた。

## 段 6 レビューが捕まえた実バグ

**申告 JSON の形式不一致。** dispatcher の writer は `indent=2` の複数行 JSON を申告 channel へ書き、
launcher の parser は空白なし 1 行 JSON を 1 行ずつ読む実装だった。
**段階 P 着地後の正常な dispatch がすべて land 不能になる。**
片側の serializer だけを使うテストでは検出できない型なので、
writer の bytes を parser へ直結する seam テスト (`test_binding_report_writer_output_parses_in_launcher`)
を置き、変異 M13 で殺せることを実測した。

## 実走で初めて出た赤 2 件 (静的レビュー 2 本を通り抜けた)

- **`parametrize` した引数に既定値。** pytest は収集を拒否し、**その file 全体が落ちる**。
  計算ノードでの初回焦点走が 48 worker から同一の収集エラーを返した。
  親が 4 file を AST で全走査し、同型は 1 件だけと確定した。
- **消費者の取り残し 2 段。** `test_resume_gate_acceptance_boundary.py` は実装子が自分で見つけて
  報告し止まった。**`test_dev_wave_land.py` の実 Git E2E 2 本は親の初回閉包判定が粗く取り逃した** —
  同 file 内の `acceptance_launcher` 参照 29 件を「path 文字列の fixture」と一括判定したためである。
  2 回目は全 test file を対象に走査し直し、候補 5 file を実走 (886 passed / 2 skipped) して
  緑を確認した。**閉包は「参照がある file」でなく「実 launcher を端から端まで駆動する node」で引く。**

## 子の一覧

plan 1、敵対相談 2、実装 1、レビュー 2、fix 3 の計 9 本。すべて `gpt-5.6-sol` / `xhigh` /
`check_codex_output.py` rc=0。実測 (テスト実走・変異・受入) はすべて親が行った。
