## 対応表

| 初回所見 | 状態 | 再レビュー判定 |
|---|---|---|
| レビュー A #1 — NUL blocker | closed | submit は walltime を Python 内で出力前に比較するため、NUL が command substitution に到達しない。親の実測とも一致。 |
| レビュー A #2 — 型による層の分裂 | closed | submit/job とも数値 7 key を strict `int` に統一。親実測でも equal-float/near-float は両側同じ `type mismatch`。 |
| レビュー A #3 — 単独削除の等価性が偽 | closed | strict int 下では整数和から削除した cap が一意に決まる。整数反例なし。下記 F3 参照。 |
| レビュー A #4 — mode drift | closed | override 無しは `copy2`、有りは `copymode`。生成先 mode assert は非恒真で、`copymode` 削除を検出する。ただし新規 nit #2 あり。 |
| レビュー B #1 — 整数型未凍結 | partial | production guard は閉じたが、型テスト・変異証拠は key 単位で未完。equal-float の単一理由負例は member だけで、新規 must-fix #1 が残る。 |
| レビュー B #2 — mode drift | closed | 全共有 caller の無条件 `write_text` は解消。既存 caller は従来の `copy2` に戻った。 |
| レビュー B #3 — 末尾 newline | partial | 意図どおり未修正。両 script の command substitution は今も末尾空行を正規化する。regression はない。 |

## 新規所見

1 / must-fix / [test_t126_pegasus_tools.py:3083](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/orchestrator/tests/test_t126_pegasus_tools.py:3083)、[同:3977](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/orchestrator/tests/test_t126_pegasus_tools.py:3977)、[submit:211](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/tools/pegasus/submit_t126_qualification.sh:211)、[job:466](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/tools/pegasus/t126_qualification.sh:466)

成果物影響: strict 型集合から一 key が脱落する回帰を検出できず、異なる policy hash／series identity を持つ同値 float policy が再び受理集合へ入る。

scope: 内。型凍結 fix の検出力。

実証: 静的実証。pytest は未実行。

型負例のうち単一理由なのは `member_cap_s=900.0` だけである。

- `attestation_cap_s=600.0000000000001` は型と値の両方で拒否。
- `round_gap_s=True` は型、値、submit では和も不一致。
- `walltime=10` は型と値の両方で拒否。非文字列で canonical 文字列と等価な JSON 値はないため、型 guard 自体も受理集合上は冗長。
- bool は意図どおり `type(True) is int` が偽となり型診断が先に出るが、`isinstance` へ退行しても値比較が拒否する。これは semantic KILL ではなく診断感度 pin にすぎない。

具体的には、submit の prologue/finalize、job の finalize を strict 型走査から外す変異は、現テストを通したまま `900.0` / `600.0` を受理できる。静的 freeze test も `==` だけなので float を区別しない。

2 / nit / [test_t126_pegasus_tools.py:829](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/orchestrator/tests/test_t126_pegasus_tools.py:829)

成果物影響: 成果物値は変わらないが、Git 上は同じ executable mode の正当な checkout でも共有 fixture が作成前に偽赤となり得る。

scope: 内。mode fix の付随 assert。

実証: 静的。異なる umask での実走は未実証。

`assert source_mode == 0o755` は Git の tracked `100755` より強い。Git が実質的に追跡する executable bit を保った `0700` 等の checkout も拒否する。一方、生成先と source の mode 比較は恒真ではなく、`copymode` の no-op 化を検出できる。

`copymode` が timestamp/xattr を複製しない点は成果物 drift ではない。override 無しは `copy2` のままであり、override 有りは内容を変更後に Git commit され、tree/series identity が見るのは内容と tracked mode であって timestamp/xattr ではない。

## F3 の整数反例監査

固定部分は `16×900 + 7×1800 = 27000`。

- prologue 比較削除: `p + 600 + 600 + 27000 = 29100` より `p=900`
- attestation 比較削除: `900 + a + 600 + 27000 = 29100` より `a=600`
- finalize 比較削除: `900 + 600 + f + 27000 = 29100` より `f=600`

Python 整数は overflow せず、bool/float は先行型 guard が拒否する。`[-40000,40000]` の整数 probe でも解はそれぞれ canonical 1 点だけだった。

したがって、fix 子の「strict int 下では submit の cap 比較単独削除は等価変異へ戻る」という結論は成立する。

## 変異監査

s4 C 節の登録済み変異で、fix 後に静的に殺せなくなった ID はない。

| 登録済み変異 | 静的判定 |
|---|---|
| M-S1〜M-S4 | int の compensating vector が型 guard を越え、対象比較削除後に scheduler 到達するため KILL 可能 |
| M-S5 | 完全出力後 rc=73 の production reader 経路で KILL 可能 |
| M-J1〜M-J5 | 対応する単一 drift が downstream marker へ到達して KILL 可能 |
| M-J6〜M-J8 | Python 値 guard＋mapping guard の登録済み両層変異で KILL 可能 |
| M-J9 | canonical 正例が mapping assert で停止するため KILL 可能 |
| M-J10 | late-failure producer を無視して downstream へ進むため KILL 可能 |
| M-C1〜M-C4 | 全 vector が positivity/type guard を越え、比較削除後に受理されるため KILL 可能 |

新規登録が必要な変異は次のとおり。

- `U-S-WALL-NUL`: submit の Python 内 walltime 値比較を削除。NUL 負例が scheduler 到達へ変わるため、現 NUL テストで semantic KILL 可能。
- `U-S-TYPE-*` / `U-J-TYPE-*`: 数値 key ごとの strict-int guard 脱落。各 canonical 値の `.0` を単一理由負例にする。
  - submit の member/gap/prologue/attestation/finalize は単層。
  - job の member/gap/attestation/finalize は単層。
  - submit の walltime_s/wmax、job の walltime_s/wmax/prologue は mapping assert に mask されるため両層変異として登録。
- `U-FIXTURE-COPYMODE`: `copymode` を no-op 化。生成先 mode assert が赤になるため KILL 可能。

現状で semantic KILL 証拠がないのは、少なくとも submit の prologue/finalize、job の finalize、ならびに gap/attestation の過剰決定型ケースと上記 mapping 両層変異である。

## scope 監査

scope 外 4 件への production 変更はない。

- A2 残余: collector/public verifier の予約 policy 意味論検証は未追加。
- A5: submit の `no_dups` と job の last-wins 非対称は残存。
- B6: 予約 block 以外の 7 readarray は未変更。
- A8: `member_term_grace_s` は引き続き両 script の射影外。

F5 も未修正で、[submit:189](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/tools/pegasus/submit_t126_qualification.sh:189) と [job:453](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/tools/pegasus/t126_qualification.sh:453) の command substitution は末尾空行を消す。

新設 subprocess テストは production script を通っている。job 側の変更は scratch path 一箇所だけで、reservation parser は production 本文である。問題は到達性ではなく負例の単一理由性である。

既存・履歴上の承認済み予約 policy は canonical な整数表記のみで、control protocol も既に strict int だった。strict 型検査による既存の正当な policy の過剰拒否は見つからなかった。

## 総括

(a) 未 closed の初回所見: レビュー B #1 は検出力が partial、レビュー B #3 は意図的に partial。regressed はなし。

(b) 新規 blocker: なし。新規 must-fix は型 guard の key 単位 mutation proof 欠落 1 件。

(c) 殺せない変異: s4 C 節の登録済み ID はなし。未登録では `U-S-TYPE-PROLOGUE`、`U-S-TYPE-FINALIZE`、`U-J-TYPE-FINALIZE` と、過剰決定・mapping mask を持つ型変異群が未 KILL。

(d) 判定: NO-GO。production の現在値は親実測どおり揃っているが、新設 strict 型 guard の semantic mutation 証拠が不足している。equal-float を数値 key ごとに追加し、mask される key は両層変異で閉じる必要がある。pytest は実行しておらず、緑は主張しない。