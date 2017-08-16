# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os
import time

import pytest
    
@pytest.fixture(scope="session")
def DB_Session(tmpdir_factory):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from yawxt.persistence import create_all

    engine = create_engine('sqlite:///%s ' % tmpdir_factory.mktemp("data").join("data.db").realpath(), echo=True)
    create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session
    
@pytest.fixture()
def db_session(DB_Session):
    s = DB_Session()
    yield s
    s.close()
    
@pytest.fixture(scope="session", autouse=True)
def location_report(client, DB_Session, xml_builder):
    from yawxt.persistence import PersistMessageHandler
    locations = [(37.2356, 120.001, 40),
                       (38.1478, 118.456, 50),
                       (39.1353, 117.518, 30),]
    location_str = '''<Latitude>%s</Latitude>
<Longitude>%s</Longitude>
<Precision>%s</Precision>'''
    for loc in locations:
        msg_text = xml_builder("event_LOCATION", location_str % loc)
        processor = PersistMessageHandler(msg_text, 
            client, db_session_maker = DB_Session, 
            debug_to_wechat = True)
        processor.reply()
        time.sleep(2)