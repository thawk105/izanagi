## 所見

### RA-1

- **区分**: MUST
- **主張**: 最後の holdout 再読後から adapter 完了まで canonical path が無防備であり、現在の path が不正な bytes を指していても CLI は緑を返せる。
- **具体的な失敗経路**: 正規 bytes `L` を capture し、`verify_receipt()` が `active-valid` を返し、[s8b_holdout_freeze.py:920](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_holdout_freeze.py:920) の再読も `L` になった直後、canonical path を未受領 drift `D` へ atomic replace する。adapter には path の現物ではなく capture 済み `L` が [同:939](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_holdout_freeze.py:939) で渡され、その後 path は再検査されないため、[同:951](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_holdout_freeze.py:951) が成功し `verified:` が出る。同型で、[同:934](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_holdout_freeze.py:934) の `known_raw` capture 後に known-axes canonical path を差し替えても、adapter は古い `known_raw` を検査するだけである。
- **成果物への影響**: 単体 verify の rc と運用上の検証報告が、実際の canonical holdout／known-axes が壊れている状態で緑になる。oracle driver は従来の programmatic `verify()` を使うため certified 選択と台帳の直接の受理集合は変わらないが、再開判断・worklog・人間の発効判断が偽の緑を参照する。

### RA-2

- **区分**: MUST
- **主張**: 新規テストは receipt の `invalid`／`issued-but-missing` 状態を一度も与えないため、禁止された legacy fallback への拡張変異が生き残る。
- **具体的な失敗経路**: [s8b_holdout_freeze.py:904](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_holdout_freeze.py:904) を `if resolution.state != "active-valid": return verify(...)` に変異させる。新規テストが作る状態は `active-valid` と `never-issued` だけ（[test_s8b_holdout_freeze.py:469](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/tests/test_s8b_holdout_freeze.py:469)、[同:562](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/tests/test_s8b_holdout_freeze.py:562)）なので、5ケースはこの変異を検出しない。receipt を一度発行した後に invalid または missing にし、canonical path へ現行 source/head に合う legacy 文書を置けば、変異後は `verify()` が通す。
- **成果物への影響**: 発行済み receipt の破損・欠落時に CLI の受理集合が空集合から legacy verifier の受理集合へ広がり、receipt 異常を検証報告から消す。certified 集合は直接変わらないが、T-080 発効状態の報告が偽になる。

### RA-3

- **区分**: MUST
- **主張**: `known_axes_freeze` 発火条件は helper 側だけが adapter の非発火を拒否する防壁だが、その撤去変異を新規テストは検出しない。
- **具体的な失敗経路**: 実 holdout 文書の `known_axes_freeze.sha256` を別値にした raw を作り、その raw hash を持つ mocked `active-valid` resolution と非空 observation を返す。現在は [s8b_holdout_freeze.py:928](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_holdout_freeze.py:928)–932 が拒否する。しかしこのブロックを外すと、adapter は発火条件不一致時に refusal を追加せず既存 observation を返す（[t080_freeze_migration.py:2091](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/t080_freeze_migration.py:2091)–2099）ため helper は緑になる。現行 production `verify_receipt()` は receipt の artifact hash を固定値へ束縛するので安定状態では hash 条件から間接的に導けるが、helper の mock seam を使う既存5ケースにはこの負例がなく、撤去変異がすべて生き残る。
- **成果物への影響**: receipt verifier 側の将来の退行と組み合わさると、adapter が実際には一度も発火していない文書へ T-080 observation を流用し、CLI 検証報告の受理集合を広げる。

### RA-4

- **区分**: SHOULD
- **主張**: non-regular file の検査前に blocking open するため、canonical path が FIFO の場合は「条件1が崩れたら赤」ではなく無期限停止になりうる。
- **具体的な失敗経路**: canonical path を reader のいない FIFO にすると、[s8b_holdout_freeze.py:846](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_holdout_freeze.py:846) の `lstat()` は成功するが、regular 判定より先の [同:847](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_holdout_freeze.py:847) の `os.open(..., O_RDONLY)` が待ち続ける。新規テストには symlink／FIFO／device の負例がない。
- **成果物への影響**: certified 値を誤受理はしないが、再開 preflight と検証レポートが生成されず、運用が停止する。

## その他の検査結果

5条件はいずれも恒真ではない。安定した入力では、alternate path、読めない canonical file、非 `active-valid`／refusal あり、receipt hash 不一致、receipt 検証中の永続的な bytes 差替えをそれぞれ赤にできる。ただし RA-1 の再読後の窓と RA-4 の FIFO は残る。

安定した filesystem に限れば、受理集合は次のとおりである。

- `never-issued` の非 canonical path は従来どおり `verify(path)` に委譲されるため、差分前から広がっていない。
- `path_refusal` を先に作り receipt 検証後に適用する順序から、`active-valid`／invalid 状態で漏れる経路は見つからない。
- `active-valid` では canonical path と receipt 固定 hash の bytes に限定され、意図した T-080 drift 以外の安定文書は構成できない。

`verify()`、`verify_document()`、`generate`、`search` の本体には差分がなく、`s8b_oracle_driver.py` も未変更で引き続き programmatic `verify()` を呼んでいるため、programmatic oracle の受理集合変更は見つからない。

事前登録された MU-1〜MU-4 は対応する負例で検出でき、MU-5 は正例を与えている。一方、RA-2・RA-3 の変異および RA-1 の再読後差替えは生き残る。

## 総括

**NO-GO**。

BLOCKER に相当する programmatic／certified 経路の変更はない。しかし、TOCTOU 硬化を目的とした変更に再読後の偽緑経路が残り、receipt 状態機械と adapter 発火防壁の緩和変異を新規テストが検出しない。RA-1〜RA-3を閉じるまでは commit 前ゲートを通すべきではない。pytest は依頼どおり実行しておらず、緑は主張しない。