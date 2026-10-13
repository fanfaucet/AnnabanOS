import unittest

from model_providers.actor_registry import ActorProviderRegistry
from model_providers.actor_schemas import Actor, InputCreate, ProviderRecord, RoleBindingUpdate


class ActorProviderTests(unittest.TestCase):
    def setUp(self):
        self.registry = ActorProviderRegistry()
        self.registry.register(ProviderRecord(
            provider_id="alice",
            kind="human",
            current_dba="Alice Chen (DBA)",
            capabilities=["database-review"],
        ))
        self.registry.register(ProviderRecord(
            provider_id="openai:gpt-4o",
            kind="model",
            current_dba="OpenAI GPT-4o",
            capabilities=["database-review"],
            model_meta={"context_window": 128000, "temperature": 0.2},
        ))

    def test_role_binding_can_swap_provider_without_changing_role(self):
        self.registry.bind_role("database-expert", RoleBindingUpdate(
            provider_id="alice", dba="Alice Chen (DBA)"
        ))
        human_actor = self.registry.resolve_actor("database-expert")
        self.registry.bind_role("database-expert", RoleBindingUpdate(
            provider_id="openai:gpt-4o", dba="OpenAI GPT-4o (acting as DBA)"
        ))
        model_actor = self.registry.resolve_actor("database-expert")
        self.assertEqual(human_actor.role, model_actor.role)
        self.assertEqual(human_actor.provider.id, "alice")
        self.assertEqual(model_actor.provider.id, "openai:gpt-4o")
        self.assertEqual(model_actor.provider.kind, "model")

    def test_provider_id_cannot_change_kind(self):
        with self.assertRaises(ValueError):
            self.registry.register(ProviderRecord(
                provider_id="alice", kind="model", current_dba="Renamed Alice"
            ))

    def test_model_metadata_rejected_for_non_model(self):
        with self.assertRaises(ValueError):
            Actor.model_validate({
                "role": "database-expert",
                "provider": {
                    "kind": "human",
                    "id": "alice",
                    "model_meta": {"context_window": 128000}
                }
            })

    def test_actor_snapshot_contract_accepts_parent_link(self):
        request = InputCreate.model_validate({
            "content": "Replica lag detected.",
            "actor": {
                "role": "database-expert",
                "provider": {"kind": "model", "id": "openai:gpt-4o",
                             "model_meta": {"context_window": 128000, "temperature": 0.2}},
                "dba": "OpenAI GPT-4o (acting as DBA)"
            },
            "context": {"severity": "high"},
            "parent_id": "inp_parent"
        })
        snapshot = request.actor.model_copy(deep=True)
        self.assertEqual(snapshot.role, "database-expert")
        self.assertEqual(request.parent_id, "inp_parent")
        self.assertEqual(snapshot.provider.id, "openai:gpt-4o")


if __name__ == "__main__":
    unittest.main()
