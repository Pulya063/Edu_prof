from alembic.config import Config
from alembic.script import ScriptDirectory


def test_alembic_revision_graph_has_one_head():
    scripts = ScriptDirectory.from_config(Config("alembic.ini"))
    assert len(scripts.get_heads()) == 1
    assert list(scripts.walk_revisions())
