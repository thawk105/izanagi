**job 2 は機構診断の材料として十分です。ただし、D2120 項12が求める比較の全面成立と、試作の runner 受入れは未達です。** 新たな計算ノード再投入を要する probe 障害は見つかりませんでした。

参照略号：`J2/J1`＝各 `receipts/probe-result-{2,1}.json`、`P`＝`probe/t2737_gate_probe.py`、`R`＝runner。`cells[id=…]` は receipt 内の該当 cell を指します。本レビューでは読取・集計のみ実施し、テストは実行していません。

**1. 分類：裁定充足 — real：D2120 の必要比較は未成立**

根拠：`J2.cells` の warm 結果は以下です。軸順は IMPL/KIND/DLR/WFG。

| patch / 登録簿 | S | phase1 |
|---|---|---|
| current/O | O/C/O/O | D/E/A/D |
| current/T− | M/M/M/M | 未実施 |
| revS/O | O/C/O/O | E/E/E/E |
| revS/T+ | M/C/M/M | KIND のみ E |
| revS/T− | M/M/M/M | E/B/E/E |
| abort-unconditional/T− | M/M/M/M | 未実施 |

O＝owner 未解決、C＝configure 失敗、D＝依存閉包 drift、A＝compile command drift、E＝要求値/default の前処理差あり、B＝同一、M＝stock inert 不一致。

target 変更で stock owner 比較まで進み、KIND はさらに companion 除去で configure を通過します。しかし revS/T−/S も全軸 M。`root_diff_line_count=1` が残ります。revS/O/S は stock YCSB 側の障害を閉じていません。

放置時の影響：TPCC の到達段階を YCSB stock 比較の成立と誤認し、採用条件を満たしたように見せます。  
是正案：insight の先頭に **「shadow-T は機構診断であり、D2120 の YCSB 比較は未成立」** を置き、上記の鎖を「到達した層／停止理由」として説明する。

**2. 分類：裁定充足 — refuted：非 inert の対応と KIND 固定 target 対が欠ける**

根拠：`J2.cells[id=current.O.phase1.*.warm / revs.O.phase1.*.warm].supply_canonical_json.evidence` で対応を確認できます。

- IMPL：現行の study header／rwlock の閉包差が revS で消える。無条件 include＋宣言の条件化に対応。
- DLR：現行の `-DDLR0`／`-DDLR1` 差が revS で消える。marker 固定に対応し、数値分岐による前処理差は残る。
- WFG：現行の `ss2pl_wfg.hh` の閉包差が revS で消える。owner の無条件 include に対応。
- KIND：現行から E。修復した drift はない。

`revs.T+.phase1.kind.warm=E` と `revs.T-.phase1.kind.warm=B` も存在し、登録簿生成の差は companion の有無だけです（P:49–58）。

放置時の影響：「4軸すべての drift を修復」と書くと KIND を誤説明します。  
是正案：上の対応を表に載せる。ただし複数変更をまとめた試作なので、各 hunk の独立した必要十分性まで実測したとは書かない。45 cell の追加欠落はありません。

**3. 分類：runner 契約 — real：plain build 成功でも試作を runner がそのまま受理できない**

根拠：

- `J2.static_contracts.revs.abort_ownership.accepted=false`：transaction 増分1／workload 増分2。R:1061 の走査は条件分岐内の復元増分も数えます。
- 無条件除去版の所有権検査は受理されますが、S は4軸とも M。
- `J2.abort_patch_pair.accepted=true` と `applied_pair_only_abort` が、2版の差を abort ブロックに限定。
- 両版の study header 宣言抽出は受理。
- `J2.builds.S.wfg_absence.accepted=true`、検査 TU は3本。S／phase1 の plain build も成功。

放置時の影響：WFG 不在性・build 成功を runner 全体の受入れと混同します。  
是正案：abort 所有権と S 復元の衝突を独立行にする。両版とも M なので「abort 復元だけで S が緑になる」とは書けません。`collect_inert_witness` と stock-lock 不在性は未実走で、宣言一致 flag の false 自体は契約例外ではない、という B3 注記を維持する。

**4. 分類：運用 — refuted：job 2 の warm-up 対・診断・実行予算に欠落がある**

根拠：`J2.attempt` は `attempt-0fe27f4c152b4eed8cdd433215703e03`。`staging_before == warm_up.before`、config.h は不在。helper 完了後は10,448 bytes、SHA256 `e9a4ecd3…1494a`。全37 warm cell の `staging_config` が `warm_up.after` と一致します。clone は P:573–579 で一度作成され、前後対で交換されません。

トップレベルの `staging_after` はありませんが、各 cell の記録で補えています。`staging_original_after == staging_original` も成立。ただしこれは **config.h の状態**の一致であり、staging 全ファイルの不変証明ではありません。

運用記録も揃っています。

- `/tmp` 空き138,581,934,080 bytes、空き inode 104,567,065。
- `c++` は実体 g++-11／11.4.0、CMake は `/usr/bin/cmake`／3.22.1。
- 45 cell 全実施、cell 内部例外0、予算未実施0。
- 各 cell 1.662–5.672秒、計104.475秒。warm-up 13.696秒、build 12.442＋5.437秒、全体143.852秒。dispatch の149秒も40分枠内。
- configure 失敗3 cell の診断は requested/control とも rc=0。control stderr 全文に `CCBENCH_SS2PL_LOCK_IMPL` の未使用変数警告があります。

放置時の影響：rc=0 の configure を成功扱いしたり、config.h の一致を staging 全体へ拡張すると誤読になります。  
是正案：上記の限定で記載。job 2 の再投入は不要です。

**5. 分類：運用 — real：job 1 の「plain build 後16 cell」は20 cell**

根拠：`J1.order` の `plain-build.phase1` 後は、current/O/S、current/T−/S、revS/O/S、revS/O/phase1、revS/T+/S の5組×4軸です。全20 cell が生成済み config.h を観測しています。

job 1 は `warm_up.status=internal-exception`、全体 rc=1。先行する warm 名の17 cell は config.h 不在のままです。job 1／2 の候補 ID はそれぞれ `0:5036.nqsv`／`0:5051.nqsv` で、候補の source にある dispatch ディレクトリも `compute-1.log`／`compute-2.log` の receipt 出力先と対応しています。

放置時の影響：有効な後段証拠を4 cell落とす一方、warm-up 失敗後の前段を正常な warm 対照に混ぜる恐れがあります。  
是正案：「後段20 cell」と訂正し、(iii) の主証拠は job 2 に限定。PBS ID は候補の原記録を保ち、log との対応を別記する。

**6. 分類：F29 — refuted：gate 呼び出し／configure 引数が production と異なる**

根拠：P:298–306 と R:1988–2003 は同じ順序・内容です。Release／sanitizer の重複指定も一致し、4軸 cache は除外、`FETCHCONTENT_BASE_DIR` は渡しません。P:686–701 は同じ request 条件で supply、runtime meaning、family の3呼び出しを行います。

差は次の運用部分です：shadow module／試作 patch、attempt staging の準備、cell ごとの結果保存、family 拒否でも継続、T+ の KIND 単独には family を作らないこと、admission を要求しない診断 build。

なお `J2.families[key=["revs","O","phase1","warm"]]` は **admitted=true** です。全 cell の meaning は未宣言ですが、「全 family が拒否」とは書けません。

放置時の影響：probe 完走・family admission・runtime meaning の成立を取り違えます。  
是正案：一致部分と上記差分を明記し、非 inert の raw-measurement admission 成立を限定して記載する。

**7. 分類：表 — real：「残差は `#line` でしか消えない」は証拠を超える**

根拠：`s6-fix1.md`、README の F1 記録は `ERR` の `__LINE__` 展開値97→154を示し、`J2` の S 比較も残差1行を示します。しかし、他のソース配置変更などを排除した唯一性の証明ではありません。

放置時の影響：未検証の設計選択肢を排除し、裁定を先取りします。  
是正案：**「今回の固定復元範囲では `__LINE__` 残差が残った。`#line` による同期は未実施」** とする。表は「warm-up／非 inert patch／S の target・companion／abort 所有権」を別行にし、成立・未成立・必要な変更層・未検証点・cell を対応させれば採否を先取りしません。

**8. 分類：scope — refuted：現時点で production 実装差分が混入している**

根拠：読取時の tracked／staged diff は空、status は `?? output/insights/2026-09-18/` のみでした。最終 insight と commit 内容自体は今回の射影資料にないため、完成物としての確認は未実施です。

放置時の影響：予定と実際の commit 範囲を混同すると、実装差分0の前提が崩れます。  
是正案：段7は insight docs＋spool fragment に限定。probe／patch の逐語を `.md` に保存する形は妥当ですが、元名・版・SHA256・抽出方法を付け、拡張子変更を provenance 免除の根拠にしないこと。job 1 の旧 probe hash は現行ファイルと異なるため、job 1 の逐語も残すなら旧版を区別して保存する。

## 総括

- **real 4件**：D2120 未充足、runner 所有権拒否、job 1 の件数誤記、`#line` の唯一性断定。
- 最重要は、非 inert の改善を stock YCSB 比較の成立へ拡張しないこと。
- job 2 の45 cell・warm-up 対・診断・時間記録に、再投入を要する欠落はありません。
- 必要なのは材料の記述修正。S 成立を主張するには別の設計・実測が必要です。
- 書けること：3軸 drift 解消、KIND companion 対、config.h 障害解消、診断 build／WFG 不在性成功。
- 書けないこと：D2120 全面充足、S 一致、runner 全体受入れ、runtime correctness、`#line` の唯一性。