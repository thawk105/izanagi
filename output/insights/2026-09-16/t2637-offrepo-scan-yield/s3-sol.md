## blocker (このまま進めてはいけないもの)

### 1. 案4の「抑止集合は厳密に不変」は refuted

段2プランによる案4の不採用を支持する。親の P3 は撤回が必要。

[現行の候補集約](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2637-offrepo-scan-yield/tools/audit_dangling_commits.py:944) は `(OID, device, inode)` ごとに owner と alias を集め、比較成功時に**全 owner へ全 alias を配る**。

反例：

- 到達不能側に、同じ blob の `a.py` と `b.py` がある。
- `/R/out/a.py` と `/R/in/b.py` が hardlink。
- landed 参照は `/R/in/b.py` だけ。

現行全走査では `a.py` にも参照済み alias が配られて抑止される。候補先行で `/R/in/b.py` だけを列挙すると、その owner に `a.py` が入らず抑止が消える。これは既存実装の basename 条件の穴でもあり、「現行等価」と「D247適合」は別である。

さらに、同名 hardlink の最初の代表が親 directory の権限等で open 不能、被覆内の別 alias は読める場合、枝刈りで代表が交代し、**現行では無かった抑止が生まれる**。中間 directory symlink を経由した候補への直接アクセスにも同じ方向の危険がある。

**成果物影響：findings と救出台帳への通知対象が増減し、場合によっては「抑止を広げない」という不変条件に違反する。**

### 2. D970／D1031を将来の findings 全体への破棄許可として使ってはならない — real

[D970](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2637-offrepo-scan-yield/docs/decisions.md:34492) は特定の28件、[D1031](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2637-offrepo-scan-yield/docs/decisions.md:35981) は追加の19件についての裁定である。「控えが一部でもあれば、今後の任意の commit を破棄できる」という一般権限ではない。

off により再表示された新しい commit にこの分類を無条件適用すると、full 再走後に一部の控えが見つかっただけで、残りの未保全 path まで破棄対象にできてしまう。これは単なる注記欠落とは別の、**分類規則の適用対象を広げる危険**である。

**成果物影響：新規 object の台帳 status を、救出未完了のまま `accepted-loss` にする受理集合が広がる。**

プランは「人間の明示的受容」を維持している。この条件に、**既裁定の対象集合を越えた破棄には新しい判断が必要**と明記すれば防げる。

## must-fix (進めてよいが直すもの)

### 1. 案5は台帳と rescue gate の出力を変える — real

「掃除への利得は実質ゼロ」「報告が増えるだけ」は不十分。

[台帳の追記条件](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2637-offrepo-scan-yield/docs/unreachable-object-ledger.md:44) は `unledgered-audit-finding` も対象にする。[`_ledger_check()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2637-offrepo-scan-yield/tools/check_branch_rescue.py:1782) は抑止前後の事情を解析せず、監査に出た commit と台帳を照合する。

したがって、full で全 path が抑止されていた未記帳 commit が off で再表示されると、

- `unledgered-audit-finding` が増える。
- 他に通知が無ければ rescue gate は rc0 から rc3 へ変わる。
- 契約上、新たな `pending` entry の追記対象になる。
- 解決済み entry なら stale resolution 通知が増える場合もある。

**成果物影響：台帳の entry 集合、通知集合、gate の rc が変わる。削除可否を直接表す rc ではないが、出力不変ではない。**

この変化を裁定パッケージに含めること。また、cleanup 本文は同一実行で台帳編集・救出 ref 作成を許さないため、追加された判断・記録は別の明示起動作業へ引き渡す必要がある。

### 2. 「triage 前に full」だけでは完全性を保証しない — real

現行は、root 未指定・拒否、巨大 blob、読出し失敗、参照確認失敗でも、注記が空になり得る。`scan_performed=True` も全対象の確認成功を意味しない。

特に [抑止集約](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2637-offrepo-scan-yield/tools/audit_dangling_commits.py:1651) は `reference_failure` があると、bytes 一致を得ていても注記を出さない。

**成果物影響：`full` という方針名だけで「外部控え皆無」を確定すると、分類レポートの根拠が誤る。**

プランの「未実施と否定結果を分離」を、root・失敗・上限除外にも広げること。確認不能は確認不能として残し、過去の注記を現在の控え存在証明として再利用しない。

### 3. 案4を再検討する場合の境界条件

| 対象 | 静的検査結果 |
|---|---|
| 内部 symlink | 現行は directory symlink を辿らず、file symlink を除外。被覆 path から直接開始するとこの条件を迂回し、抑止が増え得る。 |
| hardlink | 上記の owner／alias 交差、代表選択の順序依存で厳密等価が破れる。 |
| bind mount | 現行に mount 境界の除外は無く、通常 directory として辿る。同一 inode の alias 集約も起こり得る。`-xdev` 等を追加すれば射程が変わる。 |
| 複数・入れ子 root | `/R/sub` は内側 root 自身でも、外側 `/R` に対して有効な祖先。root 文字列の一律除外や被覆 directory の新 root 化は不正。 |
| 拒否 root | `_validate_offrepo_roots()` を先行させ、拒否された根から探索開始点を作らない。 |
| 非NFC・非ASCII・不正UTF-8 | 現行は filesystem byte の完全一致。Unicode 正規化・置換 decode・Unicode の `\s` は等価でない。 |
| 改行・制御文字 | 下記のとおり二つの matcher 自体が一般には非等価。VT・FF 等を空白として追加するのも境界拡張。 |
| `MAX_BLOB_SIZE` | 到達不能側の候補制限。landed 側の参照抽出に流用すると既存参照を失う。 |
| 二つの include flag | findings 側の除外解除。landed 検索へ同じ除外を適用してはならない。 |
| `main_ref` の移動 | 現行は入口で commit OID を一度だけ固定する。先行抽出も同じ OID を使う必要がある。 |

**成果物影響：いずれも抑止対象・注記対象・証拠 path が変わる条件であり、単なる実装上の好みではない。**

byte 単位の反例は明確である：

```text
root    = b"/R"
pattern = b"/R/job/a b.py"
content = pattern + b"\n"
```

`_has_bounded_path_reference()` は左右だけを見るので真。本番 `_bounded_path_reference_matches()` は root 末尾から最初の空白で切るため、この pattern は不一致。

逆に root 自体が `b"/R x"` なら、本番 matcher は root 内部の空白を飛び越して検索する。content 全体を極大非境界列へ分割する方式は、この一致を取り落とす。

したがって「二方向が等価」は、少なくとも境界 byte の位置に条件を付けなければ成立しない。旧 helper に合わせて本番 matcher を直すことも、**現行より抑止を増やす別変更**になる。

## nit

- 「17件」は実体 file 数。注記・分類の単位は23 `(commit,path)` 対と区別する。
- 段2プランは既に案4の反例、main 固定、symlink、byte path 等を挙げている。これらを未対処の推奨案5の欠陥として重複計上する必要はない。
- pytest・監査全走は実施していない。ここでの反例は静的検査であり、テスト緑の報告ではない。

## 親の実測とその一般化への反証

### P1の「祖先条項は構造的にほぼ不発」は refuted

**現在の main に、祖先条項が成立する実在経路がある。**

[land 済みの probe:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2637-offrepo-scan-yield/orchestrator/manual_probes/test_t2397_a1_source.py:21) は次を記載している：

```python
job = Path("/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2397-a1-attempt4")
```

同 directory と、その子 `probe-head.txt` は stat でそれぞれ directory／regular file と確認できた。この子から生成する祖先 pattern は、上記文字列と一致する。左右は引用符であり、両 matcher で有効な参照になる。

これは**条件5の実在の成立経路**である。現在の到達不能 blob と bytes が一致することまでは主張しない。また、実装は「文書」を拡張子で限定せず、main のコードも参照証拠に使う。

既存の祖先参照陽性テストも同じ構造を固定している。

### 2走・30 commit・探索根1本から収量の一般則は出せない

2走は同じ17 file・23対を再観測しており、独立した広い母集団の標本ではない。30 commit は core の選別後の集合で、他時点・他 root・今後の未着地作業を代表しない。

また、123/1,188 は深さ1の被覆に関する数であり、深い directory の祖先参照を含めた発火率ではない。

**成果物影響：「今後も抑止はほぼ無い」を案選択の根拠にすると、再表示件数・台帳作業量の見積りを過小評価する。**

### 292対→0対を D957 では説明できない

[2026-08-26 の記録](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2637-offrepo-scan-yield/docs/archive/worklog-phase3-0826-980.md:6) は、**抑止292対と除外13,488対が同時に存在し、4走とも同値**と明記している。292は D957 後の値である。

したがって、build cache 除外は以前の大幅減少の説明候補でも、**292→0の説明にはならない**。同じ境界規則の下でも、対象 commit、bytes 一致候補、参照、実体の残存状態が変われば両観測は両立する。ただし、どれが実際の原因かは提示資料から確定できない。

必要なのは当時の292対との対応比較である。復元できなければ、結論は「原因未確定」とする。現在の17 file の表記事情から過去の消失原因を逆算してはならない。

## 総括

**案4の厳密等価性と P1 の構造的一般化は refuted。段2の案4不採用を支持する。**

**案5の「注記欠落だけで救出対象が破棄側へ倒れる」は refuted。** 固定した core に対して抑止は消えるだけで、欠落した控え情報は通常、余分な救出側へ倒れる。自動 gate に破棄分類を行う経路も無い。

ただし、案5でも台帳・通知集合は変わる。既裁定を新規対象へ無条件拡張したり、未確認を確認済みに変換したりすれば危険になる。案4には、枝刈りによって新しい抑止を作る直接の経路がある。

推奨案5は、**台帳への影響、full の確認限界、破棄裁定の対象範囲**を追記したうえで裁定へ進めてよい。「抑止が構造的にゼロだから安全」を採用理由にはしない。