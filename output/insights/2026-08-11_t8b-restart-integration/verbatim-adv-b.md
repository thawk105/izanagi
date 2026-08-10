4ファイルは全文読了した。以下は静的検査のみの所見であり、ファイル編集・pytest実走・緑判定は行っていない。

### B-1

- **区分**: BLOCKER
- **主張**: W-1 は admission を現行 claim 処理より前へ物理的に移動しない限り、D86 の副作用ゼロ契約を満たさない。
- **根拠**: [plan.md:92](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t8b-restart-integration/plan.md:92) は「campaign claim … より前」とする一方、現行コードは [s8b_floor_campaign.py:2949](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_floor_campaign.py:2949) 付近で `campaign_claim.acquire_claim(...)` を実行し、その後の [s8b_floor_campaign.py:2983](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_floor_campaign.py:2983) 以降で official preflight を行う。
- **成果物への影響**: admission 失敗でも claim が残り、再試行が既存 claim 拒否になる。certificate、journal、floor result は無いのに claim 台帳だけが残り、certified 選択は空のままとなる。

### B-2

- **区分**: MUST
- **主張**: 新 leaf の固定 ROOT・内部 receipt 契約と、既存 certified-writer admission の可変 root／receipt／環境入力の契約を分離する API が未定義である。
- **根拠**: 計画は [plan.md:62](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t8b-restart-integration/plan.md:62) で `_admit_official` への `repo_root`、`receipt_path`、`environ` を禁止し、[plan.md:123](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t8b-restart-integration/plan.md:123) で既存 `_admit_floor` の委譲を要求する。しかし現行は [certified_writer_admission.py:177](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/certified_writer_admission.py:177) の `def _admit_floor(repo_root, receipt_path, environ)` であり、[test_campaign.py:4924](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/tests/test_campaign.py:4924) もその3入力を渡している。
- **成果物への影響**: 直接委譲すると既存の certified-writer／T126 admission と一時 repo fixture が壊れ、floor submission の受理結果や attempt ledger が赤になる。固定入力を優先すると既存の read-only admission 意味論が変わる。

### B-3

- **区分**: MUST
- **主張**: 固定拒否を削除すると、現行の official 拒否テストは意図した赤になるため、admission failure fixture へ明示的に置換しなければならない。
- **根拠**: [test_s8b_floor_campaign.py:1115](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/tests/test_s8b_floor_campaign.py:1115) は `main(["--mode", "official", ...])` に対して `assert rc == 2`、`payload["status"] == "refused"`、`"§8" in payload["reason"]` を要求している。計画は [plan.md:116](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t8b-restart-integration/plan.md:116) でこの固定拒否を削除する。
- **成果物への影響**: このテストを残すと、実装が正しくても wave の検査成果物が赤になり、official CLI の rc=2 admission 拒否を証明できない。

### B-4

- **区分**: MUST
- **主張**: 編集ファイル集合は素集合でも、A が変更する test helper を B のテストが import しており、実装契約の所有集合は素集合ではない。
- **根拠**: 計画は [plan.md:370](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t8b-restart-integration/plan.md:370) で編集集合を「素集合」とするが、[test_s8b_oracle_driver.py:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/tests/test_s8b_oracle_driver.py:35)、[test_s8b_oracle_report.py:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/tests/test_s8b_oracle_report.py:27)、[test_s8b_ratified_verify.py:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/tests/test_s8b_ratified_verify.py:34) はいずれも `test_s8b_ratified_freeze` を fixture として import している。
- **成果物への影響**: A の seam 移行で B の driver／report fixture が壊れるか、古い拒否 seam を使い続けて偽の緑になる。oracle の certified 選択・report・ledger 経路の検査証拠が無効になる。

### B-5

- **区分**: BLOCKER
- **主張**: T-749 の「raw bytes を一度だけ capture」という計画は、`verify_receipt()` が holdout を内部で再読する現行 API と両立していない。
- **根拠**: [plan.md:158](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t8b-restart-integration/plan.md:158) は raw capture 後に `verify_receipt()` を一度呼ぶ。一方、[t080_freeze_migration.py:1979](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/t080_freeze_migration.py:1979) は `_load_artifact(root, HOLDOUT_REL, ...)` で再読し、[t080_freeze_migration.py:2077](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/t080_freeze_migration.py:2077) の adapter は別途 caller の `holdout_raw` を受け取る。
- **成果物への影響**: receipt 検証時の bytes と adapter が判定する bytes が異なる TOCTOU 窓が残り、現在の active file と異なる bytes に対して rc=0 の T-080 exemption を返す、または誤った rc=1 を返す。CLI の受理集合と移行観測値が不確定になる。

### B-6

- **区分**: MUST
- **主張**: W-3 の処理手順にある `_validate_execution_snapshot` は ratified freeze module の関数ではなく、B 所有の oracle manifest module の private helper である。
- **根拠**: [plan.md:240](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t8b-restart-integration/plan.md:240) は同名関数を列挙するが、ratified 側は [s8b_ratified_freeze.py:1003](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_ratified_freeze.py:1003) で `_verify_snapshot_layer1(document)` を呼ぶだけである。同名関数の実在箇所は [s8b_oracle_manifest.py:626](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_oracle_manifest.py:626) である。
- **成果物への影響**: C が未修飾名として実装すると生成 CLI が動かず、複製実装すると floor／budget／holdout 受理条件が二重化する。candidate が生成できず、v2 freeze と manifest の受理集合は空のままとなる。

### B-7

- **区分**: BLOCKER
- **主張**: W-3 の producer 検査項目は、既存 launch validator が要求する certificate・manifest・journal・result の binding graph 全体を覆っていない。
- **根拠**: 計画の手順は [plan.md:231](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t8b-restart-integration/plan.md:231) で result と floor projection を検査し、[plan.md:240](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t8b-restart-integration/plan.md:240) で structural helper を呼ぶ。一方、既存 verifier は [s8b_ratified_freeze.py:2897](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_ratified_freeze.py:2897) で専用 role path を導出し、[s8b_ratified_freeze.py:2962](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_ratified_freeze.py:2962) 以降で protocol、certificate、manifest、result、journal を strict load する。
- **成果物への影響**: producer が candidate を書けても、後段の `launch_validate` で初めて拒否される candidate が生成される。人間手番・manifest 生成・certified 選択まで到達せず、失敗理由が producer ではなく後段へ漏れる。

### B-8

- **区分**: MUST
- **主張**: W-3 の「candidate 単体でも `load_ratified_freeze` は no-active」というテスト期待値は、canonical namespace へ未追跡 candidate を書く現在の verifier と衝突する。
- **根拠**: 計画は [plan.md:242](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t8b-restart-integration/plan.md:242) で `holdout_freeze.v2.g{N}.json` を出力し、[plan.md:244](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t8b-restart-integration/plan.md:244) で `load_ratified_freeze` が `no-active` のままとする。実際の canonical path は [s8b_ratified_freeze.py:1040](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_ratified_freeze.py:1040) で `output/s8b-freeze` 配下に固定され、[s8b_ratified_freeze.py:346](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_ratified_freeze.py:346) はその配下の untracked を `namespace-dirty` として拒否する。
- **成果物への影響**: candidate 作成直後の検査結果は `no-active` ではなく `namespace-dirty` になる。期待値を合わせるため verifier の namespace gate を緩めると、未 commit artifact が ratified namespace に入り、active／certified 受理境界を変える。

### B-9

- **区分**: BLOCKER
- **主張**: W-4 CLI は `--freeze` と `--output` の path を固定 ROOT に閉じる契約がなく、canonical repo 外の manifest を生成・配置できる。
- **根拠**: 計画は [plan.md:273](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t8b-restart-integration/plan.md:273) で3つの PATH 引数を要求し、[plan.md:280](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t8b-restart-integration/plan.md:280) で `--root` を設けない。しかし現行 builder は [s8b_oracle_manifest.py:698](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_oracle_manifest.py:698) で `freeze_path = Path(freeze_path)` とし、writer は [s8b_oracle_manifest.py:772](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_oracle_manifest.py:772) で任意の `path.parent` を作成する。
- **成果物への影響**: canonical freeze と無関係な manifest が生成され、driver／report がその manifest の `manifest_id`、`manifest_sha256`、schedule を台帳へ記録できる。certified report が参照する manifest path と実凍結 namespace が一致しなくなる。

### B-10

- **区分**: MUST
- **主張**: W-4 の exact spec は構文検証に過ぎず、schedule・run contract・campaign ID が人間レビュー済みの実験契約であることを証明しない。
- **根拠**: 計画自身が [plan.md:447](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t8b-restart-integration/plan.md:447) で production source の不在を認めている。現行 builder は [s8b_oracle_manifest.py:707](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_oracle_manifest.py:707) で schedule を検査し、[s8b_oracle_manifest.py:710](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_oracle_manifest.py:710) で campaign ID の集合だけを照合している。
- **成果物への影響**: 構造的に正しい別 schedule、別 campaign ID、別 run contract から manifest を作れてしまい、oracle の実行行、budget ledger、report の campaign 集計が意図した reviewed spec と異なる。

### B-11

- **区分**: BLOCKER
- **主張**: 親の「Pegasus では gcc module が物理的に存在しない」という M1 は、現資料だけでは login／compute／個人 module／Spack／container を閉包しておらず、R-4(b)を確定できない。
- **根拠**: 親は [ruling-package-r4.md:18](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t8b-restart-integration/ruling-package-r4.md:18) で「gcc の module は無い」とするが、実測 script は [probe-toolchain.sh:6](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-jobs/dev-wave-t8b-restart-integration/probe-toolchain.sh:6) の現在 shell の `type module`、[probe-toolchain.sh:7](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t8b-restart-integration/probe-toolchain.sh:7) の一つの `MODULEPATH`、[probe-toolchain.sh:9](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t8b-restart-integration/probe-toolchain.sh:9) と [probe-toolchain.sh:11](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t8b-restart-integration/probe-toolchain.sh:11) の `head` 付き出力しか取っていない。Spack／個人 module root／container は [probe-toolchain.sh:23](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t8b-restart-integration/probe-toolchain.sh:23) の `/opt` 先頭20件以外を検査していない。
- **成果物への影響**: 実は利用可能な gcc-13 相当経路が残っているのに system compiler を選ぶと、R-4 の選択、env/toolchain pin、floor protocol、最終 floor 値が別物になる。R-4 の受理集合と certified 値の前提が未確定である。

### B-12

- **区分**: MUST
- **主張**: 親の M4 は legacy `build()` には成立するが、floor の v2 build まで一括して偽 hit と読むのは誤りであり、legacy と v2 を分けて対策すべきである。
- **根拠**: legacy key は [buildcache.py:130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/buildcache.py:130) で、[buildcache.py:144](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/buildcache.py:144) は既定 `(cc,cxx)` の toolchain token を空にする。一方 v2 preimage は [buildcache.py:246](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/buildcache.py:246) で `cc`、`cxx`、toolchain manifest hash を含む。floor は [s8b_floor_campaign.py:1095](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_floor_campaign.py:1095) で v2 build を呼ぶ。
- **成果物への影響**: 旧 legacy binary を gcc-13、新 default を gcc/g++ とし、source digest が同じ `STOCK` になる系列では同一 legacy key の hit が成立し、current compiler と記録された configure command が実 binary と食い違う。floor v2 自体は別 namespace の toolchain preimage で保護されるため、M4 の影響範囲を誤ると legacy report だけを汚染するか、逆に floor の必要防壁を見落とす。

### B-13

- **区分**: MUST
- **主張**: W-2／W-5 は実走そのものは再裁定・人間発効まで止まるが、実装・preflight・cache collision 検査まで「実行不能」と扱うのは過剰である。
- **根拠**: 現行には [buildcache.py:454](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/buildcache.py:454) の site compiler selector があるのに、floor は [s8b_floor_campaign.py:1075](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_floor_campaign.py:1075) と [s8b_floor_campaign.py:1095](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_floor_campaign.py:1095) で `DEFAULT_CC/CXX` を直接使う。W-5 の実走が止まる根拠は [s8b_oracle_driver.py:432](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_oracle_driver.py:432) の `freeze.floor`／`budget` null 拒否である。
- **成果物への影響**: 再裁定なしの実測値を certified として作ることはできないが、compiler binding、legacy cache 防壁、候補／manifest の静的検証は前進できる。ここを計画しないと、再裁定後も floor／budget が null のままで certified 選択が空になる。

### B-14

- **区分**: MUST
- **主張**: W-1の防壁変更、T-749のTOCTOUを含むCLI変更、W-3/W-4のartifact producerを同一waveで完成判定する規模は過大である。
- **根拠**: Aだけでも [plan.md:365](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t8b-restart-integration/plan.md:365) の9ファイルを跨ぎ、現行 claim／certificate の境界は [s8b_floor_campaign.py:2949](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_floor_campaign.py:2949) にある。W-3は ratified semantic／launch validation、W-4は builder／writerを跨ぎ、B/C共有の private helper も [plan.md:376](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t8b-restart-integration/plan.md:376) で指定されている。
- **成果物への影響**: 一部の子だけ完成した状態を wave 全体の certified 実装と誤認しやすく、candidate、manifest、report、ledger の参照整合を一括で保証できない。W-1 admission、T-749、W-3、W-4を少なくとも別の検証境界に分けるべきである。

### B-15

- **区分**: SHOULD
- **主張**: W-4の consumer test に oracle report が含まれておらず、CLI生成 manifest の最終 report 経路が未検証である。
- **根拠**: W-4のテスト一覧は [plan.md:352](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t8b-restart-integration/plan.md:352) と [plan.md:357](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t8b-restart-integration/plan.md:357) の manifest／driver に限られるが、production consumer 一覧には report も含まれる。実際に [s8b_oracle_report.py:1757](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_oracle_report.py:1757) が `verify_manifest` を呼ぶ。
- **成果物への影響**: driver では通る manifest が report の `manifest_sha256`、freeze reverify、観測行生成で失敗する可能性を残し、最終 report と ledger の受理集合を証明できない。

## 総括

- **判定: NO-GO**。少なくとも B-1、B-5、B-7、B-9、B-11 を解消するまで、実装開始後に「計画どおり成立する」とは認定できない。
- ユーザー裁定が必要な点:
  - Pegasus の login／compute 両方で、全 `MODULEPATH`、個人 module、Spack、container、wrapper の有無を含む M1 を再実測するか。
  - R-4 の A/B/C のどれを採るか、legacy cache と v2 cache をどう分離・無効化するか。
  - W-1 の admission を claim より前へ移すこと、fixed FD の失敗時意味論、certified-writer leaf の二層 API。
  - T-749 で一つの raw snapshot を保証するため T-080 API を変更するか、再読検査を追加するか。
  - W-3 の production budget の人間レビュー済み入力、canonical namespace と commit handoff、g2以降を候補だけ生成する方針。
  - W-4 の reviewed spec の出所・hashと、freeze／manifest output path を固定 ROOT 内に制限する方針。
  - wave を W-1／T-749／W-3／W-4 に分割し、共有 fixture と report consumer の所有者を決めること。