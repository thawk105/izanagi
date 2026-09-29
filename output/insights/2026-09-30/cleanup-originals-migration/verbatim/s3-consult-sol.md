## 総括

A・B の対象木は、**T-2871 の WAL 2 本だけを回収してから撤去**し、ほかは回収せず撤去する。稼働中として残すと判定した対象はない。ただし撤去直前の占有確認で稼働が判明した木は、その時点で対象から外す。  
B-5 の発効 commit は tag と bundle で到達性を保ち、元 branch は消す。D2242 の branch 保存指定は、D2243 の後続裁定を根拠に新しい D で改めてから消す。  
新しい tar 退避を全木に作る P6 は採らない。branch の bundle 退避と、価値を示せた WAL の照合付き回収は行う。

## 系列ごとの決定

| 系列 | 決定 | 根拠の一次資料 file:line |
|---|---|---|
| A T-1505 A-1 sized | 回収せず消す | 公開 leaf は複製済み。撤去を別途の掃除判断に委ねている。[README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/output/insights/2026-09-18/t1505-a1-sized-attempt1/README.md:8)、同 :84 |
| A T-2489 A-2 nodes5 | 回収せず消す | branch の差分は policy 1 行の使い捨て commit。[README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/output/insights/2026-09-18/t2489-a2-nodes5-probe/README.md:11) |
| A T-2792 A-1 attempt2 | 回収せず消す | 公開 leaf 4 file を byte 保持で複製済み。[README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/output/insights/2026-09-20/t2792-a1-sized-attempt2/README.md:16) |
| A T-2795 K2 pair・pair2・r4 | 回収せず消す | campaign 原本 3 組は既存 archive に照合済みの写しがある。[再現資料](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/output/insights/2026-09-23/t2853-repro-package-archive/README.md:68)。結果稿の原本 path は撤去後に古くなるため、所在注記が必要。[結果稿](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/docs/paper-story/results/2026-09-23-k2-manual-loop-four-rounds.md:174) |
| A T-2797 B-5 試走 | 回収せず消す | campaign 53 本を既存 archive に照合済みで写した。[再現資料](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/output/insights/2026-09-23/t2853-repro-package-archive/README.md:66) |
| A T-2797 B-5 本走 16 木 | 回収せず消す | v1 cohort は閉鎖され、6 比較は判定不能で確定。tree 外の台帳から費用を記録している。[事前登録 §15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/docs/b5-generator-contrast-preregistration.md:598)、[費用資料](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/output/insights/2026-09-26/t2797-b5-cost-options/README.md:32) |
| A T-2847 verifier-capacity | 回収せず消す | 原本 stdout と起動器は tree 外の job dir、値は insight にある。[README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/output/insights/2026-09-23/t2847-verifier-capacity/README.md:53) |
| A T-2849 mocc 挿入 | 回収せず消す | 生死確認の値は insight に記録済み。[README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/output/insights/2026-09-26/t2849-mocc-insertion/README.md:86) |
| A T-2849 mocc-conn 22 木 | 回収せず消す | campaign を持つ 21 木の原本は既存 archive に照合済みで写した。[再現資料](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/output/insights/2026-09-27/t2853-repro-rest/README.md:63) |
| A T-2850 concurrent-verify・試走 v2 | 回収せず消す | 試走 v2 原本は既存 archive に写した。有効な追補が固定するのは main から辿れる commit `299aa022e` で、既存木ではない。[再現資料](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/output/insights/2026-09-27/t2853-repro-rest/README.md:64)、[追補 3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/docs/search-repetition-trial-preregistration-addendum-3.md:19) |
| A T-2850 試走 v1・vprobe 木 | 回収せず消す | 判断に使う block 1 と vprobe の台帳・生データは**木の外**。`vprobe/runs/` 等は残す。[費用資料](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/output/insights/2026-09-26/t2850-trial-pause-cost-options/README.md:6) |
| A T-2865 系列 B | 回収せず消す | 計測値は insight に記録済み。[README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/output/insights/2026-09-27/t2865-silo-policy-iter2/README.md:55) |
| A T-2865 系列 C | 回収せず消す | 候補と 5 rep の値は記録済みで、1 候補 1 観測の性能主張には使わない。[README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/output/insights/2026-09-29/t2865-silo-policy-series-c/README.md:65) |
| A T-2865 段階 F | 回収せず消す | tree 内原本を既存 archive に照合済みで写した。[再現資料](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/output/insights/2026-09-27/t2853-repro-rest/README.md:62) |
| **A T-2871 policy-loop-iter** | **回収して消す** | gen-opt 設計が WAL 2 本を §6.1 の新しい単価分解の生データと明示し、その値を設計の前提にしている。[設計 README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/output/insights/2026-09-29/gen-opt-evolution-design/README.md:43)、同 :208・:224 |
| A T-2868 sb1〜sb4 | 回収せず消す | 再検査の要点は insight にあり、全出力は tree 外の job dir。[README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/output/insights/2026-09-27/t2868-mocc-g2-cause/README.md:35) |
| B B-5 発効木・元 branch | 回収せず消す〔commit は tag・bundle で保持〕 | 論文関連資料が発効 SHA を provenance として名指す。[方法対応メモ](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/output/insights/2026-09-26/paper-methods-ja/implementation.md:51)、[ComSys 記録](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/output/insights/2026-09-22/comsys2026-manuscript/README.md:263) |
| B T-2868 probe-author | 回収せず消す | probe は branch と job dir に同じものを置いた記録。次の入力として既存木を指定していない。[README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/output/insights/2026-09-27/t2868-mocc-g2-cause/README.md:8) |
| B T-2724 scratch・g1-gen | 回収せず消す | T-2724 は旧系列として取り下げられ、再開時は再起票。[withdrawn.tsv](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/output/insights/2026-09-26/carry-triage/withdrawn.tsv:472) |
| B T-2853 fig8b 作図 3 木・fig6 作図 1 木 | 回収せず消す | 最終 wrapper と図の保管先は既に tree 外。fig8b R2 図は論文図ではない。[fig8b README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/output/insights/2026-09-28/t2853-r2-fig8b/README.md:230)、同 :235・:242、[fig6 README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/output/insights/2026-09-29/t2853-r2-fig6/README.md:123) |
| B vhb-mw9・mw10 | 回収せず消す | 名指しは raw JSON 内の実行時 bench path。[mw9 raw](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/output/insights/2026-09-29/vhash-hot-block-microbench/raw/run2-b42cba01e/20260928T232237Z-4a650961.json:16)、[mw10 raw](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/output/insights/2026-09-29/vhash-hot-block-microbench/raw/run2-b42cba01e/20260928T232340Z-00bc28d9.json:16) |
| B mutation scratch2 の `repo` 木 | 回収せず消す | 調査時点で終了済みの harness 残置で、対象 path の repo 内名指しは 0 件。[調査表](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cleanup-originals-migration/s1-survey-3.md:100) |
| B `md2-pack-hint-fix` branch | 回収せず消す | fix は親 wave に統合され、対象の文書予算は main 側に反映済み。[handoff-final.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-md2-push-pack-hint/handoff-final.md:43)、[check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/tools/check_docs.py:288) |
| B T-2273 branch | 回収せず消す〔新 D が条件〕 | D2242 は branch 保存を明記したが、保留していた中立 land は D2243 項 2 で不採用となった。[D2242](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/docs/decisions.md:72114)、[D2243](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/docs/decisions.md:72165) |

## P2〜P8 の決定

- **P2 — 一部採用。** T-2871 は回収する。ただし一次資料が使うのは指定された **WAL 2 file** なので、campaign dir 全体の回収までは根拠がない。2 file を展開した形で保存し、件数・bytes・SHA-256 を原本と写しで照合する。値が README に転記済みでも、設計が新事実の生データとして WAL を指定している点を重く見る。
- **P3 — tag を作る。** `archive/t2797-b5-effect` を `6fce61d6e` に向け、到達性を検査してから元 branch を消す。bundle も取る。SHA を挙げた論文資料の検証を通常の Git 操作で続けられる。[ComSys 記録](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/output/insights/2026-09-22/comsys2026-manuscript/README.md:263) の「branch にだけあり」は所在注記で更新する。
- **P4 — 新しい D で改めて削除可。** D2242 の「branch は残す」を黙って無視してはいけない。D2243 が保留中だった中立 land を不採用にしたこと、研究の次の入力として branch を指定していないこと、bundle で実装 commit を取り出せることを新 D に明記する。D2243 自体は branch 削除を命じていない。
- **P5 — 採用。** main 非祖先の削除対象 branch は、期待 tip を固定した一覧を作り、bundle の `verify` と head 一致を確認してから削除する。tag 作成も branch 削除より先。main 祖先の `freeze-g1-gen-t2724` は通常削除でよい。
- **P6 — 不採用。** 退避のない無価値木にも一律に tar を作るのは、依頼者の「適当なテストや計測なら回収不要」「損失ゼロは要件でない」と合わない。既存退避は有効な分だけ所在を記録し、退避がないことだけを撤去の阻止条件にしない。非祖先 branch の bundle は P5、T-2871 の回収は P2 に従う。既存 tar の `backup_ok: false` を「退避済み」と数えない。
- **P7 — 範囲を修正して採用。** 集約 insight を逆引きの入口にし、現存する原本・branch を指す読み方になる各 insight README に日付付き追記を置く。K2 の凍結結果稿の path は [paper-story README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/docs/paper-story/README.md:193) から訂正先を指す。結果稿・版・claim-evidence・receipt・MANIFEST・verbatim・raw は変更しない。追加で、ComSys README の branch 所在、paper-methods-ja の親 README から辿れる所在、D2242 に対する新 D、必要なら [到達不能 object 台帳](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/docs/unreachable-object-ledger.md:47) の削除後監査結果を扱う。archive README は表の行追加だけでは足りない。冒頭の「正本は元の path のまま」という[規約](/work/1/SFC/tanab/izanagi-repro-archive/README.md:5)にも、撤去後の所在を日付付きで注記する。写しを無断で新たな official 入力に昇格させない。
- **P8 — 条件を強めて採用。** `mv` は登録された**木の絶対 path だけ**を対象にし、移動先は元 path ごとに一意で、既存 destination への上書きを拒否する。`dev-wave-t2850-trial-run/vprobe/submit-tree-vp` だけを動かし、隣の `vprobe/runs/` や `consult-option/` は動かさない。prune の照合は admin 名だけでなく、各 admin entry の元 worktree 絶対 path と、自分が移した集合の完全一致で行う。scratch2 の admin 名 `repo` は汎用なので特に path と `.git` の相互参照を確認する。撤去直前に占有・HEAD・branch tip・lock・同一 FS・移動先不存在を再確認し、他の prune 候補が一つでもあれば prune しない。land 調整役の OK 後にのみ実行する。

## brief の誤り・漏れ

- [brief:12](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cleanup-originals-migration/brief.md:12) は B 群 11 木とするが、[targets-t0-backup.json](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cleanup-originals-migration/targets-t0-backup.json) は **A 80・B 9、計 89 木**。B の `t2853-r2-plot-fix1/fix2` が JSON にない。[調査表](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cleanup-originals-migration/s1-survey-3.md:41) には両木がある。撤去実行用の集合に明示的に補う必要がある。
- [brief:17](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cleanup-originals-migration/brief.md:17) の「A 群 56 本を前日退避」は、その JSON では確認できない。記録は **A の backup 指定 52 本、`backup_ok: true` は 47 本**、B を含めても指定 55 本・`true` 49 本である。別の退避を数えるなら対応表が要る。
- [brief:14–15](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cleanup-originals-migration/brief.md:14) の「有効な事前登録が入力に取る系列 0」は一般化しすぎ。T-2850 の追補 3 は `299aa022e` を入力に指定する。ただし commit は main の祖先であり、既存 tree を残す理由にはならない。[追補 3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/docs/search-repetition-trial-preregistration-addendum-3.md:19)
- [brief:21–22](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cleanup-originals-migration/brief.md:21) の T-2871「campaign dir ごと」は、示した使用根拠より広い。根拠は WAL 2 file。
- [brief:25](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cleanup-originals-migration/brief.md:25) の tag「0 費用」は正確でない。保存・管理する ref が増える。ただし発効 SHA の到達性を保つ小さい費用として採用する。
- [brief:31–32](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cleanup-originals-migration/brief.md:31) は価値判定と無関係な tar を広く要求し、`backup_ok: false` の扱いも曖昧。[brief:37–38](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cleanup-originals-migration/brief.md:37) の prune 完全一致は admin 名だけでは不足する。
- [brief:33–36](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cleanup-originals-migration/brief.md:33) は、ComSys の現存 branch 断定と archive README 冒頭の正本所在の注記を落としている。「T-2853 の写しが唯一の控え」と一括で書くのも過大で、系列ごとに job dir 内の複製など残る場所を区別すべき。

## 確かめたこと

指定された md_1、brief、調査表 3 本、退避対応 JSON、archive README を開き、判断に使う節を照合した。repo では D2242・D2243、B-5 v1 §15、T-2850 追補 3、T-2871 の設計 §6.1、K2 結果稿、各系列の insight README と raw の名指しを開いた。JSON は読み取りで集計した。

調査表の「コード consumer 0 件」、既存 archive の全 file の現時点の hash 一致、各木の未追跡物の全数、現在の占有・HEAD・mtime、同一 FS、prune 候補は独立再走査していない。したがってこの決定は**静的な撤去方針**であり、実行時の対象確定と照合結果まで保証するものではない。