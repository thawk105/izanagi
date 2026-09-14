# land の lock 待ち予算が lock 外の作業に食われる会計 — 実測と是正

- authority: none
- default_effect: no-state-change
- 作成: 2026-09-14
- branch: worktree-dev-wave-t758-docs-corrections、実装 commit `0ec8d0faf`
- 設計判断の正本は decisions の当該 D。本書は実測値と、倒された仮説の記録

## 何が起きていたか

`tools/dev_wave_land.py` は lock 待ちの予算 180 秒を、lock 外で走る 2 つの作業
(全史 provenance 監査 `:4987`、fold gate `:5270`) と共有していた。`_run_outside_land_lock` が
窓開始 + 180 秒の絶対 deadline をそのまま再取得へ渡すため、lock 外の作業が 180 秒を超えると
再取得の実待ち時間がゼロになる。

**ただし「監査が窓を食うこと」自体は失敗の原因ではない。** `_acquire_land_lock` の deadline 検査は
`except BlockingIOError` の内側にしかなく、非 blocking `flock` が成功すれば deadline 超過でも
取得できる。

| lock 外の作業後の状況 | 結果 |
|---|---|
| lock が空いている | deadline 超過でも成功 |
| 埋まっている & 予算内 | 残予算まで待てる |
| 埋まっている & 予算切れ | 1 回試して即失敗 (rc=11) |

**真の失敗条件は「lock 外の作業中に他の land が lock を取り、かつ自分の予算が尽きていること」。**
予算を食った結果、待つ権利を失った状態で鉢合わせると落ちる。

## 本 wave の実測 (land 42 回投入・status 記録 41 回・成功 0)

| status | 件数 |
|---|---:|
| `lock-busy` (rc=11) | 30 |
| `rejected` (rc=29) | 8 |
| `stale-main` (rc=10) | 3 |

`lock-busy` の phase 内訳: `initial` 7 (全件 `waited_s == window_elapsed_s == 180.00x`)、
`post-provenance` 18、`post-fold-gate` 4 (最悪 `0.005 / 652.829`)。

`rc=29` の reason 内訳は **dispatch rc=16 が 5 回、480 秒 timeout が 2 回、監査中の head 移動が 1 回**。
head 移動は最少であって主因ではない。

`post-provenance` 18 件のうち 4 件は lock 外の時間が 180 秒未満 (56.1 / 69.1 / 82.7 / 144.0 秒)
だった。**全史監査が窓に収まる回は実在する。**

## 別 wave の実測 (借用。31 件の phase 別分解)

監査が窓に収まっていたのに lock 待ちで予算を食われて落ちた回が 2 件ある。

- `waited_s=150.481 / window_elapsed_s=272.504` → 監査推定 122.0 秒
- `waited_s=141.590 / window_elapsed_s=305.791` → 監査推定 164.2 秒

**この 2 件を変異テストの正例に使った。** 合成 fixture より現実の形に近い。

救う手が 3 つに分かれ、重ならない。

| 群 | 件数 | 救う手 |
|---|---:|---|
| `post-provenance` (監査 ≤480 秒) | 17 | 本 wave の会計是正 |
| `post-fold-gate` | 2 | 同 |
| `initial` | 8 | 順番に 1 本ずつ投げる運用 |
| 監査 >480 秒 / rc=29 | 4 | 別是正 (監査の実行場所) |

会計是正の射程は 19/31 (61%)、運用と併用で 27/31 (87%)。

## 監査の所要は実行場所で 7 倍振れる

| 実行場所 | 全史監査の所要 | 観測ピーク |
|---|---|---|
| ログインノード | 428 秒 (9787 件) / 574 秒 | 686 MB / 630 MB |
| 計算ノード | 61 秒 (9800 件) | — |

原因は `tools/check_ai_provenance.py` の `_evaluate_login_admission` が
`grant_budget(min_bytes=...)` を呼び、**判定の入力が bytes だけ**で CPU 時間・予想所要を
1 つも見ないこと。監査は「メモリは軽いが CPU を長時間食う」形なので、予算 1 GB の内側に
収まる限り構造的に login へ留まる。`--force-dispatch` は既に存在し、
`authoritative = args.rev_range is None` を変えないので監査の射程を狭めない。

## 変異 matrix

実装前に 2 変異を登録し、probe で観測 node を集めてから完全集合で本走した。

| 変異 | 期待 | 結果 | 殺した node |
|---|---|---|---:|
| 取得ごとに満額補充 | KILLED | **KILLED** | 7 |
| lock 外の作業を予算に食わせる (是正前の挙動) | KILLED | **KILLED** | 9 |

baseline PASSED、期待 node 完全一致、`anchor_counts` は両方 `{"0": 1}` (置換対象一箇所)。
後者が 2 node 多いのは既存 2 テストも反応するためだが、**既存テストだけでは初回待機ゼロの
fixture のため正実装と補充変異を区別できない。** 新設の境界 fixture がその穴を埋めている。

## 倒された仮説 (次に同じ経路を見る人のため)

- **「rc=29 は監査中の head 移動」** — 8 回中 1 回だけ。主因は監査が完走しないこと。
- **「監査の範囲を縮めれば直る」** — 縮める対象が律速ではない。監査本体は計算ノードで 61 秒。
  さらに `--range` は `authoritative` 述語を落とし、fold commit の後続監査と前方 merge の
  commit を窓から落とす。
- **「予算を増やせば直る」** — 待機を増やすと監査の同時流入を増幅する。従来は即座に降りていた
  待ち手がその経路へ回る。
- **「lock 保持時間の下界 max が予算の根拠」** — それは lock 区間の上限ではないと既に反証済み。
- **「全史監査が 180 秒に収まった記録は 1 件もない」** — 本 wave の 4 件が反例。
- **「`waited_s ≈ 0` なら lock 競合ではない」** — `return False` は `except BlockingIOError` の
  内側なので、その時点で lock は実際に保持されている。誤誘導しているのは `waited_s` の側で、
  正しい読みは「予算が尽きていたので待たなかった」。
- **「land 数は `grep dev_wave_land.py` で数えられる」** — `test_dev_wave_land.py` に一致する。
  `dev_wave_land.py --main-worktree` で絞り、`--acceptance-wave` の値で uniq する。

## 次に読む人への注意

- 結果 JSON に窓の内訳を出すようにしたが、**それ以前の log には成功時の内訳が無い。** 成功した
  land の所要は外側 wall-clock でしか測れない。
- `_GIT_TIMEOUT_S = 30` は `verify_declared_fold_commit` の**全 git 呼び出しの合計予算**である
  (`_deadline` は 1 回だけ呼ばれる)。ただし同等の git 呼び出しの単独計時は 3.3 秒で、
  timeout 仮説は否定された。
- `invalid-run` を投げる箇所は `git_state.py` に 22 ある。例外経路は detail を落とすので、
  どれが発火したか判別できない。構造的拒否の経路は detail を載せるため「失敗」と「拒否」の語で
  例外か構造かは区別できる。
