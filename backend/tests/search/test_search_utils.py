import pytest

from src.settings import ELASTIC_CHATS_INDEX_NAME, ELASTIC_USERS_INDEX_NAME
from src.search.utils import parse_elastic_response

@pytest.mark.parametrize("user_uuid,index,members,expected_is_yours", [
    ("a0c1e4f1-87ca-49fd-8386-a83202cf03fe", ELASTIC_CHATS_INDEX_NAME, ["a0c1e4f1-87ca-49fd-8386-a83202cf03fe"], True),
    ("a0c1e4f1-87ca-49fd-8386-a83202cf03fe", ELASTIC_CHATS_INDEX_NAME, ["other-user"], False),
    ("a0c1e4f1-87ca-49fd-8386-a83202cf03fe", ELASTIC_USERS_INDEX_NAME, [], None),  # not a chat
])
def test_parse_elastic_response_varied_cases(user_uuid, index, members, expected_is_yours):
    response = {
        "hits": {
            "total": {"value": 1},
            "hits": [
                {
                    "_id": "some-id",
                    "_index": index,
                    "_source": {
                        "name": "Example",
                        "members": members
                    }
                }
            ]
        }
    }

    total, items = parse_elastic_response(response, user_uuid)

    assert total == 1
    assert len(items) == 1
    assert items[0]["uuid"] == "some-id"
    assert items[0]["type"] == index

    if expected_is_yours is not None:
        assert items[0]["is_yours"] is expected_is_yours
    else:
        assert "is_yours" not in items[0]

def test_parse_elastic_response_no_user_uuid():
    response = {
        "hits": {
            "total": {"value": 2},
            "hits": [
                {
                    "_id": "1",
                    "_index": ELASTIC_USERS_INDEX_NAME,
                    "_source": {"name": "User A"}
                },
                {
                    "_id": "2",
                    "_index": ELASTIC_CHATS_INDEX_NAME,
                    "_source": {"name": "Chat X", "members": ["user-uuid"]}
                }
            ]
        }
    }

    total, items = parse_elastic_response(response)

    assert total == 2
    assert len(items) == 2
    assert "is_yours" not in items[0]
    assert "is_yours" not in items[1]
