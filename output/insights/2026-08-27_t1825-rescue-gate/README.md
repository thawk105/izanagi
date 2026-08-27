# [T-1825] / [T-1826] 掃除で失われる commit を掃除の前に可視化する

wave `dev-wave-t1825-rescue-gate`、branch `worktree-dev-wave-t1825-rescue-gate`。
base = local main `b253e0b7`。実装 tip = `9f8646e06`。

## 何を作ったか

`tools/check_branch_rescue.py` (schema `izanagi-branch-rescue-v1`)。
branch 削除と worktree 撤去を**ひとつの操作**として受け、その操作で最後の恒久的な根を失う
commit を列挙し、各 commit に着地判定と自動 gc が回収しうる最早時刻の**下界**を添える。
`docs/unreachable-object-ledger.md` に期限つき台帳を置き、`/cleanup-branches` の §1 と §5 へ配線した。

rc は「削除してよいか」ではなく「**完全な絵を描けたか**」だけを表す。
判断するのはユーザーであり、道具の仕事は判断の前に材料を出すことである。

## 一次資料

- 親の実測: `verbatim/s1-measurements.md` (M1〜M9)、`parent-dogfood-1.md`、`parent-dogfood-2.md`
- 段 2 プラン (採用せず): `verbatim/s2-plan.md`
- 段 3 独立検証 2 本 (両方 NO-GO): `verbatim/s3-lensA.md`、`verbatim/s3-lensB.md`
- 段 4 裁定とプラン v2: `verbatim/s4-adjudication.md`
- 段 5 実装報告: `verbatim/s5-A.md`、`verbatim/s5-B.md`
- 段 6 敵対レビュー 2 本: `verbatim/s6-reviewA.md`、`verbatim/s6-reviewB.md`
- 段 6 裁定と 2 つの追補: `verbatim/s6-adjudication.md`、`...-addendum.md`、`...-addendum2.md`
- 焦点再レビュー: `verbatim/s6-focus.md`
- 段 6 fix 4 本: `verbatim/s6-fix3.md`〜`s6-fix6.md`
- 変異: `mutation-probe-out.json` (観測)、`mutation-final-spec.json`、`mutation-final-out.json`

## 決め手になった実測 (すべて親が独立に取った)

| # | 実測 | 値 |
|---|---|---|
| N1 | `git rev-list --stdin` の stdin に `--not` を置く | `fatal: options not supported in --stdin mode`。`^<oid>` なら通る |
| N3 | non-main local branch と checkout 中 | 31 本中 27 本 |
| N4 | `ahead=0` の branch と checkout 中 | 20 本中 18 本 |
| N5 | git 2.34.1 の loose auto-gc 標本 (`objects/17`) | 22 個。閾値 `(6700+255)/256` = 27。**残り 5** |
| N6 | `git count-objects -v` の総数 | 6422 (総数由来の余裕は 432 で、これは発火余裕ではない) |
| N7 | 真の root 集合で喪失閉包が非空の branch | 31 本中 10 本、1〜12 commit |
| — | 喪失閉包に入る commit の storage | 39 件中 **23 件 (59%) が packed** |
| — | `git worktree list --porcelain` の `locked` | 53 worktree 中 **37 本** |
| E6 | `t1629` を branch だけ消す / worktree も畳む | **0 commit / 12 commit** |

## 設計上いちばん効いた判断

依頼の文言は「branch 削除前の rescue gate」だったが、実装は**掃除操作そのもの**をモデルにした。
E6 のとおり、branch だけを消す前提では「失われるものは無い」と出る同じ branch が、
worktree も畳む前提では 12 commit を失う。`/cleanup-branches` §3 は worktree を撤去するので、
文言どおりに作っていれば安全だと報告した直後に 12 commit を失っていた。

## 4 つの検証層がそれぞれ違う型の欠陥を出した

| 層 | 出した欠陥 |
|---|---|
| 段 3 独立検証 | プランの中心 command が動かない。配線先が構造的に一度も発火しない |
| 段 6 敵対レビュー | 削除される ref の reflog を引き算側にしか置かず、commit が閉包から丸ごと消える。新 schema へ呼び手ゼロの定数を再生成 |
| 焦点再レビュー | 「全 19 件 closed」の申告のうち **6 件が未了**。防壁の wrapper が任意実行の入口に |
| 親の実データ試走 | `locked` を拒否して実 repo で常に rc=2。packed を判定不能扱いにすると 59% で止まる |
| 変異検査 | レビュー 4 本が見逃した 1 件。正例の走行が変異箇所を通っていなかった |

どれか 1 つでも省いていれば通っていた。

## 検査結果

- テスト: **614 passed, 3 skipped** (親が実走。子は sandbox の制約で pytest を一度も実走できず、
  そのことを正直に申告した)
- `python3 tools/check_docs.py`: 違反なし
- `python3 tools/check_ai_provenance.py`: 6279 件、新規違反なし
- 変異 matrix: baseline `PASSED`、**9/9 KILLED、SURVIVED 0、MISMATCH 0**
  (anchor は `9f8646e06` に束縛)
- 実 repo dogfood: rc=0 / 閉包 1 commit / issues 空 / repo control bytes 不変

## Codex resume 監査 (2026-08-28)

Claude 中断後、foreign/locked な元 worktree は編集せず、tip `7048282f9` から専用 Codex resume
worktree を作った。main 未到達 8 commit を固定 diff と独立 Codex review で再監査し、次の 3 件を
scope 内の real blocker として追加修正した。

- scoped `gc.<pattern>.reflogExpire` を無視すると喪失期限の下界を未来へ出せる。
- child landed report が対象 OID に束縛されず、別 commit の判定を誤帰属できる。
- ledger の解決 field と status が不整合でも受理し、解決済み object の audit 再報告を通知しない。

修正後の焦点 review は先行所見を含め blocker 0 / GO。関連 3 file は **677 passed, 3 skipped**。
変異は既存 9 件を final merged tip `d269408cb` で再走して 9/9 KILLED。新規 M31〜M35 は初回
4 KILLED / M34 MISMATCH (期待 node 1 件漏れ) だったため結果を残し、期待完全集合を 2 node へ
訂正した M34 を再走して KILLED とした。受入全走が露出した Python child の bytecode 無効化 env と
pytest-only ledger test の runner 契約も追加修正し、env 2 経路を M36/M37 で個別に KILL した。
したがって最終 matrix は baseline PASSED、**16/16 KILLED、SURVIVED 0、MISMATCH 0**。
一次資料は `mutation-resume-*.json`。

final tip の実 repo dogfood は、元/resume 両 branch と両 worktree の仮想撤去で閉包 10 commit、
単一 branch `worktree-cleanup-branches-20260825` で閉包 1 commit / landed 1 を得た。ただし共有 repo の
ref/worktree が走行中に動き、いずれも `root-snapshot-moved` で rc=2。古い根で完全な絵を主張せず
fail-closed に停止した。元 worktree/branch と resume worktree/branch は削除していない。

## 覆わない範囲 (成果物へ固定した)

1. 手で打つ `git branch -d`
2. `DW-O28` の自動撤去 (`tools/dev_wave_cleanup.py`)
3. D978 の未施行部分

この gate の**阻止側**が意味を持つのは D978 の施行 ([T-1754]) の後である。
現行の削除条件 (`ahead=0` のみ) の下では喪失閉包は構造的に空なので、
本 wave が置いたのは可視化と報告の経路である。
