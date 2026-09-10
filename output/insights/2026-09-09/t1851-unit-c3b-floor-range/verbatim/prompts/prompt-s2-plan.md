単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2

必読事項の射影 (いずれも絶対パス。読めなければ即停止し、その旨を出力に書いて終わること):

- 作業 root (read-only): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2`
- **親の段 1 brief (scope の正本)**: `/home/SFC/tanab/.claude/jobs/c311da24/tmp/dev-wave-t1851-unit-c3b/s1-brief.md`
- **直前単位 C3a の記録 (配線の実体)**: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-09_t1851-unit-c3a-wiring/README.md`
- C3a の裁定パッケージ (裁定 4 が C3b の設計): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-09_t1851-unit-c3a-wiring/ruling-package.md`
- C3a の段 4 裁定と変異事前登録: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-09_t1851-unit-c3a-wiring/s4-adjudication.md`
- **契約の正本**: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.1.md`
- 契約の追記訂正 1: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-08_t1851-unit-c2-derivation/contract-v3.1-erratum-1.md`
- 契約の追記訂正 2 (C3a 発行、ordinal 軸): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-09_t1851-unit-c3a-wiring/contract-v3.1-erratum-2.md`
- 投入手順の正本 (§4・§5・§6): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/README.md`
- 床値実走の runbook (W-2 節): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/docs/phase3-8b-restart-runbook.md`
- 機体固有情報の正本: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/docs/pegasus-runbook.md`
- pilot 走行の一次資料: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-08-25_t1431-floor-pilot-values/README.md`
- 共通規律: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/CLAUDE.md`

# 段 2 — 単位 C3b の実行 plan を file:line 粒度で起草する

作業 root は read-only である。**書込み可能な tmp は無い。** したがって
**pytest 緑を要求しない。静的読解と grep による実測だけで結論を出す。**
テストの実走と Pegasus への投入は親が行う。**走らせていないものを緑と書かないこと。**

**file を 1 つも作れない。** 成果物は**最終メッセージの本文へ全文を書く**こと。
「file へ書いた」と述べても親には届かない。

予算が尽きそうなら、**途中結論を下の出力形式どおりに書いて終わること** (無出力が最悪)。

この段では commit を作らない。git の状態を変えない。

## この単位の性質 — 通常の実装 wave と違う点

C3b の成果物は**コードではなく実測と記録**である。C3a が配線した
`campaign → certified launcher → attempt registry → result v5` の経路を、Pegasus 上の
official floor campaign 1 本で実際に通し、**gate 入力の実観測値を receipt にする**。

親は「実装面の差分 0」を狙っている (段 1 brief の (P1-2))。plan はこの狙いが成立するかを
検査し、成立しないなら**何が最小の実装面か**を file:line で示すこと。

## plan に必ず入れること

1. **投入手順の file:line 粒度の実行計画。** `tools/pegasus/submit_floor.sh` と
   `tools/pegasus/floor_campaign.sh` を読み、投入前に満たさねばならない前提を全列挙する。
   とくに次を現物の行番号で示すこと。
   - drift 検査 (未 commit の tracked 変更があると qsub 前に止まる) が見る対象は何か。
     `.codex/worktrees/` のような untracked directory は掛かるか。
   - third-party staging root の要求 (`floor third-party source root is missing or unsafe`) を
     出す実体はどの行か。`fetch_third_party.py hydrate` の出力のどの field を渡すのか。
   - `output/claims` の mode 0700 要求 (README §4) を実装している行。
   - 承認 nonce 束縛 (`IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN` と `IZANAGI_SUBMISSION_NONCE` の
     exact 一致) を検査する行。
   - reservation preflight の `required_s` 導出 (README §5 は minimum envelope 30600 秒と書く)。
     job script の `elapstim_req=10:00:00` との関係を行で示す。
2. **gate 入力の完全列挙。** 段 1 brief の (P1-3) は 8 種を挙げているが、これは親の推定である。
   **C3a が新設・改訂した述語を現物で読み、それらが実際に消費する field を全列挙し直すこと。**
   最低限、次の source を読むこと。
   - `orchestrator/campaign/s8b_floor_attempt_launcher.py` の
     `probe_floor_attempt_preconditions` (:687)、`read_floor_attempt_pre_probe` (:709)、
     `launch_floor_attempt` (:1576)、`launch_probed_floor_attempt` (:1605)
   - `orchestrator/campaign/s8b_floor_campaign.py` の production 配線部と :6816 の schema 分岐
   - `orchestrator/campaign/s8b_floor_contract.py` の v5 key 集合
   - attempt registry 側の受理述語 (`attempt_ordinal != 0` を拒否する箇所など)
   各 field について「どの述語が消費するか」「run artifact のどの path のどの JSON key に現れるか」を
   表で示す。**artifact 上の所在が示せない field は、その旨を明記すること** (receipt に書けないため)。
3. **抽出経路。** 完走後の run artifact から 2 の値を取り出す手順。既存の reader (例:
   `s8b_floor_stats.py`) が使えるか、`jq`/`python3` の一回限りの読み出しで足りるかを判定する。
   **新しい producer script を repo へ足す必要があるか**を明示的に判定すること。要るなら
   その file path と概形、要らないならその理由を書く。
4. **pin 閉包 (DW-O09)。** この単位で新しく作る成果物名 (insight directory 名、receipt file 名) が
   既存の凍結 gate・登録簿・exact 閉包に触れるかを検査する。触れるなら全列挙する。
   走行が repo の `output/` 配下へ書く成果物が、holdout clean-scan の hit 0 件要求を破らないかも
   検査する (restart runbook W-2 の最終段落)。
5. **停止条件。** 投入後に「これが起きたら止めて報告する」条件を列挙する。
   `driver_rc=0` かつ `status: completed` でも床値が全 null になりうる、
   `job-result.json` の書込み失敗が rc に出ない、といった既知の穴を含めること。
6. **段 1 brief の (P1-1)〜(P1-4) への評価。** それぞれ支持 / 反対を根拠つきで書く。とくに
   **(P1-1) 未 land commit での official 走行**は、D811・D926・D1161・D1398 の逐語を
   `docs/decisions.md` から引いて評価すること (行番号ではなく `## D<番号>` の見出しで引く)。

## 出力形式

次の H2 だけを使い、この順で書く。

## 総括
## 投入手順の実行計画
## gate 入力の完全列挙
## 抽出経路
## pin 閉包
## 停止条件
## (P1) への評価
## 未解決の問い

結合文字 U+0300〜U+036F を出力に使わないこと。
