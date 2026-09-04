## 受理集合の差分

現行の判定式は次の集合だけを真にする。

`E = { mode が exact official ∧ resume_dir is None ∧ 18 名の raw 引数 seam がすべて default }`

根拠は [s8b_floor_campaign.py:6918](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:6918) と [s8b_floor_campaign.py:6954](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:6954)。プランは literal を変えないため、構文上の集合 `E` は不変である。

ただし、`E` のうち完走できる部分は変わる。

| 経路 | 適用前 | 適用後 |
|---|---|---|
| official・fresh・raw seam ゼロ | 空の `mkdtemp` base から外部 FetchContent。offline production では失敗 | ambient submission nonce が選ぶ repo 内 payload を TMPDIR へコピーし、pin 検査後に完走可能 |
| pilot・fresh | 正規 job は explicit seam のため `nondefault_seams={fetchcontent_base_dir}`、適格性は false | 正規 job は seam ゼロになるが、mode が pilot なので false |
| official resume | resume 条件で false | false のまま |
| pilot resume | mode と resume の両方で false | false のまま |
| official test・直接 core | permit gate の monkeypatch に加え、旧 network/stub が必要 | permit gate の monkeypatchと環境変数、payload fixture だけで true の artifact を作れる経路が増える |

したがって、production で観測可能な `eligible_for_refreeze=true` の集合は適用前後とも空である。CLI は [s8b_floor_campaign.py:8433](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:8433)、public/core は [s8b_floor_campaign.py:7038](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:7038) と [s8b_floor_campaign.py:7140](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:7140) で official を拒否し、正規 job も [floor_campaign.sh:1227](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/floor_campaign.sh:1227) で pilot 固定だからである。

一方、permit gate の内側にある潜在的な受理集合は緩む。正規 job 内では注入者は従来どおり submitter、qsub、submission payload を書ける主体に限られる。しかし直接 CLI、public API、private core、テストでは、プロセス環境を設定できる者と、選択した submission leaf を書ける者が、raw seam を立てずに payload を注入できる。

## real 所見

1. **最上位: ambient submission nonce が未分類かつ reservation authority と未束縛で、gate の意味を迂回する。**  
   [s2-plan.md:36](/work/1/SFC/tanab/dev-wave-jobs/t2262-floor-staged-transport/s2-plan.md:36) は `os.environ["IZANAGI_SUBMISSION_NONCE"]` を直接 authority にし、[s2-plan.md:67](/work/1/SFC/tanab/dev-wave-jobs/t2262-floor-staged-transport/s2-plan.md:67) はその実体化を seam 分類後へ置く。一方、現行 core が検証する submit receipt は `reservation_binding.nonce` で選ばれる [s8b_floor_campaign.py:7253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:7253)。両 nonce の等値を保証するのは正規 shell の [floor_campaign.sh:971](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/floor_campaign.sh:971) だけで、driver API 自身には等値検査がない。直接呼出しでは、有効な reservation/receipt の nonce N2 と payload を選ぶ submission nonce N1 を別々に設定できる。32 桁 hex は traversal を防ぐだけで、N1=N2 を証明しない。  
   **成果物影響:** N1 由来 payload を使った official run が `nondefault_seams=[]` と `eligible_for_refreeze=true` を記録し、[s8b_holdout_admission.py:6164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_holdout_admission.py:6164) と [s8b_holdout_freeze.py:1642](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_holdout_freeze.py:1642) が receipt N2 に束縛されていない参照を certified 候補として受理する。

   修正は新しい seam の追加ではなく、default payload nonce を検証済み `reservation_binding.nonce` から内部導出すること、または staging 前に submission nonce との exact equality を要求すること。raw ambient 値だけを authority にしてはならない。

2. **固定 prefix の ancestor symlink が plan の検査対象から漏れている。**  
   プラン自身が prefix symlink を未解決と認識する [s2-plan.md:45](/work/1/SFC/tanab/dev-wave-jobs/t2262-floor-staged-transport/s2-plan.md:45) 一方、helper の指定は payload root と三つの leaf の `lstat` に限られる [s2-plan.md:61](/work/1/SFC/tanab/dev-wave-jobs/t2262-floor-staged-transport/s2-plan.md:61)。現行正規 shell は全 path component を検査する [floor_campaign.sh:299](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/floor_campaign.sh:299) が、直接 driver 経路にはこの検査がない。`submissions` 等の ancestor が symlink でも、最終 payload leaf 自体は non-symlink directory になりうる。  
   **成果物影響:** 固定 submission namespace 外の payload を default 入力として選べるのに claim は seam ゼロとなり、certified 選択の参照 authority が広がる。

pin と network の production 経路自体には real な bypass は見つからなかった。プランどおり repo 内 payload を [s2-plan.md:41](/work/1/SFC/tanab/dev-wave-jobs/t2262-floor-staged-transport/s2-plan.md:41) の repo 外 TMPDIR base へコピーし、その base を `_verify_pristine_floor_dependency_sources` に渡せば、repo 内 base は [s8b_floor_campaign.py:2605](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:2605) で拒否される。プランはこの二つを取り違えていない。

また、プランの [s2-plan.md:65](/work/1/SFC/tanab/dev-wave-jobs/t2262-floor-staged-transport/s2-plan.md:65) を厳密に実装すれば、三つの Git pin/clean 検査と [s8b_floor_campaign.py:2410](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:2410) の v3 policy を通らず prebuild へ到達する production default 経路はない。

## 疑い

- prebuild は三つの `FETCHCONTENT_SOURCE_DIR_*` を渡すが、`FETCHCONTENT_FULLY_DISCONNECTED=ON` 自体は付けない [buildcache.py:2035](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/buildcache.py:2035)。現 CCBench の top-level FetchContent 宣言は masstree、mimalloc、googletest の三つだけなので、静的には全て覆われる [ThirdParty.cmake:42](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/external/ccbench/cmake/ThirdParty.cmake:42)。ただし投入される upstream source 内部の nested FetchContent までは射影ファイルから確定できない。network-denied 環境で actual configure の接続試行を観測すれば決まる。接続が発生して失敗しても、例外は [s8b_floor_campaign.py:3274](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:3274) で preflight failure になり、oracle/build へ進まないため fail-closed である。

## 親 brief の反証

- **「ATTEMPT_DIR と SUBMISSION_DIR は互いに導出できない」は、driver 起動時点では誤り。** Path 式だけなら job ID と nonce は相互変換できないが、`SUBMISSION_DIR/submit-receipt.json` は job ID と nonce を持ち、同 receipt は `ATTEMPT_DIR` へコピーされる [floor_campaign.sh:552](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/floor_campaign.sh:552)、[floor_campaign.sh:581](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/floor_campaign.sh:581)、[floor_campaign.sh:647](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/floor_campaign.sh:647)。したがって、実在する receipt を含む runtime directory 同士は相互導出できる。

- **「pilot は mode 条件で不適格のまま」は追認。** [s8b_floor_campaign.py:6963](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:6963) の `mode == "official"` が支配する。seam が空になっても pilot は true にならない。

- **「凍結 bytes の pin は不在」は DW-O09 の閉包主張として誤り。** 少なくとも tracked の歴史 submit receipt が `tools/pegasus/floor_campaign.sh` の path と bytes SHA-256 を持つ [submit-receipt.json:4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/output/env/pegasus/floor/attempts/submissions/e587c22d7588e5aea760754e88092142/submit-receipt.json:4)。これは歴史記録なので更新対象ではないが、「pin 不在」ではない。`admission_registry.json` が dispatch 分類だけ、`test_official_perf_closure.py` が perf 述語だけ、という個別主張は正しいが閉包として不完全である。

- **pilot の `nondefault_seams` が「結果から消える」という記述も誤り。** Public result schema にその field はない [s8b_floor_contract.py:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_contract.py:81)。値は private measurement-generation claim に保存される [s8b_holdout_admission.py:1604](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_holdout_admission.py:1604)。consumer は同 module の live inspector で、pilot では mode 条件により判定は false のまま。公開 result、report、certified selection はこの変更だけでは壊れない。

- **erratum 2 は追認。** CLI、public wrapper、core の三箇所の無条件拒否は実在し、プランの変更行はどれにも触れない。さらに job script の pilot 固定も残る。したがって本 wave 後も production official の起動集合は空である。

## 検査されていない主張

- **導出 authority の非拡大:** N1=`IZANAGI_SUBMISSION_NONCE` と N2=`reservation_binding.nonce` を不一致にした負例がない。ancestor symlink の負例もない。項目 1 の中心命題は未検査である。

- **semantic な eligible 集合:** pilot と resume の純粋関数負例はあるが、valid default payload、live claim、result finalizer まで通した official 正例がない。既存 full-run 正例は `_derive_refreeze_eligibility` と classifier を直接 monkeypatch する [test_s8b_floor_campaign.py:8993](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/tests/test_s8b_floor_campaign.py:8993) ため、受理集合の証明にならない。

- **default 経路の pin failure:** 新規計画には default の pin 検査を呼ぶ正例はあるが、default payload の HEAD mismatch、dirty、v3 policy mismatch が prebuild/build 前に拒否される負例がない。既存 staged verifier 単体の dirty 負例 [test_s8b_floor_campaign.py:4481](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/tests/test_s8b_floor_campaign.py:4481) だけでは、default 側が例外を握り潰さないことを固定できない。

- **network 不使用:** source-dir 三本の forwarding は検査されるが、actual configure が offline で接続を試みないことは未検査。静的な top-level 閉包だけである。

- **恒真検査:** 計画中の `test_default_staged_transport_is_not_counted_as_refreeze_seam` [s2-plan.md:99](/work/1/SFC/tanab/dev-wave-jobs/t2262-floor-staged-transport/s2-plan.md:99) は、classifier に default 引数を渡せば必ず空になる。helper が任意の環境変数、探索結果、別 receipt を読んでも classifier から不可視なので、gate 迂回を検出できない。既存の policy-unit 正例 [test_s8b_floor_campaign.py:7235](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/tests/test_s8b_floor_campaign.py:7235) も同じ性質を持つ。

official の §8 拒否については既存の CLI 正例 [test_s8b_floor_campaign.py:6533](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/tests/test_s8b_floor_campaign.py:6533) と core/public の副作用ゼロ負例 [test_s8b_floor_campaign.py:6694](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/tests/test_s8b_floor_campaign.py:6694) が発火する。

## scope 外候補

- prebuild にも `FETCHCONTENT_FULLY_DISCONNECTED=ON` を追加する一般的な hardening。現 top-level 三依存は source-dir で閉じるため、offline 観測で nested fetch が見つからない限り本 wave へは入れない。
- §8 permit gate の解除、承認束縛、job script の official mode 結線、official 実走は既定どおり別 wave。
- 歴史 submit receipt の再発行や hash 更新。これらは歴史記録なので変更してはならない。

## 総括

構文上の適格式は不変だが、default が読む ambient authority は 18 seam に記録されず、意味上の受理集合は緩む。  
最大の危険は submission nonce と検証済み reservation nonce が driver 内で束縛されていない点である。  
実装前に、payload nonce を検証済み `reservation_binding.nonce` から内部導出し、固定 prefix の全 ancestor を検査する形へプランを直すべきである。  
pin 検査、repo 外 staging base、三 source-dir の production 到達性はプランどおりなら保たれる。  
pilot と resume は `eligible_for_refreeze=false` のままで、pilot の変化は private claim の seam 列だけである。  
§8 の無条件拒否と job の pilot 固定は弱まらず、production official は本 wave 後も起動できない。