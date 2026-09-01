## 所見

静的検査のみを行い、pytest は実行していない。

## 正しさ境界に関わる所見

### 1. D1050 の「1 本」を driver ごとの 3 path とする解釈は未裁定

- 実測した file:line: `rulings-verbatim.md:3-13,88-93`、`s2-plan.md:31-57`、`p3_b4_admission_record.py:226-255,760-775`
- なぜ問題か: D1050 の逐語は無限定に「置き場所を 1 本」としており、案 A は repository 全体では 3 path を正とする。一方、§10 の「driver ごとに発行する」と、現 schema が projection を単一値しか持たないことは、親の「固定 driver について 1 本」という解釈を支持する。どちらを優先するかは逐語資料だけでは断定できない。特に direct API では caller が `driver_kind` を変えれば 3 path 全てを受理対象として検証できる。
- 成果物への影響: **global 1 path か driver ごと 1 path かを親の裁定へ戻すまで、案 A の定数を正本として実装しない。**

文言に忠実な global 1 file 案では、次の変更が必要になる。

- canonical path は driver 非依存の単一定数にする。
- 現在の schema は projection 期待値を単一 `str` として厳密検査するため、3 driver の値を持つ exact mapping または 3 固定 key へ変え、schema version を上げる。
- record の 3 値全てを §5 の 3 値および live closure と照合し、実走 driver の receipt には該当値だけを束縛する。
- record hash は全 driver で共通になる反面、1 driver の closure 変更でも共有 record の再発行が必要になる。これは結合度を上げるが、同時に存在する正本を本当に 1 file にできる。

### 2. canonical path 固定が閉じるのは、同一時点の空間的選択だけ

- 実測した file:line: `p3_b4_admission_record.py:699-712,719-758`、`p3_b4_launcher.py:346-367,405-433,516-609`、`s2-plan.md:101-110,182-187`
- なぜ問題か: verifier は検証時点の `HEAD` blob と worktree bytes の一致を要求するだけで、過去に受理された record hash の不変な pin は持たない。運用者は canonical file を別の valid record に書き換えて新しい `HEAD` を commit し、別 invocation で再受理させられる。continuation は最終 pair 検査までは再検証するが、`assert_b4_certified_arm_pair` 後の ready-signal 待ちから driver 起動までには再検証しない。ただし context と receipt は旧 record の hash/commit に束縛されたままなので、現行 pair が新 record にすり替わるわけではない。
- 成果物への影響: **「複数 path からの同時選択は閉じるが、commit をまたぐ record の差し替えと事後再発行は閉じない」と明記する。**

### 3. 経路ごとの閉包は次の通り

|経路|閉じるもの|閉じないもの|
|---|---|---|
|production factory (`p3_b4_closed_critic.py:1226-1286`)|固定 driver の非 canonical path。launch context と再検証結果の相違も拒否する|別 commit での canonical record 再発行、same-process 改変|
|test factory (`:1360-1414`)|production certification への昇格はしない|admission verifier 自体を一切通らず、結果を先に知ることは可能|
|generic pair 検査 (`:1889-1896`)|同一 evidence class の構造検査|`test-only` pair も検査可能。ただし certified とはしない|
|certified pair 検査 (`:1899-1981`)|factory 時の verified record と最終時点の record の相違|検査完了後の canonical file 差し替え|
|bootstrap (`p3_b4_launcher.py:516-556`)|driver を触る前の 1 回の canonical 検査|context 発行後の file 変更。起動は発行時の旧 hash/commit に束縛されたまま|
|continuation (`:558-609`)|context 発行、factory、最終 pair の各段で非 canonical path を拒否|最終検査後の差し替え、別 invocation での再 commit|
|CLI (`:632-658`)|`--admission-record` に別 path を指定しても中央 verifier が拒否|`--driver` によって 3 canonical path のどれを使うかは運用者が選べる|
|direct verifier API (`p3_b4_admission_record.py:671-797`)|指定 driver に対する非 canonical path|driver を変えた 3 record の個別検証、production 外での結果利用|

- 実測した file:line: 上表の各位置、および certified sink の `p3_b4_closed_critic.py:1764-1777`
- なぜ問題か: test factory の receipt は `require_b4_closed_critic_receipt` が `test-only` として拒否するため、通常 API 上の production bypass ではない。しかし「record commit 前に別経路で結果を知る」穴は明確に残る。
- 成果物への影響: **production-certified 経路だけを閉包対象とし、test-only と direct API による事前知得は非保証として残す。**

### 4. 受理集合は狭まる方向にしか変わらない

- 実測した file:line: `p3_b4_admission_record.py:678-775`、`s2-plan.md:76-99,176-180`
- なぜ問題か: 提案は `_repository_relative_regular_file` 後に新しい必要条件を conjunction として加えるだけで、既存の比較・分岐を削除しない。repo 外、missing、directory、`.git`、symlink は `:415-442` で従来どおり先に拒否される。非 canonical な既存拒否入力は失敗理由が早まる場合があるが、受理への反転はない。
- 成果物への影響: **変更前に拒否され変更後に受理される具体的入力は、提示された実装差分からは構成できない。**

## 整合・実効性に関わる所見

### 5. 新関門は発火可能で、既存検査による恒真化はない

- 実測した file:line: `p3_b4_admission_record.py:415-442,690-775`、`s2-plan.md:76-100,161-172`
- なぜ問題か: resolver は repository 内の regular file かだけを検査し、path 名の固定は行わない。提案 fixture のように、正しい canonical record と完全に同じ bytes を `admission.json` に置き、両方を同じ `HEAD` に commit すれば、非 canonical file は resolver、HEAD blob、schema、document binding、projection の全検査を通る。新しい比較を無効化した場合にだけ verifier が正常 return するため、負例が失敗する理由を path 関門 1 個に絞れる。
- 成果物への影響: **関門位置と「同一 HEAD・同一 bytes」の fixture は技術的に妥当であり、resolver 攻撃入力をこの関門の証明に流用しない。**

### 6. 変異の帰属は、変異点を branch の no-op に固定した場合だけ明瞭

- 実測した file:line: `s2-plan.md:155-174`
- なぜ問題か: `raise` を通らないようにするだけの変異なら、canonical 正例と全後続検査は変わらず、非 canonical の exact-error 期待だけが失敗する。一方、mapping 自体を `admission.json` へ変える変異では、同じテスト内の「production mapping と期待 mapping の一致」が先に失敗し、関門の実効性へ到達しない。
- 成果物への影響: **mapping literal 検査と enforcement 検査を分離し、変異は mapping を残したまま conditional raise だけを no-op にする。**

enforcement fixture は、各 driver について次の形にすれば単一理由になる。

1. 独立 literal で決めた選択先に valid record を commit する。
2. 同一 bytes を非選択 path にも同じ `HEAD` で commit する。
3. 選択先が成功することを確認する。
4. 非選択 path が exact path-mismatch だけで拒否されることを確認する。
5. このテスト内では production mapping との equality assertion を行わない。

### 7. 命名は D1000 の禁止語を直接使ってはいないが、未裁定の正本性を先取りする

- 実測した file:line: `s2-plan.md:39-72,101-110,155-170`、`rulings-verbatim.md:31-56`
- なぜ問題か: 「正当」「§6 を充足」「内容を検証済み」という直接の過剰主張はない。しかし、`B4_CANONICAL_ADMISSION_RECORD_REPOSITORY_PATH_BY_DRIVER`、`_RECORD_CANONICAL_REPOSITORY_PATH_CONTRACT_FAILED`、文言の `canonical path` と `contract` は、まだ文書またはユーザー裁定で確立していない path を規範的正本と呼ぶ。テスト名の `accepts_driver_canonical_path` も、path 一致が受理の十分条件であるように読める。提案 docstring は内容・差し替え・Git 外時系列の非保証を明記している点は適切だが、「code mapping が事前登録された正本であることは証明しない」「driver をまたいで global 1 path であることは証明しない」が欠ける。
- 成果物への影響: **裁定前は `REQUIRED...PATH_BY_DRIVER`、`_RECORD_REPOSITORY_PATH_MISMATCH`、`path selected for driver_kind` など機械的比較だけを示す語へ縮める。**

## 親 brief への所見

### D1332 による残り 9 欄の scope 外化

- 実測した file:line: `rulings-verbatim.md:15-29,31-56`、`s1-brief.md:15-20`
- なぜ問題か: D1332 の主題は、依頼の「§5 残り 9 欄の型検査」と一致しており、D1000 も残り 9 欄の型・意味・artifact 実在を検査しないと明記する。したがって、再訪条件が成立していない限り scope 外とする判断は正しい。ただし「D1060 により未記入で、実際の型誤りが 0 件」という根拠は射影資料内では親 brief の主張しかなく、独立確認できない。
- 成果物への影響: **9 欄検査は scope 外のままでよいが、再訪条件未成立の根拠は親側で現物確認を補う。**

`rulings-verbatim.md:1` は `docs/decisions.md` からの抜粋だと述べるが、`docs/decisions.md` 自体は必読事項の射影に含まれていない。この単独段では現物との逐語一致を追加確認できなかった。

### (P1-b) 実装側が canonical path を先に決めること

- 実測した file:line: `rulings-verbatim.md:46-50,81-86`、`s1-brief.md:83-85`、`s2-plan.md:19-57`
- なぜ問題か: D1050 が決めたのは置き場所の本数であり、`docs/...base.json` などの literal path ではない。起票時の T-1847 は固定 path を「文書側の規約」と明記している。実装が先に path を定数化し、後から事前登録文書をそれへ合わせるなら、D1000 が警戒する「実装が事前登録内容を支配する」構造と同型である。「待つか、D1050 を実装しないか」の二択ではなく、先に人間が path を文書または裁定で固定してから gate を実装できる。
- 成果物への影響: **P1-b は是認できず、literal path の選定を人間の裁定または先行する文書固定へ戻す。**

### (P1-d) repo に record file が存在しないという主張

- 実測した file:line: `s1-brief.md:88-89`、`s2-plan.md:23-29`、`p3_b4_closed_critic.py:1306-1310`、`p3_b4_launcher.py:405-433`
- なぜ問題か: 射影された production code が書くのは admission sidecar と launch sidecar だけで、canonical admission record producer は見当たらない。ただし、repo 全体の tracked file 一覧や schema 検索は射影されていない。`s2-plan.md` の `tracked=no`、`exists=no` はプラン作成者の報告であり、この consult の独立実測ではない。
- 成果物への影響: **P1-d は「射影コード内に producer なし」までは確認済みだが、「repo 全体で 0 件」は未確認として扱う。**

### (P1-c) verifier 1 箇所への集約

- 実測した file:line: `p3_b4_closed_critic.py:1268-1286,1931-1940`、`p3_b4_launcher.py:346-359,516-609,632-658`
- なぜ問題か: 通常の production factory、certified pair、bootstrap、continuation、CLI は全て `verify_b4_admission_record` へ収束する。test factory だけは意図的に外れるが、production-certified へ昇格できない。
- 成果物への影響: **通常 production 経路について二重 gate は不要で、中央 chokepoint 1 箇所で足りる。**

## 総括

- 最大の問題は、D1050 の global 1 path と per-driver 3 path のどちらが正本か未裁定なことである。
- 技術面では、新関門は現実に発火し、同一 HEAD・同一 bytes の fixture で単独の拒否理由にできる。
- この変更は受理集合を広げないが、commit をまたぐ canonical record の差し替えや test-only の事前知得は閉じない。
- P1-b の実装先行は D1000 の信頼境界に触れるため、literal path は人間側で先に固定すべきである。
- **以上 2 点の裁定前には実装へ進めず、裁定後は提示された chokepoint と fixture 方針で進めてよい。**