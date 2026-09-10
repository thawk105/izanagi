## 所見

### 1. `real` / must-fix — `VerifiedAcceptanceReceipt` は gate を通らず生成できる

`VerifiedAcceptanceReceipt` は公開 dataclass で、`_seal` もコンストラクタ引数です。seal 本体も module 属性として参照できるため、`verify_acceptance_receipt` を呼ばずに任意の `AcceptanceReceipt` を封入できます。[s8c_acceptance_receipt.py:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:87) [s8c_acceptance_receipt.py:125](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:125) [s8c_acceptance_receipt.py:144](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:144)

さらに、正規の verified object を一つ得た後なら、`dataclasses.replace` で `receipt` だけを差し替えて同一 seal を継承できます。`require_current_verified_receipt` を必ず呼ぶ consumer は再検証されますが、型または seal を直接 capability として信じる入口は迂回されます。[s8c_acceptance_receipt.py:1183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:1183)

成果物影響: 直接 capability を信じる consumer では、任意の `certifying`、arm execution、trial 参照を certified 選択・レポート・台帳へ渡せる。全 consumer が `require_current_verified_receipt` を通す場合だけ影響しない。

### 2. `real` / must-fix — resolver の誤りを共有して緑になる正例がある

fixture は `resolve_arm_input` の結果を descriptor、receipt、report、journal の actual 全部へ入れています。[test_s8c_acceptance_receipt_v2.py:100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:100) [test_s8c_acceptance_receipt_v2.py:106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:106) [test_s8c_acceptance_receipt_v2.py:112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:112) [test_s8c_acceptance_receipt_v2.py:139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:139)

verifier の expected も同じ `resolve_arm_input` から取得します。[s8c_acceptance_receipt.py:813](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:813)

この自己整合で誤 resolver を隠す正例は少なくとも次です。

- `test_v2_producer_equivalent_full_verify_drops_only_c02` [test_s8c_acceptance_receipt_v2.py:264](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:264)
- `test_origin_terminal_projection_is_retained_and_reverified` の最初の受理 [test_s8c_acceptance_receipt_v2.py:460](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:460)
- `test_v2_never_routes_through_v1_mandatory_reason_set` [test_s8c_acceptance_receipt_v2.py:533](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:533)
- `test_v3_requires_cross_binding_receipt_sha256` の最初の受理 [test_s8c_acceptance_receipt_v2.py:549](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:549)

M1 は比率 80 を独立に assert して 79 へ変えるため、その一点については自己整合を破っています。しかし他 field、他 arm、off artifact、holdout mapping の resolver 誤りは正例で検出できません。[test_s8c_acceptance_receipt_v2.py:289](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:289)

成果物影響: resolver の共通誤実装がそのまま受理 oracle となり、将来の certified 選択・レポート・台帳が ratified freeze と異なる digest または条件を記録しうる。

### 3. `real` / nit — M2 は正規実環境では恒真で、KILLED が人工的

legacy entry の 6-key 検査は、hash 固定された legacy document とコード内の固定 literal set の比較です。[s8c_acceptance_receipt.py:706](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:706) [s8c_acceptance_receipt.py:728](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:728) 裁定は V1 hash の差し替えを禁止しています。[s4-adjudication.md:66](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1726-freeze-rederive/s4-adjudication.md:66)

M2 test は artifact bytes を変えず、検証済み document と旧 sha の対応を壊した `LegacyFreeze` を直接作り、loader 自体を差し替えています。[test_s8c_acceptance_receipt_v2.py:320](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:320) [test_s8c_acceptance_receipt_v2.py:326](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:326) したがって正規 loader と固定 hash の組み合わせでは key-set 述語は偽にならず、M2 の KILLED は receipt 受理集合への検出力を示しません。

4-key 投影と derangement 比較は完全な論理的恒真ではありません。legacy 側は固定なので、偽になるのは in-source `HOLDOUTS` または `DERANGEMENT` が独立に変わった場合、loader 契約が破られた場合、または裁定に反して authority 世代を更新した場合だけです。[s8c_acceptance_receipt.py:759](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:759) [s8c_acceptance_receipt.py:784](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:784) M3 はこのうち source drift を monkeypatch しています。[test_s8c_acceptance_receipt_v2.py:346](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:346)

成果物影響: 現行の compliant verifier では receipt の値や受理集合は変わらないため nit。これらは receipt mutation gate ではなく verifier authority drift gate である。

### 4. `refuted` — M1 positive control の単一理由性は静的には成立する

M1 は descriptor の整数を変え、receipt・report・run-start の content digest と binding digest、参照 hash、tracked receipt を同期しています。[test_s8c_acceptance_receipt_v2.py:281](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:281) [test_s8c_acceptance_receipt_v2.py:296](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:296)

既存 gate は descriptor hash、report arm execution、binding digest、run-start equality を順に検査しますが、すべて同期済みです。[s8c_acceptance_receipt.py:935](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:935) [s8c_acceptance_receipt.py:957](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:957) [s8c_acceptance_receipt.py:962](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:962) [s8c_acceptance_receipt.py:970](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:970) `binding.ycsb_rratio` は既存比較対象ではなく、追加された head も変更されていません。[s8c_acceptance_receipt.py:920](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:920)

最初の不一致は expected content digest 比較です。[s8c_acceptance_receipt.py:841](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:841) test は完全な最終メッセージを要求するため、別の authority error が先行すれば緑になりません。[test_s8c_acceptance_receipt_v2.py:306](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:306)

成果物影響: 先行 gate による偽の KILLED は認められず、M1 に関する受理集合の評価は変わらない。

### 5. `real` / nit — 例外変換が原因別診断を同じ gate へ潰す

全 `RatifiedFreezeError` が一つの `ratified legacy freeze cannot be loaded` へ、全 `ArmInputError` が一つの `trial arm input cannot be rederived` へ変換されます。[s8c_acceptance_receipt.py:706](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:706) [s8c_acceptance_receipt.py:813](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:813) canonical JSON の失敗も投影用の同一理由へ再分類されます。[s8c_acceptance_receipt.py:771](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:771) [s8c_acceptance_receipt.py:787](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:787)

例外 chain は残るものの、最上位メッセージまたは gate 名だけを記録する診断では、artifact hash 不一致、read failure、commit 不在、off artifact 不正、JSON 不正を帰属できません。

成果物影響: すべて fail-closed なので値と受理集合は変わらない。診断と再処置だけの問題であり nit。

### 6. `refuted` — authority をループ前に一回検査する順序で、通常の trial 別 authority は落ちない

parser は六 trial の `measurement_head` が一つであることを先に強制しています。[s8c_acceptance_receipt.py:499](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:499) global legacy/source authority は全 holdout を一回で検査し、各 trial では `holdout`、`arm`、共通 head を渡して resolver を個別に呼びます。[s8c_acceptance_receipt.py:736](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:736) [s8c_acceptance_receipt.py:835](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:835) [s8c_acceptance_receipt.py:1125](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:1125)

同一 call 中に module global を別 thread が差し替えるような trust-boundary 外の変更を除けば、trial ごとに変化する未検査 authority は対象コードから確認できません。

成果物影響: 順序に起因する追加の誤受理は認められず、受理集合と成果物は変わらない。

### 7. `refuted` — `measurement_head` 比較の意味は内部整合に限られる

追加比較は report top-level と receipt で既に一致する head を `launch_admission.binding` にも束縛し、binding だけが別 commit を名乗る receipt を拒否する。[s8c_acceptance_receipt.py:890](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:890) [s8c_acceptance_receipt.py:929](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:929) 一方で ancestor、registry head、実際に走った commit は証明せず無関係な commit 参照を許すが、off はその commit の bytes から再導出されるため誤条件拒否という本レンズでは scope 外判断は誤りではない。[s8c_acceptance_receipt.py:835](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:835)

成果物影響: 条件値と certified 受理集合は変わらないが、レポート・台帳の `measurement_head` 参照は無関係な commit を指しうる。

## 総括

must-fix は重い順に次の 2 件です。

1. `VerifiedAcceptanceReceipt` を gate 外で生成・複製でき、直接 capability を信じる consumer を迂回できる。
2. 正例 fixture が resolver を actual と expected の両方に使い、M1 の比率一点以外の resolver 誤実装を隠す。

nit は次の 2 件です。

1. M2 の key-set gate は固定 hash と正規 loader の下で恒真で、monkeypatch による KILLED は receipt 検出力を示さない。4-key 投影と derangement は source drift gate であって receipt mutation gate ではない。
2. 例外変換が複数原因を同一 gate に潰すが、fail-closed のため成果物値は変えない。

M1 の既存 gate 先行発火、ループ前一回の authority 検査、`measurement_head` の ancestor scope 外判断については、本レンズ上の欠陥を refute します。

pytest を含む動的検査はすべて未実走です。静的検査のみです。