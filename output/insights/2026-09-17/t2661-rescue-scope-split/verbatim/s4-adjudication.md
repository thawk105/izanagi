# 段 4 裁定 — [T-2661] 用途分離 (掃除 = off、救出 triage = full)

作成: 2026-09-17 22:45 JST 頃。入力: 段 1 brief、段 2 plan (`s2-plan.md`)、段 3 レンズ A (`s3-a.md`、luna) / レンズ B (`s3-b.md`、sol)。
main は wave 開始後に `38353207f` → `05eca6af4` (第 21 回裁定 `fd6aea6d1` + fold) へ進んだ。編集面 (2 tool・3 test・command・
check_docs・台帳 doc・runbook) との重なりは無し。

## 0. 段 4 直前の裁定 inbox 再走査 — 新事実

- **D2120 項 24 (T-2661、2026-09-17):** 「掃除では repo 外走査を off、救出 triage では full にする用途分離を採る。付ける条件 5 件は
  2026-09-16 の一次資料 README §5 のとおり。設計と実装は branch で行い、land は通常の受入による。」 — 本 wave の依頼と同内容の
  明示採用。承認前提を覆す事実ではなく、逆に「有効化」から「具体契約の採否」まで裁定済みになった。brief の「確定済みユーザー裁定」へ
  D2120 項 24 を加える。
- **D2120 項 25 (T-2707):** 台帳 doc の `--ledger-check` 説明を現挙動へ限定する別 wave。同じ `docs/unreachable-object-ledger.md` の
  「rescue gate の運用契約」段落を触る予定。本 wave は「dangling audit の分岐」小節だけを書き換え、運用契約の段落 (62〜98) は
  触らない (レンズ A も逐語 pin の保存を要求)。稼働は未確認 (ListAgents に無し)。
- **D2120 項 20 (T-2749):** rescue の予算定数を変える別 wave。`check_branch_rescue.py` 冒頭の定数行で、本 wave の編集行
  (`_child_env` 220、`_audit` 1797〜1843) とは別。
- 裁定 inbox (`rulings-inbox/`) に T-2661 の新規裁定は無し (hit 3 件は 2026-08-05/07 の設計時の控えで、既に D247 等へ着地済み)。

## 1. 所見の裁定 (real / refuted / 採否 / scope)

| ID | 判定 | 採否 | 裁定 |
|---|---|---|---|
| A1 | real | **採用 (must-fix)** | 「full で全対抑止なら台帳 entry 不要」(brief P4、plan §台帳 doc 第 4 段落) は台帳 doc 47〜48 行の追記契約 (`unledgered-audit-finding` を出した object も追記対象、新規 `pending`) と矛盾する。撤回。docs は「off で追記候補集合が増える (従来 full で抑止され通知されなかった object を含む)、状態遷移は既存契約に従う、full の抑止行は §5 報告と当該 entry の判断材料 (`resolution_note`) に残す」とだけ書く。新しい運用例外・通知 kind・field は作らない (scope 外)。 |
| A2 / B1 | real | **採用 (must-fix、凍結前)** | P5 は D958 / D2116 の読替えでは導けない。**本 wave の明示判断として固定する:** 所要受理の対象は掃除入口 (`--offrepo-scan off`) の所要であり、実 repo と走査強制 fixture の両方で D958 項 1 の形 (warm-up 1 走捨て + 独立 3 走、max/min > 1.5 なら +3 走) を取る。off は走査しないので D2116 の「走査を強制した所要」は取れない — これは D2116 を満たしたと記録せず「本 wave の受理対象は掃除入口」と decisions fragment に書く。full (triage) は本 wave で変更せず、所要の再判定も上限達成の主張もしない。full 1 走は「fixture A が off で再表示・full で抑止」の実根デモに限る。D2117 の追補は流用しない。off が上限を超えたらそのまま不合格として記録する (結果を見てから条件を替えない)。 |
| A3 | real / nit | 採用 | I1 の「full は現行と同一出力」を「同じ root を与えた既存経路と findings / suppressions / unreferenced_copies / 非時間依存の報告行が同一」へ限定。full + root 無しの rc 2 と `AuditReport` の新 field は意図した差。 |
| A4 | unknown / nit | 採用 | 「現在 145 本」は親の `scan_overlap.py` (21:5x JST、`git worktree list --porcelain` の worktree 行数) が出所。insight に採取法と時刻を書く。 |
| A5 | unknown / nit | 採用 | 段 1 probe の JSON は rc と要約 hash だけで生 stdout が無い。変更後の実測 (d) では子の stdout (開示行) を捕捉して残す。 |
| A6〜A10 | refuted | 修正不要 | 受理集合不変 (core を返すだけ)、開示の区別、D970 / D1031 の限定、D247 との両立、既存 test の互換は plan の設計で成立。 |
| B2 | unknown / nit | **採用 (変異登録へ反映)** | M1 の killer は API 経路 `audit_with_offrepo(..., offrepo_scan="off", offrepo_roots=(root,))` (非空 roots) で off が roots を無視することを検査する node にする。CLI off は先に roots を空にするので M1 を殺せない。 |
| B3 | unknown / nit | 採用 | P1 の却下理由から「127 test」の数量を外し、「flag 省略の互換契約 (CLI root 優先・env 既定・未指定の開示) を維持する」で説明する。 |
| B4 | real / 意図した残存 | 記録 | flag 省略 + env root は full 相当のまま (第 3 の入口)。固定するのは掃除の規範入口 2 箇所 (command §1、rescue gate の子) であり、任意の ad-hoc 実行の機械封鎖とは報告しない。insight に書く。 |
| B5〜B9 | refuted | 修正不要 | 別 env 経路無し、JSON / rc 契約整合、pin 閉包整合 (文案 6,181 bytes / sha256 `7cc008fa…` は親も独立検算で一致)、p04 は rc 0 維持 + 非空 fixture を別に、T-2639 残骸は着地済み patch と一致。 |

`DW-O13` (gate 新設) の再評価: `full` + root 無しの rc 2 は新設 mode の入力検査 (fail-closed、条件 2) で、成果物 field を述語にする gate ではない。不成立。`DW-O11` (削除) 不成立。`DW-O14` (no-touch への monkeypatch) 不成立 (test の trap は自 tool の関数・`os.walk` 等で、no-touch 対象でない)。

## 2. プラン v2 (段 2 plan を正とし、次を上書き)

### 2.1 `tools/audit_dangling_commits.py`
- `--offrepo-scan {off,full}` (default None、`--offrepo-root` の隣)。省略時は現行維持。off + `--offrepo-root` は `parser.error` (rc 2、usage、elapsed 行なし)。full + root 無し (CLI も env も) は `audit_with_offrepo` 冒頭で `RuntimeError` → 既存の「実行できません」経路 (stderr、stdout に terminal 行 1 本、rc 2)。
- `audit_with_offrepo(..., *, offrepo_scan: str | None = None)`。off は `_validate_offrepo_roots` を呼ばず requested / accepted / rejected を空、core snapshot はそのまま、既存の走査なし返却 (1750〜1764) へ入る。`_load_blob_metadata` / `_enumerate_offrepo_candidates` / cat-file / `os.walk` / `os.scandir` のいずれにも触れない。API で off + 非空 roots は roots を無視する。
- `AuditReport.offrepo_scan: str = "full"` (末尾、既定付き。方針を表し完走の証明ではない。off だけ `"off"`)。
- `main` の root 決定 (2004〜2010) は最初に off を判定して `roots=()`、off では env を読まない。
- `_print_offrepo_report` 先頭に off 専用 1 行 (plan の文案を採用。「探索を未実施」「未指定」の文字列を含まない、「env の指定も無視」「同一実体は未確認」「findings は full なら抑止されうる対を含みうる」「救出 triage は `--offrepo-scan full --offrepo-root <root>` を単独実行」)。既存の「repo 外の同一実体で抑止 0」は維持。

### 2.2 `tools/check_branch_rescue.py`
- `_audit` の子 argv に `"--offrepo-scan", "off"`。`_child_env` の allowlist から `IZANAGI_DEV_WAVE_JOBS_DIR` を除く (`IZANAGI_AUDIT_SCAN_WORKERS` は足さない)。
- summary dict 3 箇所 (timeout / decode 失敗 / 通常) に `"offrepo_scan": "off"`。`_base_payload` の `audit: None` は維持。rc・通知 kind・parser は不変。

### 2.3 `.claude/commands/cleanup-branches.md` §1 (exact、37〜38 行のみ)
```
- `python3 tools/audit_dangling_commits.py --offrepo-scan off` を単独実行
  (パイプ禁止、rc直後保存、F152)。分岐: `docs/unreachable-object-ledger.md`
```
全体 6,181 bytes、sha256 `7cc008fabc10b3b495eedfeb0bfbee2de14a3c908e1eb5aa6dd7ff4d7ebaf8ae`、最長行 105。
`tools/check_docs.py:789` と `test_check_docs.py:581` の digest、`_SYNTHETIC_CLEANUP_COMMAND` の該当 2 行、予算 test の `6_201` → `6_181` (2 箇所) と超過 fixture `"x" * 23` (6,205 bytes 維持) を同時更新。

### 2.4 test (author が書く。node 名は plan の提案を既定とし、変えたら報告)
plan §test の 12 件 (TA 8 + TR 4) + p04 に `offrepo_scan == "off"` と `complete` の assert 追加。B2 のとおり (d) の off 側は API + 非空 roots。既存 test の期待値は変えない (p04 は rc 0 のまま)。

### 2.5 docs (親、段 7)
- 台帳 doc「dangling audit の分岐」: plan の文案から第 4 段落の「台帳 entry は不要」を A1 のとおり撤回し、追記候補集合の増加と既存契約への従属、full の抑止行を判断材料に残すことを書く。D970 / D1031 の射程限定はそのまま。運用契約 (62〜98)・schema・状態遷移の逐語 pin は触らない。
- runbook §7.2: 用途を triage に限定、CLI 例に `--offrepo-scan full`、export 例の説明、864 行の 3 文置換 (plan のとおり)。
- decisions fragment: 本 wave の所要受理対象 (A2/B1) と用途分離の設計判断。worklog fragment。insight README + verbatim + 変異台帳。

### 2.6 段 5 の規模上限
production 差分: ADC ≤ 120 行、CBR ≤ 30 行、check_docs 定数 1 箇所。test 追加 ≤ 450 行 (TA + TR)、TD は定数・synthetic・予算 fixture の該当行のみ。超過は所見が閉じても差し戻す。

## 3. 変異事前登録 (DW-M01、位置と anchor は実装後の最終 commit で凍結、probe 走で観測 node を集めてから本走)

| ID | 対象 | 変異 | 期待 | 専属 killer (候補) |
|---|---|---|---|---|
| M0 | ADC `audit_with_offrepo` docstring | comment だけ変更 | SURVIVED (等価対照) | — |
| M1 | ADC off 分岐 | off でも API roots を検証し通常走査経路へ送る (roots 非空なら走査) | KILLED | `test_explicit_full_suppresses_copy_that_off_reports` (API off + 非空 roots) |
| M2 | ADC `main` root 決定 | off でも env root を読んで roots に入れる | KILLED | `test_explicit_off_ignores_env_and_preserves_core` (env key 読出し trap) |
| M3 | ADC `audit_with_offrepo` 冒頭 | full + roots 空の拒否を削除 | KILLED | `test_explicit_full_without_root_is_execution_failure` |
| M4 | CBR `_audit` argv | `--offrepo-scan off` を落とす | KILLED | `test_audit_child_argv_is_explicit_off` |
| M5 | CBR `_child_env` | `IZANAGI_DEV_WAVE_JOBS_DIR` を allowlist へ戻す | KILLED | `test_child_env_omits_offrepo_root` |
| M6 | ADC `_print_offrepo_report` | off の開示行を従来の未指定 2 行に替える | KILLED | `test_explicit_off_disclosure_is_distinct_from_missing_root` |
| M7 | ADC `main` | off + `--offrepo-root` の usage 拒否を削除 | KILLED | `test_explicit_off_with_cli_root_is_usage_error` |
| M8 | CBR `_audit` summary 3 箇所 | `offrepo_scan` を全部落とす | KILLED | `test_audit_summary_discloses_off_for_all_outcomes` |
| M9 | `tools/check_docs.py` `CLEANUP_COMMAND_SHA256` | 旧値 `a6380f90…` へ戻す | KILLED | `test_check_docs.py` の digest 契約 node |
| M10 | ADC off 分岐 | 早期返却前に `_load_blob_metadata` を呼ぶ | KILLED | `test_explicit_off_touches_no_offrepo_io` |
| M11 | ADC off 分岐 | 早期返却前に `_enumerate_offrepo_candidates` (walk) を呼ぶ | KILLED | 同上 |

- 「`or offrepo_scan == "off"` だけを削る」局所変異は roots 空で既存条件が返すため等価 → 登録しない (plan の指摘)。
- M4 と M5 は結果 (findings) では互いに mask される二重防壁なので、argv / env を直接 assert する node を専属 killer にする。
- 本走の期待 node は probe 走 (全件 SURVIVED 登録) の観測 node を写して完全一致で判定 (DW-M08)。runner は `tools/run_tests.py` に
  `test_audit_dangling_commits.py` `test_check_branch_rescue.py` `test_check_docs.py -k cleanup` を渡す (所要は probe で測る)。
  container worktree (`.codex/worktrees/t2661-mutcontainer`) へ最終 commit を当て、計算ノード dispatch。

## 4. 計測計画 (P5 確定版、親、login node、変更後 tool の絶対 path)
- (a) 実 repo `/work/1/SFC/tanab/izanagi` (`--repo` 明示) に `--offrepo-scan off`: warm-up 1 + 独立 3 走。
- (b) fixture `/work/1/SFC/tanab/t2637-audit-fixture/repo` に off: warm-up 1 + 独立 3 走。
- (c) fixture に `--offrepo-scan full --offrepo-root /work/1/SFC/tanab/dev-wave-jobs`: 1 走 (A が抑止、off で再表示の実根デモ。所要判定に使わない)。
- (d) 変更後 `check_branch_rescue.py --ledger-check` を fixture repo (`--repo`) に env root ありで 1 走: JSON の `offrepo_scan`、rc 3、子の stdout の開示行 (段 1 probe と対にする)。
- 各走の前に `ps -eo pid,args | grep "[a]udit_dangling_commits"` で他走行 0 を確認。stdout / stderr / rc / 開始時刻 / tool sha256 を job dir へ保存。
