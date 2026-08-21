"""Tests for the Portkey model catalog."""

from src.providers.portkey_catalog import (
    CATALOG,
    FAMILY_LABELS,
    all_models,
    families,
    find,
    find_any,
    models_for_family,
)


class TestCatalog:
    """Structural integrity checks for CATALOG."""

    def test_slugs_are_unique(self):
        slugs = [spec.slug for spec in CATALOG]
        assert len(slugs) == len(set(slugs))

    def test_every_family_is_labeled(self):
        for spec in CATALOG:
            assert spec.family in FAMILY_LABELS, f"unlabeled family: {spec.family}"

    def test_pricing_has_both_keys_when_present(self):
        for spec in CATALOG:
            if spec.pricing is not None:
                assert "input" in spec.pricing
                assert "output" in spec.pricing

    def test_model_id_combines_route_and_remote_id(self):
        spec = CATALOG[0]
        assert spec.model_id == f"{spec.route}/{spec.remote_id}"

    def test_families_only_lists_nonempty(self):
        for family in families():
            assert len(models_for_family(family)) > 0

    def test_find_returns_none_for_unknown_slug(self):
        assert find("openai", "not-a-real-model") is None

    def test_find_returns_spec_for_known_slug(self):
        spec = find("anthropic", "claude-opus-5")
        assert spec is not None
        assert spec.slug == "claude-opus-5"

    def test_all_models_matches_catalog_size(self):
        assert len(all_models()) == len(CATALOG)

    def test_find_any_is_family_agnostic(self):
        spec = find_any("claude-opus-5")
        assert spec is not None
        assert spec.family == "anthropic"

    def test_find_any_returns_none_for_unknown_slug(self):
        assert find_any("not-a-real-model") is None
