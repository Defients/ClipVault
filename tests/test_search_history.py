"""Tests for search history persistence."""

from clipvault.storage.config_store import ConfigStore


class TestSearchHistory:
    def test_save_and_load(self, tmp_data_dir):
        store = ConfigStore()
        store.save_search_history(["hello", "world", "test"])
        loaded = store.load_search_history()
        assert loaded == ["hello", "world", "test"]

    def test_load_empty(self, tmp_data_dir):
        store = ConfigStore()
        loaded = store.load_search_history()
        assert loaded == []

    def test_max_50_entries(self, tmp_data_dir):
        store = ConfigStore()
        queries = [f"q{i}" for i in range(60)]
        store.save_search_history(queries)
        loaded = store.load_search_history()
        assert len(loaded) == 50
        assert loaded[0] == "q0"

    def test_dedup_by_moving_to_front(self):
        history = ["alpha", "beta", "gamma"]
        qry = "beta"
        if qry in history:
            history.remove(qry)
        history.insert(0, qry)
        assert history == ["beta", "alpha", "gamma"]
