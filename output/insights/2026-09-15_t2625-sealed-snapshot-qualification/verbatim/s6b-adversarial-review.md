以下は静的所見です。編集・テスト・ネットワーク取得は行っていません。パスは作業 root 相対、`artifact` は指定の `run-d0f8hq4f/qualification.json` を指します。ローカル man の行番号は展開後のものです。

### 1. sort_best を除外して qualification 完了にする案は採れない

- **主張**: 赤 B を限界として記録することはできるが、sort_best を除外して所定の qualification が成立したとは報告できない。
- **根拠**:
  - `docs/decisions.md:39965–39966` — 「読み取り専用の束縛または同等の実効的な不変 snapshot を計算ノードで実証するまで、正式な受入を成立させない。」
  - 同 `:39977` — 「**閉じないことを正式に受理する**」は却下。
  - 同 `:45559–45560` — 「実 CMake の qualification は毎回の受入から外し、計算ノードでの一度きりの artifact とする。」
  - `orchestrator/manual_probes/t1994_readonly_snapshot_qualification.py:42` — `"Only one freeze entry each for stock_common and sort_best is qualified."`
  - `artifact:694` — `"session_commands": []`、`:793` — `"non-writable snapshot src_token differs from prepared result"`。
  - D1439 単独は configuration 名を列挙していない。しかし driver が明示する両 configuration の射程と、sort_best の実 session 未到達を合わせれば、除外後の完了扱いは成立しない。
- **成果物への影響**: sort_best の実証がゼロのまま、両 configuration を検証済みとするレポートになる。
- **自己申告**: **real、確信度 高**。
- **区分**: **must-fix** ― この除外案を採用しないこと。

### 2. B1 の token 一致は contract id 自体の正当性を独立には保証しない

- **主張**: B1 後の一致は「同じ contract id の下で source identity が一致する」ことを検査し、contract id の選択が正しいことの再検証にはならない。
- **根拠**:
  - `orchestrator/campaign/source_digest.py:2236–2237` — contract／grammar 束縛なしでは `"return raw_digest"`。
  - 同 `:2267–2273` — preimage は `"sort-src-token/v1\0contract="`、contract id、`"\0source="`、`raw_digest` の連結を SHA-256 にする。
  - 同 `:2285–2286` — `"if current == baseline_digest: return STOCK"`。stock 分岐では contract id は token に入らない。これは既存仕様。
  - `orchestrator/campaign/s1_direct_comparison.py:916` — `"sort_oracle_contract_id = oracle.contract_id"`。
  - driver `:639–647` — `prepared.sort_oracle_contract_id` を `extra` に入れ、evidence 導出と build 引数の双方へ渡す。B1 はこの同じ値を再導出にも渡す変更になる。
  - **同じ誤った id を両側へ渡せば、その誤りだけでは不一致にならない。** ただし準備側には既に `s1_direct_comparison.py:903–904` の `"oracle.contract_id != ORACLE_CONTRACT_ID"` による拒否と、`:914–915` の PASS 要求がある。
  - `source_digest.py:2410–2416` は `current = compute(...)` を実行してから token を作る。`s8b_expected_materialization.py:918` の `"if evidence.src_token != prepared_src_token"` は独立に計算した内容側を比較する。
- **成果物への影響**: token 一致を「oracle 契約の独立再検証」と記載すると保証を過大評価するが、同じ id を使うだけで内容照合が恒真になるわけではない。
- **自己申告**: **real〔保証の限界〕／refuted〔B1 が内容差を隠すという攻撃〕、確信度 高**。
- **区分**: **must-fix〔保証の記述〕**。新たな gate の追加は要求しない。

補足すると、contract id は内容 digest を**置換せず追加**する。異なる内容 digest を一致させるには、通常の SHA-256 衝突耐性の前提を破る必要がある。また、token 自体は全ファイルの生 bytes 一致を保証するものではない。全 tree は `s8b_expected_materialization.py:884–892` の宣言再生成・照合、full evidence は `buildcache.py:3358` の `"if admitted.source_evidence != source_evidence"` が別に検査している。これらを残す限り、B1 によって失われる既存の内容保証は見つからなかった。

### 3. A1 の「chmod の EROFS は mount-ro だけで説明できる」は強すぎる

- **主張**: EROFS 単独は mount 属性の一意な証明ではないが、今回の連言を mode bits だけで通す反例は構成できなかった。
- **根拠**:
  - driver `:260` — `"target.chmod(0o600)"`、`:264` — `"code = write_errno(target)"`。chmod が成功すれば、続く書込みは変更後の mode で試される。
  - ローカル `/usr/share/man/man2/chmod.2.gz:162–165` — `"The effective UID of the calling process must match the owner of the file"`。**0444 自体は所有者の chmod を禁止しない**。ただし祖先の検索権限、immutable、filesystem 等の制約がない場合の話であり、「常に成功」は誤り。
  - 同 `:292–298` — immutable／append-only は `"EPERM"`、read-only filesystem は `"EROFS"`。
  - `orchestrator/campaign/s8b_expected_materialization.py:1066–1075` — 既存 seccomp は EPERM／ENOSYS を返し、最後は ALLOW。chmod を EROFS に置換する規則はない。
  - `artifact:571` — source 行は `"ro,relatime - tmpfs tmpfs rw,..."`。mount 側は ro、superblock 側は rw である。
  - driver `:719–721` — source mount 行を必須とし、各行の mount options に ro、filesystem に tmpfs を要求する。
- **成果物への影響**: A1 は EACCES の観測を新たに受理するが、「任意の環境で EROFS だけから mount-ro を証明した」と一般化すると証拠の射程を超える。
- **自己申告**: **real〔説明の過大さ〕／refuted〔現行の mode bits だけで全条件が緑になる〕、確信度 高**。
- **区分**: **nit〔説明の限定〕**。

原因別の整理は次のとおりです。

| 原因 | 評価 |
|---|---|
| file が 0444 | それだけでは所有者の chmod を拒否しない |
| immutable／append-only | 通常は EPERM。EROFS の代替説明にならない |
| superblock が ro | EROFS の原因になり得る。今回の mountinfo は superblock rw |
| seccomp | 一般には任意 errno を返せる。ただし現行 filter は chmod に EROFS を返さない |
| LSM | **推測**: hook の実装によって EROFS を返す余地はある。今回の LSM 実装は確認していない |

mount-ro を外した通常の所有者・tmpfs では、chmod が成功して `chmod_errno == EROFS` が落ちる。chmod だけを別機構で EROFS にしても、実際の source mount が rw なら mountinfo 条件が落ちる。**観測値の偽造などを持ち込まず、現行経路で全条件を満たす反例は得られていない。**

### 4. directory も非 writable だが、新規作成時の errno を既存 file の open から推定してはいけない

- **主張**: directory の write bits も落ちているが、「新規作成でも必ず DAC が先」とは結論できず、write による直接 witness の追加候補はある。
- **根拠**:
  - `s8b_expected_materialization.py:488–489` — `"if stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)"` を対象に追加。
  - 同 `:496–497` は root、`:587` は parent も追加し、`:596` の `"mode & ~0o222"` を適用する。したがって 0755 directory は 0555 になる。
  - driver `:160` は `"os.open(path, os.O_WRONLY)"`。**現在の観測は既存 file の open であり、新規作成の観測ではない。**
  - ローカル `/usr/share/man/man2/open.2.gz:798–814` は `O_TMPFILE` を `"Create an unnamed temporary regular file"` と定義し、directory を指定して `O_RDWR`／`O_WRONLY` と併用する。
- **成果物への影響**: 操作ごとの拒否順序を混同すると、追加した観測でも意図した mount-ro の証拠が得られない。
- **自己申告**: **real〔directory を含む〕、確信度 高／直接 witness 案は推測、確信度 中**。
- **区分**: **nit**。

**強い追加観測の候補**は、同じ source root に対する `open(root, O_TMPFILE | O_RDWR, 0600)` の EROFS 要求である。Linux の `do_tmpfile` が mount の write access を directory の書込み権限検査より先に取得する経路なら、0555 の DAC に遮られず mount-ro を観測できる。通常の名前付き新規作成も既存 file の open とは経路が異なり、0555 だけから EACCES 優先とは言えない。

**この kernel 順序は推測として留保する。** ローカルには対象 kernel の headers はあったが `fs/namei.c` 本体はなく、今回ネットワーク取得・実走は禁止されているため、5.15.0-173 で確認済みとは報告しない。

なお、**現在赤である同じ `write_errno == EROFS` を据え置いたまま、条件を追加するだけで緑にする方法は無い**。上の案は A1 に直接 witness を追加する候補であり、現行の赤い連言を追加だけで修復する案ではない。

### 5. 禁止する直し方には、比較対象のすり替えと後段保証の省略も含める必要がある

- **主張**: errno 条件や token 比較を表面上残したまま、比較入力や後段の検査を変えて赤を消す修正も弱体化になる。
- **根拠**:
  - driver `:257–264` は **source 内の `CMakeLists.txt`** を実際に chmod／write し、`:268` は root と一致する mountpoint を選ぶ。別の ro mount に観測対象を替える、errno を期待値へ変換する、mount 行を別 path から拾う修正は、この対応を壊す。
  - `s8b_expected_materialization.py:902–918` は再計算後に準備 token と比較する。再計算値で `prepared_src_token` を上書きする、準備 evidence をそのまま返す、mismatch 時だけ unbound token に fallback する修正は、内容差を拒否する性質を失わせる。
  - `buildcache.py:3358` は full `SourceEvidence` 比較。token だけ合ったことを理由にこれを外すのも別の弱体化。
  - `s1_direct_comparison.py:903–915` は contract id 一致と oracle PASS を要求する。両側へ同じ id が届くことを理由に、この準備側検査を省いてはいけない。
  - driver `:796–798` は `"status"] == 'blocked'` と `"sealed_seen and build_finished"` を要求する。単なる build 失敗や session 開始を代入してはいけない。
- **成果物への影響**: 検査の名前や比較式を残しながら、誤った材料・未実行の攻撃・未完了 build を受理できるようになる。
- **自己申告**: **real〔禁止対象の漏れ〕、確信度 高**。現行実装がこれらを行っているという指摘ではない。
- **区分**: **must-fix〔修正案の選別〕**。

### 6. `attack_executed_and_blocked` の赤は今回 `:seal` に従属している

- **主張**: stock 2 件について、独立した攻撃機構の欠陥を示す artifact ではなく、seal 拒否による未実行を示している。
- **根拠**:
  - `artifact:549–551` と `:913–915` — `"status": "not-started"`、source／ancestor の rename は false。
  - `artifact:618` と `:982` — build exception の原因はそれぞれ `stock_common:aba:seal`、`stock_common:persistent:seal`。
  - driver `:716–721` の seal require は失敗時に例外となる（`:63–66`）。
  - 攻撃開始はその後の `:735–736` — `"if is_build and attack_mode != 'none' and not mutated: mutate()"`。
  - 捕捉後の `:796–797` が未開始状態に対して blocked を要求し、二つ目の赤を記録する。
- **成果物への影響**: 二重の赤を独立欠陥と数えると原因数を誤る一方、従属だからと攻撃 check を外すと未実行でも受理できてしまう。
- **自己申告**: **refuted〔独立欠陥〕、確信度 高**。
- **区分**: **nit〔原因の分類〕**。A1 後に攻撃が成功裏に検証されることは、まだ未実証。

## 総括

**A1・B1 が現行の信頼境界内で内容不正を新たに受理する具体的経路は、今回の静的検査では見つからなかった。** ただし、EROFS を mount-ro の一意な証明とする説明と、token 一致を contract id の独立検証とする説明は成立しない。

sort_best の除外による完了扱いは不可。stock の攻撃赤は seal の従属だが、攻撃の成立自体は未検証である。直接 write witness の候補は示したものの、kernel の拒否順序と修正後の qualification は親の実走で確認する必要がある。