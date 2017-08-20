# -*- coding:utf-8 -*-
import requests
import pytest

from yawxt import (
    APIError, MaxQuotaError, SemanticAPIError,
    SystemAPIError, ChangeIndustryError)


def test_exception(client, openid, monkeypatch):

    result = {"errcode": 45001}
    def mock_api_return(resp):
        return result

    monkeypatch.setattr(requests.Response, "json", mock_api_return)

    with pytest.raises(APIError):
        user = client.get_user(openid)

    result = {"errcode": 45009, "errmsg": "reach max api daily quota limit"}
    with pytest.raises(MaxQuotaError):
        user = client.get_user(openid)

    result = {
        "errcode": 43100,
        "errmsg": "industry can be set once per month"}
    with pytest.raises(ChangeIndustryError) as e:
        user = client.get_user(openid)
        assert e.value.errmsg == result["query"]

    query = "天津静海区天气怎么样？"
    result = {
        "errcode": 7000030,
        "query": query
    }
    with pytest.raises(SemanticAPIError) as e:
        client.semantic_parse(query, city="天津")
        assert e.value.errmsg == query

    result = {
        'errcode': -1,
        'errmsg': 'system error hint: [Qy4FvA0642vr24]'}
    with pytest.raises(SystemAPIError):
        user = client.get_user(openid)
