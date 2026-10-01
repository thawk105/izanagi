### A-1

**重大度: must-fix — 最古項が commit になった reflog で、land 済みの block が消える**

根拠: [tools/dev_wave_cleanup_stop_hook.py:75](/work/1/SFC/tanab/izanagi/.codex/worktrees/csh-author/tools/dev_wave_cleanup_stop_hook.py:75)、[ruling-stage4.md:7](/home/SFC/tanab/.claude/jobs/d2fe5f67/wave/ruling-stage4.md:7)。

B → C → D を異なる有効な commit OID とする。wave で C を commit → main に land → main が D へ前進 → wave が main を ff 取込み、という順序の後、古い作成記録だけが期限切れになれば、branch reflog は新しい順に次になる。

```text
D merge main: Fast-forward
C commit: wave
```

`HEAD = refs/heads/main = D`。旧判定は最古 OID の C と HEAD が異なり、祖先判定も成立するため block。新判定は **実際の commit 項 C を作成点として除外**し、残りが ff main だけなので通過する。

[hooks/README.md:351](/work/1/SFC/tanab/izanagi/.codex/worktrees/csh-author/hooks/README.md:351) に期限切れの限界は既記載だが、この状態で従来出ていた block を新たに消すことの根拠にはならない。実装は P1 に従っており、裁定側にも欠落がある。

成果物影響: 本当に land 済みの wave 木に対する撤去の促しが失われる。

推奨: 最古項を作成記録と確認できる場合だけ免除し、それ以外は従来判定へ戻す。上記状態の実 Git 回帰テストを追加する。

### A-2

**重大度: must-fix — 有効な Unicode subject を解析不能として通してしまう**

根拠: [tools/dev_wave_cleanup_stop_hook.py:71](/work/1/SFC/tanab/izanagi/.codex/worktrees/csh-author/tools/dev_wave_cleanup_stop_hook.py:71)。

wave で、件名に実際の U+2028 を含む `fix<U+2028>details` を commit し、main へ ff land する。branch reflog は次になる。

```text
C commit: fix<U+2028>details
B branch: Created from HEAD
```

`HEAD = main = C`。Git はこの文字を通常の LF 区切りへ変換しない。commit 件名の取出しと reflog 正規化は、ここで問題となる Unicode 改行文字を保持する。[Git の件名取出し](https://raw.githubusercontent.com/git/git/v2.34.1/sequencer.c)、[reflog 正規化](https://raw.githubusercontent.com/git/git/v2.34.1/refs.c)

一方、Python の `str.splitlines()` は U+2028 も分割するため、`details` が独立した「行」になる。その OID 検査が失敗して通過する。旧 `%H` 出力では subject が解析に入らず block していた。これは不正な Git 出力ではなく、追加した解析処理が作る退行である。

成果物影響: 通常の commit を持つ land 済み wave が、件名の文字によって撤去対象から漏れる。

推奨: レコード境界を実際の LF に限定する。実 Git で U+2028 を含む subject を確認した後、land 済みで block するテストを追加する。

### A-3

**重大度: must-fix — 最古項の空 subject は `.strip()` によって区切りまで失う**

根拠: [tools/dev_wave_cleanup_stop_hook.py:47](/work/1/SFC/tanab/izanagi/.codex/worktrees/csh-author/tools/dev_wave_cleanup_stop_hook.py:47)、[追加テスト:5503](/work/1/SFC/tanab/izanagi/.codex/worktrees/csh-author/orchestrator/tests/test_hooks.py:5503)。

B を指す wave を `git update-ref --create-reflog refs/heads/wave B` で作成し、その既存 branch を `worktree add` で開く。そこで C を commit して main へ land すれば、次の有効な出力になる。`␠` は空白を表す。

```text
C␠commit: wave
B␠
```

`HEAD = main = C`。`run()` の `.strip()` が末尾の `B␠\n` を `B` に変えるため、72 行目で「区切り欠落」とされて通過する。旧 `%H` 判定は block。

追加された空 subject テストは、空 subject が**最新項**で、末尾に作成記録がある場合だけを扱う。この境界を検出できない。

成果物影響: 有効な空 subject を持つ land 済み branch で、従来の block が消える。

推奨: reflog 出力の末尾空白を保持し、レコード終端だけを除去する。最古項が空 subject のケースも、加工前の出力を assert して検査する。

### A-4

**重大度: must-fix — 許可した subject は local main の取込みを証明しない**

根拠: [tools/dev_wave_cleanup_stop_hook.py:75](/work/1/SFC/tanab/izanagi/.codex/worktrees/csh-author/tools/dev_wave_cleanup_stop_hook.py:75)、[brief-stage1.md:17](/home/SFC/tanab/.claude/jobs/d2fe5f67/wave/brief-stage1.md:17)。

次の状態を構成できる。

1. local main と wave は B。別 branch の C は B の子。
2. lightweight tag `refs/tags/main` が C を指す。
3. wave で `git merge --ff-only main` を実行。
4. primary checkout の local main に wave を ff land。

曖昧な `main` は branch より tag が優先されるが、merge の reflog action には引数名が使われる。[Git の参照解決順](https://git-scm.com/docs/gitrevisions)、[merge 実装](https://raw.githubusercontent.com/git/git/v2.34.1/builtin/merge.c)

したがって wave の reflog は次になり、`HEAD = refs/heads/main = C` で旧判定は block、新判定は通過する。

```text
C merge main: Fast-forward
B branch: Created from HEAD
```

これは追加テストが守ろうとする「main 以外から取込み、その後 land」に相当する。さらに、`GIT_REFLOG_ACTION='merge main'` を設定した `git commit -m Fast-forward` でも同じ subject を生成できる。[commit の action 選択](https://raw.githubusercontent.com/git/git/v2.34.1/builtin/commit.c)

成果物影響: subject の完全一致を根拠に、実際には作業 commit を取り込んで land した wave を免除する。

推奨: P1 を再裁定する。subject だけでは「自分の commit 0」と広い非退行条件を保証できない。要件を維持するなら、同期操作の来歴を確認する設計が必要になる。

## 総括

**NO-GO。** 指定された基本例は満たすが、上記はいずれも従来 block していた land 済み状態が通過する反例であり、「撤去の促しが消える方向の緩和はしない」に反する。A-1・A-4 は親の P1 自体にも修正が必要。

その他の監査結果は以下のとおり。

- **差分の範囲:** `stage5.patch` は完全な `HEAD^..HEAD` 差分とバイト単位で一致。所有する 2 ファイルだけで、既存テスト・既存 helper の変更、隠れた分岐、所有外変更はない。HEAD に対する追加入力済み差分もない。ただし、これは初回委任時の guard 発火を証明するものではない。
- **不変条件:** Git 呼出しごと最大 2 秒、合計予算 5 秒、`stop_hook_active`、入力上限 1 MiB、REASON、例外時の fail-open はコード上不変。ただし A-2・A-3 は、新たに正常入力を fail-open 経路へ送る。
- **残る誤 block:** SHA 指定 ff、`pull --ff-only`、`reset --hard main` は免除されない。`merge --ff-only main -m ...` も subject に追加文言が付くため対象外。通常の引数による DW-O20 の修正として限定することは裁定と整合するが、「ff-only 全般を解消」とは報告できない。[merge](https://raw.githubusercontent.com/git/git/v2.34.1/builtin/merge.c)、[pull](https://raw.githubusercontent.com/git/git/v2.34.1/builtin/pull.c)、[reset](https://raw.githubusercontent.com/git/git/v2.34.1/builtin/reset.c)
- **他の経路:** 通常の commit・rebase・cherry-pick・am・非 ff merge・`branch -f` の subject は許可集合と異なる。`worktree add -b` は作成記録を置く。許可対象の merge 文言と作成文言は英語リテラルで、ロケール変更による翻訳を前提にした欠陥は見つからない。
- **追加テスト:** 実 Git を使用し、subject を判定前に assert している。固定 OID 等の揮発値、既存期待値の緩和はない。ただし環境・ユーザー設定は既存 helper から継承するため、`GIT_REFLOG_ACTION` 等による環境依存の赤はありうる。

M1〜M5 は、正常な Git 実行を前提とすると、次の追加テストが他の判定による覆い隠しなしに検出する構成になっている。

| 変異 | 対応テスト（`test_cleanup_stop_` 以下） | 失敗する理由 |
|---|---|---|
| M1 | `blocks_commit_landed_after_ff_main` | 必要な block が消える |
| M2 | `allows_ff_main_with_zero_commits` | 不要な block が出る |
| M3 | `blocks_landed_ff_from_other_branch` | side の ff が免除される |
| M4 | `blocks_landed_commit_after_another_ff_main` | 過去の commit が無視される |
| M5 | `allows_ff_main_with_zero_commits` | 作成記録が免除を妨げる |

**すべて静的評価。委任・書込み・テスト実行はしておらず、変異 KILLED や受入成功の実測とは扱わない。**