from xlingual_papers_recommender.app import receive_new_paper

from flask import url_for


def test_get_linked_paper(client, db, linked_paper, admin_headers):
    # test 404
    linked_paper_url = url_for(
        'api.linked_paper_by_id', linked_paper_id="100000")
    rep = client.get(linked_paper_url, headers=admin_headers)
    assert rep.status_code == 404

    data = dict(
        network_collection="collection",
        pid="100000", main_lang=None, doi=None, pub_year=None,
        subject_areas=None,
        paper_titles=None,
        abstracts=None,
        keywords=None,
        references=None,
    )
    receive_new_paper(data)

    # test get_linked_paper
    linked_paper_url = url_for(
        'api.linked_paper_by_id', linked_paper_id="100000")
    rep = client.get(linked_paper_url, headers=admin_headers)
    assert rep.status_code == 200

    data = rep.get_json()["linked_paper"]
    assert data["linked_paper"] == "created"


def test_put_linked_paper(client, db, linked_paper, admin_headers):
    # test 404
    linked_paper_url = url_for('api.linked_paper_by_id',
                               linked_paper_id="100000")
    rep = client.put(linked_paper_url, headers=admin_headers)
    assert rep.status_code == 404

    data = dict(
        network_collection="collection",
        pid="100000", main_lang=None, doi=None, pub_year=None,
        subject_areas=None,
        paper_titles=None,
        abstracts=None,
        keywords=None,
        references=None,
    )
    receive_new_paper(data)

    new_data = dict(
        network_collection="collection",
        pid="100000", main_lang=None, doi=None, pub_year=None,
        subject_areas=["Area"],
        paper_titles=None,
        abstracts=None,
        keywords=None,
        references=None,
    )
    linked_paper_url = url_for('api.linked_paper_by_id',
                               linked_paper_id="100000")
    # test update linked_paper
    rep = client.put(linked_paper_url, json=new_data, headers=admin_headers)
    assert rep.status_code == 200

    data = rep.get_json()["linked_paper"]
    assert data["linked_paper"] == "updated"


def test_create_linked_paper(client, db, admin_headers):
    # test bad data
    linked_papers_url = url_for('api.linked_papers')
    data = {"linked_paper": "created"}
    rep = client.post(linked_papers_url, json=data, headers=admin_headers)
    assert rep.status_code == 400

    new_data = dict(
        network_collection="collection",
        pid="100000", main_lang=None, doi=None, pub_year=None,
        subject_areas=["Area"],
        paper_titles=None,
        abstracts=None,
        keywords=None,
        references=None,
    )

    rep = client.post(linked_papers_url, json=new_data, headers=admin_headers)
    assert rep.status_code == 201

    data = rep.get_json()

    assert data["linked_paper"] == "created"
