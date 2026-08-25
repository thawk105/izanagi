結論は、既存 provider を無変更で包む B-4 専用 controller を新設し、`p3_s4_loop.py` のアーム切替点や WAL 経路には触れない設計が妥当です。以下は静的検査に基づく実装プランであり、実装・pytest 実走はしていません。

## 1. 変更面

- 新規 production: `orchestrator/campaign/p3_b4_closed_critic.py`
- 新規 test: `orchestrator/tests/test_p3_b4_closed_critic.py`
- 親が更新: [phase3-b4-reflux-ablation-preregistration.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1697-closed-critic/docs/phase3-b4-reflux-ablation-preregistration.md:181)
- 無変更: `p3_s4_loop.py`、`claude_projected_provider.py`、両 critic role、runbook、main experiment、指定された併走 wave 5 file。
- `make_critic_digest` の signature と `reflux=` 切替は [542-572 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1697-closed-critic/orchestrator/campaign/p3_s4_loop.py:542) のまま使う。

## 2. 新規 module の行配置

`orchestrator/campaign/p3_b4_closed_critic.py` の予定配置:

- `1-40`: import、arm 値域、exact payload keys、8c と同型の mediated critic contract。
- `42-70`: 例外型。
- `72-130`: decision、receipt、invocation result の frozen dataclass。
- `132-165`: payload projector と critic response parser。
- `167-205`: campaign identity 非開示検査。
- `207-325`: arm-bound controller。
- `327-355`: on/off receipt の対検査、receipt 永続化。
- `357-370`: `close()` と context-manager support。

[critic.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1697-closed-critic/.claude/agents/critic.md:1) は固定 source とし、`review_ledger.SOURCE_FILE_SHA256["critic"]` との一致も初期化時に検査します。

## 3. 公開 API

```python
def project_b4_critic_payload(
    *, projected_digest: str, whiteboard_entry: WhiteboardEntry
) -> dict[str, str]

def assert_no_campaign_identity(
    payload_bytes: bytes, *,
    campaign_path: Path, campaign_id: str, repository_root: Path
) -> None

def parse_b4_critic_response(raw_response: str) -> B4CriticDecision

class B4ClosedCriticController:
    def __init__(
        self, *, arm: Literal["on", "off"], cfg: CampaignConfig,
        artifact_root: Path, repository_root: Path,
        executable: str | os.PathLike[str] = "claude",
        runner: Callable[..., Any] = subprocess.run,
        environ: Mapping[str, str] | None = None,
    ) -> None
    def invoke(
        self, *, arm: Literal["on", "off"], invocation_id: str
    ) -> B4ClosedCriticInvocation
    def close(self) -> None

def assert_b4_arm_pair(
    on: B4ClosedCriticReceipt, off: B4ClosedCriticReceipt
) -> None
```

- `project_b4_critic_payload` と非開示検査が性質 2 を閉じます。
- controller が tool-less provider を所有して性質 1、生成時 arm 束縛と provider 分離で性質 3 を閉じます。
- receipt と `assert_b4_arm_pair` が 1/2/3 の実測証拠を固定します。
- response parser は 1/2/3 の追加チャネルを作らず、自由文による harness 分岐を防ぐ出力ゲートです。

## 4. controller の処理順

`B4ClosedCriticController.__init__` で次を固定します。

1. `cfg.search_config["reflux"]` と指定 arm の一致を検査する。
2. `ident.campaign_id(cfg)` と `exploration_campaign_layout(campaign_id)` を一度だけ導出する。
3. arm 固有 `controller_id` と artifact subdirectory を生成する。
4. 未改変 `critic.md` と B-4 mediated contract から、新しい `ClaudeProjectedRoleProvider` を1個生成する。
5. runtime tools が `[]`、role hash が ledger pin と一致することを検査する。

`invoke` は campaign view と checkpoint を同じ束縛済み layout から読み、digest を生成し、非開示検査後にだけ provider を呼びます。

## 5. payload の exact schema

Canonical JSON の論理 schema は次の2 keyだけです。

```json
{
  "projected_digest": "string",
  "result": "success|fail|rejected"
}
```

- `projected_digest`: `make_critic_digest(view, reflux=self.arm == "on", identity_projection=...)` の戻り値。
- `result`: `load_loop_state(layout).whiteboard[-1].result`。元の生成点は [project_whiteboard](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1697-closed-critic/orchestrator/campaign/p3_s4_loop.py:577)。
- state 不在、whiteboard 空、末尾 entry の iteration 不一致は invocation 前に拒否する。
- `direction`、`magnitude`、`delta_pct`、variant、records、verdict、policy hint、campaign metadata は載せない。

これは事前登録 §2.1 の共通 coarse outcome と treatment 対象 digest だけを渡し、`run_one_iteration()` が返す raw `digest` や `records` を別チャネルにしないためです。

## 6. campaign identity 非開示述語

検査対象は、provider と同じ `_canonical_json_bytes(payload)` が生成し、そのまま stdin に渡される全 bytes です。

禁止語は次の supervisor-side 実値です。

- `Path(layout.root).resolve()` の絶対 campaign path。
- `str(ident.campaign_id(cfg))`。
- `Path(repository_root).resolve()` の絶対 repository root。

各値について raw UTF-8 bytes と canonical JSON 内での escaped bytes を検索します。空文字、相対 path、空の禁止語集合は検査開始時に拒否します。

違反時は値そのものを表示せず、`B4CampaignDisclosureError("B-4 critic payload contains forbidden campaign_path bytes")` の形で fail-closed にします。

## 7. 非恒真性の正負対

正例は admitted fixture から実際に `make_critic_digest` を on/off 両方で呼び、実 `WhiteboardEntry(result="rejected")` と組み合わせます。

- 3禁止語が全て非空であることを先に assert。
- 実 on digest と実 off digest の canonical payload が非開示検査を通ることを assert。
- off payload に coarse `result="rejected"` は残る一方、赤詳細は無いことを assert。

負例では各禁止語の実値を1つずつ `projected_digest` に混入し、canonical 化後に対応する例外で落とします。したがって、空集合の件数確認だけで緑になる検査ではありません。

## 8. arm 束縛

arm は controller の生成時に固定し、digest の `reflux` 引数は controller 内部だけで導出します。呼び手は digest や reflux を直接渡せません。

拒否する操作:

- on cfg と `arm="off"` の組合せ。
- on controller に対する `invoke(arm="off", ...)`。
- close 後の invoke。
- on/off receipt で同一 controller ID、同一 session ID、同一 campaign ID を観測すること。

代表的な例外は `B4ArmBindingError("B-4 critic controller is bound to arm='on'; requested arm='off'")`。正例は `default_cfg(reflux=True)` から作った on controller への `invoke(arm="on", ...)` です。

## 9. fresh controller の実体

on/off ごとに別の `ClaudeProjectedRoleProvider`、別 controller ID、別 artifact directory、別 neutral root を持たせます。

既存 provider は [101-241 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1697-closed-critic/orchestrator/campaign/claude_projected_provider.py:101) で inline `tools=[]`、空 MCP、neutral cwd、`--no-session-persistence` を構成します。

[259-381 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1697-closed-critic/orchestrator/campaign/claude_projected_provider.py:259) の session 重複、permission denial、server tool use 検査をそのまま再利用します。provider 自体を変更する必要はありません。

## 10. receipt fields

`B4ClosedCriticReceipt` は次を持ち、canonical JSON で `receipt_<invocation_id>.json` に保存します。

- `schema_version`, `arm`, `campaign_id`, `controller_id`, `invocation_id`, `session_id`
- `provider_kind`, `model_snapshot`, `claude_executable_sha256`
- `role_file_sha256`, `effective_prompt_sha256`, `projection_sha256`
- `digest_sha256`, `payload_sha256`
- `fresh_context`, `capability_lowering`
- `source_declared_tools`, `declared_tools`, `observed_tool_events`
- `permission_denials_empty`, `server_tool_use_all_zero`
- `campaign_identity_absence_checked`

`projection_sha256` は payload schema、非開示述語、controller を含む新規 module 全 bytes の hash とし、arm 固有 payload hashとは分けます。

## 11. prereg 欄との対応

- §5 model snapshot: `model_snapshot` と `claude_executable_sha256`。
- §5 prompt hash: provider 由来 `effective_prompt_sha256`。
- §5 projection hash: `projection_sha256`。on/off 同一 checkout なら一致必須。
- 性質 1: `declared_tools=[]`、`observed_tool_events=[]`、`server_tool_use_all_zero=true`。
- 性質 2: `campaign_identity_absence_checked=true` と `payload_sha256`。
- 性質 3: `arm`、異なる `controller_id`、異なる `session_id`、`fresh_context=true`。
- treatment 束縛: `arm` と `digest_sha256`。実 payload 固有値は `payload_sha256`。

`assert_b4_arm_pair` は model、role、prompt、projection hash の一致と、campaign/controller/session ID の相違を同時に検査します。

## 12. 新規 test 前半

prefix は `orchestrator/tests/test_p3_b4_closed_critic.py` です。

- `::test_payload_exact_schema_from_real_digest_and_whiteboard_result`
- `::test_identity_gate_accepts_real_on_and_off_digest`
- `::test_identity_gate_rejects_injected_campaign_path`
- `::test_identity_gate_rejects_injected_campaign_id`
- `::test_identity_gate_rejects_injected_repository_root`
- `::test_controller_accepts_matching_arm_with_toolless_fresh_context`
- `::test_controller_rejects_cross_arm_reuse_before_read_or_cli`

予定行は helper・fake CLI が `1-90`、payload と非開示正負対が `92-185`、arm 正負対が `187-245` です。

## 13. 新規 test 後半

- `::test_controller_rejects_nonempty_runtime_declared_tools`
- `::test_arm_pair_uses_distinct_controller_context_and_session`
- `::test_arm_pair_rejects_reused_controller_or_session`
- `::test_receipt_binds_role_prompt_projection_payload_and_digest_hashes`
- `::test_off_invocation_preserves_red_wal_and_projects_only_coarse_result`
- `::test_critic_response_accepts_exact_schema_without_prose_branch`
- `::test_critic_response_rejects_extra_or_wrong_typed_keys`

全 test を引数なし関数にし、`tempfile` と `unittest.mock` を使います。`350-363` に [既存末尾](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1697-closed-critic/orchestrator/tests/test_p3_s4_loop.py:3831) と同じ sorted-globals 自走 harness を置きます。

## 14. 焦点走の参照閉包

変更 production を直接 import する consumer は、新規 test の次の明示 importで生じます。

```python
from orchestrator.campaign import p3_b4_closed_critic as C
```

したがって production 変更に対する直接 consumer test は `test_p3_b4_closed_critic.py` 全体です。加えて、新 module が依存する digest 契約の既存3 nodeidを上流契約試験として焦点走へ含めます。

- `test_p3_s4_loop.py::test_make_critic_digest_reflux_off_drops_red_section`
- `test_p3_s4_loop.py::test_make_critic_digest_reflux_off_skips_all_structured_anomaly_loaders`
- `test_p3_s4_loop.py::test_make_critic_digest_reflux_off_is_byte_identical_to_green_only`

`p3_s4_loop.py` と provider は変更しないため、それらの全 consumer を「変更 production の consumer」と偽って広げません。

## 15. prereg 文書更新

[§6.3 181-184 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1697-closed-critic/docs/phase3-b4-reflux-ablation-preregistration.md:181) は「receipt 付き専用 controller が利用可能」に更新します。ただし発効宣言はしません。

[§7.2 220-224 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1697-closed-critic/docs/phase3-b4-reflux-ablation-preregistration.md:220) は、専用 route 内で閉じた Bash/digest CLI と、依然開く API return/policy hint を分離します。

[§8 242-248 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1697-closed-critic/docs/phase3-b4-reflux-ablation-preregistration.md:242) は、既存 T1-T5 単独では能力遮断を証明しないが、新 test と receipt が別途固定する、と限定します。

[§10 271-278 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1697-closed-critic/docs/phase3-b4-reflux-ablation-preregistration.md:271) から閉じた invocation と role-facing coarse projection だけを外し、他項目は残します。

## 16. この実装が閉じないもの

閉じるのは、新 controller 経由の critic に限った tools、stdin payload、controller/context/session 分離です。

閉じないもの:

- 現行 runbook の `Agent(subagent_type='critic')` 経路。B-4 標本として不適格なままです。
- Python caller が `run_one_iteration()` の `digest` や `records` を読む経路。
- `policy_hint`、`prior_critic_reverse` の供給・receipt 束縛。
- file-drawer、append-only registry、全件完全性 consumer。
- 別 root、直接注入 layout、誤った `--campaign-dir` を使う外部 controller。
- `build_digest()` の別経路変異と、他 campaign module に reflux 分岐を足す生存変異。
- provider が列挙する neutral cwd/MCP transport metadata の role 不可視性そのもの。
- 第3 arm、新架構、実走、floor、数値欄、他の §6 前提条件。

## 17. 静的検査状態

指定された射影対象だけを読み、既存 signature、digest 書き出し点、provider postcondition、負の対照、自走 harness を確認しました。

ファイル変更、pytest、CLI invocation は実施していません。したがって test 結果は全て「未実走」であり、緑とは報告しません。

## 総括

骨子は、arm と ID 由来 layout を生成時に束縛した専用 controller が、既存 `make_critic_digest(reflux=)` と最新 `whiteboard.result` だけを exact 2-key payload に射影し、canonical stdin bytes の秘密語検査後に既存 tool-less provider を呼ぶ形です。on/off の controller、provider、context、session は分離し、receipt で model・prompt・projection・digest・role・tool 状態を結びます。

最大の未解決点は、この module が存在しても旧 `Agent(critic)` や Python API 直読みを全域では禁止できないことです。B-4 の採用条件を「本 controller の有効 receipt がある標本だけ」に限定する文書・運用ゲートが引き続き load-bearing です。