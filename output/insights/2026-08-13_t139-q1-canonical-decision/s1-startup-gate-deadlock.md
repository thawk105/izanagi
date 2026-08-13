# scope 外 real 所見 — main が全 background job wave の起動 gate を恒久的に赤にしている

```text
発見: 2026-08-13 07:30 JST、wave dev-wave-t139-q1-canonical-decision の段 1 (起動直後)
発見者: 親 (dev-wave manager)
分類: scope 外 real。本 wave の scope (canonical decision の起草) と無関係で、実装面の手当てを要する
authority: parent。**ユーザー裁定はまだ無い。**
```

## 事実 (すべて実測)

**1. `docs/handoff/` 直下に、所有 wave が終了した handoff が tracked のまま残っている。**

```text
docs/handoff/2026-08-13-known-red-octopus.md   (tracked in main)
docs/handoff/README.md
```

**2. それは意図的に復元されたものである。** 所有 wave は `docs/handoff/README.md` の
「正常終了時は worklog へ吸収してファイルを削除する」に従って削除したが、land に拒否されて戻した。

| commit | 時刻 (JST) | 内容 |
|---|---|---|
| `f0b5cc99` | — | known-red-octopus wave の handoff を置く |
| `57355bf1` | 2026-08-13 04:53:48 | worklog へ吸収して削除する |
| `aedc04ec` | 2026-08-13 05:18:04 | **land が保護する control-plane path なので撤去を取り消す** |

`tools/dev_wave_land.py` は `docs/handoff/` 直下を validated foreign control-plane path として扱い、
**その path を変更する tip を rc=21 で拒否する。追加は通るが削除は通らない。**

**3. 一方、背景 job の起動 gate はその path が空であることを要求する。**

`DW-O20` は背景 job に `tools/check_wave_startup.py --external-handoff <handoff>` を必須としている。
`tools/check_wave_startup.py:350` の実装はこうである。

```python
if forbid_worktree_handoff or external_handoff is not None:
```

つまり **`--external-handoff` を渡すと `--forbid-worktree-handoff` が含意される。**
その検査は `docs/handoff/` 直下に `README.md` 以外の regular file があれば失敗する
(`tools/check_wave_startup.py:253-259`)。

**4. 実測。** 本 wave の worktree で `DW-O20` どおりに実行した結果:

```text
INFO: local main との乖離なし (0 commit; HEAD は refs/heads/main を含む)
NG: worktree-local handoff remains (2026-08-13-known-red-octopus.md): 外部 handoff を正本にして worktree 内の残置を除く
RC=1
```

**5. main 単独で再現する。** main checkout (`/work/1/SFC/tanab/izanagi`) で同じ command を
実行しても同じ `NG: worktree-local handoff remains` が出る (branch 判定の NG は main では当然出るので別)。
**本 wave の branch は `docs/handoff/` を 1 bit も変更していない**
(`git status --short docs/handoff/` = 0 行、untracked 0 件)。

**6. `check_docs.py` も同じファイルについて警告を出す** (rc には算入しない)。

```text
docs/handoff/2026-08-13-known-red-octopus.md: 基準コミット '01487bb4' が 40 桁または 64 桁の hex ではない
```

## なぜこれが構造的な袋小路なのか

- land は `docs/handoff/` 直下の**削除**を拒む (control-plane 保護)。
- 起動 gate は `docs/handoff/` 直下が**空**であることを要求する (残置検出)。
- したがって **wave の中からは解消できない。** 削除すれば land が rc=21 で止まり、
  残せば次の全 wave の起動 gate が rc=1 で止まる。
- **2026-08-13 05:18 以降に起動する背景 job の dev-wave は、すべてこの赤を踏む。**
  本 wave が最初の 1 本である可能性が高い (直前に land した wave はそれ以前に起動している)。

## 既存台帳との関係

`docs/failures.md` の `check_wave_startup` 関連エントリ 3 件 (`:2090` / `:2108` / `:2117`) は
いずれも **local main との乖離**および**同一 worktree の二重起動**の事象であり、
本件 (handoff 残置と land 保護の衝突) は記録されていない。**新規の失敗型である。**

## 本 wave の扱い

**この赤を本 wave 由来としない。** 根拠は 2 つ。

1. 本 wave は untracked handoff を 1 件も作っていない。専用 handoff は repo 外
   (`/work/1/SFC/tanab/dev-wave-jobs/handoff/dev-wave-t139-q1-canonical-decision.md`) にある。
   したがって `DW-O20` の趣旨 (「untracked handoff を残して gate を走らせない」) は満たしている。
2. 赤は main 単独で決定的に再現する。本 wave の branch は当該 path を変更していない。

**この判断自体をユーザー裁定へ返す。** `DW-STOP` は「検査が赤」を停止条件としており、
親が「趣旨は満たしている」と読んで先へ進んだことは規律の緩和と読まれうる。

## 問い (ユーザー裁定を求める)

### S-1. この袋小路をどう解くか

- **(a) 起動 gate 側を直す — `docs/handoff/` 直下の *tracked* file を残置と数えない** (親推奨)。
  **理由:** 検査の目的は「自分の untracked 残置を持ち込ませない」ことであり、
  main が tracked で持つ control-plane file はその対象ではない。land の保護と衝突しない。
  実装面なので Codex `role=author` の子が要る。
- (b) land 側を直す — 所有 wave が終了した handoff の削除を通す。
  → 親は反対する。land の control-plane 保護は**並行 wave が互いの生きた handoff を消すこと**を
  防いでいる当の機構である。「所有 wave が終了した」を land が機械判定できる根拠が無い。
- (c) 人間が通常セッションで当該 file を削除する (wave の外なので land を通らない)。
  → 一度は解けるが**再発する。** 次に handoff を land 対象の tip に含めた wave が
  同じ状態を作る。`docs/handoff/README.md` の「正常終了時に削除する」という契約自体が
  land の保護と噛み合っていない。
- (d) 現状維持 — 各 wave が赤を読んで「main 由来」と判断して進む。
  → 親は反対する。**`DW-STOP` の「検査が赤なら停止」が形骸化する。**
  赤を各 wave の裁量で越えてよいことにすると、本物の赤も同じ扱いになる。

### S-2. `docs/handoff/README.md` の契約を是正するか

現行の「正常終了時は worklog へ吸収して**削除する**」は、land の control-plane 保護と
直接矛盾する。`aedc04ec` はその矛盾に実際にぶつかった commit である。

- **(a) 「land 対象の tip に削除を含めない。land 後に wave の外で消す」へ是正する** (親推奨)。
- (b) そのまま → 次の wave が同じ往復 (受入全走をやり直す約 15 分の損失) を繰り返す。

## この所見が成果物に与える影響

**直接の影響は無い** — certified 選択・レポート・試行台帳のどの値も変わらない。
影響するのは**開発ループの可用性**である。放置すると、背景 job で起動する dev-wave が
すべて起動直後に fail-closed 停止するか、または全 wave が `DW-STOP` を裁量で越えることになる。
後者は正しさ規律の運用そのものを弱める。
