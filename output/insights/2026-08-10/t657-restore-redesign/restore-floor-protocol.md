# floor protocol の復元手順 — [T-657] 裁定 A (i)

由来: ユーザー裁定 2026-08-10 §54「[T-657] = A。活性化を見送り floor protocol を復元 (手順は
wave 用意、実行はユーザー手番)」。旧 wave = `dev-wave-t657-t660-g2-activation`。

## 0. 結論 (先に読む)

**書き戻しは不要である。** 2026-08-10 時点で、`git worktree list` が列挙した全 checkout の
`output/s8b-freeze/floor_protocol.json` は活性化前 (G1) の bytes を保持していた。第 2 世代の
再発行 commit も activation record 2 も、未 land branch の上にしか存在しない。

したがって本書は「戻す手順」ではなく、**戻っていることを確かめる照合手順**と、
**万一戻っていない場合の判断手順**である。ユーザーの対話 shell が要るのは §4 だけで、
そこで確認するのは repo ではなく scheduler と稼働 process である。

### 状態を 4 つに分ける

安易に「復元済み」と言わないため、状態を次の 4 つに分ける。混ぜてはいけない。

| 状態 | 定義 | 2026-08-10 の判定 |
|---|---|---|
| `RESTORED-REPO` | 時点 T に `git worktree list` が列挙した checkout の現 floor projection が G1 と一致 | **成立** (§2 の照合で確認) |
| `REINTRODUCIBLE` | 現在 authority ではないが repo 内に残る再導入源 (旧 branch、stash、reflog、未登録 clone) | **存在する** (旧 branch。異常ではないが §5 の規律が要る) |
| `EXTERNAL-UNCONFIRMED` | scheduler の投入済み job、稼働 process、計算ノード上の checkout | **未確認** (AI から観測不能。§4 がユーザー手番) |
| `CONTAMINATED` | G2 bytes が HEAD ancestry・current authority・queued job・claim のいずれかへ入った | **不成立** (§2 の範囲では) |

`RESTORED-REPO` は**時点付きの射影**であり、「live state が存在しない」という主張ではない。
`git worktree list` が含むのは Git に登録された worktree だけで、通常の clone、未登録 checkout、
別 `out_root`、計算ノード上の checkout、実行中 process は含まない。

## 1. 正準値台帳

以下の literal はこの文書で一度だけ定義し、以降は名前で参照する。すべて 2026-08-10 に
repo root で実測した値である。

| 名前 | 値 | 取得元 |
|---|---|---|
| G1 floor blob OID | `3acd995ae3d45f012040c5a23a089a64328201aa` | `git rev-parse HEAD:output/s8b-freeze/floor_protocol.json` |
| G1 floor SHA-256 | `261cec1c7f423b3eebff41ee716d2bfe2c6fa9a10a9dd86d91eaf71612e74aac` | `sha256sum` (774 bytes) |
| G1 pegasus contract SHA | `e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01` | `floor_protocol.json` の `contract_sha256` |
| G1 linux-baremetal contract SHA | `1b2ee85346a4c867754bda497b23d649e66027011167cfb0f9c7f9a1a5fa1dc7` | activation record の `active_contracts[]` |
| 現 activation serial | `1` | `env_contract_activations/00000001.json` の `activation_serial` |
| 現 activation state SHA | `f78072854651b316e1f2d78c2dfc58bfd995160515ed721a80a267ced54cd3ed` | 同 `activation_state_sha256` |
| prediction 全体 SHA-256 | `5884c83f010f73914fe121e9eb7b2fe047a4739087a984d17287cfa338fd73f1` | `sha256sum output/s8b-freeze/selector_predictions.json` |
| **危険** floor SHA-256 (G2 再発行版) | `c0eeed87ab1f449b97c0b7d88654a8c3a5c07fae3565dc90c5724e29f1cb660d` | 旧 branch の同 path (774 bytes、`contract_sha256` の 1 箇所だけが異なる) |
| **危険** commit | `8780332c580b5a7a53fa31181f9093ac13a31a30` | 旧 branch。`AI-Agent: none` の人間 commit |
| pegasus G2 contract SHA | `1346c20b5519be4b4d3aef19adc5a93ce2804ad4e0428dc5095635f54187ad1c` | `env_contract.GENERATIONS["pegasus"][1]` |

**pegasus G2 の calibration file と registry entry が repo に在ることは汚染ではない。**
これは `registered-inactive` という正常な状態である。authority は registry ではなく、
activation record の `active_contracts[].generation` と `contract_sha256` が持つ。

## 2. 照合手順 (AI が read-only で実行できる)

**1 コマンドが 1 つの値を出し、それを台帳の literal と目視で比較する。** 一致しなければそこで止める。
複合スクリプト・ループ・正規表現による自動分類は**意図的に置いていない**。段 3 の敵対レビュー 2 本が
独立に「複合 shell は終了値が判定として機能せず、危険状態を緑にしうる」を実証したためである
(先行失敗を握り潰すループ、`|| true` による fail-open、no-match と検出が同じ終了値になる分類器)。

| # | コマンド | 期待 | 不一致なら |
|---|---|---|---|
| 2-1 | `git rev-parse HEAD:output/s8b-freeze/floor_protocol.json` | G1 floor blob OID | §3 へ |
| 2-2 | `sha256sum output/s8b-freeze/floor_protocol.json` | G1 floor SHA-256 | §3 へ |
| 2-3 | `git status --short output/s8b-freeze/` | 出力が空 | §3 へ |
| 2-4 | `git log --oneline HEAD -- output/s8b-freeze/floor_protocol.json` | 1 行 (初回凍結 `c8cbd17c`) のみ | §3 へ。2 行以上なら `CONTAMINATED` |
| 2-5 | `git rev-parse HEAD:orchestrator/campaign/env_contract_activations/00000002.json` | **失敗する** (存在しないのが正常) | 成功したら `CONTAMINATED` |
| 2-6 | `grep -n "_ACTIVATION_HEAD_SERIAL" orchestrator/campaign/env_contract.py` | `= 1` | `CONTAMINATED` |
| 2-7 | `grep -n "_ACTIVATION_HEAD_STATE_SHA256" orchestrator/campaign/env_contract.py` | 現 activation state SHA | `CONTAMINATED` |
| 2-8 | `grep -c "261cec1c7f423b3eebff41ee716d2bfe2c6fa9a10a9dd86d91eaf71612e74aac" orchestrator/tests/test_frozen_artifacts.py` | `1` 以上 | pin が追随変更された。`CONTAMINATED` |
| 2-9 | `grep -c "c0eeed87ab1f449b97c0b7d88654a8c3a5c07fae3565dc90c5724e29f1cb660d" orchestrator/tests/test_frozen_artifacts.py` | `0` | `CONTAMINATED` |

登録 worktree を横断するときは、**1 worktree につき 2-1 と 2-2 を個別に実行し、個別に比較する。**
一括ループにしない (先行する不一致を握り潰さないため)。対象一覧は `git worktree list` で得るが、
**列挙件数を文書へ固定しない** — worktree は wave ごとに増減する (本 wave 中も 9 → 13 → 16 と動いた)。

### 2-10. 内容で判定する (commit 名で判定しない)

危険 commit `8780332c` の子孫かどうかで判定してはならない。同じ bytes を別 commit へ
cherry-pick すれば別 OID になり、祖先判定をすり抜ける。**判定は常に blob の内容で行う。**

    git rev-list HEAD | while read c; do git rev-parse "$c:output/s8b-freeze/floor_protocol.json"; done

を一括で回すのではなく、疑いが生じた個別 commit に対して
`git rev-parse <commit>:output/s8b-freeze/floor_protocol.json` を実行し、G1 floor blob OID と
比較する。全履歴の機械検査が要るなら、それは本文書の手順ではなく
`s8b_ratified_freeze.py` の `_immutable_introductions` (実装済みの正本) を走らせて判定する。

## 3. 復元判断木 (照合が不一致だったとき)

1. **worktree だけが dirty で、HEAD の blob は G1** — ユーザーが対話 shell で
   `git restore --source=HEAD -- output/s8b-freeze/floor_protocol.json` を実行し、§2 を再走する。
   AI は `output/s8b-freeze/` へ書けない (guard hook + isatty gate + create-only writer)。
2. **HEAD ancestry に別 bytes が入った** — forward revert では履歴不変条件は回復しない。
   不変条件は「∀C ∈ rev-list(HEAD): entry(C, path) ∈ {absent, HEAD の oid}」であり、
   revert commit を積んでも過去の commit に別 bytes が残る。異 bytes を含まない line から
   branch を作り直し、安全な変更だけを再導出する。**履歴の書き換えと force update は
   ユーザー裁定なしに行わない。**
3. **backup からの復元** — 旧 wave の
   `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-t660-g2-activation/floor_protocol.pre-g2.json`
   は G1 の bytes を持つ (2026-08-10 に確認)。ただし**現行ファイルとの `cmp` だけで判定しない。**
   両方が同じ汚染 bytes に差し替わっていれば `cmp` は成功してしまう。必ず `sha256sum` を取り、
   §1 の G1 floor SHA-256 という**固定 literal**と比較する。
4. **claim を見つけた** — 自動削除しない。owner PID・job ID・boot ID・run directory を照合し、
   ユーザー裁定へ返す。

## 4. ユーザーの対話 shell が必要な確認 (`EXTERNAL-UNCONFIRMED`)

repo の外は AI から観測できない。次はユーザーが確認する。**ここが裁定 §54 の
「実行はユーザー手番」の実体であり、書き戻しではなく確認である。**

1. **投入済み・実行中の PBS job** — `qstat -u "$USER"` で自分の job を列挙し、floor campaign に
   関係する job があれば、その job が読む source commit の floor blob を
   `git rev-parse <source_commit>:output/s8b-freeze/floor_protocol.json` で取り出し、
   G1 floor blob OID と比較する。**job ID から source commit への対応が取れない job は、
   安全と判定せず停止する。** receipt が source commit を持たない形なら判定不能である。
2. **稼働中の process** — repo を触っている process の有無。`/proc` の cwd を glob で探す方法は、
   repo root そのものを cwd に持つ process、authorization 取得後に別 directory へ移った process、
   別ノード上の process を取り逃がす。**「見つからなかった」を「無い」と読み替えない。**
3. **未登録の clone / 別 `out_root`** — `git worktree list` には出ない。心当たりのある場所を
   個別に確認する。campaign の排他機構も、clone ごとに `out_root` が違えば効かない。

### 判定できないものは判定できないと書く

claim record は protocol SHA を**先頭 8 桁しか持たない** (run ID 経由)。したがって危険 floor SHA の
64 桁全体で claim を検索しても当たらない。探すなら先頭 8 桁 `c0eeed87` で探す。
それでも取りこぼしうるため、疑わしい claim は個別に owner を照合する。

## 5. 旧 branch の取扱い規範

`worktree-dev-wave-t657-t660-g2-activation` (tip `74cceee5`) は **repo に置いたままでよい。**
凍結の履歴不変条件は `rev-list(HEAD)` だけを見るため、branch が存在するだけでは main は壊れない。

**唯一の禁止は main への merge である。** merge すると危険 commit が `rev-list(HEAD)` に入り、
freeze ratification が恒久的に `history-mutated` で拒否され、certified writer admission と
floor campaign launch が全面的に止まる。**そのまま取り込める commit は 14 件中 0 件である。**

| 区分 | commit | 理由 |
|---|---|---|
| 赤 (本体) | `8780332c` | floor protocol を別 bytes へ変える唯一の commit |
| 赤 (活性化) | `677d0952` | activation head を 2 にし `00000002.json` を導入する |
| 赤 (追随 pin) | `104f9c0d` | `FROZEN_MANIFEST` と protocol golden を危険 SHA へ変える |
| 赤 (再発行経路) | `6875a9c5`, `3bf0377a` | 同一 path への再発行 script |
| 赤 (merge) | `8d05861e`, `5d881259`, `3a06e90c` | branch 側差分を暗黙に運ぶ。`-m` 付き cherry-pick も禁止 |
| 赤 (前提が異なる) | `61cdc572` | G2-current / G1-history を前提にした test lane。再設計から再導出する |
| 黄 (史料のみ) | `65f89059`, `4afe2c1a`, `a1764c8c`, `acefcf64`, `74cceee5` | 内容は `git show <branch>:<path>` で読める。commit 全体には stale な brief と台帳 fragment を含み、変異 spec と ledger は旧 branch の tree を anchor にするため現行の受入へ流用できない |

再利用は `git show <branch>:<path>` で**内容を読んで再導出する**か、新しい設計から作り直す。
危険 commit の判定を自動化する分類器は置かない — 段 3 のレビューが、path と literal の
正規表現による分類器は (a) 別ファイル経由の等価な変更を取り逃がし、(b) 危険 SHA を引用しただけの
文書 commit を誤って赤にし、(c) no-match と検出を同じ終了値で返すことを実証したためである。

## 6. 再混入したときに何が起きるか

| 混入 | 発火する検査 | 拒否の理由 |
|---|---|---|
| 同一 floor path の別 bytes が HEAD ancestry に入る | `_immutable_introductions` | `history-mutated` |
| floor を G2 にしたが prediction / journal は旧のまま | floor preflight の freeze allowlist | 封印時 floor と現行 floor の不一致で launch 拒否 |
| activation serial が 2、floor は G1 | `validate_protocol_against_current` | certified admission が floor protocol の current 検証失敗として拒否 |
| `00000002.json` はあるが head pin は 1 | activation chain の terminal/head 比較 | activation head の serial / state hash 不一致 |
| generation record だけで active pointer が無い | `resolve_active_generation` | `no-active` |
| active freeze generation が 2 以上 | launch 検証 | `certificate-generation-scope` (launch certificate は generation 1 専用) |

いずれも production の正しい fail-closed である。**これらの拒否を緩めて通すことはしない。**
裁定 §54 は案 B (履歴不変条件の違反を拒否から記録へ落とす) を、唯一の事後検出層を除去し
規律 2 に触れるため不採用としている。
