# 静的焦点再レビュー

結論は **NO-GO**。§2 の frontier と 92 ledger-entry の算術は正しいが、未台帳の数値を「実測」とした箇所、closure の過大主張、単発時間からの因果断定、§6 の推奨飛躍が残っている。pytest・mutation harness・probe は実走しておらず、緑判定はしていない。

## 1. 数値照合

### §2 frontier

[refuted] 14 列 × 6 行、84 マスに `status` 不一致はない。

| 案 | ledger 集計 | frontier 表 |
|---|---:|---|
| A focal | K=6 / S=8 | 一致 |
| A′ | K=8 / S=6 | 一致 |
| B1 | K=12 / S=2 | 一致 |
| B2 | K=12 / S=2 | 一致 |
| C1 | K=14 / S=0 | 一致 |
| C3 | K=7 / S=7 | 一致 |

A full-file の追加 8 件も全件 SURVIVED で、§2 の「N≥4 は full-file でも生存」と一致する。

判断への影響: frontier 表自体を誤記として棄却する必要はない。

### 「92 変異、不一致 0」

[real] 七台帳の `summary` 合計は `registered=92 / matching=92 / MISMATCH=0 / KILLED=59 / SURVIVED=33` である。

ただし一意な mutant ID と injection diff は各 14 件しかない。92 は同じ 14 変異を複数候補・scopeで評価した **92 mutation executions / ledger entries** であり、92 種類の変異ではない。

判断への影響: 「92 変異」と書くと攻撃面の多様性を約 6.6 倍に誇張するため、「92 実行、14 distinct mutations」へ直す必要がある。

### §3.1 node 数・時間・行数

[refuted] node 数、pytest stdout の秒数、候補 commit の物理行数はすべて一致する。77 node / 5.41 s も A-full baseline と一致する。

[real] 2.37〜2.45 s は ledger の `baseline.duration_s` ではなく、pytest stdout の session duration である。end-to-end ledger duration は約 21.8〜26.9 s。列名「pytest 実時間」は「pytest 報告 session 時間」に限定すべきである。

判断への影響: 現表のままでは、ユーザーが dispatch・collection を含む CI wall time を 2.4 秒と誤認する。

[real] 各案 1 回だけの値から「差が出なかった」「起動時間に埋もれる」「M コスト前提は実測で否定された」とは言えない。観測値自体にも 2.37〜2.45 s の差があり、反復、空 test baseline、分散、p50/p95 がない。

判断への影響: 実行時間を裁定軸から不当に除外する。正しくは「単発観測では順位を確定できない」。

### §3.2 依存数値

[real] `1.87 s / 3.25 s / 6.3 MB / 117 files / 推移依存3個` は、指定された七台帳・七 spec のいずれにも存在しない。ユーザー指定の基準では捏造数値である。`s6-lensD.md` が値を再掲しているだけで測定台帳にはならない。

判断への影響: B2 の導入費を再現可能な測定値と誤認し、依存コストを過小または過大評価する。

[real] 一方、B2 の top-level `hypothesis` import、未導入時の collection error、repo に依存宣言ファイルがないことは候補逐語と repo 静的検査で確認できる。

判断への影響: collection 脆弱性は有効な比較材料だが、未台帳の install 数値と分離すべきである。

### §3.3 C1 負制御

[real] 負制御結果を記録した spec・ledger は存在しない。`s6-corrections.md` は「実施する追加測定」と未来形で終わっているため、§3.3 を「実測」とする証拠鎖がない。

判断への影響: C1 の偽陽性・偽陰性率を確定値として比較すると、C1 の採否を架空の測定で決めることになる。

[real] 「変数 rename（意味保存）」の control は逐語上、loop の `changed` だけを `pending` に変え、定義側を rename していない。これは `NameError` を作る壊れた変更で、意味保存 refactor ではない。したがって「意味保存 3/3 誤検出」は成立しない。

判断への影響: C1 の偽陽性率を 3/3 と水増しし、C1 を不当に不利にする。

[real] `islice` の control は iterator を `changed_view` へ変える形なので C1 が名前差で検出するだけである。alias/body 内 `continue` や helper 内 `islice` は依然見逃せる。

判断への影響: 「islice を検出」と一般化すると、C1 の dataflow 耐性を実態以上に評価する。

## 2. 過大主張

[real] 冒頭の「4 env fixture + docstring の残穴明記で閉じている」は、§5/F の「閉じたとは書けない」と正面から矛盾する。

判断への影響: 現状維持を correctness closure と誤認させる。

[real] 「以下すべて実測に基づく」は偽。§3.2、§3.3、§4 の静的コード推論、未測定 D、恒久コスト列挙を含む。

判断への影響: 実測・静的推論・仮説の証拠強度を区別できなくなる。

[real] 「C1だけが族全体を閉じる」「C3はGを全N閉じる」は過大。台帳が示すのは登録した直接 `iterator[:N]` 14件の検出だけである。C1 は early return・body内絞り込み・helperを、C3は `tuple(successor_rows)[:N]`・`islice`・直接 `tuple.__getitem__` を見逃す。

判断への影響: source-shape detector を走査完全性保証として選ばせ、別構文の縮退を残したまま closure と誤認させる。

[real] `[:10^6]` は台帳にない。静的に C1 が `ast.Subscript` を拒否することは推論できるが、「別途 in-memory 実測」としては証拠不足である。

判断への影響: 未記録 probe を測定済みの追加証拠として二重計上する。

### §4-4 の独立検証

[refuted] 直接 positive-prefix `[:N]` 族に限定すれば、commit `677d0952` の実 edge に対する反証は成立しない。

- serial 1: linux-baremetal g1 / pegasus g1
- serial 2: linux-baremetal g1 / pegasus g2
- `changed` は pegasus 1 件なので P-N≥1 は恒等。
- G-N1 は先頭の据置 linux だけを見て `changed=[]` となり no-op 拒否する。誤受理ではなく誤拒否。
- G-N≥2 は 2 行をすべて見る。

判断への影響: この実 edgeについて「誤受理を作れない」は維持できる。ただし「M=2だから」だけでなく、「未検出域がN≥4でありM=2では恒等」という既存 test frontier との組合せで限定して書くべきである。

## 3. 過小主張・未反映所見

### レンズC must-fix

| 項目 | 反映判定 | 判断への影響 |
|---|---|---|
| C-1 負制御訂正 | [real] 部分反映。decoy 判定は直したが台帳がない | C1コストを未検証値で決める |
| C-2 C3を直接slice検出へ格下げ | [real] 未反映。「Gを全N閉じる」が残る | C3を完全走査保証と誤認する |
| C-3 B2 exact scope・専用環境 | [real] 部分反映。exact file scope は ledger にあるが、runner は共有 `~/.local` Hypothesis | collection隔離と依存隔離を混同する |
| C-4 sibling import束縛 | [real] 本文未反映 | 将来再実行時の別checkout誤束縛リスクを見落とす |
| C-5 scratch/out・byte receipt | [unknown] unique scratch と target restore policy は ledger にあるが、最終 production/test 全path byte一致 receipt は一次資料にない | 「1 byteも変えていない」を過信する |

### レンズD must-fix

| 項目 | 反映判定 | 判断への影響 |
|---|---|---|
| D-1 loader/issuer/serial2分離 | [refuted] 反映済み | この点の修正は不要 |
| D-2 A対B2へ戻す | [refuted] 反映済み | 選択肢構造は改善済み |
| D-3 `@example(64)` 支配 | [refuted] 反映済み | PBT一般化への限定は書かれている |
| D-4 恒久コスト | [real] 部分反映。再materialize費・false-positive SLAが脱落 | no-landとlandの所有費比較が不完全 |
| D-5 Dを未測定・不採用でないとする | [real] 文言は反映したが、§6ではD測定前にAを既定推奨 | 潜在的に優越するDを実質後回しにする |

### 段3の未反映 real 所見

[real] A full-file の P-N1 は既往実測で10 node、semantic 5 / diagnostic 5という所見が本文から消えている。

判断への影響: Aの既存検出幅をfrontierだけに縮約し、候補の純増価値を正しく比較できない。

[real] B1には先頭・中間・末尾の位置変種6 nodeがあるが、B2は末尾 witness 固定である。「B1/B2は完全に同じ」は frontier に限る。挙動カバレッジは同じではない。

判断への影響: B1とB2を実質同一テストと誤認する。

[real] 将来の env 数上限・分布、同時変更数、edge頻度、変異operatorの実在頻度は依然ない。

判断への影響: frontier を実害リスクへ換算できず、Aのrisk acceptance量を判断できない。

[real] 候補をlandしない代償は、§7で「再生成かside branchか」と質問するだけで、anchor drift、依存再配置、tracked commit再作成、再現不能化の費用を比較していない。

判断への影響: no-landを無償・可逆と誤認する。

## 4. 推奨の妥当性

[real] 実測が直接支持するのは「今回の14 direct-slice mutantでは、B2はB1よりfrontierを増やさず、追加packageとcollection failure面を持つため、B2を現時点でlandする根拠がない」までである。

判断への影響: B2 no-land は支持できる。

[real] 「ゆえにA + triggerが最善」は導けない。A′/B1は新規packageなしでfrontierを広げ、単発pytest時間でも不利が出ていない。これらの保守費は未測定で、Dも未測定である。

判断への影響: Aを選ぶと、依存ゼロの追加backstopまたはproduction guardを比較せず捨てる。

したがって、実測が支持する推奨は次である。

> **B2は今はlandしない。A / A′ / B1 / Dの最終選択は決めない。**  
> 現時点でAを採るなら、それは「現行M=2に対する暫定risk acceptance」であり、実測上の最適解ではない。triggerの所有者・記録場所・fail-closedな発火方法を同時に決める必要がある。

## 5. ユーザー判断に不足する情報

[real] 少なくとも次が未確定である。

- future `M_max`、M分布、同時変更数、activation edge頻度
- 反復timing、空pytest baseline、CI/full-suite差分
- Dのoverhead・診断・single/multi-site mutation結果
- triggerの所有者、正本、期限、見逃した場合の防壁
- candidate保存方式と再materialize費
- B2 wheel/lock/hash/offline配置証拠
- C1負制御の正式spec・ledger
- 最終production/test byte一致receipt

判断への影響: これらなしでは「Aが最小総費用」「Dより妥当」「将来再開できる」を判断できない。

## 総括

1. **§3.2・§3.3:** 台帳にない依存数値とC1負制御を「実測」から外すか、正式spec・ledgerを提示する。特に「意味保存rename」は誤り。
2. **§3.1:** 「差なし・起動時間に埋没・実測で否定」を、単発pytest報告値へ限定して撤回する。
3. **冒頭・§2・§5:** C1/C3の「閉じる」を「登録した直接sliceを検出」に格下げし、冒頭の「docstringで閉じている」を削除する。
4. **§6:** 推奨を「B2 no-land」までに限定し、A/A′/B1/Dは未決とする。Aを暫定採用するならtrigger ownerと機械的発火面を同時裁定する。
5. **§3.4・§7:** D測定、future M/exposure、候補no-landの再現費、sibling import、byte一致receiptをユーザー判断材料として補う。