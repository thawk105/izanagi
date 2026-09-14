## 実測 1 の解釈

**実測は成立したが、T-2519／T-2505 を両方完了扱いにはできない。** 確定したのは、束縛 commit `3b80b5a…` の無改変 t316 が `bnode040` で条件関門に入り、supply の `red/configure-failed` で拒否されたことまでである。[measurement-1.md:15–36,59–87](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/measurement-1.md:59)

以下、コードの行参照には次の略記を使う。

- **G** = [orchestrator/campaign/condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert/orchestrator/campaign/condition_meaning_gate.py)
- **P** = [tools/pegasus/probes/t316_sandbox_backend_probe.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert/tools/pegasus/probes/t316_sandbox_backend_probe.py)
- **B** = [tools/pegasus/probes/t316_sandbox_backend_probe.pbs](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert/tools/pegasus/probes/t316_sandbox_backend_probe.pbs)

| 対象 | 確定したこと | 完了判定 |
|---|---|---|
| T-2519 | 今回の t316・`BACKOFF_FIXED=-1`・環境では緑に到達しなかった。 | **先行観測として有効。ただし実質的な到達性判定は未完。** inert 比較前の障害なので、stock 同等性の否定にはならない。 |
| T-2505 | 名指された driver の実経路で、条件関門まで実行できた。 | **未完。** 台帳が求める `stock-inert-preprocess-root-location-only` の緑に到達した環境は得られていない。原因を特定するだけでも完了にはならない。 |

T-2519 の「到達する**か**」は、結果を緑に限定していない。一方、D1936 項17も台帳も「理由不明の configure 停止を一度観測すれば完了」とは書いていない。今回を有効な赤の観測として残しつつ、少なくとも configure 障害を弁別し、inert 比較の結果と区別すべきである。これは原因究明の明文義務ではなく、依頼された問いに答えるための判定である。[D1936:18–22](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/verbatim-d1936-item17.md:18)、[台帳:15–26](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/verbatim-tasks.md:15)

また、D1856 の解除条件は「patch stack 適用木での inert 緑」と「13 macro の runtime witness」の両方であり、今回どちらも満たしていない。[D1856:3–9](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/verbatim-d1856.md:3)

**brief 自身の完了条件も未達である。** brief:17–18 は receipt の supply entry と `comparison` の記録を要求する。しかし P:1967–1972 で例外になり、P:1922–1924 の summary 生成へ戻らず、P:2568–2569 が S6 を blocked observation に置換する。今回は例外文に reason code が残っただけで、`comparison` の観測値も supply entry も残っていない。[s1-brief.md:17](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/s1-brief.md:17)

## configure-failed の原因候補

発行経路は、G:1927–1940 で失敗を保持し、G:1967–1975 で再送出、G:2597–2605 で赤 supply record にする。**reason code だけから CMake の終了コードは決まらない。**

| 発生点 | 原因候補の全区分 | 今回の実引数での扱い |
|---|---|---|
| G:1876、1977 → G:1626–1638 | 実行名不正、PATH 探索失敗、パス解決／stat 失敗、非通常ファイル、実行権限なし | 不正名・PATH 探索失敗は除外。パス／権限の途中変化は残る。 |
| G:1712 → G:1498–1539 | configure 前の CMake を開けない、通常ファイルでない、実行不可、読取失敗、消失、読取中の identity／size 変化 | requested／stock のいずれでも起こりうる。ただし同じ CMake による依存 build 済みなので後順位。 |
| G:1713–1714 → G:1604–1609 | CMake subprocess の起動失敗 | 起こりうる。実行ファイルや実行環境の障害を含む。 |
| 同 → G:1610–1616 | CMake が非ゼロ終了 | 起こりうる。依存探索・compiler check・CMake 記述／互換性・FetchContent・書込先等の失敗、signal 終了を含む。 |
| 同 → G:1617–1622 | **CMake が rc=0 でも stderr が非空** | **起こりうる。最優先の弁別対象。** 未使用 `-D`、policy／deprecation 等の警告もこの経路で赤になる。 |
| G:3164、および同関数内からの configure | compile-time branch meaning の CMake 解決／configure 失敗 | 今回の supply 赤の原因ではない。meaning は `declaration=None`。 |

requested configure が先、stock configure が後である（G:1889–1898）。したがって、同じ reason code でも**どちらで停止したか未確定**。さらに G:1977 は両 configure 成功後の再解決なので、ここで落ちた可能性も reason code 単体では排除できない。

今回、除外できるものと残るものの根拠は次のとおり。

- **不正実行名・PATH 探索失敗は除外**：P:1841 は解決済み絶対パスを `str` で渡す。G:1629 の `shutil.which` 分岐に入らない。最初から CMake が利用不能なら、P:1843–1848 の依存 build と P:1883–1886 の停止条件により関門へ来ない。ただし、その後の消失・権限変化までは否定できない。
- **`-S/-B` の混入、要求 flag の二重供給は除外**：P:1850–1864、1892 の `configure[5:]` は先頭の source/build 指定を除く。P:1944–1947 が要求 flag を除き、G:1664–1675 が requested 側だけに再追加する。
- **stock 不在・同一 root は今回の経路では除外**：P:1887–1888 が別 root へ `copytree` し、G:828–838 が解決・別 root を確認する。失敗した場合も `input-capture-failed` または `stock-tree-unavailable` であり、今回の理由コードではない。
- **コピーだから configure も同じ結果、とはいえない**：requested 側には `-DCCBENCH_BACKOFF_FIXED=-1` があり、stock 側にはない。source/build のパスも異なる（G:1865–1897）。P:1888 は symlink を保存するため、コピーだけで参照先や位置依存挙動まで同一とは保証しない。
- **依存 build 未実施は除外、CCBench からの探索失敗は残る**：関門到達は gflags/glog の configure/build/install が rc=0 で終了した後（P:1842–1848、1873–1886）。それでも `CMAKE_PREFIX_PATH` 等による発見・利用の成功までは証明しない。
- **警告原因は未確定**：P:1852–1864 の `-D` 群をほぼそのまま渡すので、未使用変数等の stderr は候補になる。しかし、指定資料だけではどの変数が未使用かまでは断定できない。
- **timeout、configure 後の identity drift、compile database 不備、前処理差は今回の理由ではない**：順に G:1598–1603／1714、1498–1499／1716–1717、1722–1728、2663–2704 が別理由コードを出す。`stock-inert-mismatch` もまだ観測していない。

なお、射影の `_run_configure` 相当の現行関数名は **`_configure_compile_commands`（G:1683）** である。

## 弁別手段と順序

**最優先は既存 CLI による診断であり、実装面の変更は現時点で不要。** G:4210–4212 は supply の `canonical_json()` を出力するため、P の receipt が捨てた `evidence.detail` を既存機構だけで得られる。これは t316 receipt への evidence 追加ではない。

| 順序 | 場所 | 手段と分かること |
|---|---|---|
| 1 | login node | 上記の静的除外と既存記録の確認。追加 job は不要。今回の退避 stdout/stderr に原因がないことは measurement-1:83–85 で確認済みなので、同じ探索を反復しない。 |
| 2 | 計算ノード job | 同じ pin、source と stock コピー、依存 prefix、CMake/C++、filtered configure args を再現し、**既存 CLI をそのまま実行**。`detail` で「実行／identity 障害」「非ゼロ終了」「成功＋stderr」を一度に弁別する。 |
| 3 | 同じ job | detail にある失敗 argv の requested／stock を確認。末尾500 bytesでは不足する場合、同じ CMake configure を診断用 build root で直接実行し、stdout/stderr 全文と rc を保存する。これは診断であり、gate の緑の代用にはしない。 |
| 4 | 原因判明後 | 原因に必要な環境修正等だけを行い、束縛した **t316 実経路**を再実測。CLI の成功だけで T-2505 を閉じない。 |

CLI の指定は G:4160–4174 に従い、`--macro BACKOFF_FIXED --requested-value=-1 --stock-comparison`、同じ driver ID、`--source-root`／`--stock-root`／`--cxx`／`--cmake` を使う。default と meaning case は指定せず、configure args は `--configure-arg=-D…` として全件保持する。CLI の meaning declaration 選択は P と実装が異なるが、原因弁別対象の supply 呼出しは同じである（G:4177–4203）。

依存を備えない login node で configure を試しても、既知の gflags 不在を再観測するだけになりうる。[T-2213 README:76–94](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert/output/insights/2026-09-09/t2213-probe-condition-gate/README.md:76)

実測1は probe 内26.3秒、PBS記録32秒だったが、次走時間の保証ではない。**同じ job 内で依存 install を共有し、CLI と必要な追加 configure を続ける**方が、原因候補ごとに full probe を投入するより安い。前回の一時物は G:1868 の context と P:2630 の cleanup 対象なので、残存を前提にしない。

## 実装面の最小変更 (要る場合)

**まず変更なしで診断する。** CLI で再現せず、t316 の失敗したその場の detail が不可欠になった場合だけ、次を最小案とする。

P:1967–1972 の admission 拒否分岐で、既存の `supply.evidence.get("detail")` を **job stderr に一行出力してから、現行どおり例外を投げる**。受領証に入る例外メッセージへ追記せず、evidence mapping 全体も出さない。

これなら次を維持できる。

- receipt summary と schema は変更なし（P:320–354）。[D1849:3–7](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/verbatim-d1849.md:3)の「mapping 自体は受領証へ出さない」に従う。
- 二契約の exact 受理集合と検証は変更なし（P:124–133、374–386）。[D1625:3–9](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/verbatim-d1625.md:3)を緩めない。
- G:1617 の stderr 判定、family admission、configure args は変更なし。警告抑制や赤の受理によって緑を作らない。

P は B:54–60 の `BOUND_PATHS` 対象である。変更した場合、親が commit を作成し、**新 commit と clean な束縛対象で次走を投入する必要がある**（B:47–49、61–81）。実測1とは別の実装 identity の観測になる。G や B 自体を変更しても同じである。

本段では変更・テスト実走を行っていない。

## (P1-1) (P1-2) の判定

**P1-1：断定としては崩れる。測定対象の選択としては妥当。**

D1936 項17は「既存機構」を t316／`BACKOFF_FIXED` と名指していない。T-2519 はもともと backoff 系13 macro の意味検証の裁定であり、t316 を唯一の指示対象とする根拠はない。一方、既存 t316 を先行観測に使うことは裁定と整合する。[台帳:6–16](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/verbatim-tasks.md:6)

読み替えは、**「t316 を既存機構の先行測定例として選ぶ。同じ一走で新契約の緑を実際に観測できれば、T-2505 の要求と T-2519 の限定された先行観測を兼ねられる」**。今回のような configure 赤で両方満了、または旧契約の緑だけで T-2505 満了、とはいえない。

T-2518 が別に維持される点は一次資料に明記されており、支持できる。ただし別項であることは、T-2519 の「既存機構＝t316」を論理的には導かない。[D1936:20–22](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/verbatim-d1936-item17.md:20)

**P1-2：関門到達と赤の観測までは検証済み。それ以後は未検証。**

検証済みなのは、指定 commit・当該ノードで無改変のまま S6 の **outside 側**条件関門に入り、supply／meaning／admission を評価したこと。P:2043–2051 では outside が先なので、今回は inside 側 build へ進んでいない。

未検証なのは、両 configure の完遂、inert 前処理比較、新旧いずれかの緑、summary の永続化、CCBench build、S7 性能測定である。「実装面ゼロで赤の観測が得られる」は成立したが、**「実装面ゼロで台帳の完了条件まで達する」は未成立**。また、証明対象は記録された commit と一 allocation であり、将来の main や全計算ノードには拡張できない。

## 総括

実測1を「outside 条件関門到達・configure 赤・inert 比較未到達」と記録し、両タスクの完了へ格上げしない。  
次は実装無変更の既存 CLI を同等環境の計算ノード job で走らせ、まず `evidence.detail` を取得する。  
原因に必要な対処だけを行い、T-2505 は束縛した t316 実経路で新契約の緑を観測して判定する。