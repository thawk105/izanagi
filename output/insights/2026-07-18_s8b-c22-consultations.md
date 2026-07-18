# s8b C2-2 launch certificate 結線 wave — codex 敵対相談の逐語・裁定・確定プラン (2026-07-18)

**編集方針 (逐語性の例外):** §6 の相談逐語のうち、単一 holdout の三軸リテラルが同一行に並ぶ箇所は、
本ファイル自身が holdout scan の conjunction hit になるのを防ぐため `ycsb_rratio=` →
`ycsb_rratio⟦=⟧` の形で軸名直後の `=` を可視マーカーで置換した (意味は不変、機械照合のみ破壊)。
それ以外は逐語。原文はセッション一時領域のみに存在し揮発する (F20 の教訓どおり、恒久正本は本ファイル)。

## §1 背景とスコープ

- セッション: 2026-07-18 bg job (worktree s8b-c22-launch-cert、基準 e45db19)。クラス 3。
- レーン A: worklog (8) 次の一手 1 の guard_agent live 発火確認 → **不発を発見**、原因調査と文書化。
- レーン B: worklog (7) residual の C2-2 launch certificate 発行結線 + verifier lineage 照合。
- ループ: 親プラン v1 (.consult 一時ファイル、非 commit) → codex gpt-5.6-sol 敵対相談 4 本並列
  (A=発行側 max / B=検証側 max / C=テスト・スコープ・順序 max / D=guard_agent high) → 親裁定 →
  codex 並列実行 → claude opus 並列レビュー → 残所見再投げ。
- 所見総数: **must-fix 26 / should-fix 7 / nit 0、refuted 0 (全 real 裁定、ただし一部は「今 wave では
  実装せずユーザー裁定パッケージへ」)。**

## §2 親裁定表 (要旨)

| # | 所見 (severity) | 裁定 | 反映先 |
|---|---|---|---|
| A1 | repo が既に clean scan hit-0 でない — test_s8b_ratified_freeze.py が rr80/rr20 に実 hit (must) | real (親が実 scan で追認) | E2 (脱同居 + 実 scan 不変条件テスト) |
| A2 | clean_scan_digest が malformed report に fail-open — F9 型 (must) | real | E1 (_assert_search_pass 必須通過) |
| A3 | scan と digest の列挙分離 TOCTOU (must) | real | E1 (before→search(files)→after 完全一致) |
| A4 | scan hit 時 zero-side-effect とプラン順序の矛盾 (must) | real | E1 (scan を mkdir より前へ) |
| A5 | mode domain 未検証 + path traversal (must、既存バグ) | real | E1 (_validate_mode、seam より前、テストで patch 禁止) |
| A6 | output/s8b-freeze/ prefix 全除外が clean cert の盲点 (must) | real | E1 (preflight 限定 exact allowlist)。恒久設計は §5-(ix)-9 |
| A7 | 実 manifest/result 自身が hit し closure 導出と矛盾 (must、in-memory 実証付き) | real | §5-(ix)-3 (closure 契約の裁定が必要) |
| A8 | cert 発行後 campaign-start 前 crash が回復不能 + cert は一回限り問題 (must) | real | E1 (launch-start journal 耐久化)。回復 semantics と one-shot 裁定は §5-(ix)-4/5 |
| A9 | resume が bytes hash のみで意味再検証なし (should) | real | E1 (共有 validator + run_id==dirname) |
| A10 | builder 自由文字列 field 経由の hit 混入 (should) | real | E1 (canonical bytes の hit-0 自己検査) |
| B1/C3 | 「journal 束縛」が result 内 wall_ledger 自己申告に弱まる (must) | real | §5-(ix)-1 (journal.jsonl G blob 実体検証) |
| B2/C4 | cert・closure 同一 commit では時間順序を証明できない (must) | real | §5-(ix)-2 (厳密祖先 + 導入一意) |
| B3 | 複数導入の量化未定義 (削除再導入/merge/rebase bypass) (must) | real | §5-(ix)-2 |
| B4 | 裁定済み「closure を G に同時収録」を現行 V1d が強制していない (must) | real | §5-(ix)-10 (§5-(ii) 追認と同時に機械化) |
| B5 | dirname 由来 path の偽造 + symlink blob 偽装 (must) | real | §5-(ix)-7 (canonical path parser + mode 100644) |
| B6/C8 | protocol/freeze の equality chain 不完全 (must) | real | 発行側分は E1 テストで束縛、verifier 分は §5-(ix)-1 |
| B7 | 検証済み floor artifact が oracle に引き渡されない (should) | real | §5-(ix)-8 (VerifiedFloorArtifact) |
| B8 | fixture は段階 builder への再設計が必要 (should) | real | 追認後実装 note (§5 末尾) |
| B9/C1 | 検証側 normative 実装は追認待ち領域への越権 (must) | real — **方針転換の決定打** | 検証側は本 wave 実装せず §5 パッケージ化 |
| B10 | reason code 表が失敗面を閉じない (should) | real | 追認後実装 note |
| C2 | スコープ文言と tmp-only 拘束の不備 (should) | real | E1 拘束 + Lane A 別 commit + worklog 文言 |
| C5 | clean scan 恒真 + output/env の恒久拒否リスク (must) | real | E1 + §5 運用 note |
| C6 | orphan cert / 発行順矛盾 (must) | real | = A4/A8 |
| C7 | resume 意味再検証 (must) | real | = A9 |
| C9 | eligible_for_refreeze 三択未裁定のまま happy fixture 化は不可 (must) | real | §5-(ix)-6 |
| C10 | _need_v1 の pytest.skip で攻撃 matrix 全 skip (must) | real | 親直接修正 (skip→fail、E 完了後) |
| C11 | writer/verifier 別 stub では dormant 結線を証明できない (must) | real | E1 統合は production bytes 経由。full E2E は追認後 |
| C12 | 変異 2 件では不足 — 6 群列挙 (must) | real | レビュー後の変異スポット段で now-scope 群を適用 |
| C13 | Lane A の因果断定は観測超過 (should) | real | 文書化済み (F21/README は「原因未分離」記載) |
| D1 | bg 固有と断定不能 — 2.1.211/2.1.212 × bg/headless の二重交絡 (must) | real (親が transcript で version 追認) | F21/README 記載修正済み + §5 再検証条件 |
| D2 | 対照実験が enforcement 陽性対照になっていない (must) | real | 追実験実施 — §4 (3) で閉鎖 |
| D3 | worktree 仮説の refuted を明記せよ (must) | real | README/F21 に反映 |
| D4 | 「機械的防衛は無い」は偽 (must) | real | §5 Lane A 候補 (適用はユーザー判断) |
| D5 | 別 lifecycle hook は検知であって予防でない (should) | real | README 表現に反映 |
| D6 | docs-only 恒久対応は failures 契約を満たさない (must) | real | F21 は「恒久検査未実装」と正直に記載 |

Q-1 (テスト seam): 採用。条件 = _validate_mode / path 検証は seam に含めない・テストで patch しない、
CLI 拒否と unpatched core の zero-write テスト維持、production bypass なし、monkeypatch は局所 scope。
Q-2: A の回答を採用 (golden protocol は hit 0 / 自由文字列で hit 混入可 → E1 で自己検査 /
manifest・result は実 hit → (ix)-3 / cert hit-0 は「v1→g1 初回一回限り」裁定案 → (ix)-4)。
Q-3〜Q-6: B の回答を §5 の推奨案として記載 (裁定はユーザー)。Q-7: D の回答を §5 Lane A に記載。

## §3 確定プラン v2 (本 wave の実装スコープ = 判断非依存部分のみ)

- **E1 (codex, s8b_floor_campaign.py + 同テスト + builder テスト):** _validate_mode (exact
  {pilot,official}、既存 path traversal バグ修正) / _assert_official_permitted seam 抽出 (無条件
  raise 不変) / clean_scan_digest 恒真封鎖 (_assert_search_pass 必須 + 列挙 before/after 一致 +
  output/s8b-freeze exact allowlist) / validate_launch_certificate (exact 6 keys、fresh・resume 共用)
  / _official_launch_preflight (scan は mkdir 前、now 1 回捕捉、cert create-only 発行 + 自己検査 +
  launch-start journal 耐久化) / campaign-start への cert sha 束縛 (official のみ、schema bump なし)
  / _verify_resume_journal 拡張 (意味再検証 + rename 検出 + pilot 混線拒否) / builder canonical
  bytes の hit-0 自己検査 / 統合・負例・zero-side-effect テスト一式 (tmp-only、実 output/ 前後不変)
- **E2 (codex, test_s8b_ratified_freeze.py + 新規不変条件テスト):** 軸リテラルの実行時結合化
  (バイト列不変) + 実 scan hit-0 の repo 不変条件テスト (既知 hit 台帳方式、陽性対照 >0 併記)
- **Lane A (実施済み):** hooks/README hook 4 既知限界 + failures F21。コード変更なし。別 commit
- **親 follow-up:** _need_v1 skip→fail / claude opus 並列レビュー (2 レンズ × レーン) / 変異
  スポット (C12 の now-scope 群) / worklog・memory・handoff 削除
- **本 wave でやらないこと (越権防止):** launch_validate の受理条件変更・§5-(ix) の normative 実装・
  happy fixture の official 化・実 cert / 実 approval / 実凍結の生成。official 拒否 (CLI + core) 不変

## §4 本セッションの実測検証 (親またはツールによる一次事実)

1. **実 scan:** search_repository(ROOT) → rr80 / rr20 とも hit = orchestrator/tests/
   test_s8b_ratified_freeze.py の 1 件のみ。positive_control hit_count = 42 (稼働)
2. **guard_agent 不発:** 本 bg セッション (daemon 2.1.211) で model 無し general-purpose Agent
   呼び出しが素通り。同セッションで guard_bash は発火。hook 単体 stdin は exit 2
3. **enforcement 陽性対照 (headless 2.1.212):** repo と同一 command 形 ($CLAUDE_PROJECT_DIR 展開)
   + model 欠落呼び出し → PreToolUse 配送 (併設 logger が input_keys=[description,prompt,
   subagent_type] を記録) + exit 2 + spawn 阻止 + 拒否メッセージが親モデルへ逐語到達
4. **matcher 実験 (headless 2.1.212):** matcher 無し / matcher "Agent" 完全一致の両方で
   tool_name "Agent" として配送。公式 docs も matcher/tool_name とも "Agent"、hooks は live-reload

## §5 ユーザー裁定パッケージ (次回ユーザー接点で提示)

**裁定結果 (2026-07-18 ユーザー裁定 — 同日 C2-2 検証側実装 wave で発効):**
- (ix)-3 = **択 (a)** (期待 hit を union 導出)。実装解釈: 検証鎖で束縛される run_dir artifact
  (floor_protocol / floor_source=result / journal / manifest) は期待集合へ暗黙に含め、それ以外の
  hit は measurement_closure の列挙のみを想定内とする (journal/manifest も実 hit するため、
  これを含めないと (a) が成立しない — 実装 wave の敵対相談で攻撃対象)
- (ix)-4 = **初回限り** (現 schema の clean hit-0 cert は v1→g1 専用。再実測用の別 schema は将来裁定)
- (ix)-5 = **厳密検証付き pre-start resume** (ユーザーは「推奨案どおり」と裁定。本項は文書上
  推奨が明示されていなかったため、launch-start 耐久化の設計意図に沿うこの択を推奨と解釈して採用
  — 解釈である旨をユーザーに明示済み)
- (ix)-6 = **official 完走 finalize 時のみ True** の provenance フラグ (B 推奨案)
- (ix)-1 / -2 / -7 / -8 / -9 / -10 = **追認** (推奨案どおり。-2 の「履歴書換え耐性は H 内記録順
  のみ」という限界記載も含めて追認)
- 未裁定のまま残るもの: 前 wave §5 の (i)〜(viii) (strict-v2-wave-consultations.md)、
  guard_agent 防衛候補 (次回 bg セッション再検証待ち)

**master_seed / env_tag のユーザー確定 (2026-07-18):**
- **master_seed = `2026-07-18T17:16:12+09:00`** (ユーザーが「今のタイムスタンプで決めて」と委任 →
  親がメッセージ受領時刻で確定)。build_protocol_document の非空 str 制約 + hit-0 自己検査 (S0) を
  満たす (3 軸リテラルを含まない)。**発効 = 実 protocol JSON への焼き込みと `AI-Agent: none` 凍結は
  検証器実装後** (発効なし規律)。この値は確定 = 結果を見た後に選び直さない (事前登録の系)
- **env_tag = Pegasus** (ユーザー確定: 「Pegasus 使う。正式計測環境云々ではない。複数マシンで動く」)。
  D59 の「正式計測の正本 env-tag 昇格」議論とは**独立** — env_contract registry へ環境ごとにエントリを
  足す実務。スラッグ暫定 = `pegasus` (親推奨、slug 文法 [a-z0-9][a-z0-9._-]* 適合。最終確定はユーザー)。
  **ただし env_tag は値決めだけでは成立しない** — env_contract.py の registry へ Pegasus entry を
  追加するには実測が必要 (pegasus-runbook §7 登録段が正本):
  - clocks_per_us (Pegasus 実測) / numactl (Pegasus トポロジ) / calibration_ref {path, sha256}
    (Pegasus 単独ノードで calibrator 実走した成果物、自由文不可)
  - isolation_policy = single_process=True / allow_resume=False (G12、runbook 明記)
  - test 側 ENV_LITERAL_VALUES (test_env_contract.py) への新 env 値追加 (registry↔禁止 literal 同期)
  - machine-pin (contract.env_tag == p2_2.ENV_TAG。現在 p2_2.ENV_TAG = "linux-baremetal") の
    Pegasus 実行への扱いを登録段で設計 (現状 pin を変えると cygnus 実行が pin fail する)
  - 登録時 enforcement (wave3 時点で未実装と記録): walltime 事前予約検査 / WAL・成果物の永続領域
    allowlist (/scr 拒否) / PID canary probe / build cache の contract_sha256 namespace 分離 /
    実環境 attestation
  → **env_tag=Pegasus の登録は floor 実測 wave の前段作業** (calibrator を Pegasus 計算ノードで実走)。
    検証器本丸 wave と closure schema 裁定の後、floor を回す直前に行う
- **ユーザー指摘 (2026-07-18) — ログインノード ≠ 計算ノード:** 現セッションは pegasus02 =
  ログインノード上。calibration / clocks_per_us / numactl / noise floor は**計算ノード (bnodeXXX) の
  ジョブ (qsub) で取得する。ログインノードで取っても無意味** (別ハード + 割当ごとに変わる)。含意:
  - 計算ノードは全 node 同構成 (runbook §1: Xeon Platinum 8468 ×1 / 48 physical core / HT 無効)
    なので env_tag は `pegasus` 単一・契約 1 つで足りる**前提**。ただしこの前提は実行時に検証しないと
    割当変動・世代混在・BIOS/microcode 差・thermal throttle で黙って崩れ、異なる環境の測定を混ぜる
    (規律 1/4、D59「異なる env-tag の throughput を混ぜない」の実質破れ)
  - **現状の machine-pin / attestation は Pegasus に不十分**: execution_guard.assert_machine_pin は
    `contract.env_tag == p2_2.ENV_TAG` の文字列一致のみ、build_receipt の attestation は
    {hostname, boot_id, cpuset, captured_utc} の識別子記録のみで**実測照合をしない**
    (clocks_per_us / CPU model と実機の突合なし。runbook も「実環境 attestation は未実装」と明記)。
    cygnus は専有物理機で hostname 固定だったから文字列 pin で足りたが、**Pegasus は共有スケジューラで
    計算ノードが割当ごとに変動 + 専有非保証 (Exclusive submit=OFF) のため、実測照合 attestation が
    必須**: 割り当て計算ノードの実測 (CPU model / 実効クロック / core 数 / cache / NUMA) が登録契約と
    一致するかを floor/oracle 実行直前に検証し、不一致 = fail-closed
  - machine-pin (p2_2.ENV_TAG 文字列一致) を Pegasus 用に再設計 (文字列一致では実測照合にならない)
  - 専有非保証 → calibration も floor も割り当て計算ノード上で単独性確認 (pgrep) + 外乱回避/検知/
    再計測 (failures F3、memory verify-single-tenant-before-measuring)
  → env_tag=Pegasus の登録段は「値決め」でなく「計算ノード上の実測 + 実測照合 attestation の実装」。
    calibration の取得場所 (計算ノード) と実行時照合の設計を登録段で同時に固める

**検証器実装スコープの確定 (2026-07-18 ユーザー裁定):**
- **【申告リスト = 案A 確定】** v2 世代ファイルに `measurement_closure` 欄を新設 (前 wave C2-1/C2-4 の
  裁定どおり)。closure = `[{canonical_path, sha256}]` のみ (per-holdout の bool 予告は**全廃**)。
  hits_by_holdout は verifier が同一 bytes から導出し per-holdout 完全一致で照合 (自己申告 bool 不採用)。
  closure artifact は世代導入コミット G に同梱、approval/active は別コミット A (C2-3/C2-6)
- **【第2グループ = 承認】** 前 wave §5 (iii)〜(vii) を実装解釈として承認: 判定境界 (iii) / scale
  gate (iv) / protocol key に contract_sha256 を追加し 17→18 key (v) / active・revoked は検証 commit
  H 相対 (vi) / revoked successor の active 資格維持 (vii)。(i)(ii) は上記【申告リスト】で確定
- **【第3グループ = codex 推奨どおり確定】** (§8.5 各項目を codex の実際の推奨で確定):
  - full validate_protocol を launch acceptance で採用: P = canonical_sha256(**full_validate(
    strict_parse(floor_protocol blob)) の正規化戻り値**)。ハッシュ照合のみは「一貫だが未承認の別実験」を
    通すため不可 (V1 所見5)。protocol.freeze は V1 trust root へ明示 pin
  - journal / manifest は equality chain (§8.4) の**ハッシュ束縛で照合するが、導入 commit==G までは
    要求しない** (codex 推奨 = 前 wave (ii) の狭い範囲を超えないため)。manifest への mode 制約の裁定
    拡大もせず、ls-tree mode 100644/100755 の**検査** (symlink 偽装対策) のみ行う
  - cert bytes は期待 union に**非編入** + `hits(cert)==∅` を invariant 化 (Q-C)
  - crash 回復 = **L (launch-start のみ、build から再構築)** / **M (sealed manifest あり)** の二状態を
    定義し、launch-start-only も回復可能にする (V3 所見4)
  - one-shot = launch_validate で **generation_number==1 を強制** (reason certificate-generation-scope)。
    g2+ の静的 load は将来 schema のため維持
- **【限界の承認 (viii) = floor 実測直前に持ち越し】** certificate 以前の削除痕跡不可視 / ignored 領域
  scan 境界外 / 計測中 probe 時間窓 の受け入れは floor 前に最終承認 (実装は限界を docstring/保証表に明記)

**C2-2 検証側 (§5-(ix) として追認リストへ追加提案。裁定まで launch_validate は現状維持):**
- (ix)-1 journal 実体検証: floor_source と同 dir の journal.jsonl を G の regular blob として必須化し
  状態機械を検証、result.wall_ledger は raw journal からの決定的射影として照合 (自己申告排除)。
  equality chain: canonical_sha256(floor_protocol blob) == result.protocol_sha256 == journal
  campaign-start.protocol_sha256 == cert.protocol_sha256、v1/freeze hash 側も同型
- (ix)-2 cert anchor の lineage 条件: cert 導入 commit は非 merge・導入一意 (|I_cert|=1)・G の
  **厳密祖先** (同一 commit 不許可 — 同一 commit では「測定後に cert を後付け」と区別不能)。
  closure entry 側は全称条件 ∀i∈I_entry: anchor < i。rebase / 履歴書換え耐性は「検証 commit H 内の
  記録順のみ」という限界を明記 (強保証が要るなら署名 tag / 保護 remote 等の外部 anchor が別途必要)
- (ix)-3 closure 契約: 実 official campaign の manifest.json / result.json は holdout に実 hit する
  (in-memory 実証済み) ため、現行の「期待 hit = measurement_closure bytes のみ」導出では正直な
  official 実走が必ず拒否される。択: (a) 期待 hit を floor_protocol + floor_source + closure の
  union から導出 / (b) 「全 scan-hit artifact (manifest/journal/result 含む) を closure に必ず列挙」
  という契約を明文化。いずれも §5-(i) closure schema 裁定と同時に決める
- (ix)-4 cert の適用範囲: 現 schema の clean hit-0 cert は「v1→g1 の初回 official 一回限り」。
  二回目以降の official (再実測) を許すなら、active closure を baseline とした完全一致 + baseline
  digest 束縛の別 schema が必要
- (ix)-5 crash 回復: cert 発行後・campaign-start 前の crash は本 wave の launch-start journal で
  耐久化したが、その状態からの回復 (pre-start resume を許すか、cert 失効 + 再発行手順か) は未裁定
- (ix)-6 eligible_for_refreeze: 択 = field 廃止 / official 完走 finalize 時のみ true (provenance
  フラグ、B 推奨) / 非権威の診断 field と明記し verifier は別導出。裁定まで happy fixture 化しない
- (ix)-7 path 契約: floor_source.path は canonical root-relative + 正規 run layout (env_tag /
  s8b-floor-official / run-id 形式 / protocol hash prefix) 完全一致 + cert/result/journal は
  ls-tree mode 100644/100755 の regular blob 要求 (symlink blob 偽装の封鎖)
- (ix)-8 型伝搬: LaunchValidatedFreeze に検証済み floor artifact (bytes/hash/deep-immutable doc) を
  保持させ、oracle は再 parse せずそれを消費 (parser 分裂の fail-open 面を閉じる)
- (ix)-9 scan 除外の恒久設計: output/s8b-freeze/ の prefix 全除外は先行測定の隠し場所になる
  (本 wave は cert preflight 限定の exact allowlist で暫定封鎖)。恒久的には「既知宣言 artifact の
  exact path + bytes hash 免除」への移行を提案
- (ix)-10 §5-(ii) の機械強制: closure / floor_source の導入 commit == G (同時収録) を V1d に追加
- 運用 note: 過去 campaign 出力を output/env に commit すると official clean scan を恒久拒否し得る
  ((ix)-3/-4 の裁定と連動して baseline 設計を決める)。fixture は段階 builder base(clean) → C(cert)
  → G(result+closure+generation) → A(approval) へ再設計 (追認後、B8)。reason code 追加 (B10) も同時

**Lane A (guard_agent):**
- 再検証: 次回新規 bg セッションで daemon version 確認の上、model 無し Agent 呼び出しを再試験
  (拒否 = version drift だった / 素通り = bg surface の配送欠落)
- 素通りだった場合の機械的防衛候補 (いずれも副作用あり、適用はユーザー判断): permissions.deny で
  Agent 全面拒否 (orchestration 全停止) / CLAUDE_CODE_SUBAGENT_MODEL で子モデル強制 (named role の
  frontmatter ピンも上書き) / bg を使わない foreground 運用 / 絶対パス logger による
  SubagentStart/PostToolUse telemetry (検知のみ、予防ではない)
- worklog (8) の「hook 設定はセッション起動時 snapshot」という記述は現行 docs (live-reload) と
  不一致 — 本セッションでは snapshot/live-reload の切り分け実験は未実施 (どちらでも上記結論に影響なし)

## §6 相談逐語 (redacted 逐語 — 編集方針は冒頭)

### 相談 A (gpt-5.6-sol reasoning=max, read-only, cwd=worktree)

結論から言うと、現プランのままの実装開始は不可です。`must-fix` 8件、`should-fix` 2件です。特に Q-2 は将来懸念ではなく、現リポジトリですでに発火しています。

## 所見

1. {
   severity: `must-fix`  
   タイトル: 現リポジトリはすでに clean scan hit-0 ではない  
   攻撃シナリオ: 現在の `search_repository(ROOT)` を実行すると、`rr80` と `rr20` の双方が `orchestrator/tests/test_s8b_ratified_freeze.py` を conjunction hit として返す。D-1 を結線すれば、実 official は必ず certificate 発行前に拒否される。一方、計画中の統合テストは scan を stub 化するため、この本番不能を見逃す。  
   根拠: fixture が三軸を同一ファイルに直書きしている [test_s8b_ratified_freeze.py:166-168](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_freeze.py:166)。matcher は同一ファイル内の三軸一致で hit にする [s8b_holdout_freeze.py:270-282](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_holdout_freeze.py:270)。既存 clean-scan テストは検索結果を全て monkeypatch している [test_s8b_floor_campaign.py:1245-1262](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_floor_campaign.py:1245)。  
   提案: テスト fixture は `HOLDOUTS`/`concrete_axis_encodings` から実行時に組み立て、source file 自身には三軸 literal を同居させない。テストディレクトリを scan 除外してはいけない。さらに実 scan を通す repo invariant テストを追加する。
   }

2. {
   severity: `must-fix`  
   タイトル: `clean_scan_digest` の受理判定が malformed/inoperative report に fail-open  
   攻撃シナリオ: `search_repository` が回帰して `{"holdouts": {}, "positive_control": {"hit_count": 0}}` を返しても、ループは0回で終了し digest が返る。`rr20` だけ欠落した report や陽性対照が死んだ report でも certificate を発行できる。  
   根拠: 現実装は「存在する holdout」だけを走査し、holdout 集合・型・陽性対照を検査しない [s8b_floor_campaign.py:896-910](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:896)。必要な exact-name/zero-hit/positive-control 検査は既に `_assert_search_pass` にある [s8b_holdout_freeze.py:384-404](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_holdout_freeze.py:384)。これは F9 型の恒真ゲート。  
   提案: `clean_scan_digest` は `_assert_search_pass(report)` を必須通過させ、`FreezeError` を `FloorCampaignError` に翻訳する。欠落 holdout と陽性対照 0 の mutation test を置く。
   }

3. {
   severity: `must-fix`  
   タイトル: scan 対象と digest 対象が別列挙で、TOCTOU と意味不一致がある  
   攻撃シナリオ: `search_repository` が clean と判定した直後に、別プロセスが `ycsb_rratio⟦=⟧80 ycsb_zipf_skew⟦=⟧0.9 ycsb_rmw⟦=⟧0` を持つ untracked file を追加する。後段の列挙 digest はその filename を含むが、コードは再検索も集合一致検査もしないため certificate を発行する。さらに search は除外後の集合、digest は除外前の全集合を hash している。  
   根拠: search と digest が独立に列挙される [s8b_floor_campaign.py:902-910](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:902)。`search_repository` は `files` 注入を既に持ち、除外後集合を検索する [s8b_holdout_freeze.py:297-304](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_holdout_freeze.py:297)。既存 `launch_validate` は少なくとも列挙前後 digest を比較している [s8b_ratified_freeze.py:1283-1290](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:1283)。  
   提案: `files_before = enumerate...` → `search_repository(root, files=files_before)` → `files_after = enumerate...` → 完全一致要求、の順にする。digest は検索した正規化済み集合と match convention/search result を canonical に束縛する。内容 TOCTOU は single-tenant residual として明記する。
   }

4. {
   severity: `must-fix`  
   タイトル: 「scan hit 時 zero side effects」はプラン自身の順序と矛盾  
   攻撃シナリオ: 空の `out_root` で official gate だけを開け、dirty scan を返す。D-2 は先に `_fresh_run_dir` を呼ぶため、scan が拒否しても `out_root/env/.../s8b-floor-official/...` が残る。既存 zero-side-effect テストの `assert not out_root.exists()` と両立しない。  
   根拠: プランは run_dir 作成後に preflight と書く一方、テスト計画では zero side effects と記載する [.consult-c22-plan-v1.md:22-23](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:22)、[同:76-78](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:76)。実装は `mkdir(parents=True)` で親まで作る [s8b_floor_campaign.py:1864-1873](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1864)。既存テストも出力 root 不在を要求する [test_s8b_floor_campaign.py:500-516](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_floor_campaign.py:500)。  
   提案: `now_fn()` を1回だけ捕捉して候補 run ID/path を純粋計算し、scan 合格後に初めて `mkdir` と cert 発行を行う。あるいは「empty run_dir を残す」と明示して zero-side-effect 主張を削除する。
   }

5. {
   severity: `must-fix`  
   タイトル: D-5 は core の mode domain 未検証と path traversal を温存する  
   攻撃シナリオ: core を直接 `mode="pilot/../../../../../../escaped"` で呼ぶ。exact `"official"` ではないため拒否を通過し、raw mode が path に埋め込まれる。例えば `/safe/out/env/linux-baremetal/...` から `/escaped/<run-id>` へ解決でき、`out_root` 外へ書き出す。CLI の choices は core 直接呼出しを守らない。  
   根拠: core は exact official だけを拒否する [s8b_floor_campaign.py:1705-1715](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1705)。mode は無検証で path segment に入る [s8b_floor_campaign.py:1864-1870](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1864)。`choices` は CLI にしかない [s8b_floor_campaign.py:2001-2009](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:2001)。  
   提案: patchable な permission seam より前に、別の `_validate_mode(mode)` で exact `{"pilot", "official"}` を強制する。テストは permission helper だけを patch し、mode/path 検証は絶対に patch しない。
   }

6. {
   severity: `must-fix`  
   タイトル: `output/s8b-freeze/` の prefix 全除外が clean certificate の盲点になる  
   攻撃シナリオ: `output/s8b-freeze/prior_measurement.txt` を commit し、rr80 三軸を置く。tracked file なので列挙されるが prefix 除外され、clean certificate が発行される。v1/v2 generation を除外する必要性を利用して、任意の先行測定を同 namespace に隠せる。  
   根拠: 除外は directory 全体 [s8b_holdout_freeze.py:27-33](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_holdout_freeze.py:27)、判定は単純 prefix [s8b_holdout_freeze.py:232-233](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_holdout_freeze.py:232)。v2 resolver も未知の committed namespace file を無視する [s8b_ratified_freeze.py:969-973](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:969)。  
   提案: clean preflight 専用に「既知の宣言 artifact の exact path + bytes hash」だけを免除する。directory prefix の全面免除は禁止し、未知ファイルは hit 有無にかかわらず拒否する。
   }

7. {
   severity: `must-fix`  
   タイトル: 実 campaign 出力は closure fixture と異なり、manifest/floor_source 自身が hit する  
   攻撃シナリオ: official campaign を完走し、自然に `result.json` を `floor_source`、raw 計測物だけを `measurement_closure` に宣言する。実 `manifest.json` と `result.json` は rr80/rr20 の双方に hit するが、`launch_validate` の期待集合は `measurement_closure` の bytes だけから作るため、floor_source/manifest が未申告 hit になって拒否される。in-memory で実 `assemble_manifest` 形と result session 形を matcher に通し、双方が rr80/rr20 hit になることを確認済み。  
   根拠: cell workload は freeze の ycsb をそのまま持つ [s8b_floor_campaign.py:585-601](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:585)、manifest は全 cells を収録する [s8b_floor_campaign.py:845-866](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:845)、session/result も workload を保持する [s8b_floor_campaign.py:1250-1268](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1250)、[同:1528](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1528)。期待 hit は measurement closure 限定 [s8b_ratified_freeze.py:1271-1304](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:1271)。既存 fixture は floor_source に ycsb params を含めないよう明示しており、実分布を隠している [test_s8b_ratified_freeze.py:187-204](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_freeze.py:187)。これは F15 型のテスト代表性不足。  
   提案: expected hit を `floor_protocol + floor_source + measurement_closure` の union bytes から導出するか、result/manifest/journal を含む「全 scan-hit artifact を closure に必ず列挙する」契約を明文化する。実 `_result_bytes` と manifest bytes を使う統合テストが必要。
   }

8. {
   severity: `must-fix`  
   タイトル: cert 発行後・campaign-start 前の crash が回復不能状態を作る  
   攻撃シナリオ: clean scan と cert 発行に成功し、build/manifest 作成後、`_Runner.run()` の campaign-start append 前に crash する。manifest は既に holdout hit を持つ。resume は campaign-start 不在で拒否、fresh retry は manifest hit により clean scan で拒否される。削除以外に進路がなく、痕跡削除を誘発する。また完走済み closure が残る限り、二度目の fresh official も同じ hit-0 条件で必ず拒否される。  
   根拠: manifest は runner 起動前に書かれる [s8b_floor_campaign.py:1777-1823](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1777)。campaign-start は後段の `_Runner.run` で初めて書かれる [s8b_floor_campaign.py:1287-1300](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1287)。resume は campaign-start 不在を一律拒否する [s8b_floor_campaign.py:1934-1939](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1934)。production path は `output/env/...` で [layout.py:87-90](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/layout.py:87)、この領域は scan 除外されない。  
   提案: `launch-start` のような二相 journal marker を cert 直後に耐久化するか、`cert + sealed manifest + empty journal` を厳密検証して campaign-start を初回発行できる pre-start resume 状態を定義する。さらに本 certificate schema を「v1→g1 の一回限り」と明記する。再実測を許すなら hit-0 ではなく active closure を baseline とする別 schema が必要。
   }

9. {
   severity: `should-fix`  
   タイトル: D-4 の resume 検査は cert bytes hash だけで、cert の意味を再検証しない  
   攻撃シナリオ: partial official run directory を別名へ rename する。cert と journal は未変更なので bytes hash は一致し、D-4 案では resume が進む。しかし cert の `campaign_run_id` は旧 dirname のままで、後段検証で初めて拒否される。無効な official 測定を先に続行してしまう。  
   根拠: cert は protocol/freeze/run ID を持つ [s8b_floor_campaign.py:913-929](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:913)。プラン D-4 は存在と bytes hash 一致だけを要求する [.consult-c22-plan-v1.md:29-31](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:29)。現 resume API は run_dir/mode を受け取らない [s8b_floor_campaign.py:1925-1949](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1925)。  
   提案: exact-key/strict parse 後、schema、v1 freeze hash、protocol hash、UTC、`campaign_run_id == run_dir.name` を resume 前に照合する。pilot は journal key だけでなく cert file の存在も mode 混線として拒否する。
   }

10. {
    severity: `should-fix`  
    タイトル: Lane J protocol output の hit-0 は builder の型では保証されない  
    攻撃シナリオ: `master_seed="seed-ycsb_rratio⟦=⟧80 ycsb_zipf_skew⟦=⟧0.9 ycsb_rmw⟦=⟧0"`、他は golden 引数で builder を呼ぶ。この値は valid として canonical JSON に入り、matcher は protocol file を rr80 hit と判定する。実行確認では通常 golden は hit 0、この seed は rr80 hit 1だった。  
    根拠: master seed は non-empty string しか要求しない [s8b_floor_campaign.py:278-281](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:278)、builder も同様で、そのまま document に埋め込む [s8b_floor_campaign.py:406-410](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:406)、[同:438-460](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:438)。通常 golden bytes には三軸がない [test_s8b_protocol_builder.py:45-60](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_protocol_builder.py:45)。  
    提案: protocol 凍結時に canonical bytes 自身を `holdout_conjunction_hits` へ通して hit 0 を要求する。代替は master seed/stock ID を slug/hex grammar に制限する。
    }

## Q-1 への直接回答

裁定案は「D-5 の private test seam を採用」です。helper 単体テストだけでは、D-1〜D-4 の実結線が一度も実行されず、F9/F21 型の恒真保証になります。

ただし条件があります。

- patchable な `_assert_official_permitted` は official 拒否だけを担う。
- exact mode 検証と path safety は別関数で先に実行し、統合テストでも patch しない。
- CLI 拒否と、unpatched core の zero-write 拒否テストを残す。
- production flag、環境変数、公開引数による bypass は作らない。
- monkeypatch は1テストの局所 scope に限定する。

Python process 内で任意コードを実行できる主体は既存関数も差し替え可能なので、private helper 抽出自体は新しい実質的信頼境界を開きません。問題は「その seam が mode/path 検証までまとめて無効化する」設計です。

## Q-2 への直接回答

裁定は次のとおりです。

- 通常の Lane J golden protocol は conjunction hit しません。ただし builder の valid output 全体については保証されず、自由文字列で hit を作れます。
- protocol/v1/v2 generation を `output/s8b-freeze/` に置けば、現 scanner は prefix 全除外するため、それら自身は発行を妨げません。その代わり同 namespace が先行測定の隠し場所になります。
- 過去 campaign 出力は `output/env/...` に置かれ、除外されません。manifest、journal、result は実際に holdout hit になります。
- hit-0 と宣言済み closure hit は、時間軸を分ければ両立します。初回 official の直前は hit 0、実走後は `launch_validate` が hit 0 を要求せず、現 hit と closure 由来 hit の完全一致を要求しています [s8b_ratified_freeze.py:1228-1231](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:1228)、[同:1293-1304](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:1293)。

したがって現 schema の `clean hit-0` certificate は「v1→g1 の初回一回限り」と裁定すべきです。二回目以降を許すなら、active closure を baseline として完全一致を要求し、その baseline digest を束縛する別 certificate schema が必要です。また closure は manifest/journal/result/floor_source を含む全 scan-hit path を閉じなければなりません。

## 確認済み事項

- launch certificate scaffold は create-only で、実際に書いた bytes の SHA-256 を返す [s8b_floor_campaign.py:870-880](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:870)、[同:932-935](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:932)。
- D-2 が使う `freeze_sha256` は protocol の freeze hash と事前照合済み [s8b_floor_campaign.py:1746-1753](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1746)。
- preflight を fresh branch の `build_cells` 前へ置く方針自体は正しく、build/measure 前拒否を実現できる [s8b_floor_campaign.py:1777-1785](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1777)。
- campaign-start への追加 field は `wall_ledger` に全フィールドごと伝播する [s8b_floor_campaign.py:1492-1495](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1492)。
- resume の campaign-start 一意性と protocol/freeze/manifest hash 検査は既にあり、cert 検査の挿入点として妥当 [s8b_floor_campaign.py:1934-1949](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1934)。
- CLI と core の official 二重拒否は現状独立している [s8b_floor_campaign.py:1711-1715](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1711)、[同:2029-2036](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:2029)。
- scan は tracked regular files、非 ignore の untracked files、ccbench submodule regular filesを列挙する設計で、file-level conjunction の定義もコードと文言が一致している [s8b_holdout_freeze.py:90-99](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_holdout_freeze.py:90)、[同:179-212](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_holdout_freeze.py:179)。
- official journal がリポジトリ内に存在しない現状では、pilot の key 不在を維持し mode 混線を明示拒否するなら、JOURNAL_SCHEMA 据置は妥当です。
### 相談 B (gpt-5.6-sol reasoning=max, read-only, cwd=worktree)

結論: このままの実装開始は不可です。must-fix 7件、should-fix 3件。D-9 が証明できるのは「捕捉した H の DAG 上の blob 導入順」だけで、実測順序・raw journal 由来・履歴書換え耐性までは証明しません。

## 所見

1. {severity: must-fix, タイトル: D-6 は「journal 束縛」を自己申告 wall_ledger へ弱めている}

- 攻撃シナリオ: `result.json` に `mode="official"` と、`wall_ledger=[{"event":"campaign-start","launch_certificate_sha256":H}]` を直接書く。raw `journal.jsonl` は G に一切入れず、cert C の後に任意の測定 artifact B を追加して closure に載せる。D-6 は campaign-start 1件と H を取得でき、D-9 も `C < B` で通るが、journal が H を記録した事実も、B がその campaign の出力であることも証明されない。
- 根拠: 裁定は「journal が certificate hash を束縛、closure は certificate 起点 lineage から導出」とする一方、プランは result 内の projection だけを読む（[裁定:516](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:516)、[プラン:45-59](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:45)）。`assemble_result` は journal record を単に `dict(r)` で複写するだけ（[s8b_floor_campaign.py:1492-1495](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1492)）。既存 verifier 自身も raw session/journal の真正性を保証しないと明記する（[s8b_floor_stats.py:434-442](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_stats.py:434)）。
- 提案: 同一 run directory の `journal.jsonl` を G の regular blob として必須化し、campaign-start・terminal・attempt/receipt の状態機械を直接検証する。result の wall_ledger は raw journal からの完全な決定的射影として照合し、closure 各 entry は journal receipt または確定した出力 inventory から機械導出する。単なる Git 祖先関係を「lineage」と呼ばない。

2. {severity: must-fix, タイトル: D-9 の「同一 commit 可」は順序証明を消滅させる}

- 攻撃シナリオ: 未申告測定を先に行い、その後 cert、result、closure artifact、generation JSON をすべて G に押し込む。cert hash を result の wall_ledger に合わせれば、cert と closure の導入 commit はともに G。D-9 の `anchor と同一または子孫` を満たし、cert が測定後に作られたことを検出できない。
- 根拠: `_immutable_introductions` の導入とは「present かつ全 parent で absent」であり、同じ G に追加された二 path は同じ導入 commit を返す（[s8b_ratified_freeze.py:322-347](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:322)）。create-only は発行側の filesystem 操作にすぎず、後日の Git blob から実行時刻を証明できない（[s8b_floor_campaign.py:870-880](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:870)、[同:932-935](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:932)）。
- 提案: `anchor` は G の厳密な祖先、すなわち `anchor != G ∧ is_ancestor(anchor,G)` とする。運用上 cert を別 commit にできないなら Git ancestry は証明手段として不適格なので、測定前の署名済み tag、保護 remote、または append-only 外部台帳を anchor にする。

3. {severity: must-fix, タイトル: 複数導入の量化が未定義で、削除再導入・merge・rebase に選択的 bypass が残る}

- 攻撃シナリオ:
  - closure を C0 で追加→削除→cert を C1 で追加→同一 bytes の closure を C2 で再導入する。後側 C2 だけ選べば祖先条件を通る。
  - 二枝で同一 cert bytes を add/add して merge する。どちらを anchor にするかで結果が変わる。
  - closure-before-cert の履歴を rebase/squash して cert-before-closure に作り直す。検証時 H からは旧順序が不可視になる。
- 根拠: 関数は単一 commit でなく tuple を返し、同一 bytes の削除→再導入を明示的に許す（[s8b_ratified_freeze.py:325-347](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:325)）。既存テストも2導入と merge add/add を確認している（[test_s8b_ratified_freeze.py:508-559](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_freeze.py:508)）。履歴集合は `rev-list H` の到達可能 commit だけ（[s8b_ratified_freeze.py:282-292](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:282)）。
- 提案: `|I_cert|=1` を要求し、merge anchor を拒否する。§5-ii を採るなら closure は各 entry について `I_entry == {G}` とする。採らない暫定案でも、全導入に対する全称条件 `∀i∈I_entry: anchor<i` が最低線。rebase 耐性は得られないため、「H 内の記録順のみ」という限界を§5へ明記し、強い保証には外部 immutable anchor を要求する。

4. {severity: must-fix, タイトル: D-9 は裁定済みの「closure を G に同時収録」を実装しない}

- 攻撃シナリオ: cert を C、closure を E、generation を後の G に置く。`C<E<G` なので D-9 は通り、現行 V1d も G tree に同じ blob が存在するため通る。しかし closure の導入は G ではなく、裁定の発効トポロジー違反。
- 根拠: 裁定は G に「世代 file + closure artifact を同時収録」と要求する（[裁定:520](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:520)、[同:561-563](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:561)）。現行コードは G に blob が見えることしか検査せず、導入 commit == G を要求しない（[s8b_ratified_freeze.py:789-807](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:789)）。共有 fixture も closure/source を base に置き、G では generation JSON だけを追加している（[test_s8b_ratified_freeze.py:222-240](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_freeze.py:222)、[同:262-266](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_freeze.py:262)）。
- 提案: §5-ii 追認後、少なくとも `floor_source(result)` と全 `measurement_closure` entry の一意な導入 commit を G に固定する。cert は G の厳密な祖先とする。

5. {severity: must-fix, タイトル: dirname ベース D-8 は canonical path と regular-file 性を証明しない}

- 攻撃シナリオ:
  - `floor_source.path="./output/rogue/run-x/result.json"` とし、同じ任意 directory に自己整合した cert を置く。basename/run-id 比較は攻撃者が選んだ path と攻撃者が選んだ field の循環比較になる。
  - cert path を mode `120000` の Git symlink にし、その link-target blob bytes 自体を certificate JSON にする。Git symlink object は blob なので `_blob_at_or_fail` は parse でき、wall_ledger hash も一致する。実際の create-only regular JSON file は存在しなくても通る。
- 根拠: `floor_source.path` は非空文字列しか要求せず、正規 path や layout を検査しない（[s8b_ratified_freeze.py:697-705](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:697)）。`_blob_oid_at` は object type `blob` のみを見て tree mode を見ない（[同:462-473](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:462)）。正規の run layout は `output/env/<env>/calibration/s8b-floor-official/<UTC>-<protocol-prefix>`（[s8b_floor_campaign.py:1864-1868](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1864)）。symlink inventory は列挙するだけで拒否しない（[s8b_ratified_freeze.py:1207-1225](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:1207)）。
- 提案: issuer/verifier 共通の path parser を作り、POSIX root-relative canonical path、basename=`result.json`、env_tag、`s8b-floor-official`、run-id形式、protocol hash prefixを完全一致させる。cert/result/journal は `ls-tree` mode `100644` または `100755` の regular blob を要求する。UTCはrun-idと同一の一度だけ捕捉した時刻から生成する。

6. {severity: must-fix, タイトル: result→journal→cert→protocol/freeze の結合が不完全}

- 攻撃シナリオ: result に `protocol_sha256=P, freeze_sha256=X`、campaign-start に `protocol_sha256=Q, freeze_sha256=Y`、cert に `protocol_sha256=P, v1_freeze_sha256=V1` を書く。さらに cert の `clean_scan_digest=null, started_utc=[]` とする。D-8 が列挙した検査はすべて通るが、実 journal、実 protocol、実 freeze、clean scan、UTCが相互に一致しない。
- 根拠: certificate builder は6 fieldを出すが入力 validation はない（[s8b_floor_campaign.py:913-929](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:913)）。production campaign-start は protocol/freeze/manifest を持つ（[同:1287-1300](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1287)）。result にも別に protocol/freeze/manifest がある（[同:1497-1510](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1497)）。実 run の protocol hash は parsed protocol の canonical hash（[同:152-153](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:152)、[同:1761](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1761)）だが、現行 generation verifier は floor_protocol を parse するだけ（[s8b_ratified_freeze.py:808-810](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:808)）。
- 提案: cert は exact 6 keys、clean digest=64 lower-hex、started_utc=canonical UTC、run-id非空を要求する。さらに  
  `canonical_sha256(floor_protocol) == result.protocol == journal-start.protocol == cert.protocol`、  
  `V1 == result.freeze == journal-start.freeze == cert.v1`、  
  `result.manifest == journal-start.manifest`  
  を完全一致させる。result の top-level schema・型・wall_ledger shapeも exact に定義する。

7. {severity: should-fix, タイトル: D-6 で検証した floor artifact が oracle に引き渡されない}

- 攻撃シナリオ: launch_validate に strict result parserを追加しても、戻り値にはその document が無い。oracle は戻り値を捨て、同じ blob を permissive `json.loads` で再parseして binaries を消費する。現在は G blob が immutable なので直接TOCTOUではないが、「検証済み objectだけを実走へ渡す」型保証が成立せず、parser差分が将来の fail-open 面になる。
- 根拠: `LaunchValidatedFreeze` は floor artifactを保持しない（[s8b_ratified_freeze.py:604-615](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:604)）。oracle は `launch_validate()` の戻り値を捨て（[s8b_oracle_driver.py:463-476](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_driver.py:463)）、後で再読込・再parseする（[同:402-446](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_driver.py:402)）。
- 提案: `VerifiedFloorArtifact` を作り、raw bytes/hash/deep-immutable documentを `LaunchValidatedFreeze` に保持する。`_prepare_v2_execution` は戻り値を受け取り、その objectから binaries と inventory を消費する。

8. {severity: should-fix, タイトル: fixture 更新は「全面手修正」ではないが、commit topology の再設計が必要}

- 攻撃シナリオ: stubを単にofficial resultへ置換すると、closureがcert以前のbase commitにあるため、既存の `closure-hit-mismatch` 負例が先に `closure-predates-certificate` で落ちる。oracle fixtureも productionの `schema` ではなく `schema_version` しか持たず、store系テストがcertificate/schema拒否で早期終了する。
- 根拠: 共有 helper は floor source stubとclosureをbaseに置く（[test_s8b_ratified_freeze.py:169-170](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_freeze.py:169)、[同:222-240](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_freeze.py:222)）。verify側の直接 launch_validate は7箇所（代表: [test_s8b_ratified_verify.py:39-47](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_verify.py:39)、[同:227-320](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_verify.py:227)）。oracleの独自 artifact は `{schema_version,binaries}`（[test_s8b_oracle_driver.py:1268-1307](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_driver.py:1268)）。
- 提案: 中央fixtureを `base(clean) → C(cert) → G(result+closure+generation) → A(approval)` の段階builderにする。valid official result documentへの mutation hookを用意し、raw `floor_source_bytes` 差替えを主APIにしない。静的検索では呼出し19箇所・3ファイルだが、主要変更点は共有helperとoracle helperの2箇所。工数は中程度。ただし各負例の「最初に発火すべき reason」を再確認する必要がある。

9. {severity: must-fix, タイトル: 「schema変更なし」は§5追認待ち領域へ進んでよい根拠にならない}

- 攻撃シナリオ: D-9の同一commit可・複数導入解釈をテストで固定した後、ユーザーが§5-iiを「closureはGで一意、certはGより前」と追認すると、既に実装したacceptance contractが裁定と逆になる。検証追加はschema bytesを変えなくても、受理集合を変更する規範実装である。
- 根拠: §5-(i)/(ii) は明示的に追認待ち（[裁定:593-606](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:593)）。D-9自身も未裁定の(ix)追加案である（[プラン:55-59](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:55)）。現行コードには既に exact header と measurement_closure が実装されている（[s8b_ratified_freeze.py:69-79](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:69)、[同:668-684](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:668)）が、これは追加実装への白紙委任ではない。
- 提案: §5-(i)/(ii)に加え、新しい(ix)「cert anchorとGの厳密祖先関係・導入集合の量化・履歴書換え限界」を先に追認する。pure parser/helperの準備は可能だが、`launch_validate`の受理条件とnormativeテストは追認後に結線する。

10. {severity: should-fix, タイトル: D-10 の reason code 表が実際の失敗面を閉じていない}

- 攻撃シナリオ: floor_sourceを壊れたJSONにする、certにduplicate keyを入れる、certを削除→同一bytes再導入する、pathを非正規にする。既存helperをそのまま使うと `bad-json`、`json-duplicate-key`、`multiple-introduction` 等が漏れ、D-10列挙のどれにもならない。
- 根拠: `_strict_load` は複数の低レベルreasonを送出する（[s8b_ratified_freeze.py:221-248](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:221)）。複数導入にも既存reasonがある（[同:427-435](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:427)）。D-10は5種類のみ（[プラン:60-61](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:60)）。
- 提案: 少なくとも `floor-source-invalid`、`launch-certificate-invalid`、`launch-certificate-path-invalid`、`certificate-lineage-ambiguous` を追加する。低レベルparse reasonをcauseとして保持し、外向きreasonは閉じた表へ翻訳する。

## Q-3〜Q-6 裁定案

**Q-3:** official 解禁後は `eligible_for_refreeze` を「official経路で完走し、artifact自己検査を通ってfinalizeされた」というprovenanceフラグに限定する。pilot=false、official finalized=true。`launch_validate` は `mode=="official"` と `eligible_for_refreeze is True` の両方を整合検査するが、このbool自体を証拠にはしない。floorが非null等の品質意味まで持たせるなら別裁定が必要。

**Q-4:** 同一commitは不許可。certは一意・非mergeのanchor commit C、`C` は `G` の厳密祖先。§5-ii採用後は各closure/floor_sourceの導入集合を `{G}` に固定する。certの複数導入、merge add/add、削除再導入は拒否。rebase耐性まで主張するなら外部immutable anchorが必要。

**Q-5:** 無条件強制。すべての `RatifiedFreeze` の実走昇格で、floor_sourceがexact official resultでなければ拒否する。stubや「parseできる場合だけ」の互換分岐は明確なfail-open。

**Q-6:** 越権になる。D-9、G同梱、同一commit可否、複数導入裁定は受理意味論そのものであり、単なるschema非変更ではない。§5-(i)/(ii)と新(ix)、Q-3/Q-4を追認してからnormative実装へ進むべき。D-6〜D-8のpure helper準備はできるが、official発効・完了扱いは不可。

## 確認済み事項

- `launch_validate` は現在certificate検証を明示的に行わない（[s8b_ratified_freeze.py:1240-1260](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:1240)）。
- v2 headerはexact集合で、未知top-level keyは拒否される（[同:69-79](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:69)、[同:680-684](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:680)）。
- `read_floor_source_blob` はG treeから読み、記録sha256を照合する（[同:1146-1164](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:1146)）。
- cert scaffoldingは6 field・create-onlyだが未結線（[s8b_floor_campaign.py:883-935](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:883)）。
- `assemble_result` はcampaign-startを全fieldごと複写し、`eligible_for_refreeze=False`を定数出力する（[同:1492-1509](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1492)）。
- 現行fixtureのfloor_sourceはstub、closureはG以前、oracle独自artifactもproduction result schemaではない。
- oracleはlaunch検証済みobjectを保持せずfloor_sourceを再読込する。
- HEAD treeの `output/s8b-freeze/` はv1 fileのみで、実v2世代・approval・active pointerは存在しない。
- コード変更・テスト実行はしていない。指定範囲のread-only設計監査のみ。
### 相談 C (gpt-5.6-sol reasoning=max, read-only, cwd=worktree)

結論: 現状のままの実装着手は不可です。無改変の production 経路は official を拒否し続けるため「直ちに実 artifact が発効する」穴はありませんが、certificate–journal–closure の証明鎖と dormant テストに恒真化できる穴が残っています。

1. `{severity: must-fix, タイトル: ユーザー追認より先に B-II を固定すると手戻りが確定する}`

   攻撃シナリオ: ユーザーが §5-(i)/(ii)、同一 commit 可否、無条件適用、`eligible_for_refreeze` のどれかを否認すると、D-6〜D-10、fixture の全面改造、reason code、lineage テストを作り直す。プラン自身が Q-3〜Q-6 を未決のまま残している。

   根拠 file:line: [.consult-c22-plan-v1.md:55-72](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:55)、[consultations §5:593-606](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:593)、[worklog:509-513](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/worklog.md:509)

   提案: 今実装してよいのは、既存 official 拒否の負例、clean-scan の陽性対照、strict cert parser、tmp-only fixture など判断非依存の防壁まで。D-6〜D-10、happy fixture の新意味論、§5-(ix) 追加はユーザー追認後へ送る。

2. `{severity: should-fix, タイトル: 発効境界は保つが「machinery + テストのみ」という文字どおりのスコープではない}`

   攻撃シナリオ: プランは同じ wave で `hooks/README.md`、`docs/failures.md`、memory、worklog を変更するため、変更種別としては machinery + tests を超える。また patched official 統合テストの `out_root` を誤ると、実 repo の `output/env` に real-shaped cert/run artifact を作れる。

   根拠 file:line: [scope declaration:13-15](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:13)、[Lane A writes:93-95](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:93)、[wave scope:8-10](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:8)、[既存 tmp-only 規約:4-6](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_verify.py:4)

   提案: Lane A を別 wave/commit に分離するか、scope を「machinery + tests + limit documentation」に明記する。全 bypass テストは `tmp_path` の repo/root/out_root を必須にし、実 `output/s8b-freeze` と `output/env` の前後 tree 不変を検査する。

3. `{severity: must-fix, タイトル: journal 束縛が journal ではなく result の自己申告を見ている}`

   攻撃シナリオ: 攻撃者が `mode=official` の result に任意の `wall_ledger.campaign-start.launch_certificate_sha256` を書き、同じ hash の cert を添える。実 `journal.jsonl` が存在しなくても D-6〜D-8 は整合する。「通常 assembler が journal からコピーする」は provenance の証明にならない。

   根拠 file:line: [D-6:45-48](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:45)、[wall_ledger copy:1492-1495](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1492)、[`verify_floor_artifact` の保証外:438-442](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_stats.py:438)

   提案: `floor_source` と同じ directory の `journal.jsonl` を G tree から読み、immutable introduction・bytes hash・JSONL 状態機械を検証する。result の `wall_ledger` はその journal から再導出して完全一致させる。少なくとも「cert/result は一致するが journal 不在」「journal と result の campaign-start が不一致」を拒否するテストが必要。

4. `{severity: must-fix, タイトル: cert と closure の同一 commit を許すと時間順序を証明できない}`

   攻撃シナリオ: 計測を済ませた後で cert と closure artifact を作り、両方を G に一括 commit する。D-9 は同一 commit を許すため合格するが、「cert が official 開始時に存在した」ことは履歴から区別できない。さらに `_immutable_introductions` は削除後の同一 bytes 再導入を複数 anchor として返すため、どの anchor を使うかでも判定を操れる。

   根拠 file:line: [D-9:55-59](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:55)、[Q-4:65-66](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:65)、[_immutable_introductions:322-347](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:322)、[複数導入を許す既存テスト:508-521](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_freeze.py:508)

   提案: temporal proof を謳うなら cert の導入 commit を一意にし、全 closure introduction の厳密祖先にする。batch commit を維持するなら、Git lineage は「artifact 集合の同梱」しか証明しないと保証を縮小し、別の append-only/WORM anchor を置く。複数導入、兄弟 branch、pre/post 両方の導入、向きを反転した祖先判定を負例にする。

5. `{severity: must-fix, タイトル: clean scan は空集合で通る恒真ゲートであり snapshot にもなっていない}`

   攻撃シナリオ: `search_repository()` が `{holdouts:{}}`、holdout 欠落、`conjunction_hits=None` を返すとループは拒否せず digest を発行する。rr50 陽性対照も検査しない。また search 後に別途ファイル名だけを列挙するため、走査中の内容差替えや名前集合の往復も検出しない。

   根拠 file:line: [clean_scan_digest:896-910](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:896)、[既存の正しい陽性対照検査:384-404](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_holdout_freeze.py:384)、[B-III は hit だけ:76-78](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:76)、[F9:88-100](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/failures.md:88)

   提案: exact `HOLDOUTS` 集合、各結果の型、hit 空、rr50 positive control > 0 を共通 validator で強制する。列挙を `before → search(files=before) → after` で挟む。mock だけでなく tmp git repo 上の実 `search_repository` positive control を1本入れる。内容 TOCTOUを受容するなら cert の保証文にも限界を明記する。

   なお `output/env` は scan 対象で、floor artifact はそこへ出るため、過去の holdout pilot artifact は official を意図的に永久拒否し得る。[除外は freeze のみ:28-32](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_holdout_freeze.py:28)、[run_dir:1864-1869](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1864)。これを「正しい prior-measurement 検出」とするのか、別 baseline を設けるのかをテストで固定すべき。

6. `{severity: must-fix, タイトル: scan-hit zero-side-effect と実際の発行順が矛盾し、失敗時には orphan cert が残る}`

   攻撃シナリオ: D-2 は run_dir 作成後に preflight を呼ぶため、scan hit でも directory が残り、「zero side effects」テストは成立しない。さらに cert 発行後、build/store/manifest が失敗すると campaign-start がまだ書かれておらず、journal に束縛されない create-only cert だけが残る。

   根拠 file:line: [D-2:22-25](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:22)、[B-III の主張:76-78](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:76)、[fresh 順序:1777-1794](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1777)、[campaign-start は後段:1817-1831](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1817)

   提案: run id の計算と mkdir を分離し、scan は mkdir より前に行う。cert 発行後の各 failure point について、certified-attempt/refusal journal を残すか、orphan cert を正式な失敗 artifact とするかを決める。scan/build/store/manifest/journal failure の注入テストを置く。

7. `{severity: must-fix, タイトル: resume は cert の bytes hash しか見ず、意味論を再検証しない}`

   攻撃シナリオ: cert の `v1_freeze_sha256`、`protocol_sha256`、run id、schema を改変し、その新 bytes hash を campaign-start に書き直す。D-4 の条件は満たすため、無効な cert のまま計測を再開できる。D-8 が後で拒否しても測定後では遅い。

   根拠 file:line: [D-4:29-31](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:29)、[D-8 の完全検査:52-54](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:52)、[F2 の validator 分裂教訓:28-34](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/failures.md:28)

   提案: exact parse と field cross-check を行う単一 `validate_launch_certificate(...)` を fresh、resume、ratified verifier で共有する。resume 負例は「cert だけ改変」だけでなく「cert と journal hash を整合して同時改変」を必須にする。

8. `{severity: must-fix, タイトル: protocol–result–journal–cert の束縛鎖が閉じていない}`

   攻撃シナリオ: cert と result の `protocol_sha256` を同じ攻撃者値へ変更し、G の `floor_protocol` blob は別物のままにする。D-8 は cert==result だけなので合格する。同様に result の `freeze_sha256` は cert の固定 v1 hashと照合されない。さらに `floor_source.path` は現状 non-empty string しか要求せず、任意 namespace から cert path を導出できる。

   根拠 file:line: [D-8:51-54](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:51)、[floor_protocol は parse のみ:789-810](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:789)、[result hashes:1505-1509](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1505)、[source path 検査:697-705](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:697)

   提案: 次を一本の equality chain として検査する: `sha256(floor_protocol G blob) == result.protocol_sha256 == actual journal campaign-start.protocol_sha256 == cert.protocol_sha256`。v1 hash も result/journal/cert/定数で一致させる。floor_source は canonical root-relative path、公式 run namespace、ratified env_tag と一致する directory pattern を要求する。

9. `{severity: must-fix, タイトル: official happy path が eligible_for_refreeze=False を正例化する}`

   攻撃シナリオ: dormant official 経路は現行 assembler により `eligible_for_refreeze: false` を出すが、D-7 は `mode=="official"` だけを要求する。happy path がこれを受理すると、field が嘘でも無視する契約を固定するか、将来の official artifact が恒常的に ineligible になる。

   根拠 file:line: [D-7:49-50](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:49)、[Q-3:63-64](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:63)、[定数 False:1497-1504](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1497)

   提案: 実装前に三択を裁定する: field 廃止、official 完走時だけ true、または非権威な診断 field と明記して verifier は別の導出条件を使う。未裁定のまま happy fixture を作らない。

10. `{severity: must-fix, タイトル: critical attack matrix が trust root 不在時に全 skip できる}`

   攻撃シナリオ: 実 v1 freeze が改名・欠落すると `_need_v1()` が `pytest.skip` し、certificate matrix を含む verifier の主要統合テストが緑扱いになる。F9 と同じ「対象が消えると検査も消える」型。

   根拠 file:line: [_need_v1:27-32](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_verify.py:27)、[happy path:39-47](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_verify.py:39)、[F9 再発記録:88-100](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/failures.md:88)

   提案: trust-root file は「無ければ fail」にするか、bytes を hermetic fixture として固定する。少なくとも新 certificate matrix は skip 条件を継承しない。

11. `{severity: must-fix, タイトル: writer と verifier の別々の stub テストでは dormant 結線を証明できない}`

   攻撃シナリオ: 発行テストは monkeypatch した official core、検証テストは手書き `floor_source_bytes` でそれぞれ緑になるが、production `assemble_result` の出力と verifier parser が相互運用しない。あるいは oracle から `launch_validate` 呼出しを削除しても直接テストは緑のまま。

   根拠 file:line: [B-III:76-82](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:76)、[stub fixture:187-204](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_freeze.py:187)、[直接 happy path:39-45](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_verify.py:39)、[oracle consumer:463-470](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_driver.py:463)、[F15:141-152](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/failures.md:141)、[F19:214-229](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/failures.md:214)

   提案: tmp repo 内で一本の E2E を置く。production dormant coreで cert/journal/result を生成 → exact bytes を G に収録 → approval/active fixture → `load_ratified_freeze` → `launch_validate` → oracle preflight まで通す。mock は official refusal seam、measure、重い build 境界に限定する。oracle の `launch_validate` call 除去 mutation も殺す。

12. `{severity: must-fix, タイトル: 変異スポット2件では信頼境界を覆えていない}`

   攻撃シナリオ: D-9 と binding 比較だけは生きていても、scan 呼出し、陽性対照、journal 実体、resume、official 二重拒否、consumer 呼出しのどれかが消えている。現行2変異は「局所比較がある」ことしか証明しない。

   根拠 file:line: [提案変異2件:82](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:82)、[前 wave の信頼境界別方針:545](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:545)、[F9 positive control 教訓:92-100](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/failures.md:92)

   提案: 最低限、次の変異を掛ける。

   - 発行: official core guard 除去、preflight を build/measure 後へ移動、clean scan 呼出し除去、scan root 取り違え、create-only を overwrite 化、cert bytes でなく再直列化 hash を使用。
   - scan: holdouts 空/1件欠落、positive control 0、hit 条件反転、HEAD cache 化、search 前後で file 追加・内容差替え。
   - journal/resume: actual journal 不在、result wall_ledger のみ偽造、cert+campaign-start hash の同時改変、campaign-start 0/2件・先頭でない、pilot/official cross-resume。
   - parser/binding: duplicate key、NaN、非UTF-8、extra/missing key、bad 64hex、非UTC時刻、cert+result protocol の同時改変、floor_protocol/freeze との鎖切断、非正規 path/別 namespace。
   - lineage: 祖先判定反転、同一 commit 許否反転、兄弟 branch、cert 複数導入、closure の pre-cert 導入後 delete/re-add、immutable-history 検査除去。
   - consumer/scope: oracle の `launch_validate` 呼出し除去、v1 欠落を skip、実 `output/env` 書込み、cert 発行後の build/store/manifest failure、official なのに eligible false。

13. `{severity: should-fix, タイトル: Lane A は観測事実から内部原因まで断定している}`

   攻撃シナリオ: 「この bg harness では Agent の PreToolUse が発火しなかった」は観測できても、「非同期 Agent が PreToolUse を通さないことが原因」は dispatch trace なしでは推論である。原因断定を failures 台帳へ入れると、別 runtime でも同じ説明を転写する F16 型になる。

   根拠 file:line: [plan:86-95](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:86)、[直前 worklog の live 確認残:533-536](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/worklog.md:533)、[F16:154-165](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/failures.md:154)

   提案: docs/failures には「当該 bg surface で不発、内部原因未確定」と記録する。fresh runtime の positive/negative control と tool-dispatch evidence が取れた時だけ原因を確定する。

## (1)〜(5) への直接回答

1. スコープ規律: 無改変の実行経路は適合しています。CLI と core の二重拒否は現存し、既存テストも拒否と `out_root` 不生成を固定しています。[core:1711-1715](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1711)、[CLI:2030-2036](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:2030)、[tests:490-516](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_floor_campaign.py:490)。実 approval/active/v2/protocol を生成する通常経路はプランにない。ただし patched test の tmp-only 条件が未明記で、D-2 の scan-hit は空 run_dir を残す。Lane A docs/memory は文字どおりの「machinery + tests」外なので分離が必要です。

2. 今実装する順序: 正しくありません。worklog の正本は「ユーザー接点で追認 → その後 protocol 凍結・floor」の順です。D-6〜D-10、Q-3〜Q-6、§5-(ix)、fixture 全面更新は追認後にすべきです。今進められるのは判断非依存の fail-closed parser、positive control、拒否負例、tmp-only E2E harness までです。

3. 恒真リスク: 高いです。主因は、`_need_v1()` の全 skip、wall_ledger 自己申告、発行側と検証側の別 fixture、monkeypatch seam だけの成功、oracle consumer E2E 不在、clean scan の陽性対照不在です。seam 抽出自体は許容できますが、private/test-only、runtime flag 無し、既存 CLI/core 拒否負例維持、一本の production-bytes E2E が条件です。helper 単体だけに退く案はさらに悪いです。

4. 変異スポット: 所見12の6群を最低セットとします。特に必須なのは「scan 呼出し除去」「空 holdouts」「cert+wall_ledger の整合同時偽造」「actual journal 不在」「cert+result protocol 同時偽造」「同一/兄弟/multiple-introduction lineage」「oracle call 除去」「v1 欠落 skip」「実出力 path 誤爆」です。D-9除去とbinding除去の2件だけでは不足です。

5. 過去失敗型の再発面:

   - F2 `[ドリフト]`: fresh/resume/verifier で cert validator が分裂。
   - F7 `[権限逸脱]`: patched test の実 filesystem 書込みを prompt 規律だけに依存。
   - F9/F14 `[恒真ゲート]`: v1 欠落 skip、空 scan、monkeypatch 成功を実防壁と誤認。
   - F15 `[テスト代表性]`: handwritten floor_source stub が production result/journal 分布を表さない。
   - F16/F17 `[恒真ゲート][権限逸脱][ドリフト]`: field/call の存在や自己申告 wall_ledgerを runtime lineage の証明と誤認。
   - F19 `[手順漏れ]`: build/manifest failure 後の orphan cert を stubbed happy pathが踏まない。
   - Lane A の原因断定には F8/F16 型の「観測以上の説明を確定する」再発面があります。
### 相談 D (gpt-5.6-sol reasoning=high, read-only, cwd=worktree)

{severity: must-fix, タイトル: 「bg 非同期 Agent が PreToolUse を通らない」という因果断定は成立しない, 攻撃シナリオ: 既知限界を bg ハーネス固有として固定すると、実因が旧 daemon/runtime、hook command の環境変数展開、または bg sessionKind 固有の設定解決だった場合に再発を放置する。実際、不発側は Claude Code 2.1.211・`sessionKind:"bg"`、対照側は 2.1.212・`sdk-cli` であり、バージョンと entrypoint が同時に変わっている。さらに対照側 Agent も async 起動なので、「async だから迂回」は対照自身が反証している, 根拠: [.consult-c22-plan-v1.md:86](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:86), [.consult-c22-plan-v1.md:90](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:90), [不発 transcript:62](/home/SFC/tanab/.claude/projects/-home-SFC-tanab-github-izanagi--claude-worktrees-s8b-c22-launch-cert/d0d2218c-cafc-4e24-886f-77bfffb5254a.jsonl:62), [不発 transcript:63](/home/SFC/tanab/.claude/projects/-home-SFC-tanab-github-izanagi--claude-worktrees-s8b-c22-launch-cert/d0d2218c-cafc-4e24-886f-77bfffb5254a.jsonl:63), [2.1.212 対照 transcript:9](/home/SFC/tanab/.claude/projects/-home-SFC-tanab--claude-jobs-9b2bec65-tmp-hookprobe/50aedebc-0c7c-422a-be7b-6492cda1e40c.jsonl:9), 提案: 2.1.212 で daemon/background session を新規作成し、同じ project settings・同じ model 欠落 payload を再試験する。可能なら 2.1.211/2.1.212 × bg/headless の 2×2 を取る。原因確定までは「2.1.211 の bg session で不発を観測。原因未分離」とだけ記録する}

{severity: must-fix, タイトル: 対照実験は guard の enforcement positive control になっていない, 攻撃シナリオ: 対照は絶対パスの logger hookを使い、Agent input に `model:"haiku"` を含めている。これは matcher がイベントを観測できることしか証明せず、repo の `$CLAUDE_PROJECT_DIR/hooks/guard_agent.py` が起動して exit 2 を返し、child spawn を阻止できることは証明しない。Agent hook workerだけ `$CLAUDE_PROJECT_DIR` を失う仮説も残る, 根拠: [.claude/settings.json:35](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.claude/settings.json:35), [.claude/settings.json:39](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.claude/settings.json:39), [hookprobe settings:5](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/hookprobe/.claude/settings.json:5), [hookprobe settings:7](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/hookprobe/.claude/settings.json:7), [test_hooks.py:733](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_hooks.py:733), [test_hooks.py:757](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_hooks.py:757), [test_hooks.py:782](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_hooks.py:782), 提案: 対照を repo の実 command と model 欠落 input で行い、(a) exit 2 が親へ返る、(b) async child artifact/notification が生成されない、の両方を確認する。catch-all logger は絶対パスで併設し、「イベント無し」と「command 起動失敗」を分離する}

{severity: must-fix, タイトル: worktree 起因仮説は棄却できるが、現プランはその重要事実を落としている, 攻撃シナリオ: worktree の project-dir 解決を原因候補として追い続ける一方、実際の不発プローブは main checkout cwd で行われ、`EnterWorktree` は約4分後だった。誤った環境記述を failures/memory に固定すると、再現手順が別物になる, 根拠: [不発 transcript:62](/home/SFC/tanab/.claude/projects/-home-SFC-tanab-github-izanagi--claude-worktrees-s8b-c22-launch-cert/d0d2218c-cafc-4e24-886f-77bfffb5254a.jsonl:62), [EnterWorktree:126](/home/SFC/tanab/.claude/projects/-home-SFC-tanab-github-izanagi--claude-worktrees-s8b-c22-launch-cert/d0d2218c-cafc-4e24-886f-77bfffb5254a.jsonl:126), [handoff:26](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-18-s8b-c22-launch-cert.md:26), 提案: 観測表に `version / entrypoint / sessionKind / cwd / settings source / model key / hook command / spawn結果` を必須列として残す。今回の worktree 仮説は refuted と明記する}

{severity: must-fix, タイトル: 「repo 側で取れる機械的防衛は無い」は偽, 攻撃シナリオ: PreToolUse が再び欠落すれば、現在は prompt/memory だけで fable 子を止められない。しかし repoまたは bg launcher には、Agent 全面 deny、脆弱 surface の foreground 化、subagent model の安全な fallback設定という別の機械点がある, 根拠: [.claude/settings.json:5](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.claude/settings.json:5), [guard_agent.py:25](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/hooks/guard_agent.py:25), [guard_agent.py:116](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/hooks/guard_agent.py:116), [hooks/README.md:114](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/hooks/README.md:114), 提案: 原因確定までは bg surface を fail-closed にし、`permissions.deny: ["Agent"]` または launcher の `--disallowedTools Agent` を候補にする。可用性を優先するなら bg launcher限定で `CLAUDE_CODE_SUBAGENT_MODEL=sonnet` を検討できるが、これは invocation/frontmatter より優先されるため全子を同モデルに上書きする副作用を明記し、必ず実測する。foreground 運用へ切り替えられる場合は `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` も候補。公式仕様上、Agent deny と model 解決順位は [permissions](https://code.claude.com/docs/en/permissions)・[subagents](https://code.claude.com/docs/en/sub-agents) に存在する}

{severity: should-fix, タイトル: 別 lifecycle hook は予防ではなく検知・封じ込めにしかならない, 攻撃シナリオ: `SubagentStart` や `SubagentStop` を第二の拒否点と数えると、spawn・モデル消費後のイベントを事前防壁として誤記する。既存 guard_bash/read/write も各自の tool eventしか見ず、Agent 呼び出しを側面検査できない, 根拠: [guard_write.py:62](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/hooks/guard_write.py:62), [guard_read.py:44](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/hooks/guard_read.py:44), [guard_agent.py:74](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/hooks/guard_agent.py:74), [hooks/README.md:116](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/hooks/README.md:116), 提案: `SubagentStart` は非 blockingかつ model field無し、`SubagentStop` と `PostToolUse:Agent` は事後なので enforcement と数えない。ただし絶対パス loggerによる `SubagentStart`/`PostToolUse` telemetry は、「spawn は起きたが PreToolUse だけ欠落」を機械検出する補助線として有効。公式 hook 能力表も [Hooks reference](https://code.claude.com/docs/en/hooks) と整合する}

{severity: must-fix, タイトル: docs-only の「恒久対応」は failures ledger 自身の契約を満たさない, 攻撃シナリオ: README・failures・memoryだけを追加して「環境別対照実験を行う」と宣言しても、次の runtime 導入者が実行しなければ再び恒真な防壁になる。特に現行テストは settings の文字列存在と hook script直叩きだけで、runtime dispatchを検査しない, 根拠: [.consult-c22-plan-v1.md:93](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:93), [docs/failures.md:10](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/failures.md:10), [docs/failures.md:12](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/failures.md:12), [docs/failures.md:14](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/failures.md:14), [docs/failures.md:88](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/failures.md:88), [docs/failures.md:154](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/failures.md:154), 提案: 新エントリの型タグは少なくとも `[恒真ゲート] [テスト代表性]`。原因がversion driftと確定した場合だけ `[ドリフト]` を追加する。恒久対応は checked-in runtime probe、または bg launcher の fail-closed preflightへのポインタにする。今回は docs-onlyを維持するなら「恒久対応未実装・再現条件調査中」と正直に残す}

{severity: should-fix, タイトル: README と memory に blanket な「bg セッションでは効かない」を書くと即座に腐る, 攻撃シナリオ: 2.1.212で修復済み、または2.1.211 daemon固有だった場合、全 bg sessionを恒久的に危険扱いし、不要な Agent denyや過剰なモデル固定を続ける。一方で別 entrypointの本当の穴を見逃す, 根拠: [hooks/README.md:10](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/hooks/README.md:10), [hooks/README.md:95](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/hooks/README.md:95), [.consult-c22-plan-v1.md:94](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:94), 提案: READMEには「観測済み事実」「未分離の候補」「再検証条件」を分ける。memoryは規律だけに留め、特定version/surfaceの状態正本にしない。hook 4冒頭の「止める」も「PreToolUse が配送される surface では止める」と限定する}

対抗仮説の裁定は次のとおりです。

- matcher の大小文字: 現設定と transcript の tool名はいずれも `Agent`。主因候補としては弱い。
- worktree project-dir変化: 不発が worktree進入前なので refuted。
- user/local settings上書き: 実機の user settingsに hooks無し、main checkoutの local settingsにも permission allowしかなく、`disableAllHooks`無し。さらに同sessionで guard_bash発火のため、全hook無効化説は弱い。
- settings読み込み優先順位: 静的ファイル上の衝突は見つからないが、失敗sessionの `/hooks`・`/status` または debug logによる active source確認がないため、runtime証明までは未達。
- 残る有力候補: 2.1.211 bg daemon固有、bg `sessionKind`固有、Agent hook command実行時の環境/`CLAUDE_PROJECT_DIR`差、または PreToolUse配送欠落。

Q-7への直接回答: 「無い」と断定してはいけません。別 lifecycle hookに同等の事前拒否点はありませんが、Agent全面deny、脆弱surfaceのforeground化、安全な subagent model fallback、runtime preflightという機械的防衛はあります。`SubagentStart`/`SubagentStop` は検知用であって予防ではありません。

レーンAの裁定: 不発という観測事象は real。ただし「repo配線は正しく、bgハーネスの非同期 Agent が PreToolUseを通さない」「コード変更不要で文書化のみ」という結論は要追加実験です。
## §7 付録 — 親プラン v1 全文 (相談 4 本の攻撃対象。§6 の行番号引用の対象)

    # C2-2 launch certificate 結線 + guard_agent 既知限界 — 実装プラン v1 (敵対相談用ドラフト)
    
    このファイルは相談用の一時ドラフト (untracked、commit しない)。正本ポインタ:
    - worklog (7) residual: 「C2-2 launch certificate は素体のみ — 発行の結線 + verifier の lineage 照合は
      floor 実走 wave の blocking 前提」 (docs/worklog.md)
    - 結線注記: orchestrator/campaign/s8b_floor_campaign.py:884-935 (scaffolding 3 関数) / 1706-1710
      (run_campaign の official 拒否直後の C2-2 前提条件コメント)
    - verifier 側不実装の明記: orchestrator/campaign/s8b_ratified_freeze.py:1254-1260 (launch_validate docstring)
    - 裁定: output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md §3 C2-2 行 (516) / §4 項 4 (565) /
      §5 (i)(ii)(viii)。cert フィールド = {v1 hash, clean-scan digest, protocol sha256, UTC, run id}、
      official 開始時 create-only 発行、journal が cert hash を束縛、closure は cert 起点 lineage から導出。
      closure↔cert を紐付ける具体的検証手順は文書上未確定 (= 本プランの実装解釈)
    - スコープ規律 (同 §冒頭 8-10 行): machinery + テストのみ。実 approval record / active pointer /
      v2 世代 file / protocol JSON の実凍結・発効なし。official 拒否 (CLI main 2030-2036 + core
      run_campaign 1711-1715 の二重) は不変
    
    ## レーン B-I: 発行側結線 (s8b_floor_campaign.py)
    
    - **D-1** `_official_launch_preflight(root, run_dir, *, v1_freeze_sha256, protocol_sha256, now_fn,
      campaign_run_id) -> str` を新設: clean_scan_digest(root) → build_launch_certificate(...) →
      issue_launch_certificate(run_dir / "launch_certificate.json", cert) → cert bytes sha256 を返す
    - **D-2** run_campaign fresh 分岐 (1777-1794) で run_dir 作成直後・build_cells の**前**に
      `cert_sha = _official_launch_preflight(...) if mode == "official" else None`。
      v1_freeze_sha256 = freeze_sha256 (1746-1753 で protocol の freeze.sha256 と照合済みの値)、
      campaign_run_id = run_dir.name、started_utc = now_fn().isoformat()
    - **D-3** _Runner に cert_sha (optional) を渡し、fresh の campaign-start record (1290-1300) に
      official のときのみ `"launch_certificate_sha256": cert_sha` を追加。pilot は従来どおりキー無し。
      JOURNAL_SCHEMA は bump しない (official journal は世界にまだ 1 つも存在しないため互換性問題なし)
    - **D-4** resume: _verify_resume_journal (1925-1995) を拡張 — mode == "official" なら campaign-start に
      launch_certificate_sha256 必須 + run_dir/launch_certificate.json 実在 + bytes sha 一致。
      pilot の campaign-start に同キーがあれば拒否 (mode 混線検出)
    - **D-5** 無条件 official 拒否 (1711-1715) を `_assert_official_permitted(mode)` へ抽出 (無条件 raise の
      まま意味不変)。テストはこの 1 点だけを monkeypatch して dormant official 経路を統合テストする。
      CLI 拒否と将来の F6a 承認 machinery は独立防壁として不変
    
    **Q-1** D-5 のテスト seam (monkeypatch 可能な関数抽出) は防壁の弱体化か? 代替 = seam なしで helper
    単体テストのみ (結線コード自体は一度も実行されない = 恒真保証リスク)。どちらが正しいか。
    **Q-2** clean_scan_digest の root は実リポジトリ。将来の official 実走時、凍結済み protocol JSON
    (Lane J builder 出力) や過去 campaign 出力・v2 世代 file 自体が conjunction hit して cert 発行不能に
    ならないか? s8b_holdout_freeze の match convention / _is_excluded と、closure 宣言済みファイルの
    扱い (clean scan は hit 0 を要求 — 宣言済み hit の存在と矛盾しないか) を検査せよ。
    
    ## レーン B-II: 検証側 (s8b_ratified_freeze.launch_validate 拡張)
    
    - **D-6** 到達経路: 新 header field は §4-2 exact 列挙により追加不可 → ratified.floor_source blob
      (= result artifact、read_floor_source_blob 1146-1164 で G tree から取得) を parse し、wall_ledger
      (assemble_result 1492-1495 が campaign-start record を全フィールドごと収録) の campaign-start
      ちょうど 1 件から launch_certificate_sha256 を得る
    - **D-7** floor_source は s8b-floor-result/v2 として parse でき mode == "official" であることを要求
      (無条件強制。Q-5 参照)
    - **D-8** cert blob の所在 = dirname(floor_source.path) + "/launch_certificate.json" を G tree から
      _blob_at_or_fail で読取。検査: bytes sha256 == wall_ledger の launch_certificate_sha256 /
      strict parse / schema == LAUNCH_CERT_SCHEMA / v1_freeze_sha256 == V1_FREEZE_SHA256 定数 /
      protocol_sha256 == result の protocol_sha256 / campaign_run_id == basename(dirname(floor_source.path))
    - **D-9** lineage 順序条件 (実装解釈、§5 追認リストへ (ix) として追加提案): cert path の導入 commit
      (_immutable_introductions 322-347 で取得) を anchor とし、measurement_closure 各 entry の導入
      commit が「anchor と同一 commit または anchor の子孫」であることを要求。根拠: cert の clean scan
      hit-0 が発行時点で hit を生むファイルの非存在を証明するため、closure entry が cert より古い履歴で
      導入されていれば矛盾 (未申告先行測定の再現)
    - **D-10** 拒否 reason code: "launch-certificate-missing" / "launch-certificate-binding-mismatch" /
      "launch-certificate-field-mismatch" / "closure-predates-certificate" / "floor-source-not-official"
    
    **Q-3** 現 assemble_result は eligible_for_refreeze を定数 False で書く (1501-1504)。将来 official 化の
    際この定数はどうなるべきで、launch_validate は eligible_for_refreeze を検査すべきか?
    **Q-4** D-9 で「同一 commit」を許す設計 (campaign 出力一括 commit を想定) は正しいか。merge 由来の
    複数導入 (_immutable_introductions は集合を返す) はどう裁くべきか。
    **Q-5** cert 検証は無条件強制 (提案) か、floor_source が result artifact として parse できる場合のみか。
    無条件なら既存 fixture (build_valid_semantic_g1 の floor_source = stub、test_s8b_ratified_freeze.py
    187-267) は floor_source_bytes 拡張点で全面更新 + closure ファイルの導入位置を cert 後へ再配置。
    条件付きは stub を差した bypass が成立し fail-open。
    **Q-6** §5-(i) measurement_closure schema / (ii) 世代導入 commit 機械制約はユーザー追認待ち。本実装は
    スキーマを変更せず検証を追加するのみだが、追認待ち領域への先回りとして越権になる部分はないか。
    
    ## レーン B-III: テスト計画
    
    - 発行側: seam monkeypatch + scan/measure stub で official dormant 経路統合テスト — cert create-only
      発行 / campaign-start 束縛 / resume 再検証 / scan hit 時は build 前 refuse (zero side effects) /
      pilot 不変 (キー無し)。既存 official 拒否テスト (486-, zero-side-effect) は seam 抽出後も不変で緑
    - 検証側攻撃 matrix (test_s8b_ratified_verify.py へ): binding mismatch / cert 不在 / schema 不正 /
      v1 hash 不一致 / protocol sha 不一致 / run id 不一致 / closure-predates-certificate / campaign-start
      にキー無し / wall_ledger の campaign-start 0 件・2 件 / happy path
    - 変異スポットチェック: D-9 祖先条件を外す → 攻撃テスト赤 / D-8 binding 照合を外す → 赤 (恒真防止)
    
    ## レーン A: guard_agent 既知限界の文書化 (コード変更なし)
    
    事実 (本セッション実測): (1) model 未指定 Agent 呼び出しが本 bg セッションで素通り、同セッションで
    guard_bash は発火。(2) hook 単体は手動 stdin で正しく exit 2。(3) 対照実験: 使い捨てプロジェクト +
    headless claude 2.1.212 で、matcher なし・matcher "Agent" 完全一致の両方で PreToolUse が
    tool_name "Agent" で発火。(4) 現行公式 docs は matcher/tool_name とも "Agent"、hooks 設定は
    live-reload。結論: repo 配線は正しく、不発は bg ハーネスの非同期 Agent ツールが PreToolUse を
    通さないことによる環境固有の穴。
    
    - 変更: hooks/README.md hook 4 節へ既知限界追記 / docs/failures.md 新エントリ (「発火しない防壁」は
      導入時に環境別対照実験で発火条件を確定する、を恒久対応に) / memory subagent-model-economy 追記
      (bg セッションでは機械防壁が効かず規律のみが防衛) / worklog (8) 次の一手 1 の消化
    **Q-7** repo 側で他に取れる機械的防衛はあるか (無いなら「無い」と断定してよいか)。
    
    ## 進め方 (このセッション)
    
    プラン → codex 並列敵対相談 (本ファイル + repo を read-only で) → 親裁定 → codex 並列実行
    (worktree 内 workspace-write) → claude opus 並列レビュー → 必要なら codex 再投げ → 親検算
    (全 suite + check_docs + 変異スポット) → AI-Agent trailer 付き commit (push はユーザー引き渡し)。
    子エージェント/codex 拘束: 作業ツリー巻き戻し系 git コマンド (stash/restore/reset/checkout -- 等) 禁止。

## §8 検証側実装 wave (2026-07-18 裁定発効) — 相談・裁定・ロードマップ

**編集方針:** §6 と同じ軸リテラル redaction (`ycsb_rratio=` → `ycsb_rratio⟦=⟧` 等、機械照合のみ破壊)。

### §8.1 この wave で確定したこと (実装済み・commit 済み)
- 基盤 S0 (s8b_launch_cert.py leaf module): LAUNCH_CERT_SCHEMA / validate_launch_certificate /
  parse_official_run_path を stdlib-only へ分離 (import 循環回避、Q-A)。run-id 時刻部と
  cert.started_utc の秒単位一致を強制 (V1 所見6 の穴を封鎖)。raw POSIX path の正規化前拒否。
  floor 側は LaunchCertError→FloorCampaignError wrapper で API 互換維持
- 基盤 H (s8b_holdout_freeze.search_repository の exempt_exact API): (ix)-9 の exact 免除基盤。
  既定 prefix 除外は bytes 不変、opt-in 時のみ exact path+sha256 一致を免除
- commit fd32b8f。全走 1363 passed / 23 skipped

### §8.2 この wave で判明した重要事実 (V2b 精査) — 検証側本丸は multi-wave
検証側 launch_validate を「正しく」実装する (F15 恒真を避ける) には、テスト fixture を手書き stub
でなく **production 経路が生成する実 bytes** にする必要がある (V-4)。V2b はこれを「条件付き feasible、
ただし production 側の決定化が前提」と判定した。前提 = 次の 3 点を production 側で先に決定化:
1. **artifact projection の決定化**: manifest/result/journal の bytes に混入する非決定値
   (hostname / boot_id / job_id / cpuset / pid / starttime / execution_uuid / build 絶対 path /
   cached フラグ) を、注入 seam (host_provenance_fn / process_identity_fn / execution_receipt_fn /
   build_cells_fn / repo_root) と emission 前正規化 (build path の out-root 相対化) で固定。
   **正規化は assemble_manifest より前** (後処理すると manifest sha が journal/result に連鎖する
   binding chain を壊す)
2. **certificate checkpoint seam**: 現 run_campaign は cert 発行→launch-start→build が連続で
   C commit を挟めない。cert 発行直後の checkpoint callback (または preflight/execute 二段 core)
3. **eligible_for_refreeze の finalize semantics 修正** ((ix)-6): official 完走 finalize 時のみ True
さらに fixture の closure record schema は前 wave §5 (i)/(ii) が**未裁定**のため、topology は組めても
closure の normative schema を golden 固定するのは早い (2 つの裁定待ちに依存)。

**結論 (マネージャー判断):** 検証器本体を今 seam 無しで書くと fixture が stub のままになり、
codex が全相談で警告した F15 / 恒真ゲート型を作り込む。よって本 wave は基盤 + 設計凍結で閉じ、
検証器本丸 (R/F/fixture/oracle/決定化 seam) は次 wave に、下記ロードマップで送る。決定化 seam を
本丸から切り離して今入れると「使われないコード」= 恒真 か 後で形が変わる手戻りになるため、
本丸と一体で設計・実装する (規律 5: 盛らない・段階導入)。

### §8.3 検証器実装ロードマップ (次 wave、V2b の安全順序を正本化)
依存順 (各段は前段の production API 固定後):
1. 決定性 characterization test (2 tmp root で 3 artifact SHA 不一致を露出) + official 拒否テスト維持
2. build artifact の portable 表現 (binary/command path を out-root 相対 or canonical placeholder、
   cached の扱い固定)。正規化は manifest hash 計算前
3. provenance/process/receipt の private seam 追加 (production default は現行関数へ委譲、
   runtime flag / CLI bypass を作らない)
4. repo_root seam (ROOT ハードコード解除) + 実 tmp-repo clean scan を通す E2E
5. certificate checkpoint seam (C commit を挟む) — pre-start resume を使うなら意味論を先に完成
6. eligible_for_refreeze の official finalize semantics 修正 ((ix)-6)
7. production-bytes staged builder (base→C→G→A、2 重生成 SHA 一致テスト)
8. mutate_g1 系移行 (source/frozen/closure/env/transition の順、各 expected first reason を維持)
9. scan/closure 負例移行 (undeclared / missing / per-holdout / enumeration / positive-control を
   独立 mutation に)。extra_closure の excluded-namespace 負例は (ix)-9 hardening 後に別 reason が
   先に出るため、namespace 拒否テストと missing-hit テストに二分
10. oracle fixture を production result schema へ (store 消費テストを最後に移行)

ファイル素集合 (並列時): S0 共有 (済) / H scan (済) / R verifier (s8b_ratified_freeze.py +
test_s8b_ratified_freeze.py + test_s8b_ratified_verify.py、V-4 fixture は R 単独所有) /
F issuer (s8b_floor_campaign.py + test) / O consumer (s8b_oracle_driver.py + test)。R と F は
決定化 seam API 固定後なら並列可。

### §8.4 検証器の検証鎖 (V1 所見、次 wave の実装契約)
launch_validate が閉じるべき binding graph (欠けると偽造可能な辺):
- equality chain 全辺: P = canonical_sha256(**full_validate(strict_parse(floor_protocol blob))**
  の正規化戻り値) == result.protocol == journal campaign-start.protocol == cert.protocol ==
  manifest.protocol / V1_FREEZE_SHA256 == result.freeze == journal.freeze == cert.v1_freeze ==
  protocol.freeze.sha256 == manifest.freeze.sha256 (path も V1_FREEZE_PATH に一致) /
  sha256(manifest raw) == result.manifest_sha256 == journal.manifest_sha256 / sha256(cert raw) ==
  launch-start.cert == campaign-start.cert == result.wall_ledger.cert / journal[event=session] ==
  result.sessions (完全一致) / result.binaries == manifest.binaries / env 全辺 (doc/path/protocol/
  result/manifest/receipt) / contract_sha256 == receipt / run-id.ts == cert.started_utc秒 ==
  launch-start.utc
- **path-set union の洗浄封鎖 (V1 critical)**: union に journal/manifest を含めるだけでは、journal の
  notes/run_cmd 等の自由記述に三軸を紛れ込ませても holdout_conjunction_hits (path 単位 bool) は
  不変で洗浄される。先に (a) event exact key schema + 未知 event 拒否 / (b) journal session ==
  result.sessions / (c) conjunction を許す JSON Pointer を構造化 workload field に限定・自由記述欄の
  conjunction は拒否、を課す。可能なら (artifact path, JSON Pointer, holdout) 単位 occurrence 検査
- **G↔worktree 間隙封鎖 (V1)**: cert/journal/manifest/result も G・H・worktree の bytes と mode を
  固定 (mode は H でも 100644/100755、worktree symlink 拒否)。_immutable_introductions は mode を
  追わないため _list_namespace 型 mode 検査を併用。小 artifact は scan 前後に内容 hash 再照合
- **lineage (V3/V1)**: cert 導入 = 一意・非 merge・G の厳密祖先 (C != G ∧ is_ancestor)。closure/
  floor_source/journal/manifest の導入集合 == {G}。ただし journal/manifest の導入==G と full
  validate 採用は前 wave (ii)/(v) 抵触のため**実装解釈として次回追認へ**。「実時間/履歴書換え耐性は
  保証しない (H 内記録順のみ)」を docstring/保証表/テストに明記
- **one-shot ((ix)-4)**: launch_validate で generation_number==1 を強制 (reason
  certificate-generation-scope)。g2+ の静的 load は将来 schema のため維持
- **eligible ((ix)-6)**: flag 単独を証拠にせず mode + 一意最終 completed terminal + 自己検査済み
  result を独立導出
- **scan 免除 ((ix)-9)**: 検証済み active-chain artifact の exact path+bytes のみ免除 (H の
  exempt_exact API 使用)。resolver の closed-world 化は (ix)-9 の代替でない (別途追認)
- **Q-B**: verify_floor_artifact は必ず回すが単独不足。expected_protocol は full-validated protocol、
  expected_binaries は exact-validated journal receipt から導出 (result/manifest から自己導出しない)
- **Q-C**: cert は union 非編入 + hits(cert)==∅ を invariant 化
- reason codes: certificate-generation-scope / scan-exemption-invalid / journal-state-invalid /
  floor-artifact-invalid / manifest-invalid / binding-chain-mismatch (低レベル reason は cause 保持)
- _closure_entries は floor_protocol/floor_source も含むため、measurement-only helper と
  bound-artifact helper に分離 (floor_protocol に誤って G-introduction==G を課さない)

### §8.5 次回ユーザー追認リストへの追加 (本 wave で新規に判明)
- full validate_protocol の launch acceptance への採用 (前 wave (v) 抵触)
- journal/manifest の導入 commit==G (前 wave (ii) の狭い部分のみ (ix)-10 で追認済み、拡大は未裁定)
- manifest への mode 制約 / cert bytes の期待 union 編入の可否
- launch-start-only (manifest 無し) crash 状態の回復方式 (L/M 二状態のうち L の扱い)
- V2 相談 (pre-start resume の悪用面) は codex の cybersecurity フィルタで失敗 → 中立言い換えの
  V2b (fixture 決定性) で代替。pre-start resume の悪用面は V1 所見 + V3 所見4 で代替カバー済み

### §8.6 相談逐語 (redacted — 方針は §8 冒頭)

#### 相談 V1 (gpt-5.6-sol reasoning=max, read-only, cwd=worktree)

結論: **プラン v3 はこのままでは reject** です。直接の裁定逸脱が1件、検証鎖の must-fix が複数あります。特に V-2 手順10と raw-byte/path-set union が重大です。

## 所見

### 1. {severity: Critical / must-fix, タイトル: 手順10は「初回限り」裁定に正面から違反}

- 攻撃シナリオ: g1 の result/journal/manifest/cert を現 tree から削除して clean scan を通し、2枚目の cert C2 を発行後、G2 で新しい floor_source/closure を同梱する。現 verifier は active tip g2 の artifact しか実体検証せず、g1→g2 では floor/protocol/source/closure の変更が許可されるため、C2 < G2 の系譜も成立する。
- 根拠: 裁定は明示的に「v1→g1 初回 official 一回限り」です。[裁定 §5:102](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-18_s8b-c22-consultations.md:102)。一方、プランは世代番号を特別扱いしないとしています。[plan:43](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22v-plan-v3.md:43)。gN→gN+1 の変更許可表には floor_source/measurement_closure 等が含まれます。[s8b_ratified_freeze.py:109](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:109)。実体検証は tip document だけです。[s8b_ratified_freeze.py:739](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:739)。clean scan は現時点の file 集合しか見ません。[s8b_floor_campaign.py:971](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:971)。
- 提案: `LAUNCH_CERT_SCHEMA/v1` は `generation_number == 1` を必須にし、g2+ は専用 reason で拒否する。再実測は裁定どおり baseline digest 付き別 schema まで不許可とする。発行側の clean scan は補助防壁であり、one-shot の正本にしてはいけない。

### 2. {severity: Critical / must-fix, タイトル: path-set union は journal 内の追加痕跡を洗浄する}

- 攻撃シナリオ: 正常な session record の `notes` に `ycsb_rratio⟦=⟧80 ycsb_zipf_skew⟦=⟧0.9 ycsb_rmw⟦=⟧0` を追加し、同じ record を result.sessions に複写する。journal/result は元から workload により hit path なので、追加痕跡を入れても期待集合も実集合も変わらない。hash と G を作り直せば通る。
- 実コード確認: 同じ path に conjunction を1回入れた場合と2回入れた場合で、`holdout_conjunction_hits` の結果が完全に同じになることを実行確認済みです。
- 根拠: `_scan_one` は各正規表現を `bool(pattern.search(...))` に潰し、pathを一度だけ返します。[s8b_holdout_freeze.py:270](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_holdout_freeze.py:270)、[同:369](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_holdout_freeze.py:369)。journal の `notes`/`run_cmd` は自由記述です。[s8b_floor_campaign.py:1334](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1334)、[同:1406](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1406)。`verify_floor_artifact` は session の必須キーしか見ず、余分な field や notes を検査しません。[s8b_floor_stats.py:406](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_stats.py:406)。
- 提案: journal/manifest/result を union に含めること自体は裁定どおり。ただしその前に、以下を必須化する。

  - event ごとの exact key schema と未知 event 拒否
  - journal session と result.sessions の完全一致
  - conjunction を許す JSON Pointer を構造化 workload field のみに限定
  - `notes`、probe 出力、自由形式 command 等に conjunction があれば拒否
  - 可能なら `(artifact path, JSON Pointer, holdout)` 単位の occurrence 検査を追加

「artifact path が期待内」だから「その中の任意文字列も期待内」とする解釈は、裁定のいう「検証鎖で束縛される artifact」には該当しません。[裁定 §5:98](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-18_s8b-c22-consultations.md:98)。

### 3. {severity: High / must-fix, タイトル: equality chain に複数の未閉鎖辺がある}

必要な全辺を照合すると以下です。

| 鎖 | 状態 | 欠けると可能な偽造 |
|---|---|---|
| `sha256(result raw) == generation.floor_source.sha256` | 既存 V1d で概ね有り | 別 result の差替え |
| `P == result.protocol == journal.campaign-start.protocol == cert.protocol` | 計画有り | — |
| `P == manifest.protocol_sha256` | **欠落** | manifest が別 protocol/build を名乗れる |
| `P[:8] == run-id.proto8` | 計画有り | path と protocol の取り違え |
| `V1 == result.freeze == journal.freeze == cert.v1_freeze` | 計画有り | — |
| `V1 == protocol.freeze.sha256 == manifest.freeze_sha256 == manifest.freeze.sha256` | **欠落** | protocol/manifestだけ別 freeze を名乗れる |
| `V1_FREEZE_PATH == protocol.freeze.path == manifest.freeze.path` | **欠落** | 同一hashを別 provenance path として申告できる |
| `sha256(manifest raw) == result.manifest_sha256 == journal.manifest_sha256` | 計画有り | — |
| `sha256(cert raw) == launch-start.cert == campaign-start.cert == result.wall_ledger.cert` | 計画有り | — |
| `journal[event=session] == result.sessions` | **欠落** | journal と無関係な throughput で result を構成できる |
| `result.binaries == manifest.binaries` | **欠落** | oracle が読む store_path 等を測定 manifest と分離できる |
| journal の全 `binary_sha256_at_measure` == result/manifest binaries | Q-B 未決 | 測定 binary と oracle 用 binary の分離 |
| `doc.env == path.env == protocol.env == result.env == manifest.env == execution_receipt.env` | **path/doc 以外欠落** | 別環境の測定として再ラベル可能 |
| `protocol.contract_sha256 == execution_receipt.contract_sha256` | **欠落** | receipt と環境契約の分離 |
| `run-id.ts == cert.started_utc秒部 == launch-start.utc` | **欠落** | launch 時刻の偽 provenance |

manifest は実際に protocol/freeze/env/binaries/schedule を持ちます。[s8b_floor_campaign.py:875](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:875)。result は binaries と sessions を別々に持ちます。[s8b_floor_campaign.py:1655](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1655)。`verify_floor_artifact` 自身も journal 真正性は責務外と明記しています。[s8b_floor_stats.py:398](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_stats.py:398)。

- 提案: union 導出前に上表を一つの binding graph として全検査する。manifest/result は top-level と重要 nested record の exact schema を要求し、hash 一致だけを意味検証の代用にしない。

### 4. {severity: High / must-fix, タイトル: G bytes と current worktree の間が journal/manifest だけ開いている}

- 攻撃シナリオ: G/H の journal は正常なまま、worktree の journal に痕跡を追加する。journal は元から hit path なので current scan の集合は変わらず、列挙 digest も path 名だけなので通る。
- 根拠: plan は journal/manifest を G から読みますが、scan は worktree を読みます。[plan:20](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22v-plan-v3.md:20)、[s8b_holdout_freeze.py:257](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_holdout_freeze.py:257)。列挙 digest は内容を含みません。[s8b_ratified_freeze.py:1195](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:1195)。既存 V1d の worktree==H 検査は `_closure_entries` 対象だけです。[s8b_ratified_freeze.py:789](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:789)。
- 提案: cert/journal/manifest/result/protocol と measurement closure すべてについて、G・H・worktree の bytes と mode を固定する。小さい bound artifact は scan 前後にも内容hashを再照合する。mode は G だけでなく H でも 100644/100755、worktree symlink も拒否する。

なお `_immutable_introductions` は blob OID だけを追い、mode を追いません。[s8b_ratified_freeze.py:322](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:322)。mode を正しく検査する既存例は `_list_namespace` です。[同:637](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:637)。

### 5. {severity: High / must-fix, タイトル: Q-D の canonical hash のみでは別実験を自己整合偽造できる}

- 攻撃シナリオ: schema/formula/n_sessions/freeze が不正な protocol を作り、その canonical hash を result/journal/cert/path に一貫して置く。hash chain は全辺一致するが、承認された floor 実験ではない。
- 根拠: `validate_protocol` は exact key、formula、env contract、承認 pin を検査します。[s8b_floor_campaign.py:247](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:247)。実行側は検証・正規化後の document を canonical hash しています。[同:1874](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1874)、[同:1912](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1912)。
- 提案: `P = canonical_sha256(full_validate(strict_parse(blob)) の正規化戻り値)` とする。raw parse の canonical hash では、例えば validator が `1` を `1.0` に正規化するケースで issuer と verifier が分裂する。さらに `protocol.freeze` は V1 trust root へ明示 pin する。

### 6. {severity: Medium / must-fix, タイトル: path 文法と timestamp binding が未仕様}

- 攻撃シナリオ: `campaign_run_id` と `started_utc` を別時刻にする。現 validator は両方が個別に妥当なら受理するため、run layout は2026年、certは2099年という provenance が通る。実コードでこの不一致が受理されることを確認済みです。
- 根拠: current validator は UTC 形式と expected run-id の個別一致しか見ません。[s8b_floor_campaign.py:1041](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1041)。issuer は同じ `started_at` を run-id/cert/journal に使っています。[同:1931](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1931)、[同:2052](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:2052)。`layout.env_scope_dir` 自体は env_tag を単純 join するだけです。[layout.py:87](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/layout.py:87)。
- 提案: raw POSIX path に次の完全一致文法を課す。

  `^output/env/[a-z0-9][a-z0-9._-]*/calibration/s8b-floor-official/[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}/result\.json$`

  その上で env の完全一致、ts の `strptime`＋round-trip、proto8、run-id、cert時刻秒部を照合する。正規化してから検査せず、`//`、`.`、`..`、`\`、制御文字を raw string 段階で拒否する。

また、既存 `_closure_entries` は名前に反して floor_protocol/floor_source まで含みます。[s8b_ratified_freeze.py:708](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:708)。plan の「closure entries + floor_source/protocol」は、実装者がこの helper を使うと重複または floor_protocol の誤った G-introduction 要求になります。measurement-only helper と bound-artifact helper に分離すべきです。

### 7. {severity: Medium / 保証境界の must-fix, タイトル: 厳密祖先は実時間順を証明しない}

- 攻撃シナリオ: 実測後に、cert commit C と artifacts commit G を C<G になるよう履歴ごと作り直す。導入一意、非merge、G同梱はすべて成立する。
- 根拠: 現実装は shallow、replace refs、grafts をよく遮断しています。[s8b_ratified_freeze.py:135](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:135)、[同:172](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:172)。しかし通常の rebase/filter/reconstructed commits は H 自体になるため検出不能です。これは裁定も「H 内記録順のみ」と明示しています。[裁定 §5:107](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-18_s8b-c22-consultations.md:107)。
- 提案: 実装は `C != G && is_ancestor(C,G)`、各 G artifact の introduction set `== {G}` を厳密実装する。同時に docstring・保証表・テストへ「実時間/履歴書換え耐性は保証しない」を明記する。強保証は将来の署名tag・保護remote等が必要。timestamp 一致を加えてもこの限界は解消しない。

### 8. {severity: Medium / implementation blocker, タイトル: Q-A の direct import は実依存グラフ上の循環}

- 攻撃シナリオ: `s8b_ratified_freeze` が top-level で `s8b_floor_campaign` を importすると、floor の import 中に partial-initialized ratified へ戻り、定義前 symbol の取得または import order 依存になる。
- 根拠: 実グラフは `floor_campaign → s8b_approved → s8b_ratified_freeze` です。[s8b_floor_campaign.py:75](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:75)、[s8b_approved.py:24](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_approved.py:24)。さらに floor は materialization/build/pipeline 系も巻き込む重い module です。[s8b_floor_campaign.py:70](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:70)。
- 提案: V-1 の shared leaf への移設を採用する。ただし shared validator 用例外と `FloorCampaignError` の互換 adapter を設計すること。単なる re-export では、現在 `FloorCampaignError` を期待する API/テストを壊す。[s8b_floor_campaign.py:1017](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1017)。

## Q-A〜Q-D への直接回答

- Q-A: **共有 leaf へ移設**。direct import は実グラフ上循環、重複実装は F2 型 drift。`s8b_launch_cert.py` は stdlib-only にし、floor 側は例外翻訳 wrapper で後方互換を保つ。Q-D 用 protocol validator も pure module に抽出する必要がある。
- Q-B: **必ず回す。ただし単独では不足**。expected_protocol の7 scalarは full-validated protocolから、`expected_cells` は ratified freeze の holdouts/variant binding から、`expected_binaries` は exact-validated journal receipt から導出する。result/manifestから expected を自己導出してはいけない。先に `journal sessions == result.sessions` を閉じること。
- Q-C: **現 v1 cert bytes は union に含めない**。裁定が暗黙許可したのは floor_protocol/result/journal/manifest で、cert は含まれていない。現 exact schema＋run-id文法なら cert hit はゼロのはずなので、`hits(cert)==∅` を invariant として拒否する。将来 cert schema に自由 field を足すなら再裁定。
- Q-D: **full validate 必須**。しかも issuer と同じ正規化戻り値を canonical hash する。canonical hash の再計算だけでは「一貫しているが未承認の別実験」を受理する。

## 確認済み事項

- `s8b_ratified_freeze.py` は全体を確認済み。
- `_strict_load` は UTF-8、duplicate key、NaN/Infinity、top-level object を適切に拒否する。
- `_closure_text` と `_read_search_text` は「先頭8192 bytesのNUL＋UTF-8全体」の判定が一致する。
- `_list_namespace` は 100644/100755 を正しく強制するが、任意 run artifact の helper にはまだなっていない。
- `verify_floor_artifact(artifact, expected_protocol, expected_binaries=None)` の保証範囲は内部再計算であり、journal真正性は明示的に範囲外。
- 実行確認で、同一 journal path 内の conjunction 追加は hit集合を変えず、run-id時刻と cert.started_utc の不一致も current validator が受理した。
- ファイル変更は行っていません。
#### 相談 V2b (gpt-5.6-sol reasoning=high (V2 は cybersec フィルタ失敗のため中立言い換え再投げ), read-only, cwd=worktree)

## 結論

V-4 は技術的には実現可能です。ただし、現行の `run_campaign` と既存の6注入点だけでは `result.json` / `journal.jsonl` / `manifest.json` の SHA-256 を再実行間で一致させられません。

成立条件は次の3点です。

1. host/process/execution receipt と build path を決定化する production 側の seam または正規化を先に追加する。
2. certificate 発行後に C commit を作り、その同じ campaign を続行できる checkpoint seam を追加する。
3. fixture の mutation API を「valid production artifact を作った後、狙った検査辺だけを壊す」段階 API に変える。

§5 の裁定では `(ix)-10` と段階 builder の方向は追認済みですが、前 wave `(i)/(ii)` の closure schema 自体は未裁定のままです。したがって topology は先に作れても、closure の最終 normative schema を fixture に固定するのはまだ早いです（`output/insights/2026-07-18_s8b-c22-consultations.md:97-110,141-144`）。

## 1. 3 artifact の完全決定性

### 現状判定

現状のままでは不可能です。

`assemble_manifest` と `assemble_result` 自体は入力に対する純粋関数ですが、入力である `built` と journal records に非決定値が入っています（`orchestrator/campaign/s8b_floor_campaign.py:875-897,1568-1576`）。JSON の直列化形式は `sort_keys=True`、固定改行なので、入力を固定できれば bytes は固定できます（同:673-678,900-910,1798-1799）。

現行の正式なテスト注入点は以下の6個です（同:1850-1857）。

- `measure_fn`
- `probe_fn`
- `sleep_fn`
- `monotonic_fn`
- `prepare_fn`
- `now_fn`

ただし `sleep_fn` は `_Runner` に保存されるだけで、現コードでは実行結果生成に使われていません（同:1177-1192）。また `prepare_fn` は materialization だけの seam で、`buildcache.build` 自体は直接呼ばれます（同:838-868）。既存テストもここを正式な引数ではなく monkeypatch しています（`orchestrator/tests/test_s8b_floor_campaign.py:186-220`）。

### 非決定値の分類

| 非決定値 | 混入先 | 現状 | 判定 |
|---|---|---|---|
| certificate `started_utc`、launch-start `utc` | certificate、journal | `started_at = now_fn()` から導出 | (a) 既存注入で決定化可能（同:1931-1965） |
| run directory ID | path、certificate | 固定時刻＋protocol hash | (a) `now_fn` と protocol 固定で決定的（同:2052-2060） |
| campaign/round/session 時刻 | journal、result.wall_ledger、result.sessions | `now_fn` | (a) 既存注入で決定化可能（同:1290-1295,1443-1477,1486-1487） |
| `duration_s` | journal session、result sessions/attempts | `monotonic_fn` の差 | (a) 既存注入で決定化可能（同:1386-1388,1418-1419,1640-1648） |
| throughput、notes、run command、retry 発生 | journal、result | `measure_fn` | (a) 既存注入で決定化可能（同:1322-1345） |
| probe stdout/stderr/rc | journal、result | `probe_fn` | (a) 既存注入で決定化可能（同:1309-1333,1419-1420） |
| schedule | manifest、実行順 | protocol `master_seed` | (a) 入力固定で決定的（同:645-666） |
| `hostname` | campaign-start、execution receipt | OS から直接取得 | (a) 新しい provenance/receipt seam が必要（同:773-780、`execution_guard.py:69-86`） |
| `boot_id` | campaign-start、execution receipt | `/proc` から直接取得 | (a) 新しい seam が必要（同:746-750,773-780、`execution_guard.py:38-44,81-85`） |
| `job_id` | campaign-start | PBS/SLURM 環境変数 | (a) 新しい seam が必要（`s8b_floor_campaign.py:773-780`） |
| `cpuset` | campaign-start、execution receipt | `/proc/self/status` または `/proc/self/cpuset` | (a) 新しい seam が必要。両実装は取得元も異なる（同:753-760、`execution_guard.py:47-53`） |
| `pid` | campaign-start/resume-start | `os.getpid()` | (a) 新しい process identity seam が必要（`s8b_floor_campaign.py:784-790`） |
| process `starttime` | campaign-start/resume-start | `/proc/self/stat` | (a) 新しい seam が必要（同:763-769,784-790） |
| `execution_uuid` | campaign-start/resume-start | `uuid.uuid4()` | (a) 新しい seam が必要（同:784-790） |
| receipt `captured_utc` | campaign-start | `now_fn` | (a) 既存 `now_fn` で固定可能（`execution_guard.py:69-86`） |
| receipt の hostname/boot/cpuset | campaign-start、result.wall_ledger | OS から直接取得 | (a) 新しい receipt seam が必要（同:77-86） |
| build binary の絶対 path | manifest.binaries、result.binaries | build root/tmp path | (b) production の artifact 化時に out-root-relative path へ正規化するのが堅い（`s8b_floor_campaign.py:838-867,1675`、`buildcache.py:123-131`） |
| `configure_cmd` / `build_cmd` 内の絶対 path | manifest、result | build/ccbench root 依存 | (b) placeholder/relative path に production emission 前に正規化、または deterministic build seam が必要（`buildcache.py:162-180`） |
| `cached` | manifest、result | cache の初回/再利用状態 | (a) build seam で固定可能。ただし portable artifact から診断 field を分離する方が長期的には安全（`s8b_floor_campaign.py:856-867`） |
| `store_path` | manifest、result | `out_root` 相対化済み | (a) 同じ layout なら決定的（同:1095-1137） |
| clean scan digest | certificate | repository の file-name 集合 | (a) 制御された tmp repo なら決定的。ただし `run_campaign` は現在 `ROOT` をハードコード（同:1937-1944） |

重要なのは、(b) の正規化を artifact 書き込み後に行ってはいけない点です。manifest bytes の SHA が journal と result に埋め込まれるため、後処理すると binding chain が壊れます（同:1447-1456,1973-1978,1665-1667）。正規化は `assemble_manifest` より前、production の正式な artifact projection として行う必要があります。

### 推奨 seam

最低限、次を追加すべきです。

- `host_provenance_fn(now_fn) -> dict`
- `process_identity_fn() -> dict`
- `execution_receipt_fn(contract, now_fn) -> dict`
- `build_fn` または `build_cells_fn`
- `repo_root` または `clean_scan_fn`
- certificate 発行直後の private `after_certificate_issued_fn`

これらに production default を割り当て、runtime flag や CLI bypass は作らない構造なら、production 経路を維持したままテストだけを決定化できます。

`(c) schema 一致のみ` に落とす必要があるフィールドは本質的にはありません。ただし上記 seam/正規化を導入しないなら、3 artifact 全体について bytes 一致を諦めるしかありません。その場合は V-4 の「実 bytes を G blob にする」という目的を満たしません。

### 既存 official 統合テストの決定化範囲

既存 helper は以下を固定しています。

- fake build
- deterministic measure
- no-conflict probe
- no-op sleep
- 通常は `monotonic_fn=lambda: 0.0`
- 固定 `now_fn`（`orchestrator/tests/test_s8b_floor_campaign.py:186-220`）

official seam は core refusal と clean scan だけを置換しています（同:290-299）。official happy test も certificate 時刻と束縛関係は検査しますが、artifact の SHA を別 run と比較していません（同:1431-1458）。

したがって hostname、boot ID、job ID、cpuset、pid、starttime、UUID、execution receipt は未決定のままです。さらに build root は `tmp_path` 依存です。このテストをそのまま V-4 generator に転用しても bytes reproducibility は得られません。

## 2. G tree blob として commit する現実的手順

Git は一度生成された非決定 bytes でも commit できます。しかし、それは「その場限りの snapshot」であり、再生成 SHA が一致しないため fixture generator としては不適格です。

現実的な手順は次です。

1. tmp repo に clean base を作る。

   - v1 trust root、known axes、design/generator source、陽性対照だけを置く。
   - holdout params、floor result、journal、manifest はまだ置かない。

2. 固定 clock、固定 host/process/receipt、固定 build/measure/probe を注入して official preflight を開始する。

3. production code が `launch_certificate.json` を create-only で発行した直後に checkpoint callback を呼ぶ。

4. callback 内で certificate だけを stage して C commit を作る。

   - campaign の clean scan は C より前に完了済み。
   - G の親が C になるため、世代 JSON の `frozen_at_head=C` も現行 V1a と整合する（`s8b_ratified_freeze.py:757-770`）。

5. 同じ campaign を継続し、manifest → journal sessions → result → terminal を production 経路で生成する。

6. closure artifacts、`result.json`、`journal.jsonl`、`manifest.json`、世代 JSON をまとめて stage し、G commit を作る。

   - generation JSON の `floor_source.sha256` は確定済み result bytes から計算する。
   - closure/floor source/journal/manifest の導入集合が `{G}` であることを検査する。
   - certificate は C にのみ導入済みで、G では変更しない。

7. approval と active pointer を A commit に載せる。

8. 別々の tmp root で同じ builder を2回実行し、少なくとも以下を比較する。

   - certificate SHA
   - result SHA
   - journal SHA
   - manifest SHA
   - 各 Git blob SHA

Git commit SHA 自体まで固定したい場合は author/committer date も固定する必要があります。現 helper は commit 時刻を固定しておらず（`test_s8b_ratified_freeze.py:34-53`）、世代 JSON は C SHA を `frozen_at_head` に持つので、C SHA が変われば generation bytes も変わります（同:240-265）。通常のテストでは commit SHA を再実行間で固定する必要はありませんが、tree/generation SHA の golden 化まで行うなら固定が必要です。

現 `run_campaign` は certificate を書いた直後に launch-start を追記してそのまま build へ進むため、C commit を挟めません（`s8b_floor_campaign.py:1951-1969`）。この checkpoint seam、または preflight/execute の二段 API が V-4 の前提です。

## 3. 負例 matrix への影響

### 現 builder の問題

現在は closure、floor protocol、floor source を base commit に置き、その後 G では世代 JSON だけを追加しています（`test_s8b_ratified_freeze.py:222-240,242-264`）。

そのまま新しい lineage 検査を有効にすると、多くの負例が狙った reason に到達する前に、共通して以下で落ちます。

- certificate より closure が古い
- closure/floor source の導入 commit が G でない
- floor source が production result schema でない
- official result の `eligible_for_refreeze` が False
- journal/manifest/certificate chain が無い

特に production result は `schema` を持つ一方（`s8b_floor_campaign.py:1655-1667`）、oracle fixture は `schema_version` と binaries しかありません（`test_s8b_oracle_driver.py:1268-1288`）。

### 影響する call site

`test_s8b_ratified_freeze.py`:

- `test_happy_path_resolves_and_loads`（274-289）
- `test_ratified_freeze_deep_immutability`（755-763）

`test_s8b_ratified_verify.py`:

- `test_semantic_happy_path_loads_and_launch_validates`
- `test_source_blob_mismatch_rejected`
- `test_design_source_worktree_drift_still_loads`
- `test_frozen_at_head_not_generation_parent_rejected`
- `test_generation_commit_merge_rejected`（専用 helper が builder を利用）
- `test_closure_entry_absent_from_generation_tree_rejected`
- `test_closure_bytes_sha_mismatch_rejected`
- `test_env_tag_unknown_rejected`
- `test_transition_out_of_enumeration_diff_rejected`
- `test_chain_g2_env_tag_unchanged_loads`
- `test_undeclared_hit_outside_closure_rejected`
- `test_declared_closure_hit_absent_from_search_rejected`
- `test_per_holdout_no_crosstalk`
- `test_enumeration_digest_shift_rejected`
- `test_positive_control_not_hit_rejected`
- `test_activation_head_moved_rejected`

直接の利用箇所は `orchestrator/tests/test_s8b_ratified_verify.py:41-157,204-210,229-322,355-385` です。

`test_s8b_oracle_driver.py` では `_build_v2_repo` が常に `floor_source_bytes` と `mutate_g1` を通すため（1291-1307）、以下すべてが影響します。

- `test_v2_gate_happy_path_completes_and_binds_env_store_receipt`
- `test_v2_freeze_bytes_not_active_generation_is_refused`
- `test_v2_launch_validate_failure_is_refused`
- `test_v2_launch_validate_non_ratified_error_is_refused`
- `test_v2_store_missing_is_refused`
- `test_v2_store_hash_mismatch_is_refused`
- `test_v2_contract_sha256_mismatch_is_refused`
- `test_v2_binary_mismatch_abort_maps_to_binary_mismatch_outcome`

利用範囲は同:1331-1494 です。

### 拡張点ごとの追随方針

`mutate_g1`:

- production artifact、全 SHA、certificate/journal chain を完成させた後の generation document に適用する。
- mutation 前に baseline が `load_ratified_freeze` と `launch_validate` を通ることを必須化する。
- 各 test は exact first reason を維持する。
- chain の一辺を狙うテストでは、他の従属 SHA を再計算する「coherent mutation」と、raw bytes を壊す「tamper mutation」を分ける。

`extra_closure`:

- base ではなく G stage に file を追加し、generation document に正しい SHA を追加する。
- 現在の `output/s8b-freeze/hidden_measure.json` は `(ix)-9` hardening 後に unknown freeze artifact reason が先に出る可能性が高い（`test_s8b_ratified_verify.py:240-252`）。
- このテストは二分するべきです。

  - unknown/excluded namespace を拒否するテスト
  - search report を局所 seam で欠落させ、純粋に expected-hit missing を検査するテスト

`floor_source_bytes`:

- raw bytes 全置換 API は廃止する。
- `mutate_floor_result(doc)`、`mutate_manifest(doc)`、`mutate_journal(records)` の段階 hook に置換する。
- 正常 oracle fixture は production result をそのまま使う。
- store missing/hash mismatch は committed result を変えず、G 検証後の store 実体だけを欠落・改竄させる。これなら intended oracle reason に到達します。

`g2`:

- `_build_g2` は現在 g1 の closure/floor artifacts を再利用します（`test_s8b_ratified_verify.py:329-343`）。
- 導入 commit `{G_N}` を各世代で要求するなら、g2 builder も新しい production run_dir 一式を G2 に導入する必要があります。
- one-shot 裁定との関係上、「g2 の load は可能だが同じ初回 cert schema で official launch は不可」なのか、「g2 自体も新 schema が必要」なのかをテスト名と gate 層で分離すべきです。

攻撃 matrix の空洞化防止には、テストを `{baseline validator, mutation stage, expected first reason}` の表として持たせるのが有効です。単に「何らかの refusal」だけを確認するテストへ緩めてはいけません。

## 4. 安全な実装順序

1. 決定性 characterization test を追加する。

   同一 protocol/freeze を異なる tmp root で2回生成し、3 artifact の SHA が現状不一致になることをまず露出する。official core refusal テストは維持する。

2. build artifact の portable 表現を決定する。

   `binary` と command path を out-root-relativeまたは canonical placeholder 化し、`cached` の扱いを固定する。正規化は manifest hash 計算前に行う。

3. provenance 注入を追加する。

   host、process identity、execution receipt を private seam 化し、production defaults は現行関数へそのまま委譲する。

4. real tmp-repo scan を通せるようにする。

   `ROOT` ハードコードを private `repo_root` seam にし、既存の clean-digest stub だけでなく実 `clean_scan_digest` を通す E2E を作る。

5. certificate checkpoint を追加する。

   certificate 発行直後に C を作り、同じ campaign が G artifact 生成まで続行できるようにする。pre-start resume を使うなら、その意味論を先に production 側で完成させる。

6. official finalize semantics を直す。

   現在は official seam で完走しても `eligible_for_refreeze=False` です（`s8b_floor_campaign.py:1659-1662`）。裁定どおり official 完走時だけ True にし、artifact verifier と同時に固定する。

7. production-bytes staged builder を作る。

   base → C → G → A を完成させ、二重生成 SHA テストを通す。

8. `mutate_g1` 系を移行する。

   source/frozen/closure/env/transition の順に、expected first reason を1件ずつ維持する。

9. scan/closure 負例を移行する。

   undeclared、missing、per-holdout、enumeration、positive-control をそれぞれ独立 mutation にする。

10. oracle fixture を production result へ移行する。

    store 消費テストを最後に移す。すべての baseline が新 `launch_validate` を通ってから store 攻撃が発火することを確認する。

## 技術的リスク

| 重大度 | 論点 | 根拠 file:line | 対処 |
|---|---|---|---|
| 重大 | 現6注入点だけでは host/process UUID を固定できず journal/result SHA が毎回変わる | `s8b_floor_campaign.py:773-790,1443-1458,1650-1690` | provenance/process/receipt の private seam を追加 |
| 重大 | manifest の絶対 build path が tmp root を bytes に混入させ、その hash が journal/result に連鎖する | `s8b_floor_campaign.py:838-867,1447-1456,1973-1978`; `buildcache.py:123-131,162-180` | emission 前に relative/canonical 化 |
| 重大 | 現 `run_campaign` は certificate 発行と journal/build が連続し、C commit を挟めない | `s8b_floor_campaign.py:1951-1969` | certificate-issued checkpoint または二段 core |
| 高 | tmp repo の実 clean scan を production 経路で使えず `ROOT` に固定される | `s8b_floor_campaign.py:1937-1944` | private `repo_root` seam |
| 高 | 既存 official 統合テストは provenance と artifact SHA 再現性を検査していない | `test_s8b_floor_campaign.py:210-220,290-299,1431-1458` | 異なる tmp root 間の SHA equality test |
| 重大 | 現 builder は closure/result を base に置くため、新 lineage では全負例が早期共通 reason に潰れる | `test_s8b_ratified_freeze.py:222-240,242-264` | closure/run_dir/generation をすべて G で初導入 |
| 高 | oracle fixture が production result schema ではない | `test_s8b_oracle_driver.py:1268-1288`; `s8b_floor_campaign.py:1655-1693` | raw `floor_source_bytes` を廃止し production result を利用 |
| 高 | official fixture が現状 `eligible_for_refreeze=False` となり、新 strict parse の happy path にならない | `s8b_floor_campaign.py:1659-1662` | official 完走 finalize 時のみ True |
| 高 | artifact 書き込み後の正規化は manifest hash chain を破壊する | `s8b_floor_campaign.py:1447-1456,1665-1667,1973-1978` | assembly/hash 前に canonical projection |
| 中 | builder の Git commit 時刻が未固定で C SHA、generation bytes、approval chain が再実行間で変わる | `test_s8b_ratified_freeze.py:34-53,240-265` | tree/commit golden が必要なら Git author/committer date を固定 |
| 高 | `extra_closure` の excluded namespace 負例は `(ix)-9` hardening 後に別 reason が先に出る | `test_s8b_ratified_verify.py:240-252` | namespace 拒否テストと missing-hit テストを分離 |
| 高 | g2 helper が g1 artifact を再利用し、導入 commit `{G2}` 条件と衝突する | `test_s8b_ratified_verify.py:329-343` | g2 用 run artifacts を G2 に新規導入、one-shot gate と load gate を分離 |
| 中 | `(ix)-10` は追認済みだが、基礎となる前 wave closure schema `(i)/(ii)` は未裁定 | `2026-07-18_s8b-c22-consultations.md:97-110,141-144` | topology と schema を分離し、builder の closure record 生成を差し替え可能に保つ |

総合裁定は「条件付き feasible」です。V-4 を最初に実装するのではなく、artifact projection、provenance injection、certificate checkpoint の3点を production 側で先に決定化する必要があります。
#### 相談 V3 (gpt-5.6-sol reasoning=max, read-only, cwd=worktree)

結論: **v3 のまま実装開始は不可**です。最大の問題は、(ix)-4 の one-shot を verifier が強制せず g2 を受理する点と、V-6 が (ix)-9 の exact path+bytes 方式と同値でない点です。

## 所見

1. `{severity: must-fix, タイトル: (ix)-4 one-shot が docstring に退化し、g2 を受理する}`

- 攻撃シナリオ: g1 用 certificate C を再利用し、C の後に自己整合した新 result/journal/manifest/closure を持つ g2 を作る。現 transition は g2 の floor/source 変更を許し、プランは全世代を同じ `launch_validate` で検証するため通る。C の clean scan は g2 測定前を証明しない。
- 根拠: プランは世代番号を検査しないと明記 [plan:43-45](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22v-plan-v3.md:43)。裁定は現 certificate を v1→g1 専用とする [裁定:102](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-18_s8b-c22-consultations.md:102)。実装は gN の floor/source 変更を許し [s8b_ratified_freeze.py:109](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:109)、既存テストも g2 load 成功を固定している [test_s8b_ratified_verify.py:204](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_verify.py:204)。
- 提案: `launch_validate` で certificate schema v1 について `generation_number == 1` と v1 supersedes を強制し、専用 reason `certificate-generation-scope` を返す。g2 の静的 load 自体は将来 schema のため維持する。

2. `{severity: must-fix, タイトル: V-6 の「未知 file 拒否」は (ix)-9 の exact 免除方式ではない}`

- 攻撃シナリオ: active g1 に加えて、正規 filename の未承認 g2、未参照 approval、revocation 等へ holdout 三軸を埋める。これらは「未知 file」ではないため resolver を通り、scanner の prefix 除外で隠れる。逆に、正当に宣言された closure file が freeze namespace 内にある場合は未知扱いで早期拒否される。
- 根拠: 裁定は「既知宣言 artifact の exact path + bytes hash 免除」を要求する [裁定:138-140](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-18_s8b-c22-consultations.md:138)。提案は resolver の未知 file 拒否へ置換している [plan:68-72](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22v-plan-v3.md:68)。resolver は正規形 record を広く受理し、その他だけを無視する [s8b_ratified_freeze.py:901](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:901)、[同:969](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:969)。scanner は依然 prefix 全除外 [s8b_holdout_freeze.py:32](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_holdout_freeze.py:32)。
- 提案: resolver ではなく scan 境界を直す。検証済み active-chain artifact の exact path/hash だけを免除し、orphan/candidate/未知 file は通常 scan または拒否へ回す。resolver の closed namespace 化も行うなら、(ix)-9 とは別の受理条件として追認を取る。

3. `{severity: must-fix, タイトル: eligible_for_refreeze の mode-only 判定は「finalize 時のみ True」ではない}`

- 攻撃シナリオ: official runner 完了後、artifact 自己検査または `_finalize` が失敗する。`assemble_result` が `mode=="official"` だけで True を生成すると、completed terminal の無い partial result に True が残り得る。
- 根拠: V-3 は `mode == "official"` とだけ規定 [plan:47-49](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22v-plan-v3.md:47)。裁定は「official 完走 finalize 時のみ True」 [裁定:106](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-18_s8b-c22-consultations.md:106)。現フローでは result 組立てが自己検査・finalize より前 [s8b_floor_campaign.py:2026](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:2026)、result 書込みも completed terminal より前 [同:1807](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1807)。
- 提案: mode-only 式を禁止し、二相 finalize 状態を定義する。verifier は `mode/flag/一意かつ最終の completed terminal/自己検査済み result` を独立導出し、bool 単体を証拠にしない。

4. `{severity: must-fix, タイトル: pre-start resume が launch-start-only crash を回収しない}`

- 攻撃シナリオ: certificate と launch-start を耐久化した直後、`build_cells` が失敗する。journal は `[launch-start]` だけだが manifest は無い。V-3 は manifest 存在を要求するため resume 不能で、fresh retry は二枚目の certificate と orphan attempt を作り得る。
- 根拠: V-3 の受理条件 [plan:50-53](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22v-plan-v3.md:50)。既存回帰テストはまさに `launch-start` のみ・manifest 無しを作る [test_s8b_floor_campaign.py:1482](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_floor_campaign.py:1482)、[同:1500](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_floor_campaign.py:1500)。現 resume は campaign-start 不在を一律拒否する [s8b_floor_campaign.py:2130](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:2130)。
- 提案: 少なくとも `L=launch-startのみ` と `M=launch-start+sealed manifest` の二状態を定義する。L から同じ run/cert の下で build/store/manifest を再構築できないなら、失効方式へ戻るため新たな裁定が必要。

5. `{severity: must-fix, タイトル: journal 状態機械が wall_ledger 射影だけに縮退している}`

- 攻撃シナリオ: campaign-start、round-start/complete、completed terminal だけを整合させ、result の全 session throughput を都合よく再生成する。`verify_floor_artifact` は内部再計算には成功するが、raw journal の attempt/session/receipt 真正性を保証しない。
- 根拠: プランは wall_ledger 対象三 event と terminal の存在だけを明記 [plan:30-33](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22v-plan-v3.md:30)。裁定は raw journal からの決定的射影を要求 [裁定:113-116](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-18_s8b-c22-consultations.md:113)。`verify_floor_artifact` 自身も raw session 真正性は保証外と明記する [s8b_floor_stats.py:438](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_stats.py:438)。
- 提案: Q-B は「実行する」が正しい。ただし補助ゲートであり代替ではない。JSONL の exact event schema、順序、session start/end、seq/attempt/retry 一意性、binary receipt、manifest schedule、result.sessions、terminal 一意・最終性まで照合する。

6. `{severity: must-fix, タイトル: run-id と certificate.started_utc の同一起点が検証鎖から抜ける}`

- 攻撃シナリオ: path は `20260718T010000Z-<proto8>`、certificate は別の正規 UTC 時刻を持たせる。run-id と protocol hashは一致するため現 validator とプランの expected_run_id 検査を通る。
- 根拠: issuer は一つの時刻から run-id を生成する [s8b_floor_campaign.py:2052](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:2052)。validator は UTC 形式と run-id を別々に見るだけ [同:1041](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1041)、[同:1063](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1063)。追認された推奨は同一時刻起点を含む [consultation:318](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-18_s8b-c22-consultations.md:318)。
- 提案: path parser が timestamp を返し、`started_utc` を canonical UTC に正規化して秒単位で完全一致させる。

7. `{severity: must-fix, タイトル: 未裁定事項が Q のまま normative 実装へ混入する}`

- 攻撃シナリオ: Q-D で既存 `validate_protocol` を採ると、未追認の exact 18-key/`contract_sha256` を launch acceptance に固定する。journal/manifest の導入 commit==G、manifest mode 制約、cert の union 編入も裁定文より広い受理条件になる。
- 根拠: Q-D と追加条件 [plan:16](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22v-plan-v3.md:16)、[同:29](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22v-plan-v3.md:29)、[同:35](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22v-plan-v3.md:35)、[同:39](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22v-plan-v3.md:39)。前 wave (v) は未裁定 [strict-v2 §5:601](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:601)。
- 提案: 本 wave は `strict parse → canonical hash` までに限定する。full protocol validate、manifest の G 同梱/mode、cert union は個別追認を取る。

8. `{severity: must-fix, タイトル: V-7 は攻撃名の列挙であり、変異を殺す executable matrix になっていない}`

- 攻撃シナリオ: one-shot check、raw journal 照合、VerifiedFloorArtifact 消費のいずれかを削除しても、「chain 改竄」「oracle mutation」という抽象行だけでは該当テストが存在せず、mutation 残群ゼロでも最終ゲートを通せる。
- 根拠: V-7 は broad category のみ [plan:74-79](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22v-plan-v3.md:74)。F9 は対象不在の偽緑を禁止 [failures:F9](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/failures.md:88)、F15 は mock 分布不足 [failures:F15](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/failures.md:141)、F21 は call/presence と実結線の混同 [failures:F21](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/failures.md:247)。
- 提案: 各 invariant に「単一負例・整合同時改竄・殺す mutation・期待 reason・副作用ゼロ」を対応付け、未実行/生存 mutant を failure にする。

9. `{severity: should-fix, タイトル: reason code の「閉じた表」が新しい失敗面を覆わない}`

- 攻撃シナリオ: g2 scope 違反、scan exemption 不正、terminal 状態不正、manifest semantic 不正が、低レベル `multiple-introduction` や汎用 `binding-chain-mismatch` に潰れる。consumer が拒否理由を安定分類できない。
- 根拠: 提案表は6分類のみ [plan:40-42](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22v-plan-v3.md:40)。元相談も既存低レベル reason 漏出を警告している [consultation:348-352](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-18_s8b-c22-consultations.md:348)。
- 提案: `certificate-generation-scope`、`scan-exemption-invalid`、`journal-state-invalid`、`floor-artifact-invalid`、`manifest-invalid` を外向き表へ追加し、低レベル reason は `cause` に残す。

## (1) 裁定 (ix)-1〜10 への準拠

| 裁定 | 判定 | 理由 |
|---|---|---|
| (ix)-1 | 部分準拠 | hash chain は概ね準拠。ただし raw attempt/session/receipt と terminal 状態機械が不足 |
| (ix)-2 | 準拠＋逸脱 | cert 一意・非merge・厳密祖先は準拠。journal/manifest 導入==G は裁定外 |
| (ix)-3 | 準拠 | closure + floor_protocol + result + journal + manifest の union は裁定どおり。cert は含めない |
| (ix)-4 | **違反** | verifier が g2+ を拒否しない |
| (ix)-5 | 部分準拠 | manifest 済み pre-start だけを扱い、launch-start-only を回収しない |
| (ix)-6 | **違反** | `mode=="official"` と finalized は同値でない |
| (ix)-7 | 部分準拠 | canonical layout/mode は方向として正しいが、UTC↔run-id が抜ける。manifest mode は裁定外 |
| (ix)-8 | 準拠条件付き | VerifiedFloorArtifact を返すだけでなく consumer がその同一 object を使う必要がある |
| (ix)-9 | **違反** | resolver closed-world は exact path+bytes exemption の代替ではない |
| (ix)-10 | 準拠＋逸脱 | closure/floor_source 導入==G は準拠。journal/manifest まで広げるのは裁定外 |

新たな追認が必要なのは、少なくとも次です。

- full `validate_protocol` の採用
- journal/manifest の導入 commit==G
- manifest への mode 制約
- cert bytes の期待 union 編入
- launch-start-only・manifest無し状態の回復方式
- resolver namespace 自体を closed-world にする追加方針

Q-A の module 移設、Q-E の helper 削除/非公開化、reason の内部翻訳は実装判断であり、新たな裁定は不要です。

## (2) 前 wave §5 (i)〜(viii) との抵触

- (i): header/schema を変更しなければ抵触なし。V-4 は現 schema を利用するだけに限定すべき。
- (ii): (ix)-10 が追認したのは **closure/floor_source 導入==G の狭い部分だけ**。journal/manifest 同梱や §5-(ii) 全体の追認と扱ってはいけない。
- (iii)、(iv): 現プランは直接触れない。`verify_floor_artifact` を理由に oracle edge/scale 判定へ変更を波及させないこと。
- (v): Q-D の full protocol validate が直接抵触する。現 validator は未追認の18 keyを強制する [s8b_floor_campaign.py:101-110](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:101)。
- (vi)、(vii): 直接抵触なし。active/revoked の意味を変更しないこと。
- (viii): V-6 を「隠し場所を閉じた」と表現すると過大保証。pre-certificate 削除痕跡、ignored領域、内容TOCTOUは残る。
- `master_seed/env_tag`: 実値の受領・凍結は行わない。`doc.env_tag` と path の一致は (ix)-7 の範囲だが、full protocol validatorによる自由 field の normative 受理は別。

## (3) Q-F / V-6 の実査結果

`git ls-tree -r -l HEAD -- output/s8b-freeze/` の実結果は一件だけです。

- `100644 output/s8b-freeze/holdout_freeze.json`
- size 27,942 bytes
- content SHA-256 `315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688`
- README、v2 generation、approval、pointer は存在しない
- 定数も同じ path/hash [s8b_ratified_freeze.py:49-50](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:49)

互換性の結論は次です。

- 実 repo の現 treeだけなら未知 file 拒否を入れても回帰しない。
- v1 の `load_legacy_freeze` は resolver を通らず、canonical path の worktree bytesだけを読む [s8b_ratified_freeze.py:1167](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:1167)。したがって resolver変更は v1 検証を強化もしない。
- untracked/modified file は既に `_assert_namespace_clean` が拒否する [同:199](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:199)。V-6 が新たに閉じるのは主に「tracked regular unknown file」だけ。
- 既存 `test_declared_closure_hit_absent_from_search_rejected` は、freeze namespace の未知 closure を静的 load させた後、scan mismatch を期待する [test_s8b_ratified_verify.py:240-252](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_verify.py:240)。resolver 拒否へ変えるとこの既存攻撃テストは早期 reason へ変質する。
- 発行側には既に exact allowlist があり [s8b_floor_campaign.py:920-977](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:920)、未知 file 拒否と exact hash 受理の正負テストも存在する [test_s8b_floor_campaign.py:1349-1374](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_floor_campaign.py:1349)。

したがって Q-F の答えは **不適合**です。resolver の未知 file 拒否は defense-in-depth にはなり得ますが、(ix)-9 の実装ではありません。

## (4) V-7 に追加すべき負例・変異

| 境界 | 必須の追加負例 | 殺すべき変異 |
|---|---|---|
| one-shot | g2 が g1 cert を再利用／g2 が新しい自己整合 result を持つ | generation check 除去、`==1`→`>=1` |
| journal | terminal 0/2件、completed が最終でない、aborted+completed、session/attempt/receipt 欠落・重複、truncated JSONL、duplicate key/NaN | raw journal 読取除去、result.wall_ledger だけ使用、event validator除去 |
| finalize | pilot true、official false、aborted/artifact-invalid true、result書込み後terminal前 crash | `mode=="official"` 単独判定 |
| pre-start resume | launch-startのみ、manifestあり、manifest欠落、store途中、二回resume、campaign-start append crash | manifest必須分岐除去、cert意味再検証除去 |
| path/time/mode | absolute、`.`/`..`、二重slash、backslash、別env、pilot namespace、proto8大小/長さ、basename違い、run時刻≠started_utc、120000/160000 | parser呼出し除去、component比較を一つずつ除去 |
| binding | protocol/freeze/manifest/cert各辺の単独破壊に加え、全値を同時に偽造した自己整合 island、manifest binaries≠journal receipt | 一辺の比較除去、raw bytes hash→再直列化 hash |
| lineage | C==G、Cが兄弟、merge C、delete/re-add、add/add merge、closure pre-C、closure intro≠G、unapproved g2 | strictness反転、全導入量化→任意一件、G equality除去 |
| union | 各 source にだけ unique hitを置く5ケース、certにhitを入れて拒否、path衝突、NUL/非UTF-8 | 各 source の union追加を一つずつ除去 |
| scan exemption | tracked/untracked unknown、exact path wrong hash、right hash wrong path、symlink、prefix似 (`s8b-freeze-evil`)、認識済み orphan record | prefix除外復活、hash検査除去、unknown `continue` 復活 |
| oracle | `launch_validate` call除去、戻り値破棄、floor blob再読込、permissive再parse、verified object不使用 | V-5で廃止する旧経路を一つずつ復活 |
| E2E | production dormant core→実bytes→C→G→A→load→launch_validate→oracle、build/store/manifest/finalize各 failure | stub artifactへの置換、official seamがmode/path検証まで無効化 |

既存 oracle fixture はまだ実 result schema ではなく `{schema_version,binaries}` の stubです [test_s8b_oracle_driver.py:1268-1287](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_driver.py:1268)。V-4 完了前に V-5/V-7 の正例を固定してはいけません。

## (5) failures 型タグによる再発面

- F2 `[ドリフト]`: fresh/resume/verifier の validator・path parser を一つの leaf moduleへ集約し、re-export identity testを置く。
- F9/F14 `[恒真ゲート]`: one-shot の docstringだけ、存在しない fixture の skip、mutation 0件を成功扱い、を禁止する。
- F15 `[テスト代表性]`: 手書き floor stubを廃止し、実 producer bytesで manifest/result/journal の実 hit分布を踏む。
- F16/F17 `[恒真ゲート][ドリフト]`: VerifiedFloorArtifact の field/call存在だけを証明にせず、consumerが同一objectを使うことを mutationで固定する。
- F19 `[手順漏れ]`: build/store/manifest/finalize failureを注入し、特に launch-start-only 状態を踏む。
- F21 `[恒真ゲート][テスト代表性]`: helper単体ではなく issuer→Git topology→verifier→oracle のlive連鎖を一本通す。
- F7 `[権限逸脱]`: 並列 Codex には重複する file ownershipを与えず、他レーン差分を取り込む際に内容監査する。

## (6) 実装順序と安全なファイル素集合

依存関係は次です。

```text
裁定穴の解消
  ├─ V-1 共有 validator/path parser
  └─ V-6' exact scan-exemption API
          ↓
      V-2 verifier ─┐
      V-3 issuer   ─┴→ V-4 production-bytes fixture → V-5 oracle型伝搬 → V-7/E2E・mutation
```

安全な順序:

1. g1-only、pre-manifest resume、exact exemption、Q-D/C の裁定を確定。
2. V-1 を単独で実施。`floor_campaign` と `ratified_freeze` の re-export/import まで同じ担当が行う。
3. corrected V-6 の scanner coreを実施。
4. V-2 と V-3 を並列実施。
5. 両 production API 固定後に V-4。
6. fixture固定後に V-5。
7. 最後に V-7/E2E/mutation。

並列ファイル素集合は以下が安全です。

- `S0` 共有部品: `s8b_launch_cert.py` + 専用テスト。`floor_campaign.py`/`ratified_freeze.py` の re-export 編集はこの段階で完了させ、後続と重ねない。
- `H` scan core: `s8b_holdout_freeze.py` + `test_s8b_holdout_freeze.py`
- `R` verifier: `s8b_ratified_freeze.py` + `test_s8b_ratified_freeze.py` + `test_s8b_ratified_verify.py`
- `F` issuer: `s8b_floor_campaign.py` + `test_s8b_floor_campaign.py`
- `O` consumer: `s8b_oracle_driver.py` + `test_s8b_oracle_driver.py`

`R` と `F` は V-1/V-6 API固定後なら並列可能です。`test_s8b_ratified_freeze.py` は verify/oracle双方が fixture として importするため、V-4を別Codexへ分けず `R` の単一所有にしてください。V-6 原案を採る場合は `s8b_ratified_freeze.py` を触るため V-2 と並列不可です。V-7 を並列化するなら、既存共有テストを同時編集せず、境界別の新規 test fileへ分けるのが安全です。
### §9 付録 — 検証側プラン v3 全文 (§8 の相談の攻撃対象)

    # C2-2 検証側実装プラン v3 (裁定発効 wave、敵対相談用ドラフト。untracked・非 commit)
    
    裁定の正本 = output/insights/2026-07-18_s8b-c22-consultations.md §5 冒頭「裁定結果」ブロック。
    (ix)-3=(a) union 導出 / (ix)-4=one-shot / (ix)-5=pre-start resume / (ix)-6=official finalize のみ True /
    (ix)-1/-2/-7/-8/-9/-10 追認。前 wave §5 (i)〜(viii) と master_seed/env_tag は未裁定のまま (越権禁止)。
    
    ## V-1 共有部品 (新 module 案: orchestrator/campaign/s8b_launch_cert.py)
    - LAUNCH_CERT_SCHEMA / validate_launch_certificate / run-layout path parser (canonical root-relative、
      output/env/<env_tag>/calibration/s8b-floor-official/<ts>-<proto8>/<basename>、成分文法) を
      floor_campaign から移設し、floor_campaign は後方互換 re-export。ratified_freeze はここから import
      (循環回避)。**Q-A**: 移設 vs ratified_freeze→floor_campaign 直 import (重依存) vs 重複実装 (F2 型)
    
    ## V-2 launch_validate 拡張 (s8b_ratified_freeze.py、現行 1240-1312 に挿入)
    1. floor_source.path を path parser で検証 ((ix)-7: env_tag == doc.env_tag、proto8 ==
       canonical_sha256(floor_protocol blob)[:8]、basename == result.json)。G tree の ls-tree mode
       100644/100755 検査 (cert/journal/manifest も同様)
    2. floor artifact strict parse (duplicate key/NaN 拒否): schema == s8b-floor-result/v2、
       mode == "official"、eligible_for_refreeze is True ((ix)-6 整合検査)。VerifiedFloorArtifact
       (bytes/sha256/deep-immutable doc) を構築し LaunchValidatedFreeze に保持 ((ix)-8)
    3. run_dir = dirname(floor_source.path)。journal.jsonl / manifest.json / launch_certificate.json を
       G tree から読取
    4. cert 束縛: bytes sha256 == journal launch-start == journal campaign-start ==
       result.wall_ledger campaign-start の launch_certificate_sha256。validate_launch_certificate
       (expected_v1 = V1_FREEZE_SHA256 / expected_protocol = 下記 P / expected_run_id = basename(run_dir))
    5. equality chain ((ix)-1): P := canonical_sha256(strict_parse(floor_protocol blob)) ==
       result.protocol_sha256 == journal campaign-start.protocol_sha256 == cert.protocol_sha256。
       freeze: V1_FREEZE_SHA256 == result.freeze_sha256 == journal.freeze_sha256 == cert.v1_freeze_sha256。
       manifest: sha256(manifest blob) == result.manifest_sha256 == journal.manifest_sha256。
       **Q-D**: protocol は validate_protocol 相当の full validate まで行うか、canonical hash 再計算のみか
    6. journal 状態機械 ((ix)-1): strict JSONL parse。launch-start 先頭一意 → campaign-start 一意 →
       terminal completed 存在。result.wall_ledger == journal からの決定的射影 (campaign-start /
       round-start / round-complete の dict 複写) の完全一致。**Q-B**: s8b_floor_stats.verify_floor_artifact
       (result 自己検査) を launch_validate 内でも回すか (expected 値が chain から揃うか実査せよ)
    7. lineage ((ix)-2 / (ix)-10): cert path の導入 = 一意・非 merge・G の**厳密祖先** (anchor != G ∧
       is_ancestor)。closure entries + floor_source + journal + manifest の導入 commit == {G} (一意)。
       既存 V1d (789-810) との統合位置
    8. 期待 hit union ((ix)-3 (a)): texts = closure entries + floor_protocol + result + journal + manifest
       の bytes → holdout_conjunction_hits → per-holdout 期待集合 → worktree scan hit と完全一致 (現行
       1294-1304 の期待側差し替え)。**Q-C**: cert bytes を union に含めるか (現状 hit なしだが将来)
    9. reason codes: floor-source-invalid / launch-certificate-invalid / launch-certificate-path-invalid /
       certificate-lineage-ambiguous / journal-invalid / binding-chain-mismatch。低レベル reason を
       cause に保持して閉じた表へ翻訳 (B10)
    10. one-shot ((ix)-4): 検証器は世代番号の特別扱いをしない (全世代同一検証)。「二回目 official が
        cert を取れない」のは発行側 (clean scan) の性質として docstring 明記のみ。**攻撃せよ**: g2+ で
        floor 変更 transition が許される現行表とこの検証の整合
    
    ## V-3 発行側の裁定追随 (s8b_floor_campaign.py)
    - eligible_for_refreeze: 定数 False → `mode == "official"` ((ix)-6)。コメント 1497-1504 の意図書き
      換え + verify_floor_artifact / 既存テスト追随
    - pre-start resume ((ix)-5): official resume で journal == [launch-start のみ] の場合に限り、
      cert bytes == launch-start sha / validate_launch_certificate (run_id == run_dir.name) /
      manifest 存在 + resume manifest 整合 / session・round record ゼロ、を全て満たせば campaign-start を
      初回発行して続行。pilot 不変。その他の campaign-start 欠落は従来どおり拒否
    
    ## V-4 fixture 段階 builder (テスト側)
    - build_valid_semantic_g1 再設計: base(clean、closure params 無し) → C commit (cert のみ) →
      G commit (run_dir 一式 = result/journal/manifest + closure params + 世代 JSON) → approval/pointer。
      run_dir 一式は production 経路 (dormant core + seam) で生成した実 bytes を使う (F15 対策、
      手書き stub 廃止)。mutate_g1 / extra_closure / floor_source_bytes 拡張点の互換方針
    - 既存 launch_validate 系テスト全 call site 追随 + 各負例の「最初に発火する reason」再確認。
      oracle fixture (test_s8b_oracle_driver.py 1268-1307) を production result schema へ
    - 三軸リテラル同居禁止 (実行時結合) 維持
    
    ## V-5 oracle 型伝搬 ((ix)-8)
    - _prepare_v2_execution が launch_validate 戻り値の VerifiedFloorArtifact を消費し再読込を廃止。
      **Q-E**: read_floor_source_blob の去就 (削除 / 内部 helper 化 / 互換維持)
    
    ## V-6 scan 除外の恒久設計 ((ix)-9)
    - 案: resolver (_collect_records、現行 969-973 は未知 file 無視) が output/s8b-freeze 内の未知
      file を fail-closed 拒否 → prefix 除外の隠し場所を閉じる (exact 免除方式と同等の安全性質)。
      **Q-F**: repo 実態 (v1 file / README 等) と v1 検証への互換性を実査し、この同等設計が (ix)-9 の
      裁定 (exact path+bytes 免除への移行) の趣旨に適合するか攻撃せよ
    
    ## V-7 テスト・変異
    - 攻撃 matrix: chain 各辺の単独改竄 + 整合同時改竄 / cert 同一 commit・複数導入・merge・後付け /
      journal 不在・状態機械破り・wall_ledger 偽造 / path 偽装 (別 namespace・symlink mode・run-id) /
      union 各ソース欠落 / eligible False official / pre-start resume 正負 / oracle mutation
      (launch_validate call 除去・verified 物の不使用)
    - 変異最終ゲート: C12 残群 (parser/binding・lineage・journal/resume・consumer)
    
    拘束: 実 artifact 生成なし (official 拒否不変・全テスト tmp-only)。前 wave §5 (i)〜(viii) の未裁定
    領域に新たに踏み込まない。子/codex は巻き戻し系 git 禁止・三軸リテラル同居禁止。
