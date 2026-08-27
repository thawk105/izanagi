## 所見

1. [real] TTY は人間性の防壁になっていない。  
   `stage2-plan.md:34-38,79-83,155-166` は承認者を controlling TTY から読み、fake TTY を正例にする。PTY を操作できる AI は任意名と `RATIFY <hash>` を入力できるため、argv・環境変数・draft を閉じても、AI が `approver` を実質決定する経路は残る。成功時には approval の `approver`、予算値、`approved_at`、approval hash、source pin の全てが確定する。これは D1161 の「AI は自分を承認者にしない」 (`d1161-verbatim.md:3-14`) を機械的には守らない。

2. [real] ratify CLI による直接批准は既存 D287 と衝突する。  
   `stage2-plan.md:20-58,105-127` は CLI が approval JSON を発行し、production source の pin を直接変更する設計である。一方 `docs/decisions.md:13151-13166` は approval 発行 CLI/API を作らず、pinned literal を人間がコード diff でレビューする境界を要求する。`docs/decisions.md:21740-21764` も、AI が書ける批准値は自己承認になると説明している。HEAD 一致は自己整合の確認にすぎず、未改変 CLI を AI が操作する経路を閉じない。批准主体が「人間の reviewed diff」から「TTY を操作した主体」へ変わる。

3. [real] ratify 後、commit 前の candidate 生成が機械的に禁止されていない。  
   計画は source を変更したまま HEAD を不変にする (`stage2-plan.md:53-58,79-83,182-184`)。新 process は worktree の非 `None` pin を import して gate を開けるが、candidate は `git rev-parse HEAD` を記録し (`s8b_holdout_freeze.py:1692-1696`)、generator hash も HEAD blob から作る (`:1731-1746`)。実行中の worktree source との比較はない。closure 比較 (`:1640-1671`) も generator 専用検査ではなく、source は具体的 axis 表現を持たないよう保護されている (`test_s8b_holdout_freeze.py:1578-1594`)。そのまま実装すると、実際は批准済み pin で動いた candidate が、`frozen_at_head` と `generator.sha256` には pin が `None` の HEAD を参照しうる。

4. [real] `approved_at` の発行前検証がプランから欠けている。  
   `stage2-plan.md:31-38` は `--approved-at` を必須にするだけで、canonical UTC seconds の検証を指定しない。loader は `s8b_holdout_freeze.py:1326-1334` で厳密に拒否する。記載どおり budget、approval、pin の順に発行すると、無効 timestamp を含む approval とその hash pin を作った後で loader が拒否する。create-only と「同じ bytes のみ再開可能」により、通常の再批准もできない。成功例で loader が受理すること (`stage2-plan.md:82-83`) だけではこの負例を固定しない。

5. [real] 親 brief は既存 pin 負例を loader 負例として誤分類している。  
   `stage1-brief.md:80-83` は `test_s8b_holdout_freeze.py:1599,1959` を「承認 loader の既存負例」とする。しかし両テストは pin を `None` にし (`:1597-1606,1955-1967`)、`_budget_approval_authority()` が入力より先に拒否する。`_load_budget_approval()` は呼ばれない。REPO 内には同 loader を直接対象にした既存テストも見当たらない。この誤分類を残すと loader の変異を殺した実績として誤計上される。

6. [real] draft raw の loader 負例は受理境界の gate にならない。  
   `stage2-plan.md:73-74,161-164` は draft の正しい hash を loader に渡し、exact key 不一致を期待する。しかし key 検査 `s8b_holdout_freeze.py:1317-1318` だけを無効化しても、draft には `approver`、`approved_at`、`budget` がなく、`:1323-1338` が引き続き拒否する。エラー文一致ならテストは赤になるが、受理集合は広がらない。「draft が authority にならない」ことを一つの支配的検査へ帰属できていない。

7. [real] 承認者 fallback の禁止を個別に帰属できる負例がない。  
   設計文は argv・環境変数・draft を禁止する (`stage2-plan.md:34-35`) が、テスト計画は `--approver` 不在と非 TTY refusal だけである (`:76-77`)。環境変数、Git `user.name`、active v1 の `confirmed_by`、draft sentinel の各 fallback を単独で生かした時に赤になる検査がない。active v1 には実値 `confirmed_by="thawk105"` が存在する (`output/s8b-freeze/holdout_freeze.json:620-626`)。確認入力の別の TTY 拒否に守られるため、単独 fallback 変異の帰属ができない。

8. [要確認] source anchor 負例は fixture の commit 順序次第で HEAD drift に隠れる。  
   `stage2-plan.md:85-86` の anchor 0 件・2 件を worktree だけで作ると、先に source-vs-HEAD 検査 (`:40-41`) が拒否する。各 anchor 変異を fixture の HEAD に commit し、CLI 自身は一致した状態にしなければ anchor 検査の実効性を証明できない。また計画には CLI 自身の HEAD 不一致を対象にした独立負例が明記されていない。

9. [real] 記載された設計は loader の構文上の受理集合を広げないが、意味上の到達集合を広げる。  
   loader は固定 path、raw hash、exact keys、canonical bytes、scope、approver、timestamp、budget を検査する (`s8b_holdout_freeze.py:1307-1339`)。新 CLI の数値・承認者制約はその部分集合であり、loader 自体を変更しない限り構文上の拡大はない。standalone budget も同じ object から canonical 化するため `:1712-1719` と整合する。ただし従来は pin `None` で空だった到達集合が、AI も操作できる PTY 入力全体へ開くため、D1161 が要求する「人間による承認」という意味上の受理集合は保たれない。

## 親 brief の主張の検証

- 「閂は 2 つ」: 限定付きで真。budget approval authority には、固定 approval file と非 `None` pin の両方が必要である。pin は `s8b_holdout_freeze.py:1297-1304`、approval file は `:1307-1315`。ただし candidate 全体には active v1、別 budget、floor result なども必要なので、「candidate の全閂が二つ」という意味なら偽である (`:1688-1724`)。

- 「草案だけでは gate が開かないのは現行実装で既に真」: 真。pin `None` は入力読取り前に拒否される (`:1297-1304`)。さらに loader は固定 path と approval exact schema を要求する (`:1307-1338`)。現行コードには draft という受理形式自体がない。

- 「D964 / D979 は予算数値の択一ではない」: 真。D964 は staged 運搬の適格性と証拠閉包 (`docs/decisions.md:34397-34406`)、D979 は役割横断の campaign 生涯観測上限 (`:34626-34635`) を裁定する。2592/1296 と 2400/1200 は T986 dossier の未裁定択である (`output/insights/2026-08-24_t986-budget-approval-package/README.md:225-238`)。

- 「holdout 集合は rr20 と rr80」: 真。実装定数は `s8b_holdout_freeze.py:100-103`、active v1 の現物は `output/s8b-freeze/holdout_freeze.json:39,307`。builder も active v1 と実装集合の一致を要求する (`s8b_holdout_freeze.py:1703-1707`)。

- 「build_v2_g1_candidate は承認 JSON と別に budget 文書を要求する」: 真。API は `budget_path` を必須とし (`:1688-1690`)、別 file を読み検証した後、approval 内 budget と canonical bytes を比較する (`:1712-1719`)。CLI の `--budget` も必須である (`:1881-1886`)。

## 恒真の疑い

| 提案負例 | 該当検査だけを無効化した時 | 判定 |
|---|---|---|
| 欠落・余分 holdout | `_validate_budget()` の集合検査 `:1281-1283` が同じ入力を拒否する | 実効 gate でない |
| bool、非有限、負数、負のゼロ | `_validate_budget()` の数値検査 `:1273-1291` が拒否する | 実効 gate でない |
| 非 canonical 数値字句 | JSON parser 自体が拒否するケースと、loader が受理するケースが混在する | ケース未指定のため要確認 |
| duplicate holdout | map 化で最後の値が残り、後段の集合検査は通る | duplicate 検査だけが赤になりうる実効 gate |
| draft の approval field 不在 | 一つ追加しても exact schema と残る必須 field が拒否する | draft 契約テストだが authority gate ではない |
| draft raw の exact key 不一致 | key 検査を外しても approver、timestamp、budget 検査が拒否する | 恒真の疑い |
| canonical approval path への draft | generic な「repo 内出力禁止」が先に拒否する | 専用 gate でない |
| symlink leaf | create-only の既存 leaf 拒否でも止まる | no-follow への帰属不能 |
| 既存 leaf | `O_EXCL` 相当の create-only が止める | 個別 precheck への帰属不能 |
| pin が既に別 hash | `None` 用旧 anchor が 0 件となり anchor 検査が止める | pin-state 検査への帰属不能 |
| anchor 0 件・2 件 | 未 commit 変異なら source-vs-HEAD が先に止める | fixture 設計次第 |
| 数値引数の required | required を外しても `None` の parse・validation が後段で失敗しうる | code 2 の契約のみで、批准 gate ではない |
| 非 TTY | TTY 判定を外しても controlling TTY の open/read 失敗で止まりうる | 独立した入力源を与えない限り帰属不能 |
| 確認 hash 不一致 | compare を外せば固定 3 path が変更される | この負例だけが赤になる実効 gate |
| draft 実行時の無変更 | draft から writer を呼ぶ変異なら canonical artifacts/source が変わる | 実効的な副作用 gate |
| 通常の repo 内 `--out` | repo 外制約だけを外せば file が作られる | 実効的な配置 gate |
| source-vs-HEAD drift | 他条件を正例に固定すれば pin 更新へ進む | 実効 gate |
| CLI-vs-HEAD drift | 対応する独立負例が計画にない | 未登録 |

変異帰属上、特に欠落・余分 holdout、各不正数値、draft loader、canonical approval path、symlink、既批准 pin、未 commit anchor は、前後の層が同じ入力を拒否するため「この検査が殺した」とは言えない。

## 総括

- プランは loader の構文上の受理条件を緩めていない。
- しかし TTY は人間と AI を分離せず、D1161 の承認者境界を成立させない。
- fake TTY 正例は、むしろプログラムが承認者を供給できることを実証する設計である。
- ratify CLI と pin の直接更新は D287 の既裁定と正面から衝突する。
- commit 前 candidate 生成では、実行 source と記録される HEAD generator がずれうる。
- `approved_at` の発行前検証がなく、拒否される批准済み部分状態を作りうる。
- 提案負例の多くは後段拒否に守られ、受理集合の変異を単独では殺せない。
- 親 brief の五つの実装上の主張は、二閂の射程を approval sub-gate に限定すれば正しい。
- P1 の直接更新案は、このままでは正しさ境界を通せない。
- pytest は実行しておらず、以上は指定一次資料の静的読解による。