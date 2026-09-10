# [T-2412] 凍結 spec loader の hash 不動点 — 実測、実装、そして裁定より狭く作ってしまった記録

2026-09-08。dev-wave `t2412-frozen-spec-fixpoint`。branch `worktree-dev-wave-t2412-frozen-spec-fixpoint`。

## 何が壊れていたか

`orchestrator/campaign/floor_pair_driver.py` の `load_frozen_spec` は次の 2 つを同時に要求していた。

1. spec の bytes が `git show HEAD:<spec relpath>` と byte 一致する
2. spec の中の `provenance.source_commit` が `git rev-parse HEAD` と一致する

spec は追跡 file なので (1) を満たすには commit しなければならない。commit すると HEAD が変わるので
(2) が満たせない。hash の不動点であり、**凍結 spec を一度も作れない。**

## 実 git での再現

親が実 repository で確かめた。

```
BASE=edb191d231d99a8af3cdab0a86bedfa2cc0f7f8f
spec 未 commit  → git show HEAD:spec.json → fatal: path 'spec.json' exists on disk, but not in 'HEAD'
spec を commit  → NEW_HEAD=badb380bc3f644b3731e0a49420215c4d4f4e6bf
                  spec 内 source_commit=edb191d2… → 一致しない
                  bytes 一致は成立 (cmp OK)
```

なお `refs/replace` を使えば現行 2 条件も同時に成立させられる (段 3 レンズ A が指摘)。
したがって「不可能」ではなく「正規の発行手順では成立しない」が正しい。

## なぜ 209 件のテストが緑だったか

`_install_git` が `subprocess.run` を差し替え、`rev-parse HEAD` を定数 `"b"*40` に、
`show HEAD:<path>` を on-disk bytes に固定していた。`SOURCE_COMMIT = HEAD` なので、模擬では
両条件が常に同時成立する。**模擬は「呼び出し側が何を尋ねたか」は検査できるが、「その問いに実 VCS が
どう答えるか」を検査できない。** 自己参照する束縛では後者が本体である。

## 直した形 (D1774)

`provenance.source_commit` は spec を含む commit の親、すなわち spec を著した時点の commit とする。
loader は `source_commit` が `loaded_head` の**真の祖先**であることを要求する
(`git merge-base --is-ancestor`、等値は拒否 — 許すと不動点が戻る)。

保証するのは 2 つだけである。

- spec の bytes が `loaded_head` の tracked blob と byte 一致する
- `source_commit` が `loaded_head` の真の祖先である

その間に何の変更が入ったかは制限しない。commit OID の同値も、実行中 module bytes が記録 commit に
対応することも保証しない。

あわせて `loaded_head` を loader の冒頭で 1 回だけ解決し、spec・calibration・build receipt の
全 blob 比較をその OID に対して行うようにした。従来は symbolic `HEAD:` を使っていたため、
blob 検査と後から解決する HEAD が別 commit を指しうった (段 6 レビュー A の real 所見)。

## 裁定より狭い形を作ってしまった記録

**段 1 で承認済みユーザー裁定 D1774 を引かなかった。** 依頼文と insight の一次資料だけを読み、
`docs/worklog.md` の T-2412 項と `docs/decisions.md` の D1774 を読まずに brief を書いた。
段 4 で親が自分で裁定した形は「HEAD が唯一の子であり、かつ差分が spec 1 path だけ」で、
D1774 の「子孫」より狭い。段 5 の実装、段 6 の敵対レビュー 2 本と変異 9 件まで、
その狭い形で進めた。

気づいたのは段 7 で台帳の base digest を取るために main の worklog を読んだときである。
**子は親が射影した資料しか見ないため、親の資料選択の誤りは子の敵対レビューでは検出されない。**

狭い形の実害は具体的である。**freeze commit の後に 1 つでも commit が乗ると、その spec は二度と
load できない。** 本 wave の最中だけで local main は 8 commit 進んだ。T-2412 が閉じようとしている
失敗 (spec が使えない) を作り直すことになる。

### 狭い形の材料 (裁定へ返す)

狭い形は捨てたが、保証は祖先形より強い (tree が spec path を除いて同値であることを主張できる)。
敵対レビュー 2 本と変異 9 件で検証済みである。採否はユーザーの判断であり、材料を残す。

- `mutation-spec-final.json` / `mutation-ledger-final.json` — 狭い形の変異本走 (9/9 KILLED)
- `mutation-spec-probe.json` / `mutation-ledger-probe.json` — その probe 段
- `verbatim/review-a.md` — 狭い形に対する敵対レビュー。`--ignore-submodules=none` が無いと
  `.gitmodules` の `ignore = all` の下で gitlink 差し替えが差分から消える、という real 所見を含む。
  **この所見は狭い形を採る場合にだけ意味を持つ。**祖先形では tree 同値を主張しないため発火しない。

## 変異

祖先形の本走は `mutation-spec-n-final.json` / `mutation-ledger-n-final.json`。probe 段で全 7 件が
検出されることを確かめてから期待 node を確定した (`mutation-spec-n-probe.json` /
`mutation-ledger-n-probe.json`)。

N01 (祖先判定の除去)、N02 (真の祖先を等値許容へ緩める)、N03 (spec blob 比較の除去)、
N04 (実行時 HEAD 判定の除去)、N07 (`_read_tracked_bound` の blob query 除去) は、いずれも
狙った 1〜2 node だけが赤になる。N05 (finalizer の期待 `runtime_head` を `source_commit` へ戻す) は
47 node、N06 (blob query を symbolic `HEAD:` へ戻す) は 2 node である。

## 受入所要台帳の欠落

`orchestrator/tests/test_floor_pair_driver.py` は 209 node すべてが受入所要台帳に未登録だった。
本 wave が 10 node 足した時点で被覆が 89.962% と 90% 閾値を割り、
`test_g5_real_ledger_covers_at_least_90_percent_of_real_collection` が赤になった。
実走 JUnit から `tools/update_acceptance_duration_ledger.py --add-only` で同 file 全件を登録した。

## 収録物

- `verbatim/` — 段 1 brief、段 2 plan、段 3 レンズ A / B、段 5 実装、段 6 レビュー A / B、
  fix 1〜4、段 4 裁定、段 6 裁定、D1774 訂正裁定
- `mutation-spec-*.json` / `mutation-ledger-*.json` — 狭い形と祖先形それぞれの probe と本走

逐語はいずれも子の出力そのままで、親は編集していない。子の主張がそのまま正しいことを意味しない —
親が real / refuted を裁定した結果は各 commit message と本書にある。

## 非保証

- 本 wave は凍結 spec を実際に発行していない。loader が spec を受理できるようになったことを、
  実 git の正例で示しただけである。
- 権威 floor 成果物の発行にはもう 1 つ障害が残る。T-2423 (成果物名の protocol 要素) は未裁定で、
  本 wave の scope 外として触っていない。
- repo 内の挙動検査は、gate と検査を同じ主体が変更できる限り、意図的な弱体化への完全な防壁ではない
  (D387)。
