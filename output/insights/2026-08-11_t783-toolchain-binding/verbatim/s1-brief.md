# 段 1 brief — [T-783] + [T-747] (B) toolchain 束縛の実装

wave `dev-wave-t783-toolchain-binding` / branch `worktree-dev-wave-t783-toolchain-binding` /
base local main `1f7e156d`。実測はすべて本 worktree (Pegasus **login** node) で親が取得した。

## scope

- **A-1 (実装)**: 床値 build の compiler 解決を site 依存化する ([T-783])。
  `orchestrator/campaign/s8b_floor_campaign.py:1079,1095` の `buildcache.DEFAULT_CC/DEFAULT_CXX`
  固定を `buildcache.compilers_for_current_site()` へ寄せる。
- **A-2 (実装)**: toolchain 束縛検査を **receipt 側** (`acquisition_receipt.toolchain` +
  `acquisition_receipt.ccbench.build_argv`) に対して行う共通 pure helper を新設し、
  floor build 前に fail-closed で発火させる ([T-747] (B))。**混用不可を機械検査で固定する。**
- **A-3 (実装)**: 既存実装 (`silo_ladder_rung1.py:3572-3588`) を同じ helper へ寄せる (S-1 (c))。
- **A-4 (実装)**: attempt 実測値の脚を配線する (S-3 (a))。`tools/pegasus/floor_campaign.sh:773-775`
  が `$ATTEMPT_DIR/{compiler,cxx,cmake}.{path,version}` へ書く値を driver へ渡し、三者照合にする。
- **scope 外**: calibration の再発行 (S-2 (b)/(c))、全 producer への展開 (S-1 (b))、
  official 解禁 (W-1 = [T-781]、裁定で保留終端)、[T-750] (W-3/W-4)。

## 確定済みユーザー裁定 (worklog 412、一次控え rulings-inbox §84)

S-1 = **(c) 共通 pure helper で floor + silo ladder の 2 者を先に寄せる** /
S-2 = **(a) 現行 calibration の範囲。cmake path と cxx version が非束縛であることを明示受諾し
手順書と成果物へ穴を明記する** / S-3 = **(a) shell の `$ATTEMPT_DIR` 値を driver へ渡す** /
S-4 = **(c) 束縛検査は W-1 の実装 wave に含める**。

**S-4 は本 wave の command 引数で上書きされている。** [T-781] (=W-1) は worklog 413 で
「実装なしで保留終端、official は空集合のまま維持」と裁定され、**W-1 の実装 wave は存在しない**。
ユーザーは本 wave で A-1 と A-2 を同時に実装せよと指示した。S-4 (c) の目的
(「解禁したが束縛が入っていない窓」を作らない) は、A-1 と A-2 を**同一 land に含める**ことで満たす。

## 不変条件 (破ったら停止)

1. **A-1 単独 land を禁じる。** A-1 は fail-closed 障壁 (gcc-13 不在で build が倒れる) を外すだけの
   変更であり、A-2 が同じ land に入らなければ「認可外 compiler で床値が通る」窓が開く。
2. `_assert_official_permitted` の official 無条件拒否を 1 bit も緩めない。bypass flag を作らない。
3. calibration JSON (`output/env/pegasus/calibration/registered/*.json`) を編集しない。
   `env_contract` の `CalibrationRef.sha256` と `contract_sha256` golden を変えない。
4. `FROZEN_MANIFEST` の 23 artifact の bytes を変えない (特に `output/s8b-freeze/floor_protocol.json`)。
5. 既存テストの期待値を反転・緩和・skip・削除しない。

## 実測 (親、login node、`probe_toolchain.py`)

- **M-1**: `_assert_official_permitted` (`:207-217`) は `mode=="official"` を無条件 raise。**確認**。
- **M-2**: `assemble_result` (`:2453`) は `eligible_for_refreeze=True` を official 限定。
  `:3174` が `eligible_for_refreeze=(mode=="official")`。**pilot は再凍結に使えない。確認**。
- **M-3**: `floor_campaign.sh:962` は `--mode official` 固定。job-result payload も `"mode":"official"`
  literal。**投入 shell 経路は official 専用 = 現状 dead。確認**。
- **M-4**: driver CLI (`:3514`) は `choices=["pilot","official"]`。**pilot は直接起動でのみ到達可能**。
- **M-5**: login では `which('gcc-13')=None` / `which('g++-13')=None`。
  `compilers_for_current_site()` は login で `('gcc-13','g++-13')`、compute でのみ `('gcc','g++')`。
- **M-6**: `_tool_version('gcc','cc')` の実測 =
  `realpath=/usr/bin/x86_64-linux-gnu-gcc-11`, `version_first_line='x86_64-linux-gnu-gcc-11 (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0'`。
  calibration `toolchain.compiler_version` 先頭行 = `'gcc (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0'`。
  **逐語一致 = False、`tool_version_body` (argv0 除去) 後 = True。** 逐語比較にすると恒真な赤になる。
- **M-7**: receipt の `toolchain` key は exact `['cmake_version','compiler_path','compiler_version','module_list']`。
  `ccbench.build_argv` に `-DCMAKE_C_COMPILER=/usr/bin/x86_64-linux-gnu-gcc-11` と
  `-DCMAKE_CXX_COMPILER=/usr/bin/x86_64-linux-gnu-g++-11`。gen1/gen2 とも同値。
  → **cxx realpath は build_argv からのみ束縛可。cxx version と cmake path は receipt に無い (S-2 の穴)**。
- **M-8 (新事実)**: **login node の cmake は `cmake version 3.22.1`、registered は `3.25.0`。**
  cmake version を束縛すると **login では必ず赤**になる。床値 build は
  `require_heavy_work_site` が login を拒否するので production 影響は無いが、
  **テストと開発機で恒真な赤を作らない設計が必要**。裁定文・worklog に記録なし。

## 既存被覆 (性質で検索し producer / consumer に分類、純増だけを書く)

性質 = 「build に使う実 toolchain が registered calibration の receipt と一致することを検査する」。

- **consumer 1 件のみ**: `silo_ladder_rung1.py:3572-3588`。自分の成果物 (`provenance.tools`) を
  事後検証する。**floor build には効かない**。
- **producer 側は 0 件**: `buildcache.py` は `acquisition_receipt` を 1 度も参照しない (grep 実測)。
  `pegasus_floor_scoping._assert_matches_calibration` が束縛するのは
  records / threads / clocks_per_us だけで toolchain ではない。
- **純増検出力** = 「**build を実行する前に**、実 toolchain が receipt と食い違えば fail-closed で
  止める」。現在この検出力はどの producer にも無い。

## 発火経路 (`DW-G04`)

- **live**: A-3 で helper へ寄せる silo ladder の照合は今日も発火している (既存テストが被覆)。
- **runnable today**: A-2 の gate は `build_cells` にあり、**pilot 床値 campaign
  (`--mode pilot` の直接起動、計算ノード)** で発火する。official 解禁を待たない。
- **dead until W-1**: A-4 の attempt 脚は `floor_campaign.sh` 経由でのみ供給され、
  同 shell は official 固定なので **W-1 が開くまで発火しない**。(P5) で扱う。

## 成果物影響 (`DW-G05`)

- 実装しない場合: 床値 (第 1 世代) は**測れないまま**で、certified 選択の floor 参照は空のまま。
  受理集合は変わらない。
- **A-1 だけ land した場合** (残余 wave が段 4 で気づいた非対称性): 床値 build の受理集合が
  **拡大**し、認可外 compiler (Pegasus の system gcc 11.4.0) で作った binary が
  床値として通るようになる。**この分割 land を不変条件 1 で禁じる。**
- **A-2 だけ land した場合**: 受理集合は変わらない (build は gcc-13 不在で従来どおり倒れる)。安全側。

## provisional 裁定 (親の暫定。攻撃対象)

- **(P1)** helper は新規 module `orchestrator/campaign/toolchain_binding.py` に置き、stdlib のみに
  依存する pure 関数にする。`tool_version_body` は silo ladder から helper へ移し、
  silo ladder は helper を re-export して呼ぶ。
- **(P2)** 束縛する field は S-2 (a) どおり — cc realpath (receipt `compiler_path` **かつ**
  build_argv `-DCMAKE_C_COMPILER`)、cxx realpath (build_argv `-DCMAKE_CXX_COMPILER`)、
  cc version body、cmake version body。**cmake path と cxx version は非束縛**と明記する。
- **(P3)** **M-8 への対処**: cmake version body の比較は「registered と一致」を要求する。
  login で赤になるのは production 経路 (`require_heavy_work_site` が login を拒否) の外なので許容し、
  **テストは実 cmake を読まない注入 seam で書く**。実 cmake を読む test を新設しない。
- **(P4)** gate の位置は `build_cells` の build 直前 (cell ループの外で 1 度)。
  `contract` から calibration を解決し、`buildcache._tool_version` と同じ値の取り方で実測する。
- **(P5)** A-4 の driver flag は `--mode official` で必須、`pilot` で任意にする。
  flag 不在なら二者照合 (authority ↔ 実測) に退行するのではなく、
  **三者のうち attempt 脚だけを省く**明示的な分岐にし、省いた事実を成果物へ記録する。
- **(P6)** 混用不可の機械検査 = 「cc と cxx が同一 toolchain 由来であること」を、
  build_argv の 2 値がいずれも registered と一致することで固定する。
  cc だけ一致・cxx だけ一致は拒否する。

## 並列分割方針 (段 5)

編集ファイル所有が素集合になる 2 単位。

- **単位 A** (`orchestrator/campaign/toolchain_binding.py` 新規 +
  `orchestrator/campaign/silo_ladder_rung1.py` + `orchestrator/tests/test_toolchain_binding.py`):
  helper の抽出と silo ladder の寄せ (A-3、P1)。
- **単位 B** (`orchestrator/campaign/s8b_floor_campaign.py` + `tools/pegasus/floor_campaign.sh` +
  `orchestrator/tests/test_s8b_floor_campaign.py`): floor の site 解決化と gate 結線、attempt 脚
  (A-1 / A-2 / A-4)。

単位 B は単位 A の helper に依存するため、**単位 A を先に完了させ、所有パス限定 patch を
展開してから単位 B を投入する** (`DW-S05-A`)。

## 停止済みの判断 — [T-748] W-2 は本 wave では投入できない

M-1 / M-2 / M-3 が独立に塞いでいる。W-1 ([T-781]) は worklog 413 で保留終端が裁定済みであり、
official は開かない。pilot は `eligible_for_refreeze=False` で再凍結に使えない。
**本 wave はキュー投入を行わず、W-2 は新事実つきでユーザーへ返す** (`DW-S04`)。
